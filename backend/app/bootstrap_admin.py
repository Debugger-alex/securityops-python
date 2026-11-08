import os
import re
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.database import SessionLocal
from app.identity_api import password_hasher
from app.models import Role, User


def main() -> int:
    required = (
        "BOOTSTRAP_ADMIN_USERNAME",
        "BOOTSTRAP_ADMIN_EMAIL",
        "BOOTSTRAP_ADMIN_NAME",
        "BOOTSTRAP_ADMIN_PASSWORD",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        print(f"Fehlende Umgebungsvariablen: {', '.join(missing)}", file=sys.stderr)
        return 2

    username = os.environ["BOOTSTRAP_ADMIN_USERNAME"].strip().lower()
    email_input = os.environ["BOOTSTRAP_ADMIN_EMAIL"].strip().lower()
    full_name = os.environ["BOOTSTRAP_ADMIN_NAME"].strip()
    password = os.environ["BOOTSTRAP_ADMIN_PASSWORD"]
    if not re.fullmatch(r"[a-zA-Z0-9._-]{3,80}", username):
        print("Der Administrator-Benutzername ist ungültig.", file=sys.stderr)
        return 2
    if not full_name or len(full_name) > 160:
        print("Der Administratorname ist ungültig.", file=sys.stderr)
        return 2
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email_input)).lower()
    except ValidationError:
        print("Die Administrator-E-Mail-Adresse ist ungültig.", file=sys.stderr)
        return 2
    if not 12 <= len(password) <= 128:
        print("Das Administratorpasswort muss 12 bis 128 Zeichen enthalten.", file=sys.stderr)
        return 2

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing_user is not None:
            print("Benutzername oder E-Mail-Adresse ist bereits vorhanden.", file=sys.stderr)
            return 1
        administrator = db.scalar(select(Role).where(Role.code == "administrator"))
        if administrator is None:
            print(
                "Rolle 'administrator' fehlt. Zuerst Alembic-Migrationen ausführen.",
                file=sys.stderr,
            )
            return 1
        db.add(
            User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hasher.hash(password),
                roles=[administrator],
            )
        )
        db.commit()
    print(f"Administratorkonto '{username}' wurde erstellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
