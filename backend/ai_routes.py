"""AI draft generation and transient document extraction endpoints."""

from flask import Blueprint, jsonify, request

from ai_service import generate_course, generate_path
from auth_routes import parse_payload
from document_service import extract_text
from schemas import CourseGenerationRequest, LearningPathGenerationRequest
from security import current_user, require_roles

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.post("/course-draft")
@require_roles("instructor")
def create_course_draft():
    """Generate structured course content without publishing or persisting it."""
    payload, error = parse_payload(CourseGenerationRequest)
    if error:
        return error
    try:
        draft = generate_course(payload.topic, payload.level, payload.requirements, payload.teaching_content)
    except RuntimeError as error:
        return jsonify(error=str(error)), 503
    return jsonify(draft=draft, editable=True), 200


@ai_bp.post("/learning-path")
@require_roles("student")
def generate_learning_path():
    """Generate and save an ordered learning path for the authenticated student."""
    from database import db
    from models import LearningPath

    payload, error = parse_payload(LearningPathGenerationRequest)
    if error:
        return error
    try:
        steps = generate_path(payload.title, payload.topics)
    except RuntimeError as error:
        return jsonify(error=str(error)), 503
    path = LearningPath(
        student_id=current_user().id,
        title=payload.title,
        topics=payload.topics,
        steps=steps,
    )
    db.session.add(path)
    db.session.commit()
    return jsonify(path={"id": path.id, "title": path.title, "topics": path.topics, "steps": path.steps}), 201


@ai_bp.post("/extract")
@require_roles("instructor")
def extract_document():
    """Extract and return temporary text for course authoring without saving the file."""
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify(error="Select a document first."), 400
    try:
        text = extract_text(uploaded.filename, uploaded.stream.read(10 * 1024 * 1024 + 1))
    except ValueError as error:
        return jsonify(error=str(error)), 415
    return jsonify(filename=uploaded.filename, text=text)