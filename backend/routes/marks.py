from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Mark, Student, Subject, GradeScale


# =========================================================
# MARKS / RESULTS ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/marks",
    tags=["Marks / Results"]
)


# =========================================================
# CREATE MARK SCHEMA
# =========================================================

class MarkCreate(BaseModel):

    student_id: int = Field(
        gt=0
    )

    subject_id: int = Field(
        gt=0
    )

    academic_year: str = Field(
        min_length=1,
        max_length=50
    )

    term: str = Field(
        min_length=1,
        max_length=50
    )

    mark: float = Field(
        ge=0,
        le=100
    )

    teacher_comment: str = Field(
        default="",
        max_length=1000
    )


# =========================================================
# UPDATE MARK SCHEMA
# =========================================================

class MarkUpdate(BaseModel):

    mark: float = Field(
        ge=0,
        le=100
    )

    teacher_comment: str = Field(
        default="",
        max_length=1000
    )


# =========================================================
# MARK RESPONSE
# =========================================================

class MarkResponse(BaseModel):

    id: int

    student_id: int
    subject_id: int

    academic_year: str
    term: str

    mark: float

    grade_name: str
    grade_point: float
    grade_remark: str

    teacher_comment: str

    class Config:
        from_attributes = True


# =========================================================
# CHECK STUDENT
# =========================================================

def check_student(
    db: Session,
    student_id: int
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

    if not student.is_active:

        raise HTTPException(
            status_code=400,
            detail="This student is inactive."
        )

    return student


# =========================================================
# CHECK SUBJECT
# =========================================================

def check_subject(
    db: Session,
    subject_id: int
):

    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id
        )
        .first()
    )

    if subject is None:

        raise HTTPException(
            status_code=404,
            detail="Subject not found."
        )

    if not subject.is_active:

        raise HTTPException(
            status_code=400,
            detail="This subject is inactive."
        )

    return subject


# =========================================================
# CALCULATE GRADE
# =========================================================

def calculate_grade(
    db: Session,
    mark_value: float
):

    grade = (
        db.query(GradeScale)
        .filter(
            GradeScale.is_active == True,
            GradeScale.minimum_mark <= mark_value,
            GradeScale.maximum_mark >= mark_value
        )
        .order_by(
            GradeScale.display_order.asc()
        )
        .first()
    )

    if grade is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "No active grading rule covers "
                f"the mark {mark_value}."
            )
        )

    return grade


# =========================================================
# CREATE MARK
# =========================================================

