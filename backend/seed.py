from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models import Campagne, Formation, User
from security import hash_password


def seed(db: Session) -> None:
    admin = db.query(User).filter(User.email.in_(["admin@univ.edu", "admin@univ.local"])).first()
    if admin and admin.email.endswith(".local"):
        admin.email = "admin@univ.edu"
    agent = db.query(User).filter(User.email.in_(["agent@univ.edu", "agent@univ.local"])).first()
    if agent and agent.email.endswith(".local"):
        agent.email = "agent@univ.edu"
    if admin and db.query(Campagne).first() and db.query(Formation).count() >= 2:
        db.commit()
        return

    now = datetime.now(timezone.utc)
    today = date.today()
    db.add_all(
        [
            *([] if admin else [User(
                email="admin@univ.edu",
                password_hash=hash_password("Admin123!"),
                role="admin",
                nom="Système",
                prenom="Admin",
                created_at=now,
            )]),
            *([] if agent else [User(
                email="agent@univ.edu",
                password_hash=hash_password("Agent123!"),
                role="agent",
                nom="Ndiaye",
                prenom="Moussa",
                created_at=now,
            )]),
            Formation(
                code="INFO-L",
                nom="Licence Informatique",
                niveau="Licence",
                description="Parcours informatique généraliste",
            ),
            Formation(
                code="DSAI-M",
                nom="Master Data et IA",
                niveau="Master",
                description="Parcours science des données et intelligence artificielle",
            ),
            Campagne(
                nom=f"Inscriptions {today.year}-{today.year + 1}",
                annee=f"{today.year}-{today.year + 1}",
                date_ouverture=today - timedelta(days=30),
                date_cloture=today + timedelta(days=120),
            ),
        ]
    )
    db.commit()
