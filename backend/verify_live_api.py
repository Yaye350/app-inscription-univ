"""Exercise the seeded Docker API through the complete dossier lifecycle."""

from uuid import uuid4

import httpx


BASE_URL = "http://localhost:8000"
PASSWORD = "Etudiant123!"


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=20) as client:
        assert client.get("/health").json() == {"status": "ok"}
        admin = client.post(
            "/auth/login", json={"email": "admin@univ.edu", "password": "Admin123!"}
        ).json()
        agent = client.post(
            "/auth/login", json={"email": "agent@univ.edu", "password": "Agent123!"}
        ).json()
        student_email = f"smoke-{uuid4().hex[:10]}@example.edu"
        registered = client.post(
            "/auth/register",
            json={
                "email": student_email,
                "password": PASSWORD,
                "nom": "Test",
                "prenom": "Etudiant",
            },
        )
        assert registered.status_code == 201, registered.text
        student = client.post(
            "/auth/login", json={"email": student_email, "password": PASSWORD}
        ).json()
        student_headers = {"Authorization": f"Bearer {student['access_token']}"}
        agent_headers = {"Authorization": f"Bearer {agent['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

        campagnes = client.get("/campagnes", headers=admin_headers).json()
        formations = client.get("/formations", headers=admin_headers).json()
        campagne = next(item for item in campagnes if item["ouverte"])
        profil = client.put(
            "/me",
            headers=student_headers,
            json={"cin": "SMOKE-12345", "date_naissance": "2002-05-01"},
        )
        assert profil.status_code == 200, profil.text
        dossier = client.post(
            "/dossiers",
            headers=student_headers,
            json={"campagne_id": campagne["id"], "formation_id": formations[0]["id"]},
        )
        assert dossier.status_code == 201, dossier.text
        dossier_id = dossier.json()["id"]

        def upload(kind: str) -> None:
            response = client.post(
                f"/dossiers/{dossier_id}/pieces",
                headers=student_headers,
                data={"type_piece": kind},
                files={"fichier": (f"{kind}.pdf", b"%PDF-1.4 dossier smoke test", "application/pdf")},
            )
            assert response.status_code == 201, response.text

        for kind in ("cin", "bac", "photo"):
            upload(kind)
        submitted = client.post(f"/dossiers/{dossier_id}/soumettre", headers=student_headers)
        assert submitted.status_code == 200 and submitted.json()["statut"] == "en_attente"
        complement = client.post(
            f"/dossiers/{dossier_id}/complement",
            headers=agent_headers,
            json={"motif": "Vérification de la lisibilité"},
        )
        assert complement.status_code == 200 and complement.json()["statut"] == "a_completer"
        upload("photo")
        resubmitted = client.post(f"/dossiers/{dossier_id}/soumettre", headers=student_headers)
        assert resubmitted.status_code == 200 and resubmitted.json()["statut"] == "en_attente"
        accepted = client.post(
            f"/dossiers/{dossier_id}/accepter",
            headers=agent_headers,
            json={"motif": "Dossier conforme"},
        )
        assert accepted.status_code == 200 and accepted.json()["statut"] == "accepte"
        final = client.get(f"/dossiers/{dossier_id}", headers=student_headers).json()
        assert final["statut"] == "accepte"
        assert [item["nouveau_statut"] for item in final["historique"]] == [
            "brouillon",
            "en_attente",
            "a_completer",
            "en_attente",
            "accepte",
        ]
        print(f"E2E OK: étudiant inscrit, dossier #{dossier_id} accepté avec historique complet.")


if __name__ == "__main__":
    main()
