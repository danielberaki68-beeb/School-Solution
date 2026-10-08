from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# =========================================================
# SCHOOL SETTINGS
# =========================================================

class SchoolSettings(Base):
    __tablename__ = "school_settings"

    id = Column(Integer, primary_key=True, index=True)

    school_name = Column(
        String(200),
        nullable=False,
        default="School Solution"
    )

    school_name_tigrinya = Column(
        String(200),
        nullable=False,
        default="መፍትሕ"
    )

    address = Column(String(300), default="")
    phone = Column(String(50), default="")
    email = Column(String(150), default="")
    website = Column(String(200), default="")
    principal_name = Column(String(200), default="")
    logo_path = Column(String(500), default="")


# =========================================================
# USERS
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    full_name = Column(
        String(200),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="teacher"
    )

    is_active = Column(
        Boolean,
        default=True
    )

    teacher = relationship(
        "Teacher",
        back_populates="user",
        uselist=False
    )


# =========================================================
# CLASSES
# =========================================================

class ClassRoom(Base):
    __tablename__ = "class_rooms"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    academic_year = Column(
        String(50),
        nullable=False
    )

    description = Column(
        Text,
        default=""
    )

    students = relationship(
        "Student",
        back_populates="class_room"
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "academic_year",
            name="uq_class_academic_year"
        ),
    )


# =========================================================
# STUDENTS
# =========================================================

class Student(Base):
    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    last_name = Column(
        String(100),
        default=""
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    gender = Column(
        String(30),
        default=""
    )

    parent_name = Column(
        String(200),
        default=""
    )

    parent_phone = Column(
        String(50),
        default=""
    )

    email = Column(
        String(150),
        default=""
    )

    address = Column(
        String(300),
        default=""
    )

    class_id = Column(
        Integer,
        ForeignKey("class_rooms.id"),
        nullable=True
    )

    admission_date = Column(
        Date,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    class_room = relationship(
        "ClassRoom",
        back_populates="students"
    )

    marks = relationship(
        "Mark",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# =========================================================
# TEACHERS
# =========================================================

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    teacher_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    last_name = Column(
        String(100),
        default=""
    )

    phone = Column(
        String(50),
        default=""
    )

    email = Column(
        String(150),
        default=""
    )

    specialization = Column(
        String(150),
        default=""
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="teacher"
    )


# =========================================================
# SUBJECTS
# =========================================================

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    subject_code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    name = Column(
        String(150),
        nullable=False
    )

    description = Column(
        Text,
        default=""
    )

    is_active = Column(
        Boolean,
        default=True
    )

    marks = relationship(
        "Mark",
        back_populates="subject"
    )


# =========================================================
# CUSTOMIZABLE GRADING SYSTEM
# =========================================================

class GradeScale(Base):
    __tablename__ = "grade_scales"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    minimum_mark = Column(
        Float,
        nullable=False
    )

    maximum_mark = Column(
        Float,
        nullable=False
    )

    grade_name = Column(
        String(50),
        nullable=False
    )

    grade_point = Column(
        Float,
        default=0.0
    )

    remark = Column(
        String(200),
        default=""
    )

    display_order = Column(
        Integer,
        default=0
    )

    is_active = Column(
        Boolean,
        default=True
    )


# =========================================================
# STUDENT MARKS
# =========================================================

class Mark(Base):
    __tablename__ = "marks"

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

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id"),
        nullable=False
    )

    academic_year = Column(
        String(50),
        nullable=False
    )

    term = Column(
        String(50),
        nullable=False
    )

    mark = Column(
        Float,
        nullable=False
    )

    # Historical grade information.
    # This protects old reports if the grading system
    # changes later.

    grade_name = Column(
        String(50),
        default=""
    )

    grade_point = Column(
        Float,
        default=0.0
    )

    grade_remark = Column(
        String(200),
        default=""
    )

    teacher_comment = Column(
        Text,
        default=""
    )

    student = relationship(
        "Student",
        back_populates="marks"
    )

    subject = relationship(
        "Subject",
        back_populates="marks"
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "academic_year",
            "term",
            name="uq_student_subject_year_term"
        ),
    )
    # =========================================================
# FEE TYPE
# =========================================================

class FeeType(Base):
    __tablename__ = "fee_types"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(150),
        nullable=False,
        unique=True
    )

    description = Column(
        Text,
        default=""
    )

    is_active = Column(
        Boolean,
        default=True
    )


# =========================================================
# FEE RECORD
# =========================================================

class FeeRecord(Base):
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    fee_type_id = Column(
        Integer,
        ForeignKey("fee_types.id"),
        nullable=False
    )

    academic_year = Column(
        String(50),
        nullable=False
    )

    term = Column(
        String(50),
        nullable=False
    )

    amount_due = Column(
        Float,
        nullable=False,
        default=0.0
    )

    amount_paid = Column(
        Float,
        nullable=False,
        default=0.0
    )

    balance = Column(
        Float,
        nullable=False,
        default=0.0
    )

    status = Column(
        String(50),
        nullable=False,
        default="Unpaid"
    )

    created_at = Column(
        String(50),
        default=""
    )

    student = relationship("Student")

    fee_type = relationship("FeeType")


# =========================================================
# PAYMENT
# =========================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    fee_record_id = Column(
        Integer,
        ForeignKey("fee_records.id"),
        nullable=False
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    payment_date = Column(
        Date,
        nullable=False
    )

    payment_method = Column(
        String(50),
        default="Cash"
    )

    reference = Column(
        String(100),
        default=""
    )

    note = Column(
        Text,
        default=""
    )

    fee_record = relationship("FeeRecord")

    student = relationship("Student")