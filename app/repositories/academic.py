from datetime import date

from sqlmodel import Session, select

from app.models.academic import Course, CourseHistory, PlanItem, SemesterPlan
from app.models.user import User


class AcademicRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_degree_progress_data(self, student_id: int):
        student = self.session.get(User, student_id)
        history = self.session.exec(
            select(CourseHistory, Course)
            .join(Course, Course.course_code == CourseHistory.course_code)
            .where(CourseHistory.student_id == student_id)
        ).all()
        completed_courses = [
            {
                "code": course.course_code,
                "name": course.course_name,
                "credits": history_item.credits_earned,
                "semester": history_item.semester_taken,
            }
            for history_item, course in history
        ]
        completed_credits = sum(item["credits"] for item in completed_courses)
        target_credits = student.target_credits if student else 120
        outstanding_requirements = {
            "core_courses": max(
                (student.required_core_courses if student else 0)
                - sum(
                    course.course_type.strip().lower() == "core"
                    for _, course in history
                ),
                0,
            ),
            "elective_courses": max(
                (student.required_elective_courses if student else 0)
                - sum(
                    course.course_type.strip().lower() == "elective"
                    for _, course in history
                ),
                0,
            ),
            "foundation_courses": max(
                (student.required_foundation_courses if student else 0)
                - sum(
                    course.course_type.strip().lower() == "foundation"
                    for _, course in history
                ),
                0,
            ),
        }

        return {
            "completed_courses": completed_courses,
            "completed_credits": completed_credits,
            "target_credits": target_credits,
            "remaining_credits": max(target_credits - completed_credits, 0),
            "outstanding_requirements": outstanding_requirements,
        }

    def get_courses(self) -> list[Course]:
        return self.session.exec(select(Course).order_by(Course.course_code)).all()

    def get_semester_plans(self, student_id: int) -> list[SemesterPlan]:
        return self.session.exec(
            select(SemesterPlan)
            .where(SemesterPlan.student_id == student_id)
            .order_by(SemesterPlan.plan_id.desc())
        ).all()

    def get_advisor_requests(self) -> list[tuple[SemesterPlan, User]]:
        return self.session.exec(
            select(SemesterPlan, User)
            .join(User, User.id == SemesterPlan.student_id)
            .where(SemesterPlan.status != "cancelled")
            .order_by(SemesterPlan.submission_date.desc(), SemesterPlan.plan_id.desc())
        ).all()

    def get_advisor_dashboard_data(self) -> dict:
        requests = self.get_advisor_requests()
        today = date.today()
        active_submitted = [
            (plan, student)
            for plan, student in requests
            if plan.status == "submitted"
        ]
        new_requests = [
            (plan, student)
            for plan, student in active_submitted
            if plan.submission_date is None
            or (today - plan.submission_date).days <= 3
        ]
        outstanding_requests = [
            (plan, student)
            for plan, student in active_submitted
            if plan.submission_date is not None
            and (today - plan.submission_date).days > 3
        ]
        level_counts = {
            "level_1": sum(
                student.degree_level == "Level 1"
                for plan, student in active_submitted
            ),
            "level_2": sum(
                student.degree_level == "Level 2"
                for plan, student in active_submitted
            ),
            "level_3": sum(
                student.degree_level == "Level 3"
                for plan, student in active_submitted
            ),
        }
        return {
            "request_count": len(active_submitted),
            "new_requests": new_requests,
            "outstanding_requests": outstanding_requests,
            "level_counts": level_counts,
        }

    def get_advisor_plan_details(
        self, plan_id: int
    ) -> tuple[SemesterPlan, User, list[tuple[PlanItem, Course]]] | None:
        plan = self.session.get(SemesterPlan, plan_id)
        if plan is None:
            return None

        student = self.session.get(User, plan.student_id)
        if student is None:
            return None

        items = self.session.exec(
            select(PlanItem, Course)
            .join(Course, Course.course_code == PlanItem.course_code)
            .where(PlanItem.plan_id == plan_id)
            .order_by(PlanItem.course_order)
        ).all()
        return plan, student, items

    def review_semester_plan(
        self,
        plan_id: int,
        advisor_id: int,
        status: str,
        advisor_feedback: str,
    ) -> SemesterPlan | None:
        plan = self.session.get(SemesterPlan, plan_id)
        if plan is None:
            return None
        if plan.status != "submitted":
            return None

        plan.advisor_id = advisor_id
        plan.status = status
        plan.advisor_feedback = advisor_feedback
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def get_semester_plan_details(
        self, student_id: int, plan_id: int
    ) -> tuple[SemesterPlan, list[tuple[PlanItem, Course]]] | None:
        plan = self.session.exec(
            select(SemesterPlan).where(
                SemesterPlan.plan_id == plan_id,
                SemesterPlan.student_id == student_id,
            )
        ).one_or_none()
        if plan is None:
            return None

        items = self.session.exec(
            select(PlanItem, Course)
            .join(Course, Course.course_code == PlanItem.course_code)
            .where(PlanItem.plan_id == plan_id)
            .order_by(PlanItem.course_order)
        ).all()
        return plan, items

    def cancel_semester_plan(
        self, student_id: int, plan_id: int
    ) -> SemesterPlan | None:
        plan = self.session.exec(
            select(SemesterPlan).where(
                SemesterPlan.plan_id == plan_id,
                SemesterPlan.student_id == student_id,
            )
        ).one_or_none()
        if plan is None or plan.status != "submitted":
            return None

        plan.status = "cancelled"
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def create_semester_plan(
        self,
        student_id: int,
        submitted_student_id: str,
        semester: str,
        student_notes: str,
        advisor_username: str,
        course_codes: list[str],
    ):
        advisor = self.session.exec(
            select(User).where(
                User.username == advisor_username,
                User.role == "admin",
            )
        ).one_or_none()
        if advisor is None:
            raise ValueError("Please select a valid advisor before submitting.")

        plan = SemesterPlan(
            student_id=student_id,
            advisor_id=advisor.id,
            submitted_student_id=submitted_student_id,
            semester=semester,
            student_notes=student_notes,
            status="submitted",
            submission_date=date.today(),
        )
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        for course_order, course_code in enumerate(course_codes, start=1):
            self.session.add(
                PlanItem(
                    plan_id=plan.plan_id,
                    course_code=course_code,
                    course_order=course_order,
                )
            )
        self.session.commit()
        return plan

    def get_course_history(self, student_id: int):
        return self.session.exec(
            select(CourseHistory, Course)
            .join(Course, Course.course_code == CourseHistory.course_code)
            .where(CourseHistory.student_id == student_id)
            .order_by(CourseHistory.semester_taken, CourseHistory.course_code)
        ).all()
