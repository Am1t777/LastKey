# create_engine builds the SQLAlchemy engine that manages the actual DB connection pool
from sqlalchemy import create_engine
# declarative_base provides the base class all ORM models inherit from
# sessionmaker creates a factory for new database sessions
from sqlalchemy.orm import declarative_base, sessionmaker

# Import settings to get the DATABASE_URL and pick the right connection arguments
from app.config import settings

# SQLite requires check_same_thread=False so the same connection can be used across
# threads (needed because FastAPI runs request handlers in a thread pool).
# For PostgreSQL and other DBs this argument is ignored/not needed.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# engine is the low-level connection to the database — it manages the connection pool
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# SessionLocal is a factory; calling SessionLocal() returns a new ORM session
# autocommit=False means we control transactions manually with db.commit()
# autoflush=False means changes are not sent to DB until we explicitly flush or commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the declarative base class — all SQLAlchemy model classes inherit from it
# so their table metadata is registered and create_all() can discover them
Base = declarative_base()


# get_db is a FastAPI dependency that provides a database session to a route handler
def get_db():
    # Open a new session from the session factory
    db = SessionLocal()
    try:
        # yield makes this a generator — FastAPI injects the yielded value into the route
        yield db
    finally:
        # Always close the session after the request finishes to return the connection to the pool
        db.close()
