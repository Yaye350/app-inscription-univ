import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from deps import get_current_user, require_roles
from models import Campagne, Dossier, Formation, Historique, Piece, User
from schemas import DossierIn, DossierUpdate, MotifIn
from serializers import (
    EDITABLE_STATUTS,
    REQUIRED_PIECES,
    STAFF_ROLES,
    campagne_ouverte,
    dossier_out,
    missing_requirements,
)

router = APIRouter(tags=["dossiers"])

ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_BYTES = 5 * 1024 * 1024
PIECE_TYPES = set(REQUIRED_PIECES) | {"autre"}


def upload_dir() -> Path:
    path = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[1] / "uploads")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def now() -> datetime:
    return datetime.now(timezone.utc)


def add_history(db: Session, dossier: Dossier, ancien: str | None, nouveau: str, acteur: User, motif: str | None):
    db.add(
        Historique(
            dossier_id=dossier.id,
            ancien_statut=ancien,
            nouveau_statut=nouveau,
            acteur_id=acteur.id,
            motif=(motif or "").strip() or None,
            created_at=now(),
        )
    )


def load_dossier(db: Session, dossier_id: int) -> Dossier | None:
    return (
        db.query(Dossier)
        .options(
            joinedload(Dossier.etudiant),
            joinedload(Dossier.campagne),
            joinedload(Dossier.formation),
            joinedload(Dossier.pieces),
            joinedload(Dossier.historique).joinedload(Historique.acteur),
        )
        .filter(Dossier.id == dossier_id)
        .first()
    )


def visible_dossier(db: Session, dossier_id: int, user: User) -> Dossier:
    dossier = load_dossier(db, dossier_id)
    if dossier is None or (user.role not in STAFF_ROLES and dossier.etudiant_id != user.id):
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


def ensure_editable(dossier: Dossier) -> None:
    if dossier.statut not in EDITABLE_STATUTS:
        raise HTTPException(
            status_code=400,
            detail="Ce dossier ne peut plus être modifié dans son statut actuel",
        )


def require_motif(payload: MotifIn) -> str:
    motif = (payload.motif or "").strip()
    if not motif:
        raise HTTPException(status_code=400, detail="Le motif est obligatoire")
    return motif


def filtered_query(
    db: Session,
    user: User,
    statut: str | None,
    campagne_id: int | None,
    formation_id: int | None,
    q: str | None,
):
    query = db.query(Dossier).options(
        joinedload(Dossier.etudiant),
        joinedload(Dossier.campagne),
        joinedload(Dossier.formation),
        joinedload(Dossier.pieces),
    )
    if user.role not in STAFF_ROLES:
        query = query.filter(Dossier.etudiant_id == user.id)
    if statut:
        query = query.filter(Dossier.statut == statut)
    if campagne_id:
        query = query.filter(Dossier.campagne_id == campagne_id)
    if formation_id:
        query = query.filter(Dossier.formation_id == formation_id)
    if q and user.role in STAFF_ROLES:
        like = f"%{q.strip()}%"
        query = query.filter(
            Dossier.etudiant.has(or_(User.nom.ilike(like), User.prenom.ilike(like), User.email.ilike(like)))
        )
    return query.order_by(Dossier.id.desc())


