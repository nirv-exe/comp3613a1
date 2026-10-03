from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password, verify_password, create_access_token
from app.schemas.user import RegularUserCreate
from typing import Optional

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_all_users(self):
        return self.user_repo.get_all_users()

    def update_academic_details(
        self,
        user_id: int,
        degree_name: str,
        degree_level: str,
        target_credits: str,
        required_core_courses: str,
        required_foundation_courses: str,
        required_elective_courses: str,
    ):
        if not degree_name.strip():
            raise ValueError("Please enter your degree name.")
        if degree_level not in {"Level 1", "Level 2", "Level 3", "Level 4"}:
            raise ValueError("Please select a valid degree level.")
        try:
            target_credits = int(target_credits)
            required_core_courses = int(required_core_courses)
            required_foundation_courses = int(required_foundation_courses)
            required_elective_courses = int(required_elective_courses)
        except ValueError as exc:
            raise ValueError("Course and credit requirements must be whole numbers.") from exc
        if target_credits <= 0:
            raise ValueError("Target credits must be greater than zero.")
        if min(
            required_core_courses,
            required_foundation_courses,
            required_elective_courses,
        ) < 0:
            raise ValueError("Course requirements cannot be negative.")
        return self.user_repo.update_academic_details(
            user_id,
            degree_name,
            degree_level,
            target_credits,
            required_core_courses,
            required_foundation_courses,
            required_elective_courses,
        )
    