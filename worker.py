"""Ejecuta las tareas pendientes vencidas. Pensado para un Cron Job de Render (cada hora).

El script respeta el intervalo configurado en la app (por defecto 12 h): si todavía no
pasó ese tiempo desde la última ejecución, sale sin hacer nada. Usa --force para ignorarlo.
"""

import argparse
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db import SessionLocal
from app.services import config as store
from app.services.logs import log_event
from app.services.tasks import run_due_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta tareas pendientes de Syncronify")
    parser.add_argument("--force", action="store_true", help="ignora el intervalo configurado")
    args = parser.parse_args()

    with SessionLocal() as db:
        default_hours = str(get_settings().default_sync_interval_hours)
        hours = int(store.get_config(db, "sync_interval_hours", default_hours))
        now = datetime.now(timezone.utc)

        last = store.get_config(db, "last_worker_run")
        if last and not args.force:
            if now - datetime.fromisoformat(last) < timedelta(hours=hours):
                print(f"Aún no toca ejecutar (intervalo de {hours} h).")
                return 0

        summary = run_due_tasks(db)
        log_event(
            db,
            "INFO",
            f"Ejecución programada: {summary['procesadas']} tareas ({summary['ok']} ok, "
            f"{summary['error']} con error, {summary['reintentar']} para reintentar)",
            module="worker",
        )
        store.set_config(db, "last_worker_run", now.isoformat())
        db.commit()
        print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
