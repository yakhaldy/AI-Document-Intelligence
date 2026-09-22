"""Seed the bootstrap admin account (README Étape 7).

Creates one approved admin user from ADMIN_USERNAME / ADMIN_PASSWORD_HASH
(.env). Idempotent: re-running just confirms the account already exists.
This is the only way to get a first admin — every other account is created
via POST /auth/register and stays 'pending' until an admin approves it.

Usage:
    python -m db.seed_admin
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models import User


def seed_admin(session: Session) -> None:
    username = os.environ.get("ADMIN_USERNAME")
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if not username or not password_hash:
        raise RuntimeError("ADMIN_USERNAME / ADMIN_PASSWORD_HASH manquant (voir .env)")

    existing = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        print(f"Admin '{username}' existe déjà (id={existing.id}, role={existing.role}, status={existing.status})")
        return

    admin = User(username=username, password_hash=password_hash, role="admin", status="approved")
    session.add(admin)
    session.commit()
    print(f"Admin '{username}' créé (id={admin.id})")


def main():
    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:
        seed_admin(session)


if __name__ == "__main__":
    main()
