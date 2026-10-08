from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FeeType, FeeRecord, Payment, Student


# =========================================================
# FEES ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/fees",
    tags=["Fees & Payments"]
)


# =========================================================
# PYDANTIC SCHEMAS
# =========================================================

class FeeTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = ""
    is_active: bool = True


class FeeTypeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = ""
    is_active: bool = True


class FeeRecordCreate(BaseModel):
    student_id: int
    fee_type_id: int
    academic_year: str = Field(min_length=1, max_length=50)
    term: str = Field(min_length=1, max_length=50)
    amount_due: float = Field(ge=0)


class FeeRecordUpdate(BaseModel):
    amount_due: float = Field(ge=0)
    academic_year: str = Field(min_length=1, max_length=50)
    term: str = Field(min_length=1, max_length=50)


class PaymentCreate(BaseModel):
    fee_record_id: int
    amount: float = Field(gt=0)
    payment_date: date
    payment_method: str = Field(
        default="Cash",
        max_length=50
    )
    reference: Optional[str] = ""
    note: Optional[str] = ""


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def calculate_status(
    amount_due: float,
    amount_paid: float
) -> str:

    if amount_paid <= 0:
        return "Unpaid"

    if amount_paid >= amount_due:
        return "Paid"

    return "Partially Paid"


def fee_to_dict(
    fee: FeeRecord
):

    student = fee.student
    fee_type = fee.fee_type

    return {
        "id": fee.id,

        "student": {
            "id": student.id if student else None,
            "student_id": (
                student.student_id
                if student
                else ""
            ),
            "name": (
                f"{student.first_name} "
                f"{student.last_name}"
                if student
                else ""
            )
        },

        "fee_type": {
            "id": (
                fee_type.id
                if fee_type
                else None
            ),
            "name": (
                fee_type.name
                if fee_type
                else ""
            )
        },

        "academic_year": fee.academic_year,
        "term": fee.term,

        "amount_due": round(
            fee.amount_due,
            2
        ),

        "amount_paid": round(
            fee.amount_paid,
            2
        ),

        "balance": round(
            fee.balance,
            2
        ),

        "status": fee.status,

        "created_at": fee.created_at
    }


# =========================================================
# FEE TYPES
# =========================================================

@router.post("/types")
def create_fee_type(
    data: FeeTypeCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(FeeType)
        .filter(
            FeeType.name.ilike(
                data.name.strip()
            )
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Fee type already exists."
        )

    fee_type = FeeType(
        name=data.name.strip(),
        description=(
            data.description or ""
        ).strip(),
        is_active=data.is_active
    )

    db.add(fee_type)
    db.commit()
    db.refresh(fee_type)

    return {
        "message": "Fee type created successfully.",
        "fee_type": {
            "id": fee_type.id,
            "name": fee_type.name,
            "description": fee_type.description,
            "is_active": fee_type.is_active
        }
    }


# =========================================================
# LIST FEE TYPES
# =========================================================

@router.get("/types")
def list_fee_types(
    active_only: bool = False,
    db: Session = Depends(get_db)
):

    query = db.query(FeeType)

    if active_only:

        query = query.filter(
            FeeType.is_active == True
        )

    fee_types = (
        query
        .order_by(FeeType.id.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "is_active": item.is_active
        }
        for item in fee_types
    ]


# =========================================================
# GET FEE TYPE
# =========================================================

@router.get("/types/{fee_type_id}")
def get_fee_type(
    fee_type_id: int,
    db: Session = Depends(get_db)
):

    fee_type = (
        db.query(FeeType)
        .filter(
            FeeType.id == fee_type_id
        )
        .first()
    )

    if fee_type is None:

        raise HTTPException(
            status_code=404,
            detail="Fee type not found."
        )

    return {
        "id": fee_type.id,
        "name": fee_type.name,
        "description": fee_type.description,
        "is_active": fee_type.is_active
    }


# =========================================================
# UPDATE FEE TYPE
# =========================================================

@router.put("/types/{fee_type_id}")
def update_fee_type(
    fee_type_id: int,
    data: FeeTypeUpdate,
    db: Session = Depends(get_db)
):

    fee_type = (
        db.query(FeeType)
        .filter(
            FeeType.id == fee_type_id
        )
        .first()
    )

    if fee_type is None:

        raise HTTPException(
            status_code=404,
            detail="Fee type not found."
        )

    duplicate = (
        db.query(FeeType)
        .filter(
            FeeType.name.ilike(
                data.name.strip()
            ),
            FeeType.id != fee_type_id
        )
        .first()
    )

    if duplicate:

        raise HTTPException(
            status_code=400,
            detail="Another fee type with this name already exists."
        )

    fee_type.name = data.name.strip()

    fee_type.description = (
        data.description or ""
    ).strip()

    fee_type.is_active = data.is_active

    db.commit()
    db.refresh(fee_type)

    return {
        "message": "Fee type updated successfully.",
        "fee_type": {
            "id": fee_type.id,
            "name": fee_type.name,
            "description": fee_type.description,
            "is_active": fee_type.is_active
        }
    }


# =========================================================
# DELETE / DEACTIVATE FEE TYPE
# =========================================================

@router.delete("/types/{fee_type_id}")
def delete_fee_type(
    fee_type_id: int,
    db: Session = Depends(get_db)
):

    fee_type = (
        db.query(FeeType)
        .filter(
            FeeType.id == fee_type_id
        )
        .first()
    )

    if fee_type is None:

        raise HTTPException(
            status_code=404,
            detail="Fee type not found."
        )

    used = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.fee_type_id
            == fee_type_id
        )
        .first()
    )

    if used:

        fee_type.is_active = False

        db.commit()

        return {
            "message":
                "Fee type has existing records, so it was deactivated."
        }

    db.delete(fee_type)
    db.commit()

    return {
        "message":
            "Fee type deleted successfully."
    }


