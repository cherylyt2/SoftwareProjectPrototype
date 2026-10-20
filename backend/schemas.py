"""Validated request payloads for the learning platform API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RoleName = Literal["admin", "instructor", "student"]


class RequestModel(BaseModel):
    """Base request model that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginRequest(RequestModel):
    """Credentials and the role selected on the login screen."""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)
    role: RoleName


class AccountCreateRequest(RequestModel):
    """Details for an account created by an administrator."""

    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["instructor", "student"]

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Store usernames in a canonical lowercase form."""
        return value.lower()


class PasswordChangeRequest(RequestModel):
    """Current and replacement account passwords."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class ProfileUpdateRequest(RequestModel):
    """Editable public profile fields for the current account."""

    display_name: str = Field(min_length=1, max_length=120)


class CourseCreateRequest(RequestModel):
    """Initial course metadata and structured teaching content."""

    title: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    content: dict[str, Any] = Field(default_factory=dict)


class CourseUpdateRequest(RequestModel):
    """A partial edit that becomes a new immutable course revision."""

    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    content: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "CourseUpdateRequest":
        """Reject empty edits so each request represents an intentional change."""
        if not self.model_fields_set:
            raise ValueError("Provide at least one course field to update.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated fields cannot be null.")
        return self


class CourseAccessRequest(RequestModel):
    """Administrator decision to open or lock a course."""

    is_open: bool


class EnrollmentRequest(RequestModel):
    """A student selected for course enrollment."""

    student_id: str = Field(min_length=36, max_length=36)


class AttemptCreateRequest(RequestModel):
    """Submitted quiz answers tied to the content version used."""

    revision_id: str = Field(min_length=36, max_length=36)
    module_key: str = Field(min_length=1, max_length=120)
    answers: dict[str, str] = Field(min_length=1, max_length=50)


class LearningPathCreateRequest(RequestModel):
    """A student's topic list for a personal learning path."""

    title: str = Field(min_length=2, max_length=160)
    topics: list[str] = Field(min_length=1, max_length=20)


class CourseGenerationRequest(RequestModel):
    """Instructor context for generating a reviewable course draft."""

    topic: str = Field(min_length=2, max_length=160)
    level: str = Field(min_length=2, max_length=80)
    requirements: str = Field(min_length=5, max_length=4000)
    teaching_content: str = Field(default="", max_length=12000)


class LearningPathGenerationRequest(RequestModel):
    """Topics a student wants to turn into an ordered learning path."""

    title: str = Field(min_length=2, max_length=160)
    topics: list[str] = Field(min_length=1, max_length=20)