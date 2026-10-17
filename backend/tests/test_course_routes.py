"""Course ownership, revision, enrollment, and score-history tests."""

from database import db
from models import Course, CourseRevision
from tests.conftest import login


def test_instructor_creates_and_edits_immutable_course_revisions(client, app, accounts):
    """Course edits create a new revision while preserving the previous one."""
    login(client, "instructor")
    created = client.post("/api/courses", json={
        "title": "Writing clearly",
        "description": "A short course",
        "content": {"modules": [{"key": "draft", "title": "First draft"}]},
    })
    course_id = created.json["course"]["id"]
    updated = client.patch(f"/api/courses/{course_id}", json={"content": {"modules": [{"key": "revise"}]}})

    assert created.status_code == 201
    assert created.json["course"]["revision"] == 1
    assert updated.status_code == 200
    assert updated.json["course"]["revision"] == 2
    with app.app_context():
        revisions = db.session.execute(
            db.select(CourseRevision).filter_by(course_id=course_id).order_by(CourseRevision.revision)
        ).scalars().all()
        assert [revision.content["modules"][0]["key"] for revision in revisions] == ["draft", "revise"]


def test_instructor_cannot_read_or_edit_another_instructors_course(client, accounts):
    """Course ownership is checked for both reads and writes."""
    login(client, "instructor")
    created = client.post("/api/courses", json={"title": "Private course"})
    course_id = created.json["course"]["id"]
    client.post("/api/auth/logout")
    login(client, "instructor", username="other")

    assert client.get(f"/api/courses/{course_id}").status_code == 404
    assert client.patch(f"/api/courses/{course_id}", json={"title": "Takeover"}).status_code == 404


def test_locked_course_is_hidden_from_students(client, accounts):
    """Students cannot discover or open courses while an admin has them locked."""
    login(client, "instructor")
    created = client.post("/api/courses", json={"title": "Locked course"})
    course_id = created.json["course"]["id"]
    client.post(f"/api/courses/{course_id}/students", json={"student_id": accounts["student"]})
    client.post("/api/auth/logout")
    login(client, "student", username="learner")

    assert client.get("/api/courses").json["courses"] == []
    assert client.get(f"/api/courses/{course_id}").status_code == 404


def test_student_retries_preserve_each_score_and_revision(client, accounts):
    """Retry submissions create separate history rows tied to the course revision."""
    login(client, "instructor")
    created = client.post("/api/courses", json={
        "title": "Practice course",
        "content": {"modules": [{"key": "quiz-1", "activities": [{"type": "quiz", "questions": [
            {"key": "q1", "answer": "b"}, {"key": "q2", "answer": "true"},
        ]}]}]},
    })
    course = created.json["course"]
    course_id = course["id"]
    client.post(f"/api/courses/{course_id}/students", json={"student_id": accounts["student"]})
    client.post("/api/auth/logout")
    login(client, "admin", username="admin")
    client.patch(f"/api/courses/{course_id}/access", json={"is_open": True})
    client.post("/api/auth/logout")
    login(client, "student", username="learner")
    student_course = client.get(f"/api/courses/{course_id}").json["course"]
    student_question = student_course["content"]["modules"][0]["activities"][0]["questions"][0]
    assert "answer" not in student_question

    first = client.post(f"/api/courses/{course_id}/attempts", json={
        "revision_id": course["revision_id"], "module_key": "quiz-1", "answers": {"q1": "b", "q2": "false"},
    })
    retry = client.post(f"/api/courses/{course_id}/attempts", json={
        "revision_id": course["revision_id"], "module_key": "quiz-1", "answers": {"q1": "b", "q2": "true"},
    })
    history = client.get(f"/api/courses/{course_id}/attempts")

    assert first.status_code == 201
    assert retry.status_code == 201
    assert {item["score"] for item in history.json["attempts"]} == {50, 100}
    assert {item["revision_id"] for item in history.json["attempts"]} == {course["revision_id"]}


def test_student_cannot_submit_arbitrary_score(client, accounts):
    """The endpoint rejects client-supplied scores instead of trusting them."""
    login(client, "instructor")
    created = client.post("/api/courses", json={"title": "Scored course"})
    course = created.json["course"]
    client.post(f"/api/courses/{course['id']}/students", json={"student_id": accounts["student"]})
    client.post("/api/auth/logout")
    login(client, "admin", username="admin")
    client.patch(f"/api/courses/{course['id']}/access", json={"is_open": True})
    client.post("/api/auth/logout")
    login(client, "student", username="learner")

    response = client.post(f"/api/courses/{course['id']}/attempts", json={
        "revision_id": course["revision_id"], "module_key": "quiz-1", "score": 100,
    })

    assert response.status_code == 400


def test_student_cannot_record_attempt_for_non_quiz_module(client, accounts):
    """A content module without quiz questions cannot create a score record."""
    login(client, "instructor")
    created = client.post("/api/courses", json={"title": "Reading course"})
    course = created.json["course"]
    client.post(f"/api/courses/{course['id']}/students", json={"student_id": accounts["student"]})
    client.post("/api/auth/logout")
    login(client, "admin", username="admin")
    client.patch(f"/api/courses/{course['id']}/access", json={"is_open": True})
    client.post("/api/auth/logout")
    login(client, "student", username="learner")

    response = client.post(f"/api/courses/{course['id']}/attempts", json={
        "revision_id": course["revision_id"], "module_key": "reading", "answers": {"q1": "yes"},
    })

    assert response.status_code == 422