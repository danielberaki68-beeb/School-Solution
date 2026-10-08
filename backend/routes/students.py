from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, ClassRoom


# =========================================================
# STUDENT ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/students",
    tags=["Students"]
)


# =========================================================
# CREATE STUDENT SCHEMA
# =========================================================

class StudentCreate(BaseModel):

    student_id: str = Field(
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

    date_of_birth: Optional[date] = None

    gender: str = Field(
        default="",
        max_length=30
    )

    parent_name: str = Field(
        default="",
        max_length=200
    )

    parent_phone: str = Field(
        default="",
        max_length=50
    )

    email: str = Field(
        default="",
        max_length=150
    )

    address: str = Field(
        default="",
        max_length=300
    )

    class_id: Optional[int] = None

    admission_date: Optional[date] = None


# =========================================================
# UPDATE STUDENT SCHEMA
# =========================================================

class StudentUpdate(BaseModel):

    first_name: str = Field(
        min_length=1,
        max_length=100
    )

    last_name: str = Field(
        default="",
        max_length=100
    )

    date_of_birth: Optional[date] = None

    gender: str = Field(
        default="",
        max_length=30
    )

    parent_name: str = Field(
        default="",
        max_length=200
    )

    parent_phone: str = Field(
        default="",
        max_length=50
    )

    email: str = Field(
        default="",
        max_length=150
    )

    address: str = Field(
        default="",
        max_length=300
    )

    class_id: Optional[int] = None

    admission_date: Optional[date] = None

    is_active: bool = True


# =========================================================
# STUDENT RESPONSE
# =========================================================

class StudentResponse(BaseModel):

    id: int
    student_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: str
    parent_name: str
    parent_phone: str
    email: str
    address: str
    class_id: Optional[int]
    admission_date: Optional[date]
    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# CHECK CLASS
# =========================================================

def check_class_exists(
    db: Session,
    class_id: Optional[int]
):

    if class_id is None:
        return

    school_class = (
        db.query(ClassRoom)
        .filter(
            ClassRoom.id == class_id
        )
        .first()
    )

    if school_class is None:

        raise HTTPException(
            status_code=404,
            detail="Class not found."
        )


# =========================================================
# CREATE STUDENT
# =========================================================

@router.post(
    "/",
    response_model=StudentResponse
)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db)
):

    # Check duplicate student ID

    existing_student = (
        db.query(Student)
        .filter(
            Student.student_id == data.student_id.strip()
        )
        .first()
    )

    if existing_student:

        raise HTTPException(
            status_code=400,
            detail="Student ID already exists."
        )


    # Check class

    check_class_exists(
        db,
        data.class_id
    )


    # Create student

    student = Student(

        student_id=data.student_id.strip(),

        first_name=data.first_name.strip(),

        last_name=data.last_name.strip(),

        date_of_birth=data.date_of_birth,

        gender=data.gender.strip(),

        parent_name=data.parent_name.strip(),

        parent_phone=data.parent_phone.strip(),

        email=data.email.strip(),

        address=data.address.strip(),

        class_id=data.class_id,

        admission_date=data.admission_date,

        is_active=True
    )


    db.add(student)

    db.commit()

    db.refresh(student)

    return student


# =========================================================
# GET ALL STUDENTS
# =========================================================

@router.get(
    "/",
    response_model=list[StudentResponse]
)
def get_students(
    search: Optional[str] = Query(
        default=None
    ),

    class_id: Optional[int] = Query(
        default=None
    ),

    active_only: bool = Query(
        default=True
    ),

    db: Session = Depends(get_db)
):

    query = db.query(Student)


    # Active students only

    if active_only:

        query = query.filter(
            Student.is_active == True
        )


    # Class filter

    if class_id is not None:

        query = query.filter(
            Student.class_id == class_id
        )


    # Search

    if search:

        search_value = (
            f"%{search.strip()}%"
        )

        query = query.filter(

            (
                Student.student_id.ilike(
                    search_value
                )
            )
            |
            (
                Student.first_name.ilike(
                    search_value
                )
            )
            |
            (
                Student.last_name.ilike(
                    search_value
                )
            )
            |
            (
                Student.parent_name.ilike(
                    search_value
                )
            )
        )


    return (
        query
        .order_by(
            Student.first_name.asc(),
            Student.last_name.asc()
        )
        .all()
    )


# =========================================================
# GET ONE STUDENT
# =========================================================

@router.get(
    "/{student_id}",
    response_model=StudentResponse
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id
        )
        .first()
    )

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )

    return student


# =========================================================
# UPDATE STUDENT
# =========================================================

@router.put(
    "/{student_id}",
    response_model=StudentResponse
)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db)
):

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id
        )
        .first()
    )

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )


    # Check class

    check_class_exists(
        db,
        data.class_id
    )


    # Update

    student.first_name = (
        data.first_name.strip()
    )

    student.last_name = (
        data.last_name.strip()
    )

    student.date_of_birth = (
        data.date_of_birth
    )

    student.gender = (
        data.gender.strip()
    )

    student.parent_name = (
        data.parent_name.strip()
    )

    student.parent_phone = (
        data.parent_phone.strip()
    )

    student.email = (
        data.email.strip()
    )

    student.address = (
        data.address.strip()
    )

    student.class_id = (
        data.class_id
    )

    student.admission_date = (
        data.admission_date
    )

    student.is_active = (
        data.is_active
    )


    db.commit()

    db.refresh(student)

    return student


# =========================================================
# DELETE STUDENT
# =========================================================

@router.delete(
    "/{student_id}"
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id
        )
        .first()
    )

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )


    # Soft delete

    student.is_active = False

    db.commit()


    return {

        "message":
            "Student deleted successfully.",

        "student_id":
            student_id
    }