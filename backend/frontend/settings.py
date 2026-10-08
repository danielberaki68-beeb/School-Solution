from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SchoolSettings


router = APIRouter(
    prefix="/api/settings",
    tags=["School Settings"]
)


# =========================================================
# SCHEMAS
# =========================================================

class SettingsCreate(BaseModel):
    school_name: str = Field(
        default="School Solution",
        min_length=1,
        max_length=200
    )

    school_name_tigrinya: str = Field(
        default="መፍትሕ",
        max_length=200
    )

    address: str = Field(
        default="",
        max_length=500
    )

    phone: str = Field(
        default="",
        max_length=100
    )

    email: str = Field(
        default="",
        max_length=200
    )

    website: str = Field(
        default="",
        max_length=300
    )

    principal_name: str = Field(
        default="",
        max_length=200
    )

    logo_path: str = Field(
        default="",
        max_length=500
    )


class SettingsUpdate(BaseModel):
    school_name: str = Field(
        min_length=1,
        max_length=200
    )

    school_name_tigrinya: str = Field(
        default="",
        max_length=200
    )

    address: str = Field(
        default="",
        max_length=500
    )

    phone: str = Field(
        default="",
        max_length=100
    )

    email: str = Field(
        default="",
        max_length=200
    )

    website: str = Field(
        default="",
        max_length=300
    )

    principal_name: str = Field(
        default="",
        max_length=200
    )

    logo_path: str = Field(
        default="",
        max_length=500
    )


# =========================================================
# RESPONSE HELPER
# =========================================================

def settings_response(settings):

    return {
        "id": settings.id,
        "school_name": settings.school_name,
        "school_name_tigrinya": settings.school_name_tigrinya or "",
        "address": settings.address or "",
        "phone": settings.phone or "",
        "email": settings.email or "",
        "website": settings.website or "",
        "principal_name": settings.principal_name or "",
        "logo_path": settings.logo_path or ""
    }


# =========================================================
# GET SETTINGS
# =========================================================

@router.get("/")
def get_settings(
    db: Session = Depends(get_db)
):

    settings = (
        db.query(SchoolSettings)
        .first()
    )

    # If no settings exist yet,
    # create default settings.
    if settings is None:

        settings = SchoolSettings(
            school_name="School Solution",
            school_name_tigrinya="መፍትሕ",
            address="",
            phone="",
            email="",
            website="",
            principal_name="",
            logo_path=""
        )

        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings_response(settings)


# =========================================================
# CREATE SETTINGS
# =========================================================

@router.post("/")
def create_settings(
    data: SettingsCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(SchoolSettings)
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="School settings already exist. Use PUT to update them."
        )


    settings = SchoolSettings(
        school_name=data.school_name.strip(),
        school_name_tigrinya=data.school_name_tigrinya.strip(),
        address=data.address.strip(),
        phone=data.phone.strip(),
        email=data.email.strip(),
        website=data.website.strip(),
        principal_name=data.principal_name.strip(),
        logo_path=data.logo_path.strip()
    )


    db.add(settings)
    db.commit()
    db.refresh(settings)


    return settings_response(settings)


# =========================================================
# UPDATE SETTINGS
# =========================================================

@router.put("/")
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db)
):

    settings = (
        db.query(SchoolSettings)
        .first()
    )


    if settings is None:

        settings = SchoolSettings(
            school_name=data.school_name.strip(),
            school_name_tigrinya=data.school_name_tigrinya.strip(),
            address=data.address.strip(),
            phone=data.phone.strip(),
            email=data.email.strip(),
            website=data.website.strip(),
            principal_name=data.principal_name.strip(),
            logo_path=data.logo_path.strip()
        )

        db.add(settings)

    else:

        settings.school_name = data.school_name.strip()
        settings.school_name_tigrinya = (
            data.school_name_tigrinya.strip()
        )
        settings.address = data.address.strip()
        settings.phone = data.phone.strip()
        settings.email = data.email.strip()
        settings.website = data.website.strip()
        settings.principal_name = (
            data.principal_name.strip()
        )
        settings.logo_path = data.logo_path.strip()


    db.commit()
    db.refresh(settings)


    return settings_response(settings)


# =========================================================
# DELETE SETTINGS
# =========================================================

@router.delete("/")
def delete_settings(
    db: Session = Depends(get_db)
):

    settings = (
        db.query(SchoolSettings)
        .first()
    )


    if settings is None:

        raise HTTPException(
            status_code=404,
            detail="School settings not found."
        )


    db.delete(settings)
    db.commit()


    return {
        "message": "School settings deleted successfully."
    }