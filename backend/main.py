# ============================================================
# SCHOOL SOLUTION / መፍትሕ
# FastAPI Backend
# ============================================================

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# ============================================================
# ROUTERS
# ============================================================

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
# APPLICATION
# ============================================================

app = FastAPI(
    title="School Solution / መፍትሕ",
    description="School Solution / መፍትሕ - School Management System",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "School Solution",
        "name_tigrinya": "መፍትሕ",
        "version": "1.0.0",
    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get("/api")
def api_information():
    return {
        "message": "School Solution / መፍትሕ API is running",
        "app": "School Solution",
        "name_tigrinya": "መፍትሕ",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ============================================================
# ROUTERS
# ============================================================

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


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


if not FRONTEND_DIR.exists():
    print(
        f"WARNING: Frontend directory not found: {FRONTEND_DIR}"
    )
else:
    print(
        f"Frontend directory: {FRONTEND_DIR}"
    )


# ============================================================
# FRONTEND FILES
# ============================================================
#
# This serves:
#
# /index.html
# /dashboard.html
# /students.html
# /classes.html
# /subjects.html
# /teachers.html
# /marks.html
# /attendance.html
# /fees.html
# /receipts.html
# /reports.html
# /settings.html
# /about.html
# /app.js
# /style.css
#
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True,
    ),
    name="frontend",
)