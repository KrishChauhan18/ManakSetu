"""
Manak Setu API — Frontend Backend
Runs on port 8000. React app talks to this.
Proxies compliance analysis to ComplyErg engine on port 8001.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.core import cloudinary_config          # initialise Cloudinary
from app.core.security import get_current_user, require_roles
from app.db.database import Base, engine, get_db
from app.db import models
from app.routers import auth, upload, inspections

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Manak Setu API",
    description="Frontend backend for the Manak Setu / ComplyErg legal-metrology compliance portal.",
    version="2.0.0",
)

# ── CORS — allow React dev server ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(inspections.router)


# ── Root / health ──────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Manak Setu API is running", "version": "2.0.0"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "healthy" if db_ok else "degraded", "database": db_ok}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "PostgreSQL connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}


# ── Dashboard stats ────────────────────────────────────────────────────────
@app.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Aggregate stats for the React dashboard cards."""
    from app.db.models import Inspection

    base_q = db.query(Inspection)
    # Inspector only sees own; supervisors/admins see all
    if current_user.role == "Inspector":
        base_q = base_q.filter(Inspection.inspector_id == current_user.id)

    total = base_q.count()
    compliant = base_q.filter(Inspection.result == "Compliant").count()
    review_req = base_q.filter(Inspection.result == "Review Required").count()
    potential = base_q.filter(Inspection.result == "Potential Issue").count()

    avg_score = db.query(func.avg(Inspection.score)).scalar() or 0.0

    # Category breakdown
    cat_rows = (
        db.query(Inspection.category, func.count(Inspection.id))
        .group_by(Inspection.category)
        .all()
    )
    by_category = {row[0] or "unknown": row[1] for row in cat_rows}

    # Recent 5
    recent = (
        base_q.order_by(Inspection.created_at.desc()).limit(5).all()
    )
    recent_list = [
        {
            "id": i.id,
            "scan_id": i.scan_id,
            "result": i.result,
            "score": i.score,
            "category": i.category,
            "created_at": str(i.created_at),
        }
        for i in recent
    ]

    return {
        "total_inspections": total,
        "compliant": compliant,
        "review_required": review_req,
        "potential_issue": potential,
        "compliance_rate": round((compliant / total * 100) if total else 0, 1),
        "avg_score": round(float(avg_score), 1),
        "by_category": by_category,
        "recent_inspections": recent_list,
    }


# ── Users management (Supervisor/Admin only) ───────────────────────────────
@app.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Supervisor", "Administrator")),
):
    officers = db.query(models.Officer).order_by(models.Officer.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "name": o.name,
            "email": o.email,
            "role": o.role,
            "is_active": o.is_active,
            "created_at": str(o.created_at),
        }
        for o in officers
    ]


@app.post("/users")
def create_user(
    name: str,
    email: str,
    password: str,
    role: str = "Inspector",
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Administrator")),
):
    from app.core.security import hash_password
    existing = db.query(models.Officer).filter(models.Officer.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    officer = models.Officer(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return {"message": "User created", "id": officer.id, "email": officer.email}


@app.patch("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Administrator")),
):
    officer = db.query(models.Officer).filter(models.Officer.id == user_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="User not found")
    officer.is_active = not officer.is_active
    db.commit()
    return {"message": f"User {'activated' if officer.is_active else 'deactivated'}", "is_active": officer.is_active}


# ── Audit log ──────────────────────────────────────────────────────────────
@app.get("/audit")
def audit_log(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Administrator")),
):
    """Return recent inspection activity as a simple audit trail."""
    from app.db.models import Inspection
    rows = (
        db.query(Inspection, models.Officer)
        .join(models.Officer, Inspection.inspector_id == models.Officer.id)
        .order_by(Inspection.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": insp.id,
            "scan_id": insp.scan_id,
            "action": f"status={insp.status}",
            "officer": off.name,
            "email": off.email,
            "role": off.role,
            "result": insp.result,
            "score": insp.score,
            "timestamp": str(insp.updated_at or insp.created_at),
        }
        for insp, off in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)