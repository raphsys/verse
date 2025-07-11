from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Translation(Base):
    __tablename__ = "translations"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    original_text = Column(String, nullable=False)
    translated_text = Column(String, nullable=False)
    provider = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

