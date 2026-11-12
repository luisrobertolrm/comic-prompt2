from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from prompt_clinica.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
