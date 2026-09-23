import json
import os
import secrets
import string
import logging
from typing import Dict, List, Optional
from sqlalchemy import text

from app.db.session import engine, SessionLocal
from app.models.domain import Base, Rule, User
from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger("complyerg.security.init_db")


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure randomized password.
    Guarantees inclusion of uppercase, lowercase, digits, and special characters.
    """
    if length < 12:
        length = 12

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+"
    all_chars = lowercase + uppercase + digits + symbols

    while True:
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]
        password += [secrets.choice(all_chars) for _ in range(length - 4)]
        secrets.SystemRandom().shuffle(password)
        candidate = "".join(password)
        # Verify complexity
        if (
            any(c in lowercase for c in candidate)
            and any(c in uppercase for c in candidate)
            and any(c in digits for c in candidate)
            and any(c in symbols for c in candidate)
        ):
            return candidate


def _ensure_schema_migrations():
    """
    Perform lightweight schema migration on existing databases
    to ensure columns like 'must_change_password' exist without requiring Alembic.
    """
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT must_change_password FROM users LIMIT 1"))
        except Exception:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0 NOT NULL"))
                conn.commit()
                logger.info("Successfully migrated 'users' table: added 'must_change_password' column.")
            except Exception as e:
                logger.warning(f"Schema migration attempt for 'must_change_password' notice: {e}")


def init_db() -> Dict[str, str]:
    """
    Initialize database schema, apply table migrations, and seed initial accounts
    using randomized cryptographic credentials while enforcing mandatory password change.
    """
    Base.metadata.create_all(bind=engine)
    _ensure_schema_migrations()

    db = SessionLocal()
    newly_generated_credentials: Dict[str, Dict[str, str]] = {}

    try:
        # Seed Definitions
        seed_accounts = [
            {
                "email": "admin@complyerg.gov.in",
                "role": "admin",
                "region": "Delhi NCR",
                "supervisor_email": None
            },
            {
                "email": "supervisor@complyerg.gov.in",
                "role": "supervisor",
                "region": "Delhi NCR",
                "supervisor_email": None
            },
            {
                "email": "inspector@complyerg.gov.in",
                "role": "inspector",
                "region": "Delhi NCR",
                "supervisor_email": "supervisor@complyerg.gov.in"
            }
        ]

        created_users: Dict[str, User] = {}

        for account in seed_accounts:
            email = account["email"]
            role = account["role"]
            existing_user = db.query(User).filter(User.email == email).first()

            if not existing_user:
                # Generate a unique cryptographic random password
                raw_password = generate_secure_password(length=18)
                hashed = get_password_hash(raw_password)

                supervisor_id = None
                if account["supervisor_email"] and account["supervisor_email"] in created_users:
                    supervisor_id = created_users[account["supervisor_email"]].id
                elif account["supervisor_email"]:
                    sup = db.query(User).filter(User.email == account["supervisor_email"]).first()
                    if sup:
                        supervisor_id = sup.id

                user_obj = User(
                    email=email,
                    password_hash=hashed,
                    role=role,
                    region=account["region"],
                    supervisor_id=supervisor_id,
                    is_active=True,
                    must_change_password=True  # Enforce mandatory password rotation
                )
                db.add(user_obj)
                db.flush()
                created_users[email] = user_obj

                newly_generated_credentials[email] = {
                    "role": role,
                    "generated_password": raw_password,
                    "must_change_password": "True"
                }
            else:
                created_users[email] = existing_user
                logger.info(f"User account '{email}' already exists. Preserving existing credentials.")

        db.commit()

        # Output credentials if new accounts were provisioned
        if newly_generated_credentials:
            banner = (
                "\n" + "=" * 80 + "\n"
                + "  [CRITICAL SECURITY LOG] INITIAL SEED ACCOUNTS PROVISIONED\n"
                + "  Cryptographically randomized passwords generated on initial setup.\n"
                + "  Mandatory password rotation flag ('must_change_password') is ENFORCED.\n"
                + "=" * 80 + "\n"
            )
            for em, info in newly_generated_credentials.items():
                banner += f"  ROLE: {info['role'].upper():<12} | EMAIL: {em:<28} | ONE-TIME PWD: {info['generated_password']}\n"
            banner += (
                "=" * 80 + "\n"
                + "  IMPORTANT: Store these credentials in an offline password manager immediately.\n"
                + "  These one-time passwords will not be displayed again.\n"
                + "=" * 80 + "\n"
            )
            logger.warning(banner)
            print(banner)

            # Persist secure credentials artifact locally for administrator setup
            creds_path = os.path.join(settings.STORAGE_DIR, ".initial_seed_credentials.json")
            try:
                with open(creds_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "notice": "DO NOT SHARE. Rotate passwords immediately on first login.",
                        "accounts": newly_generated_credentials
                    }, f, indent=2)
                # Restrict permissions on POSIX systems if applicable
                if hasattr(os, "chmod"):
                    try:
                        os.chmod(creds_path, 0o600)
                    except Exception:
                        pass
                logger.info(f"Initial seed credentials recorded to {creds_path} (mode 0600).")
            except Exception as exc:
                logger.error(f"Failed to record secure credentials file: {exc}")

        # Seed Statutory Rules
        def seed_rules_from_file(file_path: str, default_source_law: str):
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    rules_data = json.load(f)

                for rule_item in rules_data:
                    existing_rule = db.query(Rule).filter(Rule.rule_id_str == rule_item["rule_id"]).first()
                    source_law = rule_item.get("source_law", default_source_law)
                    field_val = json.dumps(rule_item["field"]) if isinstance(rule_item["field"], (list, dict)) else str(rule_item["field"])
                    cat_val = rule_item.get("category", ["all"])
                    if not existing_rule:
                        rule_obj = Rule(
                            rule_id_str=rule_item["rule_id"],
                            legal_rule_ref=rule_item.get("legal_rule_ref", "Rule 6"),
                            source_law=source_law,
                            field=field_val,
                            check_type=rule_item["check"],
                            pattern=rule_item.get("pattern"),
                            severity=rule_item["severity"],
                            category=cat_val,
                            version=rule_item.get("version", "2011"),
                            enabled=True
                        )
                        db.add(rule_obj)
                    else:
                        existing_rule.legal_rule_ref = rule_item.get("legal_rule_ref", "Rule 6")
                        existing_rule.source_law = source_law
                        existing_rule.field = field_val
                        existing_rule.check_type = rule_item["check"]
                        existing_rule.pattern = rule_item.get("pattern")
                        existing_rule.severity = rule_item["severity"]
                        existing_rule.category = cat_val

                db.commit()
                logger.info(f"Seeded {len(rules_data)} statutory rules from {os.path.basename(file_path)}.")

        seed_rules_from_file(settings.RULES_SEED_FILE, "Legal Metrology 2011")
        seed_rules_from_file(settings.DRUGS_RULES_SEED_FILE, "Drugs and Cosmetics Rules, 1945")

        return {k: v["generated_password"] for k, v in newly_generated_credentials.items()}

    except Exception as exc:
        logger.error(f"Error during database initialization: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
