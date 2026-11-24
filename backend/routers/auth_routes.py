from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models import User
from schemas import LoginIn, RegisterIn, UserUpdate
from security import create_token, hash_password, verify_password
from serializers import user_out

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["profil"])


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.post("/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email")
    from datetime import datetime, timezone

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role="etudiant",
        nom=payload.nom.strip(),
        prenom=payload.prenom.strip(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    return {
        "access_token": create_token(user.id, user.role),
        "token_type": "bearer",
        "user": user_out(user),
    }


@me_router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@me_router.put("/me")
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if "nom" in data:
        nom = _clean(data["nom"])
        if not nom:
            raise HTTPException(status_code=400, detail="Le nom est obligatoire")
        user.nom = nom
    if "prenom" in data:
        prenom = _clean(data["prenom"])
        if not prenom:
            raise HTTPException(status_code=400, detail="Le prénom est obligatoire")
        user.prenom = prenom
    if "date_naissance" in data:
        naissance = data["date_naissance"]
        if naissance is not None and naissance > date.today():
            raise HTTPException(status_code=400, detail="La date de naissance est invalide")
        user.date_naissance = naissance
    if "telephone" in data:
        user.telephone = _clean(data["telephone"])
    if "adresse" in data:
        user.adresse = _clean(data["adresse"])
    if "cin" in data:
        user.cin = _clean(data["cin"])
    db.commit()
    db.refresh(user)
    return user_out(user)
