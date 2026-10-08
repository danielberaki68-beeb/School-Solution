from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GradeScale


# =========================================================
# GRADING ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/grades",
    tags=["Grading System"]
)


# =========================================================
# DATA SCHEMA
# =========================================================

class GradeCreate(BaseModel):

    minimum_mark: float = Field(
        ge=0,
        le=100
    )

    maximum_mark: float = Field(
        ge=0,
        le=100
    )

    grade_name: str = Field(
        min_length=1,
        max_length=50
    )

    grade_point: float = Field(
        default=0.0,
        ge=0
    )

    remark: str = Field(
        default="",
        max_length=200
    )

    display_order: int = Field(
        default=0
    )


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class GradeResponse(BaseModel):

    id: int
    minimum_mark: float
    maximum_mark: float
    grade_name: str
    grade_point: float
    remark: str
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# CHECK GRADING RANGE
# =========================================================

def check_range(
    db: Session,
    minimum_mark: float,
    maximum_mark: float,
    exclude_id: int | None = None
):

    if minimum_mark > maximum_mark:

        raise HTTPException(
            status_code=400,
            detail="Minimum mark cannot be greater than maximum mark."
        )

    grades = (
        db.query(GradeScale)
        .filter(
            GradeScale.is_active == True
        )
        .all()
    )

    for grade in grades:

        if exclude_id is not None:

            if grade.id == exclude_id:
                continue

        overlapping = (
            minimum_mark <= grade.maximum_mark
            and maximum_mark >= grade.minimum_mark
        )

        if overlapping:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"This grading range overlaps with "
                    f"{grade.grade_name} "
                    f"({grade.minimum_mark}-{grade.maximum_mark})."
                )
            )


# =========================================================
# GET ALL GRADES
# =========================================================

@router.get(
    "/",
    response_model=list[GradeResponse]
)
def get_grades(
    db: Session = Depends(get_db)
):

    grades = (
        db.query(GradeScale)
        .filter(
            GradeScale.is_active == True
        )
        .order_by(
            GradeScale.display_order.asc()
        )
        .all()
    )

    return grades


# =========================================================
# CREATE DEFAULT GRADING SYSTEM
# =========================================================

@router.post(
    "/reset/default"
)
def reset_default_grading(
    db: Session = Depends(get_db)
):

    # Deactivate existing grading rules

    old_grades = (
        db.query(GradeScale)
        .filter(
            GradeScale.is_active == True
        )
        .all()
    )

    for grade in old_grades:
        grade.is_active = False


    # Create standard grading system

    default_grades = [

        GradeScale(
            minimum_mark=90,
            maximum_mark=100,
            grade_name="A+",
            grade_point=4.0,
            remark="Excellent",
            display_order=1,
            is_active=True
        ),

        GradeScale(
            minimum_mark=80,
            maximum_mark=89.99,
            grade_name="A",
            grade_point=3.7,
            remark="Very Good",
            display_order=2,
            is_active=True
        ),

        GradeScale(
            minimum_mark=70,
            maximum_mark=79.99,
            grade_name="B",
            grade_point=3.0,
            remark="Good",
            display_order=3,
            is_active=True
        ),

        GradeScale(
            minimum_mark=60,
            maximum_mark=69.99,
            grade_name="C",
            grade_point=2.0,
            remark="Satisfactory",
            display_order=4,
            is_active=True
        ),

        GradeScale(
            minimum_mark=50,
            maximum_mark=59.99,
            grade_name="D",
            grade_point=1.0,
            remark="Pass",
            display_order=5,
            is_active=True
        ),

        GradeScale(
            minimum_mark=0,
            maximum_mark=49.99,
            grade_name="F",
            grade_point=0.0,
            remark="Fail",
            display_order=6,
            is_active=True
        )

    ]

    db.add_all(default_grades)

    db.commit()


    return {
        "message": "Default grading system restored.",
        "grades_created": 6
    }


# =========================================================
# CALCULATE GRADE
# =========================================================

# IMPORTANT:
# This route comes BEFORE /{grade_id}
# so "calculate" is not treated as a grade ID.

@router.get(
    "/calculate/{mark}"
)
def calculate_grade(
    mark: float,
    db: Session = Depends(get_db)
):

    if mark < 0 or mark > 100:

        raise HTTPException(
            status_code=400,
            detail="Mark must be between 0 and 100."
        )

    grade = (
        db.query(GradeScale)
        .filter(
            GradeScale.is_active == True,
            GradeScale.minimum_mark <= mark,
            GradeScale.maximum_mark >= mark
        )
        .first()
    )

    if grade is None:

        raise HTTPException(
            status_code=404,
            detail="No grading rule covers this mark."
        )

    return {
        "mark": mark,
        "grade": grade.grade_name,
        "grade_point": grade.grade_point,
        "remark": grade.remark
    }


# =========================================================
# GET ONE GRADE
# =========================================================

@router.get(
    "/{grade_id}",
    response_model=GradeResponse
)
def get_grade(
    grade_id: int,
    db: Session = Depends(get_db)
):

    grade = (
        db.query(GradeScale)
        .filter(
            GradeScale.id == grade_id,
            GradeScale.is_active == True
        )
        .first()
    )

    if grade is None:

        raise HTTPException(
            status_code=404,
            detail="Grade not found."
        )

    return grade


# =========================================================
# CREATE CUSTOM GRADE
# =========================================================

@router.post(
    "/",
    response_model=GradeResponse
)
def create_grade(
    data: GradeCreate,
    db: Session = Depends(get_db)
):

    check_range(
        db,
        data.minimum_mark,
        data.maximum_mark
    )

    grade = GradeScale(

        minimum_mark=data.minimum_mark,

        maximum_mark=data.maximum_mark,

        grade_name=data.grade_name.strip(),

        grade_point=data.grade_point,

        remark=data.remark.strip(),

        display_order=data.display_order,

        is_active=True
    )

    db.add(grade)

    db.commit()

    db.refresh(grade)

    return grade


# =========================================================
# UPDATE GRADE
# =========================================================

@router.put(
    "/{grade_id}",
    response_model=GradeResponse
)
def update_grade(
    grade_id: int,
    data: GradeCreate,
    db: Session = Depends(get_db)
):

    grade = (
        db.query(GradeScale)
        .filter(
            GradeScale.id == grade_id
        )
        .first()
    )

    if grade is None:

        raise HTTPException(
            status_code=404,
            detail="Grade not found."
        )

    check_range(
        db,
        data.minimum_mark,
        data.maximum_mark,
        exclude_id=grade_id
    )

    grade.minimum_mark = data.minimum_mark

    grade.maximum_mark = data.maximum_mark

    grade.grade_name = data.grade_name.strip()

    grade.grade_point = data.grade_point

    grade.remark = data.remark.strip()

    grade.display_order = data.display_order

    db.commit()

    db.refresh(grade)

    return grade


# =========================================================
# DELETE GRADE
# =========================================================

@router.delete(
    "/{grade_id}"
)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db)
):

    grade = (
        db.query(GradeScale)
        .filter(
            GradeScale.id == grade_id
        )
        .first()
    )

    if grade is None:

        raise HTTPException(
            status_code=404,
            detail="Grade not found."
        )

    # Soft delete
    grade.is_active = False

    db.commit()

    return {
        "message": "Grade deleted successfully.",
        "grade_id": grade_id
    }