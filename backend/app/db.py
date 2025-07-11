from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import Base as UserBase
from app.models.translation import Base as TranslationBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"  # Pour Postgres: "postgresql+psycopg2://user:pass@localhost/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    UserBase.metadata.create_all(bind=engine)
    TranslationBase.metadata.create_all(bind=engine)

