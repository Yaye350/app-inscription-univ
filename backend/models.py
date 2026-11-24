from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="etudiant")
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    date_naissance = Column(Date, nullable=True)
    telephone = Column(String(30), nullable=True)
    adresse = Column(Text, nullable=True)
    cin = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)

    dossiers = relationship("Dossier", back_populates="etudiant", foreign_keys="Dossier.etudiant_id")


class Campagne(Base):
    __tablename__ = "campagnes"

    id = Column(Integer, primary_key=True)
    nom = Column(String(200), nullable=False)
    annee = Column(String(20), nullable=False)
    date_ouverture = Column(Date, nullable=False)
    date_cloture = Column(Date, nullable=False)

    dossiers = relationship("Dossier", back_populates="campagne")


class Formation(Base):
    __tablename__ = "formations"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    nom = Column(String(200), nullable=False)
    niveau = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    dossiers = relationship("Dossier", back_populates="formation")


class Dossier(Base):
    __tablename__ = "dossiers"
    __table_args__ = (
        Index(
            "uq_dossier_actif_etudiant_campagne",
            "etudiant_id",
            "campagne_id",
            unique=True,
            sqlite_where=text("statut IN ('brouillon', 'en_attente', 'a_completer')"),
            postgresql_where=text("statut IN ('brouillon', 'en_attente', 'a_completer')"),
        ),
    )

    id = Column(Integer, primary_key=True)
    etudiant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    campagne_id = Column(Integer, ForeignKey("campagnes.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    statut = Column(String(30), nullable=False, default="brouillon", index=True)
    commentaire = Column(Text, nullable=True)
    correction_motif = Column(Text, nullable=True)
    decision_motif = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)

    etudiant = relationship("User", foreign_keys=[etudiant_id], back_populates="dossiers")
    decided_by = relationship("User", foreign_keys=[decided_by_id])
    campagne = relationship("Campagne", back_populates="dossiers")
    formation = relationship("Formation", back_populates="dossiers")
    pieces = relationship("Piece", back_populates="dossier", cascade="all, delete-orphan")
    historique = relationship(
        "Historique",
        back_populates="dossier",
        cascade="all, delete-orphan",
        order_by="Historique.created_at",
    )


class Piece(Base):
    __tablename__ = "pieces"

    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    type_piece = Column(String(20), nullable=False)
    nom_fichier = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)

    dossier = relationship("Dossier", back_populates="pieces")


class Historique(Base):
    __tablename__ = "historique"

    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    ancien_statut = Column(String(30), nullable=True)
    nouveau_statut = Column(String(30), nullable=False)
    acteur_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    motif = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    dossier = relationship("Dossier", back_populates="historique")
    acteur = relationship("User")
