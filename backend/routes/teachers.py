from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Teacher, User


# =========================================================
# TEACHERS ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"]
)


# =========================================================
# CREATE TEACHER SCHEMA
# =========================================================

class TeacherCreate(BaseModel):

    teacher_id: str = Field(
        min_length=1,
        max_length=100
    )

    first_name: str = Field(
        min_length=1,
        max_length=100
    )

    last_name: str = Field(
        default="",
        max_length=100
    )

    phone: str = Field(
        default="",
        max_length=50
    )

    email: str = Field(
        default="",
        max_length=150
    )

    specialization: str = Field(
        default="",
        max_length=150
    )

    user_id: Optional[int] = None


# =========================================================
# UPDATE TEACHER SCHEMA
# =========================================================

class TeacherUpdate(BaseModel):

    first_name: str = Field(
        min_length=1,
        max_length=100
    )

    last_name: str = Field(
        default="",
        max_length=100
    )

    phone: str = Field(
        default="",
        max_length=50
    )

    email: str = Field(
        default="",
        max_length=150
    )

    specialization: str = Field(
        default="",
        max_length=150
    )

    user_id: Optional[int] = None


# =========================================================
# TEACHER RESPONSE
# =========================================================

class TeacherResponse(BaseModel):

    id: int
    teacher_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    specialization: str
    user_id: Optional[int]

    class Config:
        from_attributes = True


# =========================================================
# CHECK USER
# =========================================================

def check_user_exists(
    db: Session,
    user_id: Optional[int],
    teacher_id: Optional[int] = None
):

    if user_id is None:
        return

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # A user can only be connected to one teacher.
    existing_teacher = (
        db.query(Teacher)
        .filter(
            Teacher.user_id == user_id
        )
        .first()
    )

    if existing_teacher:

        if (
            teacher_id is None
            or existing_teacher.id != teacher_id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "This user is already connected "
                    "to another teacher."
                )
            )


# =========================================================
# CREATE TEACHER
# =========================================================

@router.post(
    "/",
    response_model=TeacherResponse
)
def create_teacher(
    data: TeacherCreate,
    db: Session = Depends(get_db)
):

    teacher_id = data.teacher_id.strip()

    first_name = data.first_name.strip()

    # Check duplicate Teacher ID
    existing_teacher = (
        db.query(Teacher)
        .filter(
            Teacher.teacher_id == teacher_id
        )
        .first()
    )

    if existing_teacher:

        raise HTTPException(
            status_code=400,
            detail="Teacher ID already exists."
        )

    # Check user
    check_user_exists(
        db,
        data.user_id
    )

    teacher = Teacher(
        teacher_id=teacher_id,
        first_name=first_name,
        last_name=data.last_name.strip(),
        phone=data.phone.strip(),
        email=data.email.strip(),
        specialization=data.specialization.strip(),
        user_id=data.user_id
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


# =========================================================
# GET ALL TEACHERS
# =========================================================

@router.get(
    "/",
    response_model=list[TeacherResponse]
)
def get_teachers(
    search: Optional[str] = Query(
        default=None
    ),

    specialization: Optional[str] = Query(
        default=None
    ),

    db: Session = Depends(get_db)
):

    query = db.query(Teacher)

    # Search by ID, first name, last name,
    # phone, email or specialization.

    if search:

        search_value = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            (
                Teacher.teacher_id.ilike(
                    search_value
                )
            )
            |
            (
                Teacher.first_name.ilike(
                    search_value
                )
            )
            |
            (
                Teacher.last_name.ilike(
                    search_value
                )
            )
            |
            (
                Teacher.phone.ilike(
                    search_value
                )
            )
            |
            (
                Teacher.email.ilike(
                    search_value
                )
            )
            |
            (
                Teacher.specialization.ilike(
                    search_value
                )
            )
        )

    if specialization:

        query = query.filter(
            Teacher.specialization.ilike(
                specialization.strip()
            )
        )

    return (
        query
        .order_by(
            Teacher.first_name.asc(),
            Teacher.last_name.asc()
        )
        .all()
    )


# =========================================================
# GET ONE TEACHER
# =========================================================

@router.get(
    "/{teacher_id}",
    response_model=TeacherResponse
)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):

    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id
        )
        .first()
    )

    if teacher is None:

        raise HTTPException(
            status_code=404,
            detail="Teacher not found."
        )

    return teacher


# =========================================================
# UPDATE TEACHER
# =========================================================

@router.put(
    "/{teacher_id}",
    response_model=TeacherResponse
)
def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: Session = Depends(get_db)
):

    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id
        )
        .first()
    )

    if teacher is None:

        raise HTTPException(
            status_code=404,
            detail="Teacher not found."
        )

    # Check user
    check_user_exists(
        db,
        data.user_id,
        teacher_id=teacher_id
    )

    teacher.first_name = (
        data.first_name.strip()
    )

    teacher.last_name = (
        data.last_name.strip()
    )

    teacher.phone = (
        data.phone.strip()
    )

    teacher.email = (
        data.email.strip()
    )

    teacher.specialization = (
        data.specialization.strip()
    )

    teacher.user_id = data.user_id

    db.commit()
    db.refresh(teacher)

    return teacher


# =========================================================
# DELETE TEACHER
# =========================================================

@router.delete(
    "/{teacher_id}"
)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):

    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id
        )
        .first()
    )

    if teacher is None:

        raise HTTPException(
            status_code=404,
            detail="Teacher not found."
        )

    db.delete(teacher)
    db.commit()

    return {
        "message": "Teacher deleted successfully.",
        "teacher_id": teacher_id
    }