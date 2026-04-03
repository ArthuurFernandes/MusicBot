from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from flask import current_app


class Base(DeclarativeBase):
    pass


def get_engine():
    return create_engine(
        current_app.config["DATABASE_URL"],
        pool_pre_ping=True,
    )


def get_session():
    engine  = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Cria todas as tabelas no banco se não existirem."""
    from app.database import models  # noqa: F401 — importa para registrar os modelos
    engine = get_engine()
    Base.metadata.create_all(engine)
