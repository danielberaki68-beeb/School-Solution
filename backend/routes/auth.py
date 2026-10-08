import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# ============================================================
# SECURITY SETTINGS
# ============================================================

SECRET_KEY = os.getenv(
    "SCHOOL_SOLUTION_SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_BEFORE_PRODUCTION"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Secure password hashing using PBKDF2-HMAC-SHA256.
    """

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        "pbkdf2_sha256$310000$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(
    password: str,
    stored_hash: str
) -> bool:

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations)
        )

        return hmac.compare_digest(
            calculated_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError):
        return False


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100
    )

    password: str = Field(
        min_length=8,
        max_length=128
    )

    full_name: str = Field(
        min_length=2,
        max_length=200
    )

    role: str = Field(
        default="Staff",
        max_length=50
    )


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_minutes: int


# ============================================================
# JWT
# ============================================================

def create_access_token(
    user: User
) -> str:

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(
        lambda: None
    ),
    db: Session = Depends(get_db)
):
    """
    This function is replaced by get_current_user_from_header
    below. Kept out of the public API.
    """
    raise HTTPException(
        status_code=401,
        detail="Authentication required"
    )


# ============================================================
# AUTHORIZATION HEADER DEPENDENCY
# ============================================================

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


# ============================================================
# ROLE CHECK
# ============================================================

def require_roles(*allowed_roles):

    def role_checker(
        current_user: User = Depends(
            get_authenticated_user
        )
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker


# ============================================================
# REGISTER USER
# ============================================================

@router.post("/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new school system user.
    """

    existing_user = (
        db.query(User)
        .filter(User.username == request.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    allowed_roles = {
        "Admin",
        "Teacher",
        "Accountant",
        "Staff"
    }

    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid role. Choose Admin, Teacher, "
                "Accountant, or Staff."
            )
        )

    new_user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "is_active": new_user.is_active
        }
    }


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login and receive a JWT access token.
    """

    user = (
        db.query(User)
        .filter(User.username == request.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    if not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/me")
def get_my_profile(
    current_user: User = Depends(
        get_authenticated_user
    )
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


# ============================================================
# ADMIN TEST ENDPOINT
# ============================================================

@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(
        require_roles("Admin")
    )
):
    return {
        "message": "Admin access confirmed",
        "user": current_user.username,
        "role": current_user.role
    }


# ============================================================
# TEACHER TEST ENDPOINT
# ============================================================

@router.get("/teacher-test")
def teacher_test(
    current_user: User = Depends(
        require_roles("Admin", "Teacher")
    )
):
    return {
        "message": "Teacher access confirmed",
        "user": current_user.username,
        "role": current_user.role
    }


# ============================================================
# ACCOUNTANT TEST ENDPOINT
# ============================================================

@router.get("/accountant-test")
def accountant_test(
    current_user: User = Depends(
        require_roles("Admin", "Accountant")
    )
):
    return {
        "message": "Accountant access confirmed",
        "user": current_user.username,
        "role": current_user.role
    }