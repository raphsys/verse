from sqlalchemy import Column, String, Boolean, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(30), unique=True, nullable=False, index=True)  # +22890123456
    password_hash = Column(String(255), nullable=False)
    language = Column(String(10), nullable=False, default="fr")
    gender = Column(String(16))
    birthdate = Column(Date)
    country = Column(String(64))
    city = Column(String(64))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_reset_token = Column(String(128), nullable=True)
    password_reset_expiry = Column(DateTime, nullable=True)
    email_verification_token = Column(String(128), nullable=True)
    email_verification_expiry = Column(DateTime, nullable=True)
    phone_verification_token = Column(String(128), nullable=True)
    phone_verification_expiry = Column(DateTime, nullable=True)
    
