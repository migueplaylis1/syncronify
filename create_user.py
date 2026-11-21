"""Crea un usuario. Ejemplo:

    python create_user.py --name "Miguel Angel" --email miguel@correo.com --role admin
"""

import argparse
import getpass

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=["admin", "user"], default="admin")
    args = parser.parse_args()

    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if len(password) < 8:
        raise SystemExit("La contraseña debe tener al menos 8 caracteres.")

    email = args.email.strip().lower()
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)):
            raise SystemExit("Ya existe un usuario con ese correo.")
        db.add(User(name=args.name.strip(), email=email, password_hash=hash_password(password), role=args.role))
        db.commit()
    print(f"Usuario creado: {email} ({args.role})")


if __name__ == "__main__":
    main()
