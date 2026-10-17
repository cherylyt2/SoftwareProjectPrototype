"""Role-protected AI draft and upload route tests."""

from io import BytesIO

from docx import Document

from database import db
from models import Course, LearningPath
from tests.conftest import login


def test_instructor_generation_returns_editable_draft_without_persisting(client, app, accounts, monkeypatch):
    """Generated content is returned for review and is not published automatically."""
    monkeypatch.setattr("ai_routes.generate_course", lambda *_args: {
        "title": "Generated biology", "description": "A draft", "levels": [],
    })
    login(client, "instructor")
    response = client.post("/api/ai/course-draft", json={
        "topic": "Biology", "level": "Beginner", "requirements": "Explain cell structure.",
    })

    assert response.status_code == 200
    assert response.json["editable"] is True
    assert response.json["draft"]["title"] == "Generated biology"
    with app.app_context():
        assert db.session.execute(db.select(db.func.count()).select_from(Course)).scalar_one() == 0


def test_student_cannot_generate_instructor_course_draft(client, accounts):
    """Student credentials cannot use the instructor course-generation endpoint."""
    login(client, "student", username="learner")

    assert client.post("/api/ai/course-draft", json={}).status_code == 403


def test_instructor_can_extract_uploaded_docx_without_storing_file(client, app, accounts):
    """The upload endpoint returns extracted text and leaves no source-file record."""
    document = Document()
    document.add_paragraph("Reference notes for photosynthesis")
    source = BytesIO()
    document.save(source)
    login(client, "instructor")

    response = client.post("/api/ai/extract", data={
        "file": (BytesIO(source.getvalue()), "photosynthesis.docx"),
    }, content_type="multipart/form-data")

    assert response.status_code == 200
    assert response.json["text"] == "Reference notes for photosynthesis"
    assert "file" not in response.json


def test_student_cannot_upload_course_material(client, accounts):
    """Only instructors can upload source material for course authoring."""
    login(client, "student", username="learner")
    response = client.post("/api/ai/extract", data={
        "file": (BytesIO(b"data"), "notes.pdf"),
    }, content_type="multipart/form-data")

    assert response.status_code == 403


def test_student_generated_path_is_saved_with_ordered_steps(client, app, accounts, monkeypatch):
    """A generated learning path is stored under the requesting student."""
    monkeypatch.setattr("ai_routes.generate_path", lambda *_args: [{
        "title": "Habitats", "objective": "Describe an ecosystem", "activity": "Compare two places",
    }])
    login(client, "student", username="learner")
    response = client.post("/api/ai/learning-path", json={
        "title": "Ecology", "topics": ["Habitats"],
    })

    assert response.status_code == 201
    assert response.json["path"]["steps"][0]["title"] == "Habitats"
    with app.app_context():
        assert db.session.execute(db.select(db.func.count()).select_from(LearningPath)).scalar_one() == 1