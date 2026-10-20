"""Read-only battle stage endpoints shared by every role."""

from flask import Blueprint, current_app, jsonify

from security import current_user, require_roles
from stage_service import load_stages

stages_bp = Blueprint("stages", __name__, url_prefix="/api/stages")


def _without_answers(stage: dict) -> dict:
    """Hide which cards are correct from students."""
    hands = {
        key: [{name: value for name, value in card.items() if name != "correct_choice"} for card in stage[key]]
        for key in ("turn_1_hand", "turn_2_hand")
    }
    return {**stage, **hands}


@stages_bp.get("")
@require_roles("admin", "instructor", "student")
def list_stages():
    """Return every floor in order, hiding card answers from students."""
    try:
        stages = load_stages()
    except ValueError:
        current_app.logger.exception("Battle stage files are invalid.")
        return jsonify(error="Battle stages are unavailable."), 500
    if current_user().role == "student":
        stages = [_without_answers(stage) for stage in stages]
    return jsonify(stages=stages)
