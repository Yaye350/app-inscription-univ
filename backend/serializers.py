from datetime import date, datetime

from models import Campagne, Dossier, Formation, Historique, Piece, User

REQUIRED_PIECES = ("cin", "bac", "photo")
STAFF_ROLES = ("agent", "admin")
EDITABLE_STATUTS = ("brouillon", "a_completer")


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def campagne_ouverte(campagne: Campagne, today: date | None = None) -> bool:
    today = today or date.today()
    return campagne.date_ouverture <= today <= campagne.date_cloture


def user_out(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "date_naissance": user.date_naissance.isoformat() if user.date_naissance else None,
        "telephone": user.telephone,
        "adresse": user.adresse,
        "cin": user.cin,
    }


def formation_out(formation: Formation | None) -> dict | None:
    if formation is None:
        return None
    return {
        "id": formation.id,
        "code": formation.code,
        "nom": formation.nom,
        "niveau": formation.niveau,
        "description": formation.description,
    }


def campagne_out(campagne: Campagne) -> dict:
    return {
        "id": campagne.id,
        "nom": campagne.nom,
        "annee": campagne.annee,
        "date_ouverture": campagne.date_ouverture.isoformat(),
        "date_cloture": campagne.date_cloture.isoformat(),
        "ouverte": campagne_ouverte(campagne),
    }


def piece_out(piece: Piece) -> dict:
    return {
        "id": piece.id,
        "type_piece": piece.type_piece,
        "nom_fichier": piece.nom_fichier,
        "uploaded_at": iso(piece.uploaded_at),
    }


def historique_out(item: Historique) -> dict:
    acteur = item.acteur
    return {
        "id": item.id,
        "ancien_statut": item.ancien_statut,
        "nouveau_statut": item.nouveau_statut,
        "motif": item.motif,
        "created_at": iso(item.created_at),
        "acteur": None
        if acteur is None
        else {
            "id": acteur.id,
            "nom": acteur.nom,
            "prenom": acteur.prenom,
            "role": acteur.role,
        },
    }


def dossier_out(dossier: Dossier, *, detail: bool = False) -> dict:
    etudiant = dossier.etudiant
    data = {
        "id": dossier.id,
        "statut": dossier.statut,
        "commentaire": dossier.commentaire,
        "correction_motif": dossier.correction_motif,
        "decision_motif": dossier.decision_motif,
        "submitted_at": iso(dossier.submitted_at),
        "decided_at": iso(dossier.decided_at),
        "created_at": iso(dossier.created_at),
        "campagne": campagne_out(dossier.campagne),
        "formation": formation_out(dossier.formation),
        "etudiant": {
            "id": etudiant.id,
            "nom": etudiant.nom,
            "prenom": etudiant.prenom,
            "email": etudiant.email,
        },
        "pieces": [piece_out(piece) for piece in dossier.pieces],
    }
    if detail:
        data["etudiant"].update(
            {
                "cin": etudiant.cin,
                "telephone": etudiant.telephone,
                "adresse": etudiant.adresse,
                "date_naissance": etudiant.date_naissance.isoformat() if etudiant.date_naissance else None,
            }
        )
        data["historique"] = [historique_out(item) for item in dossier.historique]
    return data


def missing_requirements(user: User, dossier: Dossier) -> list[str]:
    missing = []
    if not user.nom or not user.prenom:
        missing.append("identité")
    if not user.cin:
        missing.append("CIN")
    if not user.date_naissance:
        missing.append("date de naissance")
    if dossier.formation_id is None:
        missing.append("formation")
    present = {piece.type_piece for piece in dossier.pieces}
    for type_piece in REQUIRED_PIECES:
        if type_piece not in present:
            missing.append(f"pièce {type_piece}")
    return missing
