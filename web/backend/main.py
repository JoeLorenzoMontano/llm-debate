"""FastAPI backend for LLM Debate web UI."""

import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .ws import WebSocketDebateHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Debate Web UI",
    description="Real-time debates between LLM CLIs",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static frontend files
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# WebSocket connection manager
ws_handler = WebSocketDebateHandler()


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    html_file = frontend_dir / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    return HTMLResponse("<h1>LLM Debate UI</h1><p>Frontend not found</p>")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time debate streaming.

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await ws_handler.connect(websocket, client_id)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            await ws_handler.handle_message(client_id, data)
    except WebSocketDisconnect:
        await ws_handler.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await ws_handler.disconnect(client_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "llm-debate-web"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
