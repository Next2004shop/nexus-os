"""
NEXUS Command Layer — Router
===============================

The single point of command processing.

Flow:
1. Validate command via validator
2. If invalid → return error JSON, log via audit
3. If valid → pass to execution engine (placeholder), log via audit
4. All commands are audited regardless of outcome

ARCHITECTURE LAW:
- AI NEVER executes trades directly.
- All trades go through this router.
- No direct MetaTrader call allowed outside execution engine.
"""

import logging
from typing import Any, Dict

from command.schema import TradeCommand
from command.validator import validate_command
from command.audit import log_command

logger = logging.getLogger("nexus.command.router")


def route_command(command: TradeCommand) -> Dict[str, Any]:
    """
    Process a TradeCommand through the full pipeline.
    
    Flow:
    1. Validate → reject if invalid
    2. Execute (placeholder) → if valid
    3. Audit → always
    
    Args:
        command: Validated TradeCommand instance
    
    Returns:
        Result dict with status, errors, and execution data
    """
    command_dict = command.model_dump(mode="json")

    # =========================================================================
    # STEP 1: VALIDATE
    # =========================================================================
    validation = validate_command(command)

    if not validation["valid"]:
        logger.warning(
            f"COMMAND REJECTED: {command.asset} {command.direction} "
            f"{command.lot_size} — {validation['errors']}"
        )

        # Audit the rejection
        log_command(
            command=command_dict,
            validation_status="INVALID",
            execution_status="BLOCKED"
        )

        return {
            "status": "REJECTED",
            "valid": False,
            "errors": validation["errors"],
            "command": command_dict
        }

    # =========================================================================
    # STEP 2: EXECUTE (placeholder — routes to execution engine)
    # =========================================================================
    logger.info(
        f"COMMAND APPROVED: {command.direction.upper()} {command.lot_size} "
        f"{command.asset} from {command.source}"
    )

    try:
        # ---------------------------------------------------------------
        # PLACEHOLDER: This is where the execution engine call goes.
        # In production, this calls:
        #   execution.get_engine().execute_trade(
        #       symbol=command.asset,
        #       side=command.direction.upper(),
        #       quantity=command.lot_size
        #   )
        #
        # For now, return a structured acknowledgment.
        # ---------------------------------------------------------------
        execution_result = {
            "status": "PENDING",
            "message": f"Command queued: {command.direction.upper()} "
                       f"{command.lot_size} {command.asset}",
            "order_id": None,
            "routed_to": "execution_engine"
        }

        # Audit the approval
        log_command(
            command=command_dict,
            validation_status="VALID",
            execution_status="PENDING"
        )

        return {
            "status": "APPROVED",
            "valid": True,
            "errors": [],
            "command": command_dict,
            "execution": execution_result
        }

    except Exception as e:
        logger.error(f"Execution routing failed: {e}")

        log_command(
            command=command_dict,
            validation_status="VALID",
            execution_status="FAILED"
        )

        return {
            "status": "ERROR",
            "valid": True,
            "errors": [f"Execution failed: {str(e)}"],
            "command": command_dict
        }
