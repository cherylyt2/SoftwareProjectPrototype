"""Database models for users, courses, enrollments, and attempts."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database import db


def new_id() -> str:
    """Return a random identifier suitable for public resource IDs."""
    return str(uuid4())


class User(db.Model):
    """A platform account with a single application role."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'instructor', 'student')"),)

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(db.String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(db.String(120))
    role: Mapped[str] = mapped_column(db.String(16), nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    owned_courses: Mapped[list["Course"]] = relationship(back_populates="instructor")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")


class Course(db.Model):
    """A course and its current publication/access state."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    instructor_id: Mapped[str] = mapped_column(db.ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(db.String(160), nullable=False)
    description: Mapped[str] = mapped_column(db.String(2000), default="", nullable=False)
    is_open: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    instructor: Mapped[User] = relationship(back_populates="owned_courses")
    revisions: Mapped[list["CourseRevision"]] = relationship(back_populates="course", order_by="CourseRevision.revision")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class CourseRevision(db.Model):
    """An immutable snapshot of course content."""

    __tablename__ = "course_revisions"
    __table_args__ = (UniqueConstraint("course_id", "revision", name="uq_course_revision"),)

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(db.ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    revision: Mapped[int] = mapped_column(db.Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship(back_populates="revisions")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="course_revision")


class Enrollment(db.Model):
    """A student's enrollment in a course."""

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_course_student"),)

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(db.ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship(back_populates="enrollments")
    student: Mapped[User] = relationship(back_populates="enrollments")


class Attempt(db.Model):
    """A scored module attempt tied to the exact content revision used."""

    __tablename__ = "attempts"
    __table_args__ = (CheckConstraint("score BETWEEN 0 AND 100", name="ck_attempt_score_range"),)

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(db.ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    revision_id: Mapped[str] = mapped_column(db.ForeignKey("course_revisions.id", ondelete="RESTRICT"), index=True)
    module_key: Mapped[str] = mapped_column(db.String(120), nullable=False)
    score: Mapped[int] = mapped_column(db.Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    course_revision: Mapped[CourseRevision] = relationship(back_populates="attempts")


class LearningPath(db.Model):
    """A student's self-directed topic sequence."""

    __tablename__ = "learning_paths"

    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(db.String(160), nullable=False)
    topics: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    steps: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())