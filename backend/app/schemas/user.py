from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=150)
    last_name: str = Field(..., min_length=2, max_length=150)
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    phone_number: str = Field(..., pattern=r"^\+\d{7,15}$")
    language: str = Field(default="fr", max_length=10)
    gender: Optional[str] = Field(None, max_length=16)
    birthdate: Optional[date]
    country: Optional[str] = Field(None, max_length=64)
    city: Optional[str] = Field(None, max_length=64)

class UserSignup(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        import re
        if (len(v) < 8
            or not re.search(r"[A-Z]", v)
            or not re.search(r"[a-z]", v)
            or not re.search(r"\d", v)
            or not re.search(r"\W", v)):
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un symbole.")
        return v

class UserLogin(BaseModel):
    username: str
    password: str
    keep_signed_in: Optional[bool] = False

class UserPublic(UserBase):
    id: str
    is_active: bool
    email_verified: bool
    phone_verified: bool

    class Config:
        from_attributes = True

class PasswordResetRequest(BaseModel):
    identifier: str  # email OU téléphone

class PasswordResetConfirm(BaseModel):
    identifier: str
    reset_token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        import re
        if (len(v) < 8
            or not re.search(r"[A-Z]", v)
            or not re.search(r"[a-z]", v)
            or not re.search(r"\d", v)
            or not re.search(r"\W", v)):
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un symbole.")
        return v
        
class EmailOrPhoneValidationRequest(BaseModel):
    identifier: str  # email ou téléphone

class EmailOrPhoneValidationConfirm(BaseModel):
    identifier: str
    verification_token: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[date] = None
    country: Optional[str] = None
    city: Optional[str] = None
    # On ne change pas username, email, phone ici

