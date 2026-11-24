import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/segmentasi_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def ensure_database():
    """Otomatis bikin database kalau belum ada (PostgreSQL / MySQL)."""
    url = make_url(DATABASE_URL)
    name, backend = url.database, url.get_backend_name()
    try:
        if backend == "postgresql":
            admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
            with admin.connect() as c:
                ada = c.execute(text("SELECT 1 FROM pg_database WHERE datname=:n"), {"n": name}).scalar()
                if not ada:
                    c.execute(text(f'CREATE DATABASE "{name}"'))
        elif backend == "mysql":
            admin = create_engine(url.set(database=None))
            with admin.connect() as c:
                c.execute(text(f"CREATE DATABASE IF NOT EXISTS `{name}`"))
    except Exception as e:  # noqa
        print(f"[WARN] Gagal auto-create database: {e}")


def init_db():
    ensure_database()
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
