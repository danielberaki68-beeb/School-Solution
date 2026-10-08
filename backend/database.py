from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ---------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------

DATABASE_URL = "sqlite:///./school_solution.db"


# ---------------------------------------------------------
# DATABASE ENGINE
# ---------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# ---------------------------------------------------------
# DATABASE SESSION
# ---------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# ---------------------------------------------------------
# BASE CLASS
# ---------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    """
    Create a database session for an API request.
    The session is automatically closed after the request.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()