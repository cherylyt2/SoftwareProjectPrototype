"""Self-directed learning path endpoints for students."""

from flask import Blueprint, jsonify

from database import db
from models import LearningPath
from schemas import LearningPathCreateRequest
from security import current_user, require_roles
from auth_routes import parse_payload

learning_paths_bp = Blueprint("learning_paths", __name__, url_prefix="/api/learning-paths")


def learning_path_payload(path: LearningPath) -> dict:
    """Serialize a learning path owned by the current student."""
    return {
        "id": path.id,
        "title": path.title,
        "topics": path.topics,
        "steps": path.steps,
        "created_at": path.created_at.isoformat() if path.created_at else None,
    }


@learning_paths_bp.get("")
@require_roles("student")
def list_learning_paths():
    """List only the authenticated student's self-directed paths."""
    paths = db.session.execute(
        db.select(LearningPath)
        .filter_by(student_id=current_user().id)
        .order_by(LearningPath.updated_at.desc())
    ).scalars()
    return jsonify(paths=[learning_path_payload(path) for path in paths])


@learning_paths_bp.post("")
@require_roles("student")
def create_learning_path():
    """Save a validated self-directed topic path for the current student."""
    payload, error = parse_payload(LearningPathCreateRequest)
    if error:
        return error
    path = LearningPath(student_id=current_user().id, title=payload.title, topics=payload.topics)
    db.session.add(path)
    db.session.commit()
    return jsonify(path=learning_path_payload(path)), 201