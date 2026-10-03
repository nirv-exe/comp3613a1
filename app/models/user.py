from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr


class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""
    degree_name: str = ""
    degree_level: str = "Level 1"
    target_credits: int = 120
    required_core_courses: int = 0
    required_foundation_courses: int = 0
    required_elective_courses: int = 0

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)