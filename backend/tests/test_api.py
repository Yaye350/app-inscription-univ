from datetime import date, timedelta

from models import Campagne, Formation, User
from seed import seed


def register(client, email="etu@example.com", nom="Diop", prenom="Awa"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "motdepasse", "nom": nom, "prenom": prenom},
    )
    assert response.status_code == 201
    return response.json()


def auth(client, email="etu@example.com", password="motdepasse"):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def set_role(email, role):
    from database import SessionLocal

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).one()
    user.role = role
    db.commit()
    db.close()


def creer_referentiel(client, admin_headers, ouverte=True, code="TEST-L"):
    today = date.today()
    if ouverte:
        ouverture = today - timedelta(days=1)
        cloture = today + timedelta(days=10)
    else:
        ouverture = today - timedelta(days=20)
        cloture = today - timedelta(days=1)
    campagne = client.post(
        "/campagnes",
        headers=admin_headers,
        json={
            "nom": f"Campagne {code}",
            "annee": "2026-2027",
            "date_ouverture": ouverture.isoformat(),
            "date_cloture": cloture.isoformat(),
        },
    )
    assert campagne.status_code == 201
    formation = client.post(
        "/formations",
        headers=admin_headers,
        json={"code": code, "nom": f"Licence {code}", "niveau": "Licence", "description": "Test"},
    )
    assert formation.status_code == 201
    return campagne.json()["id"], formation.json()["id"]


def completer_profil(client, headers):
    response = client.put(
        "/me",
        headers=headers,
        json={"cin": "1234567890123", "date_naissance": "2002-05-01"},
    )
    assert response.status_code == 200


def deposer_pieces(client, headers, dossier_id):
    for type_piece in ("cin", "bac", "photo"):
        response = client.post(
            f"/dossiers/{dossier_id}/pieces",
            headers=headers,
            data={"type_piece": type_piece},
            files={"fichier": (f"{type_piece}.pdf", b"%PDF-1.4 piece", "application/pdf")},
        )
        assert response.status_code == 201, response.text


def test_accueil_et_sante(client):
    accueil = client.get("/")
    assert accueil.status_code == 200
    assert accueil.json()["message"] == "API de gestion des inscriptions universitaires"
    assert client.get("/health").json() == {"status": "ok"}


def test_mot_de_passe_non_stocke_en_clair(client, db):
    register(client)
    user = db.query(User).filter(User.email == "etu@example.com").one()
    assert user.password_hash != "motdepasse"
    assert user.password_hash.startswith("$2")


def test_seed_initial(db):
    seed(db)
    assert db.query(User).filter_by(role="admin").count() == 1
    assert db.query(User).filter_by(role="agent").count() == 1
    assert db.query(Formation).count() == 2
    campagne = db.query(Campagne).one()
    assert campagne.date_ouverture <= date.today() <= campagne.date_cloture


def test_etudiant_isole_et_soumission_incomplete(client):
    register(client, "un@example.com")
    register(client, "deux@example.com", nom="Fall", prenom="Fatou")
    register(client, "admin@example.com", nom="Admin", prenom="Test")
    set_role("admin@example.com", "admin")
    admin = auth(client, "admin@example.com")
    campagne_id, formation_id = creer_referentiel(client, admin)
    un = auth(client, "un@example.com")
    deux = auth(client, "deux@example.com")

    creation = client.post(
        "/dossiers",
        headers=un,
        json={"campagne_id": campagne_id, "formation_id": formation_id},
    )
    assert creation.status_code == 201
    dossier_id = creation.json()["id"]

    assert client.get(f"/dossiers/{dossier_id}", headers=deux).status_code == 404
    listing = client.get("/dossiers", headers=deux)
    assert listing.json() == []

    incomplet = client.post(f"/dossiers/{dossier_id}/soumettre", headers=un)
    assert incomplet.status_code == 400
    assert "incomplet" in incomplet.json()["detail"]

    double = client.post(
        "/dossiers",
        headers=un,
        json={"campagne_id": campagne_id, "formation_id": formation_id},
    )
    assert double.status_code == 409


