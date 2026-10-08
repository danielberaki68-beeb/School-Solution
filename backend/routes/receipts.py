from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

from ..database import get_db
from ..models import Payment, FeeRecord, FeeType, Student


router = APIRouter(
    prefix="/api/receipts",
    tags=["Receipts"]
)


@router.get("/payment/{payment_id}/pdf")
def generate_payment_receipt(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a professional PDF receipt for a payment.
    """

    # ---------------------------------------------------------
    # Find payment
    # ---------------------------------------------------------
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    # ---------------------------------------------------------
    # Find student
    # ---------------------------------------------------------
    student = (
        db.query(Student)
        .filter(Student.id == payment.student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    # ---------------------------------------------------------
    # Find fee record
    # ---------------------------------------------------------
    fee_record = (
        db.query(FeeRecord)
        .filter(FeeRecord.id == payment.fee_record_id)
        .first()
    )

    if not fee_record:
        raise HTTPException(
            status_code=404,
            detail="Fee record not found"
        )

    # ---------------------------------------------------------
    # Find fee type
    # ---------------------------------------------------------
    fee_type = (
        db.query(FeeType)
        .filter(FeeType.id == fee_record.fee_type_id)
        .first()
    )

    if not fee_type:
        raise HTTPException(
            status_code=404,
            detail="Fee type not found"
        )

    # ---------------------------------------------------------
    # Calculate remaining balance
    # ---------------------------------------------------------
    remaining_balance = float(fee_record.balance or 0)

    # ---------------------------------------------------------
    # Create PDF in memory
    # ---------------------------------------------------------
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Payment Receipt {payment.reference or payment.id}",
        author="School Solution"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=5
    )

    school_style = ParagraphStyle(
        "SchoolName",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=10
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "NormalReceipt",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    total_style = ParagraphStyle(
        "Total",
        parent=styles["Normal"],
        fontSize=13,
        leading=17,
        alignment=TA_LEFT
    )

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "SCHOOL SOLUTION",
            school_style
        )
    )

    story.append(
        Paragraph(
            "መፍትሕ",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            "PAYMENT RECEIPT",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Official School Payment Receipt",
            subtitle_style
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.black,
            spaceBefore=3,
            spaceAfter=12
        )
    )

    # ---------------------------------------------------------
    # Receipt information
    # ---------------------------------------------------------

    receipt_number = payment.reference or f"PAY-{payment.id:04d}"

    payment_date = payment.payment_date

    if payment_date:
        try:
            formatted_date = payment_date.strftime("%d %B %Y")
        except Exception:
            formatted_date = str(payment_date)
    else:
        formatted_date = datetime.now().strftime("%d %B %Y")

    receipt_data = [
        [
            Paragraph("<b>Receipt Number</b>", normal_style),
            Paragraph(str(receipt_number), normal_style),
            Paragraph("<b>Date</b>", normal_style),
            Paragraph(formatted_date, normal_style),
        ],
        [
            Paragraph("<b>Academic Year</b>", normal_style),
            Paragraph(str(fee_record.academic_year), normal_style),
            Paragraph("<b>Term</b>", normal_style),
            Paragraph(str(fee_record.term), normal_style),
        ],
    ]

    receipt_table = Table(
        receipt_data,
        colWidths=[
            35 * mm,
            55 * mm,
            25 * mm,
            45 * mm
        ]
    )

    receipt_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(receipt_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # Student information
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "STUDENT INFORMATION",
            section_style
        )
    )

    student_name = (
        getattr(student, "name", None)
        or f"{getattr(student, 'first_name', '')} "
           f"{getattr(student, 'last_name', '')}".strip()
    )

    student_data = [
        [
            Paragraph("<b>Student Name</b>", normal_style),
            Paragraph(str(student_name), normal_style),
        ],
        [
            Paragraph("<b>Student ID</b>", normal_style),
            Paragraph(str(student.student_id), normal_style),
        ],
    ]

    student_table = Table(
        student_data,
        colWidths=[45 * mm, 115 * mm]
    )

    student_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(student_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # Payment information
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "PAYMENT INFORMATION",
            section_style
        )
    )

    payment_data = [
        [
            Paragraph("<b>Fee Type</b>", normal_style),
            Paragraph(str(fee_type.name), normal_style),
        ],
        [
            Paragraph("<b>Amount Paid</b>", normal_style),
            Paragraph(
                f"£{float(payment.amount):,.2f}",
                normal_style
            ),
        ],
        [
            Paragraph("<b>Payment Method</b>", normal_style),
            Paragraph(
                str(payment.payment_method or "Not specified"),
                normal_style
            ),
        ],
        [
            Paragraph("<b>Reference</b>", normal_style),
            Paragraph(
                str(payment.reference or ""),
                normal_style
            ),
        ],
        [
            Paragraph("<b>Remaining Balance</b>", normal_style),
            Paragraph(
                f"£{remaining_balance:,.2f}",
                normal_style
            ),
        ],
        [
            Paragraph("<b>Status</b>", normal_style),
            Paragraph(
                str(fee_record.status),
                normal_style
            ),
        ],
    ]

    payment_table = Table(
        payment_data,
        colWidths=[55 * mm, 105 * mm]
    )

    payment_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(payment_table)
    story.append(Spacer(1, 15))

    # ---------------------------------------------------------
    # Total
    # ---------------------------------------------------------

    total_box = Table(
        [
            [
                Paragraph(
                    "<b>AMOUNT RECEIVED</b>",
                    total_style
                ),
                Paragraph(
                    f"<b>£{float(payment.amount):,.2f}</b>",
                    total_style
                ),
            ]
        ],
        colWidths=[110 * mm, 50 * mm]
    )

    total_box.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    story.append(total_box)
    story.append(Spacer(1, 18))

    # ---------------------------------------------------------
    # Note
    # ---------------------------------------------------------

    if payment.note:
        story.append(
            Paragraph(
                "<b>Note:</b> " + str(payment.note),
                normal_style
            )
        )
        story.append(Spacer(1, 15))

    # ---------------------------------------------------------
    # Signature area
    # ---------------------------------------------------------

    signature_data = [
        [
            Paragraph("____________________________", normal_style),
            Paragraph("____________________________", normal_style),
        ],
        [
            Paragraph("Accountant / Cashier", normal_style),
            Paragraph("Parent / Guardian", normal_style),
        ],
    ]

    signature_table = Table(
        signature_data,
        colWidths=[80 * mm, 80 * mm]
    )

    signature_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    story.append(signature_table)
    story.append(Spacer(1, 15))

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.grey,
            spaceBefore=5,
            spaceAfter=6
        )
    )

    story.append(
        Paragraph(
            "Thank you for your payment.",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            "School Solution — መፍትሕ",
            subtitle_style
        )
    )

    # ---------------------------------------------------------
    # Build PDF
    # ---------------------------------------------------------

    document.build(story)

    buffer.seek(0)

    filename = (
        f"payment_receipt_"
        f"{receipt_number.replace('/', '-')}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{filename}"'
            )
        }
    )