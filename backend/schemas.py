from datetime import date

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nom: str | None = Field(default=None, max_length=100)
    prenom: str | None = Field(default=None, max_length=100)
    date_naissance: date | None = None
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str | None = Field(default=None, max_length=500)
    cin: str | None = Field(default=None, max_length=50)


class RoleUpdate(BaseModel):
    role: str


class CampagneIn(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    annee: str = Field(min_length=4, max_length=20)
    date_ouverture: date
    date_cloture: date


class FormationIn(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    nom: str = Field(min_length=1, max_length=200)
    niveau: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=1000)


class DossierIn(BaseModel):
    campagne_id: int
    formation_id: int
    commentaire: str | None = Field(default=None, max_length=2000)


class DossierUpdate(BaseModel):
    formation_id: int | None = None
    commentaire: str | None = Field(default=None, max_length=2000)


class MotifIn(BaseModel):
    motif: str | None = Field(default=None, max_length=2000)