def test_transition_rejet_et_cycle_nominal(client):
    register(client, "etu@example.com")
    register(client, "agent@example.com", nom="Sarr", prenom="Ali")
    register(client, "admin@example.com", nom="Admin", prenom="Test")
    set_role("agent@example.com", "agent")
    set_role("admin@example.com", "admin")
    admin = auth(client, "admin@example.com")
    agent = auth(client, "agent@example.com")
    etudiant = auth(client)
    campagne_id, formation_id = creer_referentiel(client, admin)
    completer_profil(client, etudiant)

    dossier_id = client.post(
        "/dossiers",
        headers=etudiant,
        json={"campagne_id": campagne_id, "formation_id": formation_id, "commentaire": "Première inscription"},
    ).json()["id"]
    deposer_pieces(client, etudiant, dossier_id)

    trop_tot = client.post(f"/dossiers/{dossier_id}/accepter", headers=agent, json={"motif": "ok"})
    assert trop_tot.status_code == 400

    soumis = client.post(f"/dossiers/{dossier_id}/soumettre", headers=etudiant)
    assert soumis.status_code == 200
    assert soumis.json()["statut"] == "en_attente"

    bloque = client.put(
        f"/dossiers/{dossier_id}",
        headers=etudiant,
        json={"commentaire": "changement tardif"},
    )
    assert bloque.status_code == 400

    sans_motif = client.post(f"/dossiers/{dossier_id}/rejeter", headers=agent, json={"motif": "   "})
    assert sans_motif.status_code == 400

    complement = client.post(
        f"/dossiers/{dossier_id}/complement",
        headers=agent,
        json={"motif": "Photo illisible"},
    )
    assert complement.status_code == 200
    assert complement.json()["statut"] == "a_completer"

    deposer_pieces(client, etudiant, dossier_id)
    resoumis = client.post(f"/dossiers/{dossier_id}/soumettre", headers=etudiant)
    assert resoumis.json()["statut"] == "en_attente"

    sans_motif_acceptation = client.post(
        f"/dossiers/{dossier_id}/accepter", headers=agent, json={"motif": "   "}
    )
    assert sans_motif_acceptation.status_code == 400

    accepte = client.post(
        f"/dossiers/{dossier_id}/accepter",
        headers=agent,
        json={"motif": "Dossier conforme"},
    )
    assert accepte.status_code == 200
    body = accepte.json()
    assert body["statut"] == "accepte"
    assert body["decision_motif"] == "Dossier conforme"
    assert any(item["nouveau_statut"] == "accepte" for item in body["historique"])

    # A terminal dossier no longer blocks a new active dossier for that campaign.
    nouveau = client.post(
        "/dossiers",
        headers=etudiant,
        json={"campagne_id": campagne_id, "formation_id": formation_id},
    )
    assert nouveau.status_code == 201

    vu = client.get(f"/dossiers/{dossier_id}", headers=etudiant)
    assert vu.json()["statut"] == "accepte"
    assert client.post(f"/dossiers/{dossier_id}/rejeter", headers=etudiant, json={"motif": "non"}).status_code == 403


def test_campagne_fermee_recherche_et_export(client):
    register(client, "etu@example.com")
    register(client, "admin@example.com", nom="Ba", prenom="Aida")
    set_role("admin@example.com", "admin")
    admin = auth(client, "admin@example.com")
    etudiant = auth(client)
    campagne_id, formation_id = creer_referentiel(client, admin, ouverte=False)
    refuse = client.post(
        "/dossiers",
        headers=etudiant,
        json={"campagne_id": campagne_id, "formation_id": formation_id},
    )
    assert refuse.status_code == 400

    ouverte_id, _formation_ouverte = creer_referentiel(client, admin, ouverte=True, code="TEST-O")
    creation = client.post(
        "/dossiers",
        headers=etudiant,
        json={"campagne_id": ouverte_id, "formation_id": formation_id},
    )
    assert creation.status_code == 201

    assert client.get("/rapports/statistiques", headers=etudiant).status_code == 403
    stats = client.get("/rapports/statistiques", headers=admin)
    assert stats.status_code == 200
    assert stats.json()["total"] == 1

    export = client.get("/rapports/dossiers.csv", headers=admin, params={"q": "Diop"})
    assert export.status_code == 200
    assert "etu@example.com" in export.text
    assert client.get("/rapports/dossiers.csv").status_code == 401
    assert client.post("/formations", headers=etudiant, json={"code": "X", "nom": "X", "niveau": "L"}).status_code == 403
