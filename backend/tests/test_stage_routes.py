"""Battle stage loading, validation, and role-based access tests."""

import pytest

from stage_service import STAGES_DIR, load_stages, parse_stage
from tests.conftest import login

VALID = (STAGES_DIR / "floor-1-requirements.md").read_text(encoding="utf-8")


def test_shipped_stages_are_valid_and_ordered():
    """All four floors parse, are numbered 1 to 4, and keep the fixed card balance."""
    stages = load_stages()

    assert [stage["floor"] for stage in stages] == [1, 2, 3, 4]
    for stage in stages:
        assert stage["enemy_max_hp"] == 30
        for hand in ("turn_1_hand", "turn_2_hand"):
            assert sum(card["value"] for card in stage[hand] if card["correct_choice"]) == 15
        assert stage["incident_brief"] and stage["quick_reference"]


def test_malformed_files_are_rejected(tmp_path):
    """Missing front matter, bad hands, and duplicate floors raise a clear error."""
    with pytest.raises(ValueError, match="front matter"):
        parse_stage("# No front matter")
    with pytest.raises(ValueError, match="turn_2_hand"):
        parse_stage(VALID.replace('title: "MoSCoW Prioritization"\n    energy_cost: 2\n    value: 15', 'title: "MoSCoW Prioritization"\n    energy_cost: 2\n    value: 20'))
    with pytest.raises(ValueError, match="missing sections"):
        parse_stage(VALID.split("## Quick Reference")[0])

    (tmp_path / "a.md").write_text(VALID, encoding="utf-8")
    (tmp_path / "b.md").write_text(VALID, encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        load_stages(tmp_path)


def test_stages_require_authentication(client):
    """Anonymous visitors cannot read the stages."""
    assert client.get("/api/stages").status_code == 401


@pytest.mark.parametrize("role,username", [("admin", "admin"), ("instructor", "teacher")])
def test_staff_see_correct_cards(client, accounts, role, username):
    """Admins and instructors get every floor with the correct cards marked."""
    login(client, role, username=username)
    response = client.get("/api/stages")

    assert response.status_code == 200
    assert len(response.json["stages"]) == 4
    assert any(card["correct_choice"] for card in response.json["stages"][0]["turn_1_hand"])


def test_students_do_not_receive_card_answers(client, accounts):
    """Students get the same floors without the correct_choice flag."""
    login(client, "student", username="learner")
    response = client.get("/api/stages")

    assert response.status_code == 200
    stage = response.json["stages"][0]
    assert all("correct_choice" not in card for card in stage["turn_1_hand"] + stage["turn_2_hand"])
    assert stage["quick_reference"]
