"""Course, enrollment, and module-attempt API endpoints."""

from flask import Blueprint, jsonify, request
from sqlalchemy import and_

from assessment import calculate_score, find_module_questions
from database import db
from models import Attempt, Course, CourseRevision, Enrollment, User, new_id
from schemas import AttemptCreateRequest, CourseAccessRequest, CourseCreateRequest, CourseUpdateRequest, EnrollmentRequest
from security import current_user, require_roles, user_payload
from auth_routes import parse_payload

courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")


def latest_revision(course: Course) -> CourseRevision | None:
    """Return the newest immutable content snapshot for a course."""
    return max(course.revisions, key=lambda revision: revision.revision, default=None)


def _without_answers(value):
    """Recursively remove private answer keys from student-facing content."""
    if isinstance(value, dict):
        return {key: _without_answers(item) for key, item in value.items() if key != "answer"}
    if isinstance(value, list):
        return [_without_answers(item) for item in value]
    return value


def course_payload(course: Course, viewer: User | None = None) -> dict:
    """Serialize the newest revision, hiding quiz answers from students."""
    revision = latest_revision(course)
    content = revision.content if revision else {}
    if viewer is not None and viewer.role == "student":
        content = _without_answers(content)
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "is_open": course.is_open,
        "instructor": user_payload(course.instructor),
        "revision": revision.revision if revision else 0,
        "revision_id": revision.id if revision else None,
        "content": content,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
    }


def can_view_course(course: Course, user: User) -> bool:
    """Check that the account can view the course and its content."""
    if user.role == "admin":
        return True
    if user.role == "instructor":
        return course.instructor_id == user.id
    if not course.is_open:
        return False
    enrollment = db.session.execute(
        db.select(Enrollment.id).filter_by(course_id=course.id, student_id=user.id)
    ).first()
    return enrollment is not None


def owned_course(course_id: str) -> Course | None:
    """Return a course only when it belongs to the active instructor."""
    user = current_user()
    return db.session.execute(
        db.select(Course).filter_by(id=course_id, instructor_id=user.id)
    ).scalar_one_or_none()


@courses_bp.get("")
@require_roles("admin", "instructor", "student")
def list_courses():
    """List all, owned, or enrolled courses according to the current role."""
    user = current_user()
    query = db.select(Course)
    if user.role == "instructor":
        query = query.filter_by(instructor_id=user.id)
    elif user.role == "student":
        query = query.join(Enrollment).filter(and_(Enrollment.student_id == user.id, Course.is_open.is_(True)))
    courses = db.session.execute(query.order_by(Course.updated_at.desc())).scalars()
    return jsonify(courses=[course_payload(course, user) for course in courses])


@courses_bp.post("")
@require_roles("instructor")
def create_course():
    """Create a draft course and its first content revision."""
    payload, error = parse_payload(CourseCreateRequest)
    if error:
        return error
    course = Course(instructor_id=current_user().id, title=payload.title, description=payload.description)
    course.revisions.append(CourseRevision(revision=1, content=payload.content))
    db.session.add(course)
    db.session.commit()
    return jsonify(course=course_payload(course)), 201


@courses_bp.get("/<course_id>")
@require_roles("admin", "instructor", "student")
def get_course(course_id: str):
    """Return the latest course revision after enforcing role-specific access."""
    course = db.session.get(Course, course_id)
    user = current_user()
    if course is None or not can_view_course(course, user):
        return jsonify(error="Course not found."), 404
    return jsonify(course=course_payload(course, user))


@courses_bp.patch("/<course_id>")
@require_roles("instructor")
def update_course(course_id: str):
    """Save instructor changes as a new immutable revision."""
    course = owned_course(course_id)
    if course is None:
        return jsonify(error="Course not found."), 404
    payload, error = parse_payload(CourseUpdateRequest)
    if error:
        return error

    changes = payload.model_dump(exclude_unset=True)
    latest = latest_revision(course)
    content = changes.pop("content", latest.content if latest else {})
    for field, value in changes.items():
        setattr(course, field, value)
    course.revisions.append(CourseRevision(revision=(latest.revision + 1) if latest else 1, content=content))
    db.session.commit()
    return jsonify(course=course_payload(course))