@router.post("/dossiers", status_code=201)
def creer_dossier(
    payload: DossierIn,
    user: User = Depends(require_roles("etudiant")),
    db: Session = Depends(get_db),
):
    campagne = db.get(Campagne, payload.campagne_id)
    if campagne is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    if not campagne_ouverte(campagne):
        raise HTTPException(status_code=400, detail="La campagne n'est pas ouverte")
    formation = db.get(Formation, payload.formation_id)
    if formation is None:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    dossier = Dossier(
        etudiant_id=user.id,
        campagne_id=campagne.id,
        formation_id=formation.id,
        statut="brouillon",
        commentaire=(payload.commentaire or "").strip() or None,
        created_at=now(),
    )
    db.add(dossier)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Un dossier existe déjà pour cette campagne",
        ) from None
    add_history(db, dossier, None, "brouillon", user, "Création du dossier")
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.get("/dossiers")
def lister_dossiers(
    statut: str | None = None,
    campagne_id: int | None = None,
    formation_id: int | None = None,
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dossiers = filtered_query(db, user, statut, campagne_id, formation_id, q).all()
    return [dossier_out(dossier) for dossier in dossiers]


@router.get("/dossiers/{dossier_id}")
def obtenir_dossier(
    dossier_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dossier_out(visible_dossier(db, dossier_id, user), detail=True)


@router.put("/dossiers/{dossier_id}")
def modifier_dossier(
    dossier_id: int,
    payload: DossierUpdate,
    user: User = Depends(require_roles("etudiant")),
    db: Session = Depends(get_db),
):
    dossier = visible_dossier(db, dossier_id, user)
    ensure_editable(dossier)
    data = payload.model_dump(exclude_unset=True)
    if "formation_id" in data and data["formation_id"] is not None:
        formation = db.get(Formation, data["formation_id"])
        if formation is None:
            raise HTTPException(status_code=404, detail="Formation introuvable")
        dossier.formation_id = formation.id
    if "commentaire" in data:
        dossier.commentaire = (data["commentaire"] or "").strip() or None
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.post("/dossiers/{dossier_id}/pieces", status_code=201)
async def ajouter_piece(
    dossier_id: int,
    type_piece: str = Form(...),
    fichier: UploadFile = File(...),
    user: User = Depends(require_roles("etudiant")),
    db: Session = Depends(get_db),
):
    if type_piece not in PIECE_TYPES:
        raise HTTPException(status_code=400, detail="Type de pièce inconnu")
    dossier = visible_dossier(db, dossier_id, user)
    ensure_editable(dossier)
    original = Path(fichier.filename or "document").name
    suffix = Path(original).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Format accepté : PDF, JPG ou PNG")
    content = await fichier.read(MAX_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Le fichier est vide")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (5 Mo maximum)")
    valid_signature = (
        (suffix == ".pdf" and content.startswith(b"%PDF-"))
        or (suffix in {".jpg", ".jpeg"} and content.startswith(b"\xff\xd8\xff"))
        or (suffix == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
    )
    if not valid_signature:
        raise HTTPException(status_code=400, detail="Le contenu ne correspond pas au format du fichier")

    if type_piece in REQUIRED_PIECES:
        previous = (
            db.query(Piece)
            .filter(Piece.dossier_id == dossier.id, Piece.type_piece == type_piece)
            .all()
        )
        for piece in previous:
            stored = upload_dir() / piece.stored_name
            if stored.is_file():
                stored.unlink()
            db.delete(piece)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    (upload_dir() / stored_name).write_bytes(content)
    piece = Piece(
        dossier_id=dossier.id,
        type_piece=type_piece,
        nom_fichier=original,
        stored_name=stored_name,
        uploaded_at=now(),
    )
    db.add(piece)
    db.commit()
    db.refresh(piece)
    return {
        "id": piece.id,
        "type_piece": piece.type_piece,
        "nom_fichier": piece.nom_fichier,
        "uploaded_at": piece.uploaded_at.isoformat(),
    }


@router.get("/dossiers/{dossier_id}/pieces/{piece_id}")
def telecharger_piece(
    dossier_id: int,
    piece_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dossier = visible_dossier(db, dossier_id, user)
    piece = next((item for item in dossier.pieces if item.id == piece_id), None)
    if piece is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    path = (upload_dir() / piece.stored_name).resolve()
    if upload_dir().resolve() not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return FileResponse(path, filename=piece.nom_fichier)


@router.delete("/dossiers/{dossier_id}/pieces/{piece_id}")
def supprimer_piece(
    dossier_id: int,
    piece_id: int,
    user: User = Depends(require_roles("etudiant")),
    db: Session = Depends(get_db),
):
    dossier = visible_dossier(db, dossier_id, user)
    ensure_editable(dossier)
    piece = next((item for item in dossier.pieces if item.id == piece_id), None)
    if piece is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    stored = upload_dir() / piece.stored_name
    if stored.is_file():
        stored.unlink()
    db.delete(piece)
    db.commit()
    return {"message": "Pièce supprimée"}


@router.post("/dossiers/{dossier_id}/soumettre")
def soumettre_dossier(
    dossier_id: int,
    user: User = Depends(require_roles("etudiant")),
    db: Session = Depends(get_db),
):
    dossier = visible_dossier(db, dossier_id, user)
    if dossier.statut not in EDITABLE_STATUTS:
        raise HTTPException(status_code=400, detail="Ce dossier ne peut pas être soumis dans son statut actuel")
    if not campagne_ouverte(dossier.campagne):
        raise HTTPException(status_code=400, detail="La campagne n'est pas ouverte")
    missing = missing_requirements(user, dossier)
    if missing:
        raise HTTPException(
            status_code=400,
            detail="Le dossier est incomplet : " + ", ".join(missing),
        )
    ancien = dossier.statut
    dossier.statut = "en_attente"
    dossier.submitted_at = now()
    dossier.correction_motif = None
    add_history(db, dossier, ancien, "en_attente", user, "Soumission du dossier")
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.post("/dossiers/{dossier_id}/complement")
def demander_complement(
    dossier_id: int,
    payload: MotifIn,
    user: User = Depends(require_roles("agent", "admin")),
    db: Session = Depends(get_db),
):
    motif = require_motif(payload)
    dossier = visible_dossier(db, dossier_id, user)
    if dossier.statut != "en_attente":
        raise HTTPException(status_code=400, detail="Seuls les dossiers en attente peuvent être renvoyés")
    ancien = dossier.statut
    dossier.statut = "a_completer"
    dossier.correction_motif = motif
    add_history(db, dossier, ancien, "a_completer", user, motif)
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.post("/dossiers/{dossier_id}/accepter")
def accepter_dossier(
    dossier_id: int,
    payload: MotifIn,
    user: User = Depends(require_roles("agent", "admin")),
    db: Session = Depends(get_db),
):
    motif = require_motif(payload)
    dossier = visible_dossier(db, dossier_id, user)
    if dossier.statut != "en_attente":
        raise HTTPException(status_code=400, detail="Seuls les dossiers en attente peuvent être acceptés")
    ancien = dossier.statut
    dossier.statut = "accepte"
    dossier.decision_motif = motif
    dossier.decided_by_id = user.id
    dossier.decided_at = now()
    add_history(db, dossier, ancien, "accepte", user, motif)
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.post("/dossiers/{dossier_id}/rejeter")
def rejeter_dossier(
    dossier_id: int,
    payload: MotifIn,
    user: User = Depends(require_roles("agent", "admin")),
    db: Session = Depends(get_db),
):
    motif = require_motif(payload)
    dossier = visible_dossier(db, dossier_id, user)
    if dossier.statut != "en_attente":
        raise HTTPException(status_code=400, detail="Seuls les dossiers en attente peuvent être rejetés")
    ancien = dossier.statut
    dossier.statut = "rejete"
    dossier.decision_motif = motif
    dossier.decided_by_id = user.id
    dossier.decided_at = now()
    add_history(db, dossier, ancien, "rejete", user, motif)
    db.commit()
    return dossier_out(load_dossier(db, dossier.id), detail=True)


@router.get("/rapports/statistiques")
def statistiques(
    _: User = Depends(require_roles("agent", "admin")),
    db: Session = Depends(get_db),
):
    par_statut = {
        statut: count
        for statut, count in db.query(Dossier.statut, func.count(Dossier.id)).group_by(Dossier.statut).all()
    }
    par_formation_rows = (
        db.query(Formation.nom, func.count(Dossier.id))
        .outerjoin(Dossier, Dossier.formation_id == Formation.id)
        .group_by(Formation.id, Formation.nom)
        .order_by(Formation.nom)
        .all()
    )
    return {
        "total": db.query(func.count(Dossier.id)).scalar() or 0,
        "par_statut": par_statut,
        "par_formation": [{"formation": nom, "total": total} for nom, total in par_formation_rows],
    }


@router.get("/rapports/dossiers.csv")
def exporter_dossiers(
    statut: str | None = None,
    campagne_id: int | None = None,
    formation_id: int | None = Query(default=None),
    q: str | None = None,
    user: User = Depends(require_roles("agent", "admin")),
    db: Session = Depends(get_db),
):
    dossiers = filtered_query(db, user, statut, campagne_id, formation_id, q).all()
    lines = ["id;etudiant;email;campagne;formation;statut;soumis_le"]
    for dossier in dossiers:
        etudiant = dossier.etudiant
        soumis = dossier.submitted_at.date().isoformat() if dossier.submitted_at else ""
        values = [
            str(dossier.id),
            f"{etudiant.prenom} {etudiant.nom}",
            etudiant.email,
            dossier.campagne.nom,
            dossier.formation.nom if dossier.formation else "",
            dossier.statut,
            soumis,
        ]
        lines.append(";".join(value.replace(";", ",") for value in values))
    content = "\ufeff" + "\n".join(lines) + "\n"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=dossiers.csv"},
    )
