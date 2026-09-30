from app.api.routes.auth import router as auth_router
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.routes.institutional_accounts import (router as institutional_accounts_router)
from app.api.routes.patients import router as patients_router
from app.core.database import test_database_connection


app = FastAPI(
    title="RetiScan API",
    description="Backend API para el sistema de soporte clínico RetiScan",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(institutional_accounts_router)
app.include_router(patients_router)

@app.get("/")
def root():
    return {
        "message": "Backend RetiScan funcionando correctamente"
    }


@app.get("/health/db")
def database_health():
    result = test_database_connection()

    return {
        "status": "ok",
        "message": "Conexión con PostgreSQL exitosa",
        "database": result["database"],
        "user": result["user"]
    }

@app.get("/health/db-session")
def database_session_health(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("SELECT current_database(), current_user")
    ).one()

    return {
        "status": "ok",
        "database": result[0],
        "user": result[1],
        "session": "active"
    }
