"""REST API endpoints for LLM Debate."""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class DebateConfig(BaseModel):
    """Configuration for starting a debate."""
    topic: str = Field(..., min_length=1, description="The debate topic")
    mode: str = Field("collaborative", description="Debate mode")
    max_rounds: int = Field(5, ge=1, le=50, description="Maximum rounds")
    timeout: int = Field(120, ge=30, le=600, description="Timeout per round")
    convergence_threshold: float = Field(0.85, ge=0.0, le=1.0)
    enable_convergence: bool = Field(True)
    enable_actions: bool = Field(False, description="Enable action mode")
    output_handlers: List[str] = Field(default=["stream"])


class DebateResponse(BaseModel):
    """Response when starting a debate."""
    debate_id: str
    status: str
    message: str


class DebateStatus(BaseModel):
    """Status of a debate."""
    debate_id: str
    status: str  # "running", "completed", "failed"
    current_round: int
    total_rounds: int
    converged: bool = False
    convergence_reason: Optional[str] = None


class DebateHistory(BaseModel):
    """Historical debate record."""
    debate_id: str
    topic: str
    mode: str
    rounds: int
    converged: bool
    timestamp: str


# In-memory storage (replace with database in production)
active_debates = {}
debate_history = []


@router.post("/debates/start", response_model=DebateResponse)
async def start_debate(config: DebateConfig):
    """
    Start a new debate.

    Args:
        config: Debate configuration

    Returns:
        DebateResponse with debate ID
    """
    try:
        import uuid
        debate_id = str(uuid.uuid4())

        # Validate mode
        valid_modes = ["adversarial", "collaborative", "devils_advocate"]
        if config.mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode. Must be one of: {valid_modes}"
            )

        # Store debate configuration
        active_debates[debate_id] = {
            "config": config.dict(),
            "status": "pending",
            "current_round": 0
        }

        logger.info(f"Created debate {debate_id} with topic: {config.topic}")

        return DebateResponse(
            debate_id=debate_id,
            status="created",
            message=f"Debate created successfully. Connect to WebSocket to start."
        )

    except Exception as e:
        logger.error(f"Failed to create debate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debates/{debate_id}/status", response_model=DebateStatus)
async def get_debate_status(debate_id: str):
    """
    Get status of a debate.

    Args:
        debate_id: Debate identifier

    Returns:
        DebateStatus
    """
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")

    debate = active_debates[debate_id]
    return DebateStatus(
        debate_id=debate_id,
        status=debate["status"],
        current_round=debate.get("current_round", 0),
        total_rounds=debate["config"]["max_rounds"],
        converged=debate.get("converged", False),
        convergence_reason=debate.get("convergence_reason")
    )


@router.delete("/debates/{debate_id}")
async def stop_debate(debate_id: str):
    """
    Stop a running debate.

    Args:
        debate_id: Debate identifier

    Returns:
        Success message
    """
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")

    # Mark debate as stopped
    active_debates[debate_id]["status"] = "stopped"

    logger.info(f"Stopped debate {debate_id}")

    return {"message": "Debate stopped successfully"}


@router.get("/debates/history", response_model=List[DebateHistory])
async def get_debate_history(limit: int = 10):
    """
    Get debate history.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of debate history records
    """
    return debate_history[-limit:]


@router.get("/config/modes")
async def get_available_modes():
    """Get available debate modes with descriptions."""
    return {
        "modes": [
            {
                "id": "adversarial",
                "name": "Adversarial",
                "description": "Claude argues FOR, Codex argues AGAINST the proposition"
            },
            {
                "id": "collaborative",
                "name": "Collaborative",
                "description": "Both CLIs work together to explore the topic"
            },
            {
                "id": "devils_advocate",
                "name": "Devil's Advocate",
                "description": "Claude proposes ideas, Codex critiques them"
            }
        ]
    }


@router.get("/config/defaults")
async def get_default_config():
    """Get default debate configuration."""
    return {
        "mode": "collaborative",
        "max_rounds": 5,
        "timeout": 120,
        "convergence_threshold": 0.85,
        "enable_convergence": True,
        "enable_actions": False
    }
