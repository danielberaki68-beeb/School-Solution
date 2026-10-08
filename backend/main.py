from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine

from .routes.grades import router as grades_router
from .routes.students import router as students_router
from .routes.classes import router as classes_router
from .routes.subjects import router as subjects_router
from .routes.teachers import router as teachers_router
from .routes.marks import router as marks_router
from .routes.attendance import router as attendance_router
from .routes.reports import router as reports_router
from .routes.fees import router as fees_router
from .routes.receipts import router as receipts_router
from .routes.auth import router as auth_router


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="School Solution / መፍትሕ",
    description="Professional School Management System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================
#
# This allows the HTML/CSS/JavaScript frontend to communicate
# with the FastAPI backend.
#
# For development this allows all origins.
# We can restrict this before production deployment.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "School Solution / መፍትሕ API is running",
        "app": "School Solution",
        "name_tigrinya": "መፍትሕ",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "School Solution",
        "name_tigrinya": "መፍትሕ",
        "version": "1.0.0"
    }


# ============================================================
# REGISTER ROUTERS
# ============================================================

# Grading System
app.include_router(grades_router)

# Students
app.include_router(students_router)

# Classes
app.include_router(classes_router)

# Subjects
app.include_router(subjects_router)

# Teachers
app.include_router(teachers_router)

# Marks / Results
app.include_router(marks_router)

# Attendance
app.include_router(attendance_router)

# Reports
app.include_router(reports_router)

# Fees & Payments
app.include_router(fees_router)

# Payment Receipts
app.include_router(receipts_router)

# Authentication
app.include_router(auth_router)