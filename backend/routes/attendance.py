from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student


# =========================================================
# ATTENDANCE ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)


# =========================================================
# ATTENDANCE STORAGE
# =========================================================
#
# We will create the attendance table dynamically here
# using SQLAlchemy.
#
# This keeps the attendance system separate and easy to
# expand later.
# =========================================================

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint
)

from ..database import Base


class Attendance(Base):

    __tablename__ = "attendance"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    attendance_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False
    )

    note = Column(
        String(500),
        default=""
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "attendance_date",
            name="uq_student_attendance_date"
        ),
    )


# =========================================================
# CREATE ATTENDANCE SCHEMA
# =========================================================

class AttendanceCreate(BaseModel):

    student_id: int = Field(
        gt=0
    )

    attendance_date: date

    status: str = Field(
        min_length=1,
        max_length=30
    )

    note: str = Field(
        default="",
        max_length=500
    )


# =========================================================
# UPDATE ATTENDANCE SCHEMA
# =========================================================

class AttendanceUpdate(BaseModel):

    attendance_date: date

    status: str = Field(
        min_length=1,
        max_length=30
    )

    note: str = Field(
        default="",
        max_length=500
    )


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class AttendanceResponse(BaseModel):

    id: int

    student_id: int

    attendance_date: date

    status: str

    note: str

    class Config:
        from_attributes = True


# =========================================================
# VALID ATTENDANCE STATUSES
# =========================================================

VALID_STATUSES = {
    "Present",
    "Absent",
    "Late",
    "Excused"
}


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
# CREATE ATTENDANCE
# =========================================================

@router.post(
    "/",
    response_model=AttendanceResponse
)
def create_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db)
):

    check_student(
        db,
        data.student_id
    )

    status = data.status.strip().title()

    if status not in VALID_STATUSES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid attendance status. "
                "Use Present, Absent, Late or Excused."
            )
        )

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.student_id
            == data.student_id,

            Attendance.attendance_date
            == data.attendance_date
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail=(
                "Attendance for this student "
                "on this date already exists."
            )
        )

    attendance = Attendance(
        student_id=data.student_id,
        attendance_date=data.attendance_date,
        status=status,
        note=data.note.strip()
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


# =========================================================
# GET ALL ATTENDANCE
# =========================================================

@router.get(
    "/",
    response_model=list[AttendanceResponse]
)
def get_attendance(
    student_id: Optional[int] = Query(
        default=None
    ),

    attendance_date: Optional[date] = Query(
        default=None
    ),

    status: Optional[str] = Query(
        default=None
    ),

    db: Session = Depends(get_db)
):

    query = db.query(Attendance)

    if student_id is not None:

        query = query.filter(
            Attendance.student_id
            == student_id
        )

    if attendance_date is not None:

        query = query.filter(
            Attendance.attendance_date
            == attendance_date
        )

    if status:

        query = query.filter(
            Attendance.status
            == status.strip().title()
        )

    return (
        query
        .order_by(
            Attendance.attendance_date.desc()
        )
        .all()
    )


# =========================================================
# GET ONE ATTENDANCE RECORD
# =========================================================

@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse
)
def get_attendance_record(
    attendance_id: int,
    db: Session = Depends(get_db)
):

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.id == attendance_id
        )
        .first()
    )

    if attendance is None:

        raise HTTPException(
            status_code=404,
            detail="Attendance record not found."
        )

    return attendance


# =========================================================
# UPDATE ATTENDANCE
# =========================================================

@router.put(
    "/{attendance_id}",
    response_model=AttendanceResponse
)
def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: Session = Depends(get_db)
):

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.id == attendance_id
        )
        .first()
    )

    if attendance is None:

        raise HTTPException(
            status_code=404,
            detail="Attendance record not found."
        )

    status = data.status.strip().title()

    if status not in VALID_STATUSES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid attendance status. "
                "Use Present, Absent, Late or Excused."
            )
        )

    duplicate = (
        db.query(Attendance)
        .filter(
            Attendance.student_id
            == attendance.student_id,

            Attendance.attendance_date
            == data.attendance_date,

            Attendance.id != attendance_id
        )
        .first()
    )

    if duplicate:

        raise HTTPException(
            status_code=400,
            detail=(
                "Another attendance record "
                "already exists for this student "
                "on this date."
            )
        )

    attendance.attendance_date = (
        data.attendance_date
    )

    attendance.status = status

    attendance.note = (
        data.note.strip()
    )

    db.commit()
    db.refresh(attendance)

    return attendance


# =========================================================
# DELETE ATTENDANCE
# =========================================================

@router.delete(
    "/{attendance_id}"
)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db)
):

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.id == attendance_id
        )
        .first()
    )

    if attendance is None:

        raise HTTPException(
            status_code=404,
            detail="Attendance record not found."
        )

    db.delete(attendance)

    db.commit()

    return {
        "message":
            "Attendance record deleted successfully.",

        "attendance_id":
            attendance_id
    }


# =========================================================
# STUDENT ATTENDANCE SUMMARY
# =========================================================

@router.get(
    "/student/{student_id}/summary"
)
def get_student_attendance_summary(
    student_id: int,

    start_date: Optional[date] = Query(
        default=None
    ),

    end_date: Optional[date] = Query(
        default=None
    ),

    db: Session = Depends(get_db)
):

    student = check_student(
        db,
        student_id
    )

    query = (
        db.query(Attendance)
        .filter(
            Attendance.student_id
            == student_id
        )
    )

    if start_date:

        query = query.filter(
            Attendance.attendance_date
            >= start_date
        )

    if end_date:

        query = query.filter(
            Attendance.attendance_date
            <= end_date
        )

    records = (
        query
        .order_by(
            Attendance.attendance_date.asc()
        )
        .all()
    )

    total_days = len(records)

    present_days = sum(
        1
        for record in records
        if record.status == "Present"
    )

    absent_days = sum(
        1
        for record in records
        if record.status == "Absent"
    )

    late_days = sum(
        1
        for record in records
        if record.status == "Late"
    )

    excused_days = sum(
        1
        for record in records
        if record.status == "Excused"
    )

    attendance_percentage = (
        (
            present_days + late_days
        )
        / total_days
        * 100
        if total_days
        else 0
    )

    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name
        },

        "start_date": start_date,

        "end_date": end_date,

        "total_days": total_days,

        "present_days": present_days,

        "absent_days": absent_days,

        "late_days": late_days,

        "excused_days": excused_days,

        "attendance_percentage": round(
            attendance_percentage,
            2
        ),

        "records": [
            {
                "id": record.id,
                "date":
                    record.attendance_date,
                "status":
                    record.status,
                "note":
                    record.note
            }

            for record in records
        ]
    }