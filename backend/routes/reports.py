from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from ..database import get_db
from ..models import (
    ClassRoom,
    Mark,
    SchoolSettings,
    Student,
    Subject,
)


# =========================================================
# REPORTS ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


# =========================================================
# FONT SUPPORT
# =========================================================

def get_unicode_font():
    """
    Try to find a Unicode font that can display
    English and Tigrinya/Ethiopic characters.

    Windows commonly has Arial installed.
    DejaVu Sans is also checked if available.
    """

    possible_fonts = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/ARIAL.TTF"),
        Path("C:/Windows/Fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/DejaVuSans.ttf"),
    ]

    for font_path in possible_fonts:

        if font_path.exists():

            try:

                font_name = "SchoolSolutionUnicode"

                pdfmetrics.registerFont(
                    TTFont(
                        font_name,
                        str(font_path)
                    )
                )

                return font_name

            except Exception:
                pass

    return "Helvetica"


# =========================================================
# FIND STUDENT
# =========================================================

def find_student(
    student_id: int,
    db: Session
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
# FIND SCHOOL SETTINGS
# =========================================================

def get_school_information(db: Session):

    school = (
        db.query(SchoolSettings)
        .first()
    )

    if school is None:

        return {
            "name": "School Solution",
            "name_tigrinya": "መፍትሕ",
            "address": "",
            "phone": "",
            "email": "",
            "website": "",
            "principal_name": "",
            "logo_path": "",
        }

    return {
        "name": school.school_name,
        "name_tigrinya": school.school_name_tigrinya,
        "address": school.address or "",
        "phone": school.phone or "",
        "email": school.email or "",
        "website": school.website or "",
        "principal_name": school.principal_name or "",
        "logo_path": school.logo_path or "",
    }


# =========================================================
# BUILD REPORT DATA
# =========================================================

def build_report_data(
    student_id: int,
    academic_year: str,
    term: str,
    db: Session
):

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student = find_student(
        student_id,
        db
    )

    # -----------------------------------------------------
    # CLASS
    # -----------------------------------------------------

    class_room = None

    if student.class_id is not None:

        class_room = (
            db.query(ClassRoom)
            .filter(
                ClassRoom.id == student.class_id
            )
            .first()
        )

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    marks = (
        db.query(Mark)
        .filter(
            Mark.student_id == student_id,
            Mark.academic_year
            == academic_year.strip(),
            Mark.term
            == term.strip()
        )
        .order_by(
            Mark.subject_id.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # SCHOOL
    # -----------------------------------------------------

    school = get_school_information(db)

    # -----------------------------------------------------
    # TOTALS
    # -----------------------------------------------------

    total_marks = sum(
        item.mark
        for item in marks
    )

    subject_count = len(marks)

    average_mark = (
        total_marks / subject_count
        if subject_count > 0
        else 0
    )

    total_grade_points = sum(
        item.grade_point
        for item in marks
    )

    average_grade_point = (
        total_grade_points / subject_count
        if subject_count > 0
        else 0
    )

    # -----------------------------------------------------
    # OVERALL PERFORMANCE
    # -----------------------------------------------------

    if average_mark >= 90:

        overall_performance = "Excellent"

    elif average_mark >= 80:

        overall_performance = "Very Good"

    elif average_mark >= 70:

        overall_performance = "Good"

    elif average_mark >= 60:

        overall_performance = "Satisfactory"

    elif average_mark >= 50:

        overall_performance = "Pass"

    else:

        overall_performance = "Needs Improvement"

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------

    results = []

    for item in marks:

        subject = (
            db.query(Subject)
            .filter(
                Subject.id
                == item.subject_id
            )
            .first()
        )

        results.append({

            "mark_id":
                item.id,

            "subject_id":
                item.subject_id,

            "subject_code":
                subject.subject_code
                if subject
                else "",

            "subject_name":
                subject.name
                if subject
                else "Unknown",

            "mark":
                item.mark,

            "grade":
                item.grade_name,

            "grade_point":
                item.grade_point,

            "remark":
                item.grade_remark,

            "teacher_comment":
                item.teacher_comment
                or ""

        })

    # -----------------------------------------------------
    # BEST SUBJECT
    # -----------------------------------------------------

    best_subject = None

    if marks:

        best_mark = max(
            marks,
            key=lambda item: item.mark
        )

        subject = (
            db.query(Subject)
            .filter(
                Subject.id
                == best_mark.subject_id
            )
            .first()
        )

        if subject:

            best_subject = {

                "subject_id":
                    subject.id,

                "subject_code":
                    subject.subject_code,

                "subject_name":
                    subject.name,

                "mark":
                    best_mark.mark,

                "grade":
                    best_mark.grade_name
            }

    # -----------------------------------------------------
    # WEAKEST SUBJECT
    # -----------------------------------------------------

    weakest_subject = None

    if marks:

        weakest_mark = min(
            marks,
            key=lambda item: item.mark
        )

        subject = (
            db.query(Subject)
            .filter(
                Subject.id
                == weakest_mark.subject_id
            )
            .first()
        )

        if subject:

            weakest_subject = {

                "subject_id":
                    subject.id,

                "subject_code":
                    subject.subject_code,

                "subject_name":
                    subject.name,

                "mark":
                    weakest_mark.mark,

                "grade":
                    weakest_mark.grade_name
            }

    # -----------------------------------------------------
    # FINAL DATA
    # -----------------------------------------------------

    return {

        "school": school,

        "student": {

            "id":
                student.id,

            "student_id":
                student.student_id,

            "first_name":
                student.first_name,

            "last_name":
                student.last_name,

            "gender":
                student.gender,

            "class_id":
                student.class_id,

            "class_name":
                class_room.name
                if class_room
                else "",

            "academic_year":
                academic_year.strip(),

            "term":
                term.strip()

        },

        "summary": {

            "subject_count":
                subject_count,

            "total_marks":
                round(
                    total_marks,
                    2
                ),

            "average_mark":
                round(
                    average_mark,
                    2
                ),

            "average_grade_point":
                round(
                    average_grade_point,
                    2
                ),

            "overall_performance":
                overall_performance

        },

        "performance": {

            "best_subject":
                best_subject,

            "weakest_subject":
                weakest_subject

        },

        "results":
            results

    }


# =========================================================
# JSON REPORT CARD
# =========================================================

@router.get(
    "/student/{student_id}"
)
def get_student_report_card(

    student_id: int,

    academic_year: str = Query(
        min_length=1,
        max_length=50
    ),

    term: str = Query(
        min_length=1,
        max_length=50
    ),

    db: Session = Depends(get_db)

):

    return build_report_data(
        student_id=student_id,
        academic_year=academic_year,
        term=term,
        db=db
    )


# =========================================================
# PDF REPORT CARD
# =========================================================

@router.get(
    "/student/{student_id}/pdf"
)
def get_student_report_pdf(

    student_id: int,

    academic_year: str = Query(
        min_length=1,
        max_length=50
    ),

    term: str = Query(
        min_length=1,
        max_length=50
    ),

    db: Session = Depends(get_db)

):

    # -----------------------------------------------------
    # GET REPORT DATA
    # -----------------------------------------------------

    report = build_report_data(
        student_id=student_id,
        academic_year=academic_year,
        term=term,
        db=db
    )

    school = report["school"]
    student = report["student"]
    summary = report["summary"]
    performance = report["performance"]
    results = report["results"]

    # -----------------------------------------------------
    # CREATE PDF IN MEMORY
    # -----------------------------------------------------

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(

        pdf_buffer,

        pagesize=A4,

        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,

        title=(
            f"Report Card - "
            f"{student['first_name']} "
            f"{student['last_name']}"
        ),

        author="School Solution"
    )

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    font_name = get_unicode_font()

    # -----------------------------------------------------
    # STYLES
    # -----------------------------------------------------

    styles = getSampleStyleSheet()

    school_title_style = ParagraphStyle(

        "SchoolTitle",

        parent=styles["Title"],

        fontName=font_name,

        fontSize=20,

        leading=24,

        alignment=TA_CENTER,

        spaceAfter=4
    )

    school_tigrinya_style = ParagraphStyle(

        "SchoolTigrinya",

        parent=styles["Normal"],

        fontName=font_name,

        fontSize=16,

        leading=20,

        alignment=TA_CENTER,

        spaceAfter=4
    )

    report_title_style = ParagraphStyle(

        "ReportTitle",

        parent=styles["Heading2"],

        fontName=font_name,

        fontSize=14,

        leading=18,

        alignment=TA_CENTER,

        spaceBefore=5,

        spaceAfter=10
    )

    normal_style = ParagraphStyle(

        "NormalSchool",

        parent=styles["Normal"],

        fontName=font_name,

        fontSize=9,

        leading=12
    )

    center_style = ParagraphStyle(

        "CenterSchool",

        parent=normal_style,

        alignment=TA_CENTER
    )

    small_style = ParagraphStyle(

        "SmallSchool",

        parent=normal_style,

        fontSize=8,

        leading=10
    )

    # -----------------------------------------------------
    # STORY
    # -----------------------------------------------------

    story = []

    # -----------------------------------------------------
    # SCHOOL HEADER
    # -----------------------------------------------------

    story.append(
        Paragraph(
            school["name"],
            school_title_style
        )
    )

    if school["name_tigrinya"]:

        story.append(
            Paragraph(
                school["name_tigrinya"],
                school_tigrinya_style
            )
        )

    school_contact = []

    if school["address"]:
        school_contact.append(
            school["address"]
        )

    if school["phone"]:
        school_contact.append(
            f"Tel: {school['phone']}"
        )

    if school["email"]:
        school_contact.append(
            f"Email: {school['email']}"
        )

    if school["website"]:
        school_contact.append(
            school["website"]
        )

    if school_contact:

        story.append(
            Paragraph(
                " | ".join(school_contact),
                center_style
            )
        )

    story.append(
        Spacer(
            1,
            6 * mm
        )
    )

    story.append(
        Paragraph(
            "STUDENT REPORT CARD",
            report_title_style
        )
    )

    # -----------------------------------------------------
    # STUDENT INFORMATION
    # -----------------------------------------------------

    student_name = (
        f"{student['first_name']} "
        f"{student['last_name']}"
    )

    student_information = [

        [
            Paragraph(
                "<b>Student Name</b>",
                normal_style
            ),
            Paragraph(
                student_name,
                normal_style
            ),

            Paragraph(
                "<b>Student ID</b>",
                normal_style
            ),
            Paragraph(
                student["student_id"],
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Class</b>",
                normal_style
            ),
            Paragraph(
                student["class_name"],
                normal_style
            ),

            Paragraph(
                "<b>Academic Year</b>",
                normal_style
            ),
            Paragraph(
                student["academic_year"],
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Term</b>",
                normal_style
            ),
            Paragraph(
                student["term"],
                normal_style
            ),

            Paragraph(
                "<b>Gender</b>",
                normal_style
            ),
            Paragraph(
                student["gender"] or "",
                normal_style
            )
        ]

    ]

    student_table = Table(

        student_information,

        colWidths=[
            30 * mm,
            60 * mm,
            35 * mm,
            55 * mm
        ]
    )

    student_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF2F8")
            ),

            (
                "BACKGROUND",
                (2, 0),
                (2, -1),
                colors.HexColor("#EAF2F8")
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    story.append(
        student_table
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # -----------------------------------------------------
    # SUBJECT TABLE
    # -----------------------------------------------------

    subject_data = [

        [
            Paragraph(
                "<b>No.</b>",
                center_style
            ),

            Paragraph(
                "<b>Subject</b>",
                center_style
            ),

            Paragraph(
                "<b>Mark</b>",
                center_style
            ),

            Paragraph(
                "<b>Grade</b>",
                center_style
            ),

            Paragraph(
                "<b>Grade Point</b>",
                center_style
            ),

            Paragraph(
                "<b>Remark</b>",
                center_style
            )

        ]

    ]

    for index, result in enumerate(
        results,
        start=1
    ):

        subject_data.append(

            [

                Paragraph(
                    str(index),
                    center_style
                ),

                Paragraph(
                    (
                        f"{result['subject_name']} "
                        f"({result['subject_code']})"
                    ),
                    normal_style
                ),

                Paragraph(
                    f"{result['mark']:.2f}",
                    center_style
                ),

                Paragraph(
                    result["grade"] or "",
                    center_style
                ),

                Paragraph(
                    f"{result['grade_point']:.2f}",
                    center_style
                ),

                Paragraph(
                    result["remark"] or "",
                    normal_style
                )

            ]
        )

    subject_table = Table(

        subject_data,

        colWidths=[
            10 * mm,
            58 * mm,
            22 * mm,
            20 * mm,
            28 * mm,
            42 * mm
        ],

        repeatRows=1
    )

    subject_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E78")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, 0),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    story.append(
        subject_table
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    summary_data = [

        [
            Paragraph(
                "<b>Subjects</b>",
                center_style
            ),

            Paragraph(
                "<b>Total Marks</b>",
                center_style
            ),

            Paragraph(
                "<b>Average</b>",
                center_style
            ),

            Paragraph(
                "<b>Average Grade Point</b>",
                center_style
            ),

            Paragraph(
                "<b>Performance</b>",
                center_style
            )
        ],

        [
            Paragraph(
                str(summary["subject_count"]),
                center_style
            ),

            Paragraph(
                str(summary["total_marks"]),
                center_style
            ),

            Paragraph(
                str(summary["average_mark"]),
                center_style
            ),

            Paragraph(
                str(summary["average_grade_point"]),
                center_style
            ),

            Paragraph(
                summary["overall_performance"],
                center_style
            )
        ]

    ]

    summary_table = Table(

        summary_data,

        colWidths=[
            30 * mm,
            35 * mm,
            30 * mm,
            42 * mm,
            43 * mm
        ]
    )

    summary_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#D9EAF7")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                font_name
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # -----------------------------------------------------
    # PERFORMANCE SECTION
    # -----------------------------------------------------

    best = performance["best_subject"]
    weakest = performance["weakest_subject"]

    best_text = "N/A"

    if best:

        best_text = (
            f"{best['subject_name']} "
            f"({best['mark']:.2f}% - "
            f"{best['grade']})"
        )

    weakest_text = "N/A"

    if weakest:

        weakest_text = (
            f"{weakest['subject_name']} "
            f"({weakest['mark']:.2f}% - "
            f"{weakest['grade']})"
        )

    performance_data = [

        [
            Paragraph(
                "<b>Best Subject</b>",
                normal_style
            ),

            Paragraph(
                best_text,
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Weakest Subject</b>",
                normal_style
            ),

            Paragraph(
                weakest_text,
                normal_style
            )
        ]

    ]

    performance_table = Table(

        performance_data,

        colWidths=[
            45 * mm,
            135 * mm
        ]
    )

    performance_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF2F8")
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    story.append(
        performance_table
    )

    story.append(
        Spacer(
            1,
            8 * mm
        )
    )

    # -----------------------------------------------------
    # TEACHER COMMENTS
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "<b>Teacher Comments</b>",
            normal_style
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    comments = []

    for result in results:

        if result["teacher_comment"]:

            comments.append(

                f"<b>{result['subject_name']}:</b> "
                f"{result['teacher_comment']}"

            )

    if comments:

        for comment in comments:

            story.append(
                Paragraph(
                    comment,
                    small_style
                )

            )

            story.append(
                Spacer(
                    1,
                    1.5 * mm
                )
            )

    else:

        story.append(
            Paragraph(
                "No teacher comments recorded.",
                small_style
            )
        )

    story.append(
        Spacer(
            1,
            12 * mm
        )
    )

    # -----------------------------------------------------
    # SIGNATURE SECTION
    # -----------------------------------------------------

    signature_data = [

        [
            Paragraph(
                "____________________________",
                center_style
            ),

            Paragraph(
                "____________________________",
                center_style
            ),

            Paragraph(
                "____________________________",
                center_style
            )
        ],

        [
            Paragraph(
                "Class Teacher",
                center_style
            ),

            Paragraph(
                "Principal",
                center_style
            ),

            Paragraph(
                "Parent / Guardian",
                center_style
            )
        ]

    ]

    signature_table = Table(

        signature_data,

        colWidths=[
            60 * mm,
            60 * mm,
            60 * mm
        ]
    )

    signature_table.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            )

        ])
    )

    story.append(
        signature_table
    )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    story.append(
        Spacer(
            1,
            8 * mm
        )
    )

    story.append(
        Paragraph(
            "Generated by School Solution • መፍትሕ",
            center_style
        )
    )

    # -----------------------------------------------------
    # BUILD PDF
    # -----------------------------------------------------

    document.build(
        story
    )

    pdf_buffer.seek(0)

    # -----------------------------------------------------
    # FILE NAME
    # -----------------------------------------------------

    safe_student_name = (
        f"{student['first_name']}_"
        f"{student['last_name']}"
    )

    filename = (
        f"Report_Card_"
        f"{safe_student_name}_"
        f"{academic_year.replace('/', '-')}_"
        f"Term_{term}.pdf"
    )

    # -----------------------------------------------------
    # RETURN PDF
    # -----------------------------------------------------

    return StreamingResponse(

        pdf_buffer,

        media_type="application/pdf",

        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }

    )