"""WebSocket handler for real-time debate streaming."""

import asyncio
import logging
import json
import os
from typing import Dict
from pathlib import Path
from fastapi import WebSocket

# Import from main package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_debate.config import DebateConfig
from llm_debate.orchestrator import DebateOrchestrator, Turn, DebateResult

logger = logging.getLogger(__name__)


class WebSocketOutputHandler:
    """Output handler that streams to WebSocket."""

    def __init__(self, websocket: WebSocket, client_id: str, loop: asyncio.AbstractEventLoop):
        self.websocket = websocket
        self.client_id = client_id
        self.loop = loop  # Store event loop for cross-thread async calls

    async def send_event(self, event_type: str, data: dict):
        """Send an event to the WebSocket client."""
        try:
            await self.websocket.send_json({
                "type": event_type,
                "data": data
            })
        except Exception as e:
            logger.error(f"Failed to send WebSocket message to {self.client_id}: {e}")

    def on_debate_start(self, config):
        """Called when debate starts (from thread pool)."""
        asyncio.run_coroutine_threadsafe(
            self.send_event("debate_start", {
                "topic": config.topic,
                "mode": config.mode,
                "max_rounds": config.max_rounds,
                "convergence_enabled": config.enable_convergence
            }),
            self.loop
        )

    def on_turn_start(self, turn: Turn):
        """Called when a turn starts (from thread pool)."""
        asyncio.run_coroutine_threadsafe(
            self.send_event("turn_start", {
                "round": turn.round_number,
                "cli": turn.cli_name,
                "timestamp": turn.timestamp.isoformat()
            }),
            self.loop
        )

    def on_turn_complete(self, turn: Turn):
        """Called when a turn completes (from thread pool)."""
        asyncio.run_coroutine_threadsafe(
            self.send_event("turn_complete", {
                "round": turn.round_number,
                "cli": turn.cli_name,
                "response": turn.response,
                "execution_time": turn.execution_time,
                "success": turn.success,
                "timestamp": turn.timestamp.isoformat(),
                "actions": getattr(turn, 'actions', [])  # For action mode
            }),
            self.loop
        )

    def on_debate_complete(self, result: DebateResult):
        """Called when debate completes (from thread pool)."""
        asyncio.run_coroutine_threadsafe(
            self.send_event("debate_complete", {
                "total_rounds": result.total_rounds,
                "converged": result.converged,
                "convergence_reason": result.convergence_reason,
                "end_reason": result.end_reason
            }),
            self.loop
        )


class WebSocketDebateHandler:
    """Manages WebSocket connections and debate execution."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.running_debates: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {"client_id": client_id, "message": "Connected to LLM Debate server"}
        })

    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Cancel any running debate for this client
        if client_id in self.running_debates:
            self.running_debates[client_id].cancel()
            del self.running_debates[client_id]

        logger.info(f"Client {client_id} disconnected")

    async def handle_message(self, client_id: str, data: dict):
        """
        Handle incoming WebSocket messages.

        Args:
            client_id: Client identifier
            data: Message data
        """
        message_type = data.get("type")

        if message_type == "start_debate":
            await self.start_debate(client_id, data.get("config", {}))

        elif message_type == "stop_debate":
            await self.stop_debate(client_id)

        elif message_type == "ping":
            await self.send_to_client(client_id, {"type": "pong"})

        else:
            logger.warning(f"Unknown message type from {client_id}: {message_type}")

    async def start_debate(self, client_id: str, config_data: dict):
        """
        Start a debate for a client.

        Args:
            client_id: Client identifier
            config_data: Debate configuration dictionary
        """
        websocket = self.active_connections.get(client_id)
        if not websocket:
            logger.error(f"No WebSocket connection for client {client_id}")
            return

        try:
            # Create debate configuration
            # Use environment variables for CLI paths if set (for Docker)
            claude_bin = os.getenv("CLAUDE_BIN", "/home/jolomoadmin/.local/bin/claude")
            codex_bin = os.getenv("CODEX_BIN", "/home/jolomoadmin/.npm-global/bin/codex")

            config = DebateConfig(
                topic=config_data.get("topic", ""),
                mode=config_data.get("mode", "collaborative"),
                max_rounds=config_data.get("max_rounds", 5),
                timeout_per_round=config_data.get("timeout", 120),
                convergence_threshold=config_data.get("convergence_threshold", 0.85),
                enable_convergence=config_data.get("enable_convergence", True),
                enable_actions=config_data.get("enable_actions", False),
                output_handlers=["stream"],  # Not used here, we have custom handler
                # CLI paths (use env vars for Docker, defaults for local)
                claude_bin=claude_bin,
                codex_bin=codex_bin,
                # PR context settings
                pr_number=config_data.get("pr_number"),
                pr_repo=config_data.get("pr_repo"),
                pr_checkout=config_data.get("pr_checkout", False),
                gh_bin=config_data.get("gh_bin", "gh")
            )

            # Create orchestrator
            orchestrator = DebateOrchestrator(config)

            # Add WebSocket output handler with event loop for cross-thread async calls
            loop = asyncio.get_running_loop()
            ws_handler = WebSocketOutputHandler(websocket, client_id, loop)
            orchestrator.add_output_handler(ws_handler)

            # Run debate in background task
            task = asyncio.create_task(self._run_debate(client_id, orchestrator))
            self.running_debates[client_id] = task

            logger.info(f"Started debate for client {client_id}: {config.topic}")

        except Exception as e:
            logger.error(f"Failed to start debate for {client_id}: {e}")
            await self.send_to_client(client_id, {
                "type": "error",
                "data": {"message": f"Failed to start debate: {str(e)}"}
            })

    async def _run_debate(self, client_id: str, orchestrator: DebateOrchestrator):
        """
        Run a debate in the background.

        Args:
            client_id: Client identifier
            orchestrator: Debate orchestrator
        """
        try:
            # Run debate in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, orchestrator.run_debate)

            logger.info(f"Debate completed for client {client_id}: {result.end_reason}")

        except asyncio.CancelledError:
            logger.info(f"Debate cancelled for client {client_id}")
        except Exception as e:
            logger.error(f"Debate failed for client {client_id}: {e}")
            await self.send_to_client(client_id, {
                "type": "error",
                "data": {"message": f"Debate failed: {str(e)}"}
            })
        finally:
            if client_id in self.running_debates:
                del self.running_debates[client_id]

    async def stop_debate(self, client_id: str):
        """
        Stop a running debate.

        Args:
            client_id: Client identifier
        """
        if client_id in self.running_debates:
            self.running_debates[client_id].cancel()
            await self.send_to_client(client_id, {
                "type": "debate_stopped",
                "data": {"message": "Debate stopped by user"}
            })
            logger.info(f"Stopped debate for client {client_id}")

    async def send_to_client(self, client_id: str, message: dict):
        """
        Send a message to a specific client.

        Args:
            client_id: Client identifier
            message: Message to send
        """
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
        """
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
