from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship

from .user import User


class Course(SQLModel, table=True):
    course_code: str = Field(primary_key=True)
    course_name: str
    credit_amt: int
    prereq_code: Optional[str] = Field(default=None, foreign_key="course.course_code")
    course_type: str


class CourseHistory(SQLModel, table=True):
    history_id: Optional[int] = Field(default=None, primary_key=True)
    course_code: str = Field(foreign_key="course.course_code")
    student_id: int = Field(foreign_key="user.id")
    semester_taken: str
    credits_earned: int

    course: Course = Relationship()
    student: User = Relationship()


class SemesterPlan(SQLModel, table=True):
    plan_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id")
    advisor_id: Optional[int] = Field(default=None, foreign_key="user.id")
    submitted_student_id: str
    semester: str
    status: str = "submitted"
    advisor_feedback: Optional[str] = None
    submission_date: Optional[date] = None
    student_notes: Optional[str] = None


class PlanItem(SQLModel, table=True):
    item_id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="semesterplan.plan_id")
    course_code: str = Field(foreign_key="course.course_code")
    course_order: int
    