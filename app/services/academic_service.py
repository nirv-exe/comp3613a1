from app.repositories.academic import AcademicRepository


class AcademicService:
    def __init__(self, repository: AcademicRepository):
        self.repository = repository

    def get_degree_progress(self, student_id: int):
        return self.repository.get_degree_progress_data(student_id)

    def create_semester_plan(
        self,
        student_id: int,
        submitted_student_id: str,
        semester: str,
        student_notes: str,
    ):
        return self.repository.create_semester_plan(
            student_id, submitted_student_id, semester, student_notes, []
        )

    def get_courses(self):
        return self.repository.get_courses()

    def get_semester_plans(self, student_id: int):
        return self.repository.get_semester_plans(student_id)

    def get_advisor_requests(self):
        return self.repository.get_advisor_requests()

    def get_advisor_dashboard(self):
        return self.repository.get_advisor_dashboard_data()

    def get_advisor_plan_details(self, plan_id: int):
        return self.repository.get_advisor_plan_details(plan_id)

    def review_plan(
        self,
        plan_id: int,
        advisor_id: int,
        decision: str,
        advisor_feedback: str,
    ):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Invalid review decision.")
        feedback = advisor_feedback.strip()
        if decision == "rejected" and not feedback:
            raise ValueError("Feedback is required when rejecting a request.")
        return self.repository.review_semester_plan(
            plan_id, advisor_id, decision, feedback
        )

    def get_semester_plan_details(self, student_id: int, plan_id: int):
        return self.repository.get_semester_plan_details(student_id, plan_id)

    def cancel_plan(self, student_id: int, plan_id: int):
        return self.repository.cancel_semester_plan(student_id, plan_id)

    def create_plan(
        self,
        student_id: int,
        submitted_student_id: str,
        semester: str,
        student_notes: str,
        advisor_username: str,
        course_codes: list[str],
    ):
        if not submitted_student_id.strip():
            raise ValueError("Please enter your student ID before submitting.")
        if not advisor_username.strip():
            raise ValueError("Please select an advisor before submitting.")
        if len(course_codes) != len(set(course_codes)):
            raise ValueError("A course cannot be selected more than once.")
        return self.repository.create_semester_plan(
            student_id,
            submitted_student_id,
            semester,
            student_notes,
            advisor_username.strip(),
            course_codes,
        )

    def get_course_history(self, student_id: int):
        return self.repository.get_course_history(student_id)
