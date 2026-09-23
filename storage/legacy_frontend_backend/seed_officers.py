"""
seed_officers.py
Run once to create demo officers in the manak_setu PostgreSQL database.
Usage: python seed_officers.py (from frontend/backend/ directory)
"""

import sys
import os

# Allow running from project root OR from frontend/backend/
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import engine, SessionLocal, Base
from app.db.models import Officer
from app.core.security import hash_password

# Ensure tables exist
Base.metadata.create_all(bind=engine)

DEMO_OFFICERS = [
    {
        "name": "Anjali Sharma",
        "email": "inspector@manaksetu.gov.in",
        "password": "Inspector@123",
        "role": "Inspector",
    },
    {
        "name": "Rajesh Verma",
        "email": "supervisor@manaksetu.gov.in",
        "password": "Supervisor@123",
        "role": "Supervisor",
    },
    {
        "name": "Dr. Priya Nair",
        "email": "admin@manaksetu.gov.in",
        "password": "Admin@123",
        "role": "Administrator",
    },
    # Second inspector for demo history
    {
        "name": "Suresh Kumar",
        "email": "inspector2@manaksetu.gov.in",
        "password": "Inspector@123",
        "role": "Inspector",
    },
]


def seed():
    db = SessionLocal()
    created = 0
    try:
        for data in DEMO_OFFICERS:
            existing = db.query(Officer).filter(Officer.email == data["email"]).first()
            if existing:
                print(f"  [SKIP] Already exists: {data['email']}")
                continue
            officer = Officer(
                name=data["name"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
                is_active=True,
            )
            db.add(officer)
            created += 1
            print(f"  [OK] Created: {data['email']} [{data['role']}]")
        db.commit()
        print(f"\n[DONE] Seeding complete -- {created} officer(s) added.")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("[*] Seeding demo officers into manak_setu database...\n")
    seed()