# =========================================================
# CREATE FEE RECORD
# =========================================================

@router.post("/")
def create_fee_record(
    data: FeeRecordCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student = (
        db.query(Student)
        .filter(
            Student.id == data.student_id
        )
        .first()
    )

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )

    # -----------------------------------------------------
    # FEE TYPE
    # -----------------------------------------------------

    fee_type = (
        db.query(FeeType)
        .filter(
            FeeType.id == data.fee_type_id
        )
        .first()
    )

    if fee_type is None:

        raise HTTPException(
            status_code=404,
            detail="Fee type not found."
        )

    if not fee_type.is_active:

        raise HTTPException(
            status_code=400,
            detail="Fee type is inactive."
        )

    # -----------------------------------------------------
    # DUPLICATE CHECK
    # -----------------------------------------------------

    existing = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.student_id
            == data.student_id,

            FeeRecord.fee_type_id
            == data.fee_type_id,

            FeeRecord.academic_year
            == data.academic_year.strip(),

            FeeRecord.term
            == data.term.strip()
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail=(
                "This fee has already been assigned "
                "to this student for this academic "
                "year and term."
            )
        )

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    amount_due = round(
        data.amount_due,
        2
    )

    fee_record = FeeRecord(

        student_id=data.student_id,

        fee_type_id=data.fee_type_id,

        academic_year=data.academic_year.strip(),

        term=data.term.strip(),

        amount_due=amount_due,

        amount_paid=0.0,

        balance=amount_due,

        status=calculate_status(
            amount_due,
            0.0
        ),

        created_at=datetime.now().isoformat()
    )

    db.add(fee_record)
    db.commit()
    db.refresh(fee_record)

    return {
        "message": "Fee assigned successfully.",
        "fee": fee_to_dict(fee_record)
    }


# =========================================================
# LIST ALL FEE RECORDS
# =========================================================

@router.get("/")
def list_fee_records(
    student_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    term: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = db.query(FeeRecord)

    if student_id is not None:

        query = query.filter(
            FeeRecord.student_id
            == student_id
        )

    if academic_year:

        query = query.filter(
            FeeRecord.academic_year
            == academic_year.strip()
        )

    if term:

        query = query.filter(
            FeeRecord.term
            == term.strip()
        )

    if status:

        query = query.filter(
            FeeRecord.status
            == status.strip()
        )

    fees = (
        query
        .order_by(
            FeeRecord.id.desc()
        )
        .all()
    )

    return [
        fee_to_dict(fee)
        for fee in fees
    ]


# =========================================================
# GET SINGLE FEE RECORD
# =========================================================

@router.get("/{fee_id}")
def get_fee_record(
    fee_id: int,
    db: Session = Depends(get_db)
):

    fee = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.id == fee_id
        )
        .first()
    )

    if fee is None:

        raise HTTPException(
            status_code=404,
            detail="Fee record not found."
        )

    return fee_to_dict(fee)


# =========================================================
# UPDATE FEE RECORD
# =========================================================

@router.put("/{fee_id}")
def update_fee_record(
    fee_id: int,
    data: FeeRecordUpdate,
    db: Session = Depends(get_db)
):

    fee = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.id == fee_id
        )
        .first()
    )

    if fee is None:

        raise HTTPException(
            status_code=404,
            detail="Fee record not found."
        )

    # Do not allow amount_due to become
    # lower than the amount already paid.

    if data.amount_due < fee.amount_paid:

        raise HTTPException(
            status_code=400,
            detail=(
                "Amount due cannot be less than "
                "the amount already paid."
            )
        )

    fee.amount_due = round(
        data.amount_due,
        2
    )

    fee.academic_year = (
        data.academic_year.strip()
    )

    fee.term = (
        data.term.strip()
    )

    fee.balance = round(
        fee.amount_due - fee.amount_paid,
        2
    )

    fee.status = calculate_status(
        fee.amount_due,
        fee.amount_paid
    )

    db.commit()
    db.refresh(fee)

    return {
        "message": "Fee record updated successfully.",
        "fee": fee_to_dict(fee)
    }


# =========================================================
# DELETE FEE RECORD
# =========================================================

