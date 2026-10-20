"""Load and validate the Markdown battle stages stored under backend/stages."""

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

STAGES_DIR = Path(__file__).resolve().parent / "stages"

_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n(.*)\Z", re.DOTALL)
_SECTION_KEYS = {"The Incident Brief": "incident_brief", "Quick Reference": "quick_reference"}

# (card_type, energy_cost, value, correct_choice) required in each fixed 2-turn hand.
_PREMIUM = ("Attack", 2, 15, True)
_STRIKE = ("Attack", 1, 5, False)
_EXPECTED_HANDS = {
    "turn_1_hand": {_PREMIUM, _STRIKE, ("Defend", 1, 8, False)},
    "turn_2_hand": {_PREMIUM, _STRIKE, ("Curse", 1, 5, False)},
}


class Card(BaseModel):
    """A card presented to the student on one turn."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    energy_cost: Literal[1, 2]
    value: int = Field(ge=1)
    card_type: Literal["Attack", "Defend", "Curse"]
    correct_choice: bool


class Stage(BaseModel):
    """Flat front matter for one floor of the fixed 2-turn combat loop."""

    model_config = ConfigDict(extra="forbid")

    course_id: str = Field(min_length=1)
    topic_name: str = Field(min_length=1)
    floor: int = Field(ge=1)
    enemy_name: str = Field(min_length=1)
    enemy_max_hp: Literal[30]
    turn_1_enemy_intent: str = Field(min_length=1)
    turn_1_enemy_damage: int = Field(ge=0)
    turn_2_enemy_intent: str = Field(min_length=1)
    turn_2_enemy_damage: int = Field(ge=0)
    turn_1_hand: list[Card] = Field(min_length=3, max_length=3)
    turn_2_hand: list[Card] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def check_card_balance(self) -> "Stage":
        """Require the hands that make two correct Premium Attacks deal exactly 30 damage."""
        for field, expected in _EXPECTED_HANDS.items():
            actual = {(c.card_type, c.energy_cost, c.value, c.correct_choice) for c in getattr(self, field)}
            if actual != expected or len(getattr(self, field)) != len(expected):
                raise ValueError(f"{field} must contain the Premium Attack, Generic Strike and the fixed third card.")
        return self


def _split_body(body: str) -> dict[str, str]:
    """Return the title and named sections from the Markdown narrative body."""
    title = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    if title is None:
        raise ValueError("Stage body is missing its title heading.")
    sections = {"title": title.group(1)}
    for chunk in re.split(r"^##\s+", body, flags=re.MULTILINE)[1:]:
        heading, _, text = chunk.partition("\n")
        key = _SECTION_KEYS.get(heading.strip())
        if key:
            sections[key] = text.strip()
    missing = [name for name in _SECTION_KEYS.values() if not sections.get(name)]
    if missing:
        raise ValueError(f"Stage body is missing sections: {', '.join(missing)}.")
    return sections


def parse_stage(text: str) -> dict:
    """Parse one stage file into validated metadata plus its narrative sections."""
    match = _FRONT_MATTER.match(text)
    if match is None:
        raise ValueError("Stage file must start with YAML front matter.")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML front matter: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("Front matter must be a mapping.")
    return {**Stage.model_validate(data).model_dump(), **_split_body(match.group(2))}


def load_stages(directory: Path = STAGES_DIR) -> list[dict]:
    """Load every stage file, ordered by floor, rejecting duplicate floors."""
    stages = []
    for path in sorted(directory.glob("*.md")):
        try:
            stages.append(parse_stage(path.read_text(encoding="utf-8")))
        except ValueError as error:
            raise ValueError(f"{path.name}: {error}") from error
    floors = [stage["floor"] for stage in stages]
    if len(floors) != len(set(floors)):
        raise ValueError("Each floor number must be used by exactly one stage file.")
    return sorted(stages, key=lambda stage: stage["floor"])
