from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.schemas.user import (
    UserSignup, UserLogin, UserPublic,
    PasswordResetRequest, PasswordResetConfirm,
    EmailOrPhoneValidationRequest, EmailOrPhoneValidationConfirm, UserUpdate
)
from app.utils.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_any(db: Session, identifier: str):
    return db.query(User).filter(
        (User.username == identifier) |
        (User.email == identifier) |
        (User.phone_number == identifier)
    ).first()

@router.post("/signup", response_model=UserPublic)
def signup(user: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "Nom d'utilisateur déjà utilisé")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "Email déjà utilisé")
    if db.query(User).filter(User.phone_number == user.phone_number).first():
        raise HTTPException(400, "Numéro déjà utilisé")
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        password_hash=hash_password(user.password),
        language=user.language,
        gender=user.gender,
        birthdate=user.birthdate,
        country=user.country,
        city=user.city,
        is_active=True,
        email_verified=False,
        phone_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    identifier = form_data.username
    user = get_user_by_any(db, identifier)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Nom d'utilisateur/email/tel ou mot de passe invalide")
    # Gestion du “keep me signed in”
    keep_signed_in = "keep" in (form_data.scopes or [])
    token = create_access_token({"sub": user.username}, keep_signed_in=keep_signed_in)
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/password-reset/request")
def password_reset_request(data: PasswordResetRequest, db: Session = Depends(get_db)):
    identifier = data.identifier
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier)
    ).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    # Génère un token unique
    token = secrets.token_urlsafe(8)
    user.password_reset_token = token
    user.password_reset_expiry = datetime.utcnow() + timedelta(minutes=30)
    db.commit()
    # Ici, envoie le token par email ou SMS (mock)
    print(f"[MOCK] Code de réinitialisation envoyé à {identifier} : {token}")
    return {"msg": "Un code de réinitialisation a été envoyé (mock)"}

@router.post("/password-reset/confirm")
def password_reset_confirm(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    identifier = data.identifier
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier)
    ).first()
    if not user or not user.password_reset_token:
        raise HTTPException(400, "Aucune demande de réinitialisation en cours pour cet utilisateur")
    if user.password_reset_token != data.reset_token:
        raise HTTPException(400, "Code de réinitialisation invalide")
    if user.password_reset_expiry and user.password_reset_expiry < datetime.utcnow():
        raise HTTPException(400, "Code de réinitialisation expiré")
    # Change le mot de passe
    user.password_hash = hash_password(data.new_password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    db.commit()
    return {"msg": "Mot de passe réinitialisé avec succès"}
    
@router.post("/email-validation/request")
def email_validation_request(data: EmailOrPhoneValidationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.identifier).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    token = secrets.token_urlsafe(6)
    user.email_verification_token = token
    user.email_verification_expiry = datetime.utcnow() + timedelta(minutes=30)
    db.commit()
    # Mock : Affiche le token (à remplacer par un envoi réel)
    print(f"[MOCK] Email verification code for {user.email}: {token}")
    # Pour l’envoi réel, cf plus bas
    return {"msg": "Code envoyé à votre email (mock)"}

@router.post("/email-validation/confirm")
def email_validation_confirm(data: EmailOrPhoneValidationConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.identifier).first()
    if not user or not user.email_verification_token:
        raise HTTPException(400, "Aucune validation en attente pour ce compte")
    if user.email_verification_token != data.verification_token:
        raise HTTPException(400, "Code incorrect")
    if user.email_verification_expiry and user.email_verification_expiry < datetime.utcnow():
        raise HTTPException(400, "Code expiré")
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expiry = None
    db.commit()
    return {"msg": "Email vérifié avec succès"}

@router.post("/phone-validation/request")
def phone_validation_request(data: EmailOrPhoneValidationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == data.identifier).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    token = secrets.token_urlsafe(6)
    user.phone_verification_token = token
    user.phone_verification_expiry = datetime.utcnow() + timedelta(minutes=30)
    db.commit()
    # Mock : Affiche le token (à remplacer par un envoi réel)
    print(f"[MOCK] Phone verification code for {user.phone_number}: {token}")
    # Pour l’envoi réel, cf plus bas
    return {"msg": "Code envoyé à votre téléphone (mock)"}

@router.post("/phone-validation/confirm")
def phone_validation_confirm(data: EmailOrPhoneValidationConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == data.identifier).first()
    if not user or not user.phone_verification_token:
        raise HTTPException(400, "Aucune validation en attente pour ce compte")
    if user.phone_verification_token != data.verification_token:
        raise HTTPException(400, "Code incorrect")
    if user.phone_verification_expiry and user.phone_verification_expiry < datetime.utcnow():
        raise HTTPException(400, "Code expiré")
    user.phone_verified = True
    user.phone_verification_token = None
    user.phone_verification_expiry = None
    db.commit()
    return {"msg": "Numéro de téléphone vérifié avec succès"}

@router.put("/me", response_model=UserPublic)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me")
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"msg": "Compte supprimé avec succès"}

