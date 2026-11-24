from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user, require_roles
from models import Campagne, Dossier, Formation, User
from schemas import CampagneIn, FormationIn, RoleUpdate
from serializers import campagne_out, formation_out, user_out

router = APIRouter(tags=["referentiels"])

ROLES = {"etudiant", "agent", "admin"}


def _check_dates(payload: CampagneIn) -> None:
    if payload.date_ouverture > payload.date_cloture:
        raise HTTPException(
            status_code=400,
            detail="La date d'ouverture doit précéder la date de clôture",
        )


@router.get("/campagnes")
def lister_campagnes(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campagnes = db.query(Campagne).order_by(Campagne.date_ouverture.desc()).all()
    return [campagne_out(campagne) for campagne in campagnes]


@router.post("/campagnes", status_code=201)
def creer_campagne(
    payload: CampagneIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _check_dates(payload)
    campagne = Campagne(**payload.model_dump())
    db.add(campagne)
    db.commit()
    db.refresh(campagne)
    return campagne_out(campagne)


@router.put("/campagnes/{campagne_id}")
def modifier_campagne(
    campagne_id: int,
    payload: CampagneIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    campagne = db.get(Campagne, campagne_id)
    if campagne is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    _check_dates(payload)
    for key, value in payload.model_dump().items():
        setattr(campagne, key, value)
    db.commit()
    db.refresh(campagne)
    return campagne_out(campagne)


@router.delete("/campagnes/{campagne_id}")
def supprimer_campagne(
    campagne_id: int,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    campagne = db.get(Campagne, campagne_id)
    if campagne is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    if db.query(Dossier).filter(Dossier.campagne_id == campagne_id).first():
        raise HTTPException(status_code=409, detail="Cette campagne est déjà utilisée par des dossiers")
    db.delete(campagne)
    db.commit()
    return {"message": "Campagne supprimée"}


@router.get("/formations")
def lister_formations(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    formations = db.query(Formation).order_by(Formation.nom).all()
    return [formation_out(formation) for formation in formations]


@router.post("/formations", status_code=201)
def creer_formation(
    payload: FormationIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    formation = Formation(
        code=payload.code.strip().upper(),
        nom=payload.nom.strip(),
        niveau=payload.niveau.strip(),
        description=(payload.description or "").strip() or None,
    )
    db.add(formation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce code de formation existe déjà") from None
    db.refresh(formation)
    return formation_out(formation)


@router.put("/formations/{formation_id}")
def modifier_formation(
    formation_id: int,
    payload: FormationIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    formation = db.get(Formation, formation_id)
    if formation is None:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    formation.code = payload.code.strip().upper()
    formation.nom = payload.nom.strip()
    formation.niveau = payload.niveau.strip()
    formation.description = (payload.description or "").strip() or None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce code de formation existe déjà") from None
    db.refresh(formation)
    return formation_out(formation)


@router.delete("/formations/{formation_id}")
def supprimer_formation(
    formation_id: int,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    formation = db.get(Formation, formation_id)
    if formation is None:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    if db.query(Dossier).filter(Dossier.formation_id == formation_id).first():
        raise HTTPException(status_code=409, detail="Cette formation est déjà utilisée par des dossiers")
    db.delete(formation)
    db.commit()
    return {"message": "Formation supprimée"}


@router.get("/users")
def lister_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.nom, User.prenom).all()
    return [user_out(user) for user in users]


@router.patch("/users/{user_id}/role")
def modifier_role(
    user_id: int,
    payload: RoleUpdate,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if payload.role not in ROLES:
        raise HTTPException(status_code=400, detail="Rôle inconnu")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == actor.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas retirer votre propre rôle d'administrateur")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user_out(user)
