from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subject


# =========================================================
# SUBJECTS ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/subjects",
    tags=["Subjects"]
)


# =========================================================
# CREATE SUBJECT
# =========================================================

class SubjectCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=150
    )

    code: Optional[str] = Field(
        default=None,
        max_length=50
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )


# =========================================================
# UPDATE SUBJECT
# =========================================================

class SubjectUpdate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=150
    )

    code: Optional[str] = Field(
        default=None,
        max_length=50
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    is_active: bool = True


# =========================================================
# RESPONSE
# =========================================================

class SubjectResponse(BaseModel):

    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# CREATE SUBJECT
# =========================================================

@router.post(
    "/",
    response_model=SubjectResponse
)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db)
):

    name = data.name.strip()

    code = (
        data.code.strip().upper()
        if data.code
        else None
    )

    description = (
        data.description.strip()
        if data.description
        else ""
    )

    # -----------------------------------------------------
    # CHECK DUPLICATE CODE
    # -----------------------------------------------------

    if code:

        existing_code = (
            db.query(Subject)
            .filter(
                Subject.subject_code == code
            )
            .first()
        )

        if existing_code:

            raise HTTPException(
                status_code=400,
                detail="Subject code already exists."
            )

    # -----------------------------------------------------
    # CHECK DUPLICATE NAME
    # -----------------------------------------------------

    existing_name = (
        db.query(Subject)
        .filter(
            Subject.name == name,
            Subject.is_active == True
        )
        .first()
    )

    if existing_name:

        raise HTTPException(
            status_code=400,
            detail="This subject already exists."
        )

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    subject = Subject(
        name=name,
        subject_code=code,
        description=description,
        is_active=True
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject


# =========================================================
# GET ALL SUBJECTS
# =========================================================

@router.get(
    "/",
    response_model=list[SubjectResponse]
)
def get_subjects(
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):

    query = db.query(Subject)

    if active_only:

        query = query.filter(
            Subject.is_active == True
        )

    if search:

        search_value = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            (
                Subject.name.ilike(
                    search_value
                )
            )
            |
            (
                Subject.subject_code.ilike(
                    search_value
                )
            )
        )

    return (
        query
        .order_by(
            Subject.name.asc()
        )
        .all()
    )


# =========================================================
# GET ONE SUBJECT
# =========================================================

@router.get(
    "/{subject_id}",
    response_model=SubjectResponse
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db)
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

    return subject


# =========================================================
# UPDATE SUBJECT
# =========================================================

@router.put(
    "/{subject_id}",
    response_model=SubjectResponse
)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db)
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

    name = data.name.strip()

    code = (
        data.code.strip().upper()
        if data.code
        else None
    )

    description = (
        data.description.strip()
        if data.description
        else ""
    )

    # -----------------------------------------------------
    # CHECK DUPLICATE CODE
    # -----------------------------------------------------

    if code:

        duplicate_code = (
            db.query(Subject)
            .filter(
                Subject.subject_code == code,
                Subject.id != subject_id
            )
            .first()
        )

        if duplicate_code:

            raise HTTPException(
                status_code=400,
                detail="Subject code already exists."
            )

    # -----------------------------------------------------
    # CHECK DUPLICATE NAME
    # -----------------------------------------------------

    duplicate_name = (
        db.query(Subject)
        .filter(
            Subject.name == name,
            Subject.id != subject_id,
            Subject.is_active == True
        )
        .first()
    )

    if duplicate_name:

        raise HTTPException(
            status_code=400,
            detail="This subject already exists."
        )

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    subject.name = name
    subject.subject_code = code
    subject.description = description
    subject.is_active = data.is_active

    db.commit()
    db.refresh(subject)

    return subject


# =========================================================
# DELETE SUBJECT
# =========================================================

@router.delete(
    "/{subject_id}"
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db)
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

    # -----------------------------------------------------
    # SOFT DELETE
    # -----------------------------------------------------

    subject.is_active = False

    db.commit()

    return {
        "message": "Subject deleted successfully.",
        "subject_id": subject_id
    }