"""Usuarios sintéticos de demo. La contraseña viene de DEMO_PASSWORD (entorno)."""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import User
from app.security import ROLES, hash_password

DEMO_USERS = {f"demo_{r}": r for r in ROLES}


def seed_users(db: Session, password: str) -> int:
    created = 0
    for username, role in DEMO_USERS.items():
        if db.scalars(select(User).where(User.username == username)).first() is None:
            db.add(User(username=username, password_hash=hash_password(password), role=role))
            created += 1
    db.commit()
    return created


def main() -> None:
    password = get_settings().demo_password
    if len(password) < 12:
        sys.exit("Defina DEMO_PASSWORD (mínimo 12 caracteres) en el entorno")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(f"Usuarios demo creados: {seed_users(db, password)}")


if __name__ == "__main__":
    main()