@router.delete("/{fee_id}")
def delete_fee_record(
    fee_id: int,
    db: Session = Depends(get_db)
):

    fee = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.id == fee_id
        )
        .first()
    )

    if fee is None:

        raise HTTPException(
            status_code=404,
            detail="Fee record not found."
        )

    payments = (
        db.query(Payment)
        .filter(
            Payment.fee_record_id
            == fee_id
        )
        .all()
    )

    if payments:

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete a fee record "
                "that has payments."
            )
        )

    db.delete(fee)
    db.commit()

    return {
        "message":
            "Fee record deleted successfully."
    }


# =========================================================
# RECORD PAYMENT
# =========================================================

@router.post("/payments")
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # FIND FEE
    # -----------------------------------------------------

    fee = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.id
            == data.fee_record_id
        )
        .first()
    )

    if fee is None:

        raise HTTPException(
            status_code=404,
            detail="Fee record not found."
        )

    # -----------------------------------------------------
    # PAYMENT LIMIT
    # -----------------------------------------------------

    remaining = round(
        fee.amount_due
        - fee.amount_paid,
        2
    )

    if data.amount > remaining:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment is greater than the "
                f"remaining balance of {remaining:.2f}."
            )
        )

    # -----------------------------------------------------
    # CREATE PAYMENT
    # -----------------------------------------------------

    payment = Payment(

        fee_record_id=
            data.fee_record_id,

        student_id=
            fee.student_id,

        amount=round(
            data.amount,
            2
        ),

        payment_date=
            data.payment_date,

        payment_method=
            data.payment_method.strip(),

        reference=(
            data.reference or ""
        ).strip(),

        note=(
            data.note or ""
        ).strip()
    )

    db.add(payment)

    # -----------------------------------------------------
    # UPDATE FEE
    # -----------------------------------------------------

    fee.amount_paid = round(
        fee.amount_paid
        + data.amount,
        2
    )

    fee.balance = round(
        fee.amount_due
        - fee.amount_paid,
        2
    )

    fee.status = calculate_status(
        fee.amount_due,
        fee.amount_paid
    )

    db.commit()
    db.refresh(payment)
    db.refresh(fee)

    return {
        "message":
            "Payment recorded successfully.",

        "payment": {

            "id":
                payment.id,

            "fee_record_id":
                payment.fee_record_id,

            "student_id":
                payment.student_id,

            "amount":
                payment.amount,

            "payment_date":
                payment.payment_date,

            "payment_method":
                payment.payment_method,

            "reference":
                payment.reference,

            "note":
                payment.note
        },

        "fee": fee_to_dict(fee)
    }


# =========================================================
# PAYMENT HISTORY
# =========================================================

@router.get("/payments/history")
def payment_history(
    student_id: Optional[int] = None,
    fee_record_id: Optional[int] = None,
    db: Session = Depends(get_db)
):

    query = db.query(Payment)

    if student_id is not None:

        query = query.filter(
            Payment.student_id
            == student_id
        )

    if fee_record_id is not None:

        query = query.filter(
            Payment.fee_record_id
            == fee_record_id
        )

    payments = (
        query
        .order_by(
            Payment.id.desc()
        )
        .all()
    )

    return [

        {

            "id":
                payment.id,

            "fee_record_id":
                payment.fee_record_id,

            "student_id":
                payment.student_id,

            "amount":
                round(
                    payment.amount,
                    2
                ),

            "payment_date":
                payment.payment_date,

            "payment_method":
                payment.payment_method,

            "reference":
                payment.reference,

            "note":
                payment.note

        }

        for payment in payments
    ]


# =========================================================
# STUDENT FEE SUMMARY
# =========================================================

@router.get("/student/{student_id}/summary")
def student_fee_summary(
    student_id: int,
    academic_year: Optional[str] = None,
    term: Optional[str] = None,
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

    query = (
        db.query(FeeRecord)
        .filter(
            FeeRecord.student_id
            == student_id
        )
    )

    if academic_year:

        query = query.filter(
            FeeRecord.academic_year
            == academic_year.strip()
        )

    if term:

        query = query.filter(
            FeeRecord.term
            == term.strip()
        )

    fees = query.all()

    total_due = sum(
        fee.amount_due
        for fee in fees
    )

    total_paid = sum(
        fee.amount_paid
        for fee in fees
    )

    total_balance = sum(
        fee.balance
        for fee in fees
    )

    return {

        "student": {

            "id":
                student.id,

            "student_id":
                student.student_id,

            "name":
                f"{student.first_name} "
                f"{student.last_name}"

        },

        "academic_year":
            academic_year,

        "term":
            term,

        "fee_count":
            len(fees),

        "total_due":
            round(total_due, 2),

        "total_paid":
            round(total_paid, 2),

        "total_balance":
            round(total_balance, 2),

        "status":

            (
                "Paid"
                if total_balance <= 0
                and total_due > 0

                else
                "Partially Paid"
                if total_paid > 0

                else
                "Unpaid"
            )
    }