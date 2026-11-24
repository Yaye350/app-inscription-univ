import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from routers import auth_routes, dossiers, referentiels
from seed import seed

database.init_engine()


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    if os.getenv("SEED", "1") == "1":
        db = database.SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    yield


app = FastAPI(title="Inscriptions universitaires", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_routes.router)
app.include_router(auth_routes.me_router)
app.include_router(referentiels.router)
app.include_router(dossiers.router)


@app.get("/")
def accueil():
    return {"message": "API de gestion des inscriptions universitaires"}


@app.get("/health")
def health():
    return {"status": "ok"}
