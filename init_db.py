"""Crea todas las tablas en la base de datos indicada por DATABASE_URL."""

import app.models  # noqa: F401 - registra los modelos
from app.db import Base, engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("Tablas creadas (o ya existentes).")


if __name__ == "__main__":
    main()
