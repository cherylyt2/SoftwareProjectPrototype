"""Self-directed learning path API tests."""

from tests.conftest import login


def test_student_creates_and_lists_personal_learning_path(client, accounts):
    """Students can create and retrieve their own ordered topic path."""
    login(client, "student", username="learner")
    created = client.post("/api/learning-paths", json={
        "title": "Explore ecology",
        "topics": ["Habitats", "Food webs", "Biodiversity"],
    })

    assert created.status_code == 201
    assert created.json["path"]["topics"] == ["Habitats", "Food webs", "Biodiversity"]
    assert client.get("/api/learning-paths").json["paths"][0]["id"] == created.json["path"]["id"]


def test_instructor_cannot_read_student_learning_paths(client, accounts):
    """Learning paths are private to their student owner."""
    login(client, "instructor")

    assert client.get("/api/learning-paths").status_code == 403


def test_learning_path_requires_topics(client, accounts):
    """A path without topics fails validation rather than storing an empty plan."""
    login(client, "student", username="learner")
    response = client.post("/api/learning-paths", json={"title": "Empty path", "topics": []})

    assert response.status_code == 400