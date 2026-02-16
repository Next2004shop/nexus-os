"""
NEXUS Command API Routes
==========================

Two-step execution flow:
    POST /api/command/parse   — NL text → structured intent (preview)
    POST /api/command/execute — confirmed intent → validate → route → audit

NO auto-execution. User MUST confirm the preview before execution proceeds.

Security:
    - All endpoints require valid JWT (enforced by AuthMiddleware)
    - System mode check (reject if halted)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.intent_interpreter import get_interpreter
from command.schema import TradeCommand
from command.validator import validate_command
from command.router import route_command
from command.audit import log_command

logger = logging.getLogger("nexus.command.api")

router = APIRouter(prefix="/api/command", tags=["Command Layer"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class ExecuteRequest(BaseModel):
    asset: str
    direction: str
    volume: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    source: str = "manual"


# =============================================================================
# POST /api/command/parse
# =============================================================================

@router.post("/parse")
async def parse_command(req: ParseRequest, request: Request):
    """
    Parse natural language command into structured intent.

    Input:  {"text": "Buy gold 0.01 lot SL 20 TP 40"}
    Output: Structured intent JSON with requires_confirmation: true

    Does NOT execute. Returns preview only.
    """
    user_id = getattr(request.state, "user_id", "unknown")
    username = getattr(request.state, "username", "unknown")

    logger.info(f"PARSE [{username}]: {req.text}")

    try:
        interpreter = get_interpreter()
        intent = interpreter.interpret(text=req.text, user_id=user_id)
        intent_dict = intent.to_dict()

        # Map intent fields to API response
        response = {
            "intent": intent_dict.get("intent", "unknown"),
            "asset": intent_dict.get("asset"),
            "direction": intent_dict.get("direction"),
            "volume": intent_dict.get("lot_size"),
            "sl": intent_dict.get("stop_loss"),
            "tp": intent_dict.get("take_profit"),
            "confidence": intent_dict.get("confidence", 0),
            "reasoning": intent_dict.get("reasoning", ""),
            "requires_confirmation": True,
            "error": intent_dict.get("error"),
        }

        # Log the parse action
        log_command(
            command={
                "raw_text": req.text,
                "parsed_intent": response,
                "user_id": user_id,
                "username": username,
            },
            validation_status="PARSED",
            execution_status="AWAITING_CONFIRMATION"
        )

        if response["error"]:
            return JSONResponse(
                status_code=400,
                content={"error": response["error"], "intent": response}
            )

        return response

    except Exception as e:
        logger.error(f"Parse failed: {e}", exc_info=True)

        log_command(
            command={"raw_text": req.text, "user_id": user_id, "error": str(e)},
            validation_status="ERROR",
            execution_status="BLOCKED"
        )

        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to parse command: {str(e)}"}
        )


# =============================================================================
# POST /api/command/execute
# =============================================================================

@router.post("/execute")
async def execute_command(req: ExecuteRequest, request: Request):
    """
    Execute a confirmed trade intent through command pipeline.

    Flow:
    1. Build TradeCommand from validated intent
    2. Validate via command.validator
    3. Route via command.router (→ execution engine)
    4. Audit everything

    Does NOT bypass risk engine or execution authority.
    """
    user_id = getattr(request.state, "user_id", "unknown")
    username = getattr(request.state, "username", "unknown")

    logger.info(
        f"EXECUTE [{username}]: {req.direction} {req.asset} "
        f"vol={req.volume} sl={req.sl} tp={req.tp}"
    )

    try:
        # Build strict TradeCommand from confirmed intent
        command = TradeCommand(
            asset=req.asset,
            direction=req.direction.lower(),
            lot_size=req.volume,
            stop_loss=req.sl,
            take_profit=req.tp,
            source=req.source,
        )

        # Route through full pipeline (validate → execute → audit)
        result = route_command(command)

        # Enrich audit with user info
        log_command(
            command={
                **command.model_dump(mode="json"),
                "user_id": user_id,
                "username": username,
                "confirmed_by": username,
            },
            validation_status=result.get("status", "UNKNOWN"),
            execution_status=result.get("execution", {}).get("status", result.get("status", "UNKNOWN"))
        )

        if result["status"] == "REJECTED":
            return JSONResponse(
                status_code=422,
                content={
                    "status": "REJECTED",
                    "errors": result["errors"],
                    "command": result["command"]
                }
            )

        return {
            "status": result["status"],
            "command": result["command"],
            "execution": result.get("execution"),
            "errors": result.get("errors", [])
        }

    except ValueError as e:
        logger.warning(f"Invalid command: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid command: {str(e)}"}
        )

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)

        log_command(
            command={
                "asset": req.asset,
                "direction": req.direction,
                "volume": req.volume,
                "user_id": user_id,
                "error": str(e),
            },
            validation_status="ERROR",
            execution_status="FAILED"
        )

        return JSONResponse(
            status_code=500,
            content={"error": f"Execution failed: {str(e)}"}
        )