@courses_bp.patch("/<course_id>/access")
@require_roles("admin")
def set_course_access(course_id: str):
    """Open or lock a course, with the change enforced for student requests."""
    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify(error="Course not found."), 404
    payload, error = parse_payload(CourseAccessRequest)
    if error:
        return error
    course.is_open = payload.is_open
    db.session.commit()
    return jsonify(course=course_payload(course))


@courses_bp.get("/<course_id>/students")
@require_roles("admin", "instructor")
def list_enrolled_students(course_id: str):
    """List enrolled students for an admin or the course owner."""
    user = current_user()
    course = db.session.get(Course, course_id) if user.role == "admin" else owned_course(course_id)
    if course is None:
        return jsonify(error="Course not found."), 404
    students = db.session.execute(
        db.select(User).join(Enrollment).filter(Enrollment.course_id == course.id).order_by(User.display_name)
    ).scalars()
    return jsonify(students=[user_payload(student) for student in students])


@courses_bp.post("/<course_id>/students")
@require_roles("admin", "instructor")
def enroll_student(course_id: str):
    """Enroll a student when requested by an admin or the course owner."""
    user = current_user()
    course = db.session.get(Course, course_id) if user.role == "admin" else owned_course(course_id)
    if course is None:
        return jsonify(error="Course not found."), 404
    payload, error = parse_payload(EnrollmentRequest)
    if error:
        return error
    student = db.session.get(User, payload.student_id)
    if student is None or student.role != "student":
        return jsonify(error="Student not found."), 404
    existing = db.session.execute(
        db.select(Enrollment).filter_by(course_id=course.id, student_id=student.id)
    ).scalar_one_or_none()
    if existing:
        return jsonify(error="Student is already enrolled."), 409
    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()
    return jsonify(ok=True), 201


@courses_bp.delete("/<course_id>/students/<student_id>")
@require_roles("admin", "instructor")
def remove_student(course_id: str, student_id: str):
    """Remove a student from an admin-visible or instructor-owned course."""
    user = current_user()
    course = db.session.get(Course, course_id) if user.role == "admin" else owned_course(course_id)
    if course is None:
        return jsonify(error="Course not found."), 404
    enrollment = db.session.execute(
        db.select(Enrollment).filter_by(course_id=course.id, student_id=student_id)
    ).scalar_one_or_none()
    if enrollment is None:
        return jsonify(error="Enrollment not found."), 404
    db.session.delete(enrollment)
    db.session.commit()
    return jsonify(ok=True)


@courses_bp.get("/<course_id>/attempts")
@require_roles("admin", "instructor", "student")
def list_attempts(course_id: str):
    """List attempt history visible to the learner, course owner, or admin."""
    course = db.session.get(Course, course_id)
    user = current_user()
    if course is None or not can_view_course(course, user):
        return jsonify(error="Course not found."), 404
    query = db.select(Attempt).filter_by(course_id=course.id)
    if user.role == "student":
        query = query.filter_by(student_id=user.id)
    attempts = db.session.execute(query.order_by(Attempt.submitted_at.desc())).scalars()
    return jsonify(attempts=[{
        "id": item.id,
        "student_id": item.student_id,
        "revision_id": item.revision_id,
        "module_key": item.module_key,
        "score": item.score,
        "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
    } for item in attempts])


@courses_bp.post("/<course_id>/attempts")
@require_roles("student")
def record_attempt(course_id: str):
    """Record a student's score without overwriting earlier module attempts."""
    course = db.session.get(Course, course_id)
    user = current_user()
    if course is None or not can_view_course(course, user):
        return jsonify(error="Course not found."), 404
    payload, error = parse_payload(AttemptCreateRequest)
    if error:
        return error
    revision = db.session.execute(
        db.select(CourseRevision).filter_by(id=payload.revision_id, course_id=course.id)
    ).scalar_one_or_none()
    if revision is None:
        return jsonify(error="Course revision not found."), 404
    questions = find_module_questions(revision.content, payload.module_key)
    try:
        score = calculate_score(payload.answers, questions)
    except ValueError as error:
        return jsonify(error=str(error)), 422
    attempt = Attempt(
        student_id=user.id,
        course_id=course.id,
        revision_id=revision.id,
        module_key=payload.module_key,
        score=score,
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify(id=attempt.id, score=attempt.score, revision_id=attempt.revision_id), 201