from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClassRoom, Student


# =========================================================
# CLASSES ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/classes",
    tags=["Classes"]
)


# =========================================================
# CREATE CLASS SCHEMA
# =========================================================

class ClassCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100
    )

    academic_year: str = Field(
        min_length=1,
        max_length=50
    )

    description: str = Field(
        default="",
        max_length=500
    )


# =========================================================
# UPDATE CLASS SCHEMA
# =========================================================

class ClassUpdate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100
    )

    academic_year: str = Field(
        min_length=1,
        max_length=50
    )

    description: str = Field(
        default="",
        max_length=500
    )


# =========================================================
# CLASS RESPONSE
# =========================================================

class ClassResponse(BaseModel):

    id: int
    name: str
    academic_year: str
    description: str

    class Config:
        from_attributes = True


# =========================================================
# CREATE CLASS
# =========================================================

@router.post(
    "/",
    response_model=ClassResponse
)
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db)
):

    name = data.name.strip()

    academic_year = data.academic_year.strip()

    # Check duplicate class

    existing_class = (
        db.query(ClassRoom)
        .filter(
            ClassRoom.name == name,
            ClassRoom.academic_year == academic_year
        )
        .first()
    )

    if existing_class:

        raise HTTPException(
            status_code=400,
            detail=(
                "This class already exists "
                "for this academic year."
            )
        )

    school_class = ClassRoom(

        name=name,

        academic_year=academic_year,

        description=data.description.strip()
    )

    db.add(school_class)

    db.commit()

    db.refresh(school_class)

    return school_class


# =========================================================
# GET ALL CLASSES
# =========================================================

@router.get(
    "/",
    response_model=list[ClassResponse]
)
def get_classes(
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = db.query(ClassRoom)

    if academic_year:

        query = query.filter(
            ClassRoom.academic_year
            == academic_year.strip()
        )

    return (
        query
        .order_by(
            ClassRoom.academic_year.desc(),
            ClassRoom.name.asc()
        )
        .all()
    )


# =========================================================
# GET ONE CLASS
# =========================================================

@router.get(
    "/{class_id}",
    response_model=ClassResponse
)
def get_class(
    class_id: int,
    db: Session = Depends(get_db)
):

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

    return school_class


# =========================================================
# UPDATE CLASS
# =========================================================

@router.put(
    "/{class_id}",
    response_model=ClassResponse
)
def update_class(
    class_id: int,
    data: ClassUpdate,
    db: Session = Depends(get_db)
):

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

    name = data.name.strip()

    academic_year = data.academic_year.strip()

    # Check duplicate

    duplicate = (
        db.query(ClassRoom)
        .filter(
            ClassRoom.name == name,
            ClassRoom.academic_year == academic_year,
            ClassRoom.id != class_id
        )
        .first()
    )

    if duplicate:

        raise HTTPException(
            status_code=400,
            detail=(
                "Another class with this name "
                "already exists for this academic year."
            )
        )

    school_class.name = name

    school_class.academic_year = academic_year

    school_class.description = (
        data.description.strip()
    )

    db.commit()

    db.refresh(school_class)

    return school_class


# =========================================================
# GET STUDENTS IN A CLASS
# =========================================================

@router.get(
    "/{class_id}/students"
)
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db)
):

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

    students = (
        db.query(Student)
        .filter(
            Student.class_id == class_id,
            Student.is_active == True
        )
        .order_by(
            Student.first_name.asc(),
            Student.last_name.asc()
        )
        .all()
    )

    return {

        "class_id": class_id,

        "class_name":
            school_class.name,

        "academic_year":
            school_class.academic_year,

        "student_count":
            len(students),

        "students": [

            {
                "id": student.id,

                "student_id":
                    student.student_id,

                "first_name":
                    student.first_name,

                "last_name":
                    student.last_name,

                "gender":
                    student.gender,

                "parent_name":
                    student.parent_name,

                "parent_phone":
                    student.parent_phone
            }

            for student in students
        ]
    }


# =========================================================
# DELETE CLASS
# =========================================================

@router.delete(
    "/{class_id}"
)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db)
):

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

    # Check whether students belong to class

    students_count = (
        db.query(Student)
        .filter(
            Student.class_id == class_id,
            Student.is_active == True
        )
        .count()
    )

    if students_count > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "This class cannot be deleted because "
                f"{students_count} active student(s) "
                "are assigned to it. "
                "Move the students to another class first."
            )
        )

    db.delete(school_class)

    db.commit()

    return {

        "message":
            "Class deleted successfully.",

        "class_id":
            class_id
    }