@router.post(
    "/",
    response_model=MarkResponse
)
def create_mark(
    data: MarkCreate,
    db: Session = Depends(get_db)
):

    # Check student
    check_student(
        db,
        data.student_id
    )

    # Check subject
    check_subject(
        db,
        data.subject_id
    )

    academic_year = (
        data.academic_year.strip()
    )

    term = data.term.strip()

    # Prevent duplicate result
    existing_mark = (
        db.query(Mark)
        .filter(
            Mark.student_id == data.student_id,
            Mark.subject_id == data.subject_id,
            Mark.academic_year == academic_year,
            Mark.term == term
        )
        .first()
    )

    if existing_mark:

        raise HTTPException(
            status_code=400,
            detail=(
                "A mark already exists for this "
                "student, subject, academic year "
                "and term."
            )
        )

    # Calculate grade
    grade = calculate_grade(
        db,
        data.mark
    )

    result = Mark(
        student_id=data.student_id,
        subject_id=data.subject_id,
        academic_year=academic_year,
        term=term,
        mark=data.mark,
        grade_name=grade.grade_name,
        grade_point=grade.grade_point,
        grade_remark=grade.remark,
        teacher_comment=data.teacher_comment.strip()
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result


# =========================================================
# GET ALL MARKS
# =========================================================

@router.get(
    "/",
    response_model=list[MarkResponse]
)
def get_marks(
    student_id: Optional[int] = Query(
        default=None
    ),

    subject_id: Optional[int] = Query(
        default=None
    ),

    academic_year: Optional[str] = Query(
        default=None
    ),

    term: Optional[str] = Query(
        default=None
    ),

    db: Session = Depends(get_db)
):

    query = db.query(Mark)

    if student_id is not None:

        query = query.filter(
            Mark.student_id == student_id
        )

    if subject_id is not None:

        query = query.filter(
            Mark.subject_id == subject_id
        )

    if academic_year:

        query = query.filter(
            Mark.academic_year
            == academic_year.strip()
        )

    if term:

        query = query.filter(
            Mark.term == term.strip()
        )

    return (
        query
        .order_by(
            Mark.student_id.asc(),
            Mark.subject_id.asc()
        )
        .all()
    )


# =========================================================
# GET ONE MARK
# =========================================================

@router.get(
    "/{mark_id}",
    response_model=MarkResponse
)
def get_mark(
    mark_id: int,
    db: Session = Depends(get_db)
):

    result = (
        db.query(Mark)
        .filter(
            Mark.id == mark_id
        )
        .first()
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Mark not found."
        )

    return result


# =========================================================
# UPDATE MARK
# =========================================================

@router.put(
    "/{mark_id}",
    response_model=MarkResponse
)
def update_mark(
    mark_id: int,
    data: MarkUpdate,
    db: Session = Depends(get_db)
):

    result = (
        db.query(Mark)
        .filter(
            Mark.id == mark_id
        )
        .first()
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Mark not found."
        )

    # Recalculate grade
    grade = calculate_grade(
        db,
        data.mark
    )

    result.mark = data.mark

    result.grade_name = (
        grade.grade_name
    )

    result.grade_point = (
        grade.grade_point
    )

    result.grade_remark = (
        grade.remark
    )

    result.teacher_comment = (
        data.teacher_comment.strip()
    )

    db.commit()
    db.refresh(result)

    return result


# =========================================================
# DELETE MARK
# =========================================================

@router.delete(
    "/{mark_id}"
)
def delete_mark(
    mark_id: int,
    db: Session = Depends(get_db)
):

    result = (
        db.query(Mark)
        .filter(
            Mark.id == mark_id
        )
        .first()
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Mark not found."
        )

    db.delete(result)
    db.commit()

    return {
        "message": "Mark deleted successfully.",
        "mark_id": mark_id
    }


# =========================================================
# GET STUDENT RESULTS
# =========================================================

@router.get(
    "/student/{student_id}/results"
)
def get_student_results(
    student_id: int,

    academic_year: Optional[str] = Query(
        default=None
    ),

    term: Optional[str] = Query(
        default=None
    ),

    db: Session = Depends(get_db)
):

    student = check_student(
        db,
        student_id
    )

    query = (
        db.query(Mark)
        .filter(
            Mark.student_id == student_id
        )
    )

    if academic_year:

        query = query.filter(
            Mark.academic_year
            == academic_year.strip()
        )

    if term:

        query = query.filter(
            Mark.term == term.strip()
        )

    results = (
        query
        .order_by(
            Mark.subject_id.asc()
        )
        .all()
    )

    total_marks = sum(
        result.mark
        for result in results
    )

    average_mark = (
        total_marks / len(results)
        if results
        else 0
    )

    total_grade_points = sum(
        result.grade_point
        for result in results
    )

    average_grade_point = (
        total_grade_points / len(results)
        if results
        else 0
    )

    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name
        },

        "academic_year": academic_year,

        "term": term,

        "subject_count": len(results),

        "total_marks": round(
            total_marks,
            2
        ),

        "average_mark": round(
            average_mark,
            2
        ),

        "average_grade_point": round(
            average_grade_point,
            2
        ),

        "results": [
            {
                "id": result.id,
                "subject_id": result.subject_id,
                "mark": result.mark,
                "grade": result.grade_name,
                "grade_point": result.grade_point,
                "remark": result.grade_remark,
                "teacher_comment":
                    result.teacher_comment
            }

            for result in results
        ]
    }