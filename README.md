# Syncronify

Replica interna de tu app de sincronización de playlists de Spotify, con base de datos nueva (PostgreSQL), backend en FastAPI y despliegue en Render.

## Estructura

```
syncronify/
├── app/
│   ├── main.py              # App FastAPI, sesiones, rutas y página principal
│   ├── config.py            # Variables de entorno
│   ├── db.py / models.py    # Conexión y tablas (PostgreSQL)
│   ├── schemas.py           # Validación de entrada y salida
│   ├── spotify.py           # Cliente de la API de Spotify (OAuth y playlists)
│   ├── security.py          # Hash de contraseñas
│   ├── deps.py              # Usuario actual y control de administrador
│   ├── routers/             # Endpoints: auth, users, spotify, playlists, tracks, tasks, logs, config
│   ├── services/            # Lógica: importación, tokens, ejecución de tareas, logs
│   └── static/index.html    # Interfaz (pantallas de tu app original)
├── worker.py                # Ejecuta tareas pendientes (Cron Job en Render)
├── init_db.py               # Crea las tablas
├── create_user.py           # Crea usuarios
├── render.yaml              # Blueprint: base de datos + web + worker
└── requirements.txt
```

## Qué resuelve la versión nueva

- **Posición al agregar:** en "Playlists de destino" ves las canciones de cada playlist y eliges en qué posición entra la tuya (primero, último o antes de una canción concreta). Si agregas varias, se insertan consecutivas desde esa posición.
- **Reposicionar:** en "Posicionar múltiple" mueves canciones a una posición nueva dentro de una playlist.
- **Tareas en base de datos:** cada acción queda como tarea con estado (pendiente, ejecutando, ejecutada, error), fecha, intentos y último error. Se pueden editar o eliminar mientras estén pendientes.
- **Logs en base de datos:** cada acción, error, inicio de sesión y sincronización queda registrada con usuario, módulo y fecha. Puedes filtrar por mes y nivel.
- **Ejecución segura:** el worker toma las tareas con bloqueo de fila (`SKIP LOCKED`), así dos ejecuciones no procesan la misma tarea.

## Ejecutar en local

1. Crea una base PostgreSQL local (o usa una de Render) y copia `.env.example` a `.env`.
2. Instala dependencias y crea las tablas:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python create_user.py --name "Miguel Angel" --email tu@correo.com --role admin
uvicorn app.main:app --reload
```

3. Abre http://localhost:8000 e inicia sesión.

## Configurar Spotify

1. En https://developer.spotify.com/dashboard crea una app.
2. En **Redirect URIs** agrega `http://localhost:8000/api/spotify/callback` (local) y `https://TU-APP.onrender.com/api/spotify/callback` (producción). Deben coincidir exactamente con `SPOTIFY_REDIRECT_URI`.
3. Copia el Client ID y el Client Secret a `.env` (o a las variables de Render).
4. Dentro de la app, ve a **Configuración** y pulsa **Vincular Spotify**.

Revisa en el dashboard de Spotify los límites vigentes del modo desarrollo (por ejemplo, cuántos usuarios puede tener la app), porque pueden afectar a tu cuenta.

## Desplegar en Render

1. Sube el proyecto a un repositorio de GitHub.
2. En Render elige **New → Blueprint** y selecciona el repositorio. Render leerá `render.yaml` y creará la base de datos, la web app y el worker.
3. Completa las variables marcadas como `sync: false`:
   - `FRONTEND_URL` = `https://TU-APP.onrender.com`
   - `SPOTIFY_REDIRECT_URI` = `https://TU-APP.onrender.com/api/spotify/callback`
   - `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET`
   - Repite `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` en el worker.
4. En el shell de la web app (pestaña Shell de Render, disponible en planes de pago) ejecuta:

```bash
python init_db.py
python create_user.py --name "Miguel Angel" --email tu@correo.com --role admin
```

5. Abre la URL de tu app, inicia sesión y vincula Spotify.

El worker corre cada hora (`0 * * * *`). Cada ejecución real respeta el intervalo configurado en la app (12 h por defecto), así que el cron puede ser horario sin ejecutar Spotify cada hora.

## Notas importantes

- **No he podido probar esto contra Spotify ni contra Render.** Revisé la sintaxis del Python y del JavaScript, y probé el hash de contraseñas, pero no ejecuté el servidor completo. La primera vez, prueba la vinculación de Spotify y una tarea de prueba con una playlist que no uses en producción.
- **Nombres de endpoints de Spotify:** Spotify ha cambiado algunos nombres de sus endpoints de playlists. Por eso el segmento se configura con `SPOTIFY_ITEMS_SEGMENT`. Si una llamada devuelve 404, prueba `tracks`.
- **Posición en Spotify:** Spotify usa posiciones que empiezan en 0. La app convierte la posición que ves en pantalla (1, 2, 3…) a ese índice. Al mover una canción hacia abajo, la app compensa el desplazamiento que Spotify aplica al quitar el elemento.
- **Días de proyección:** se guardan en cada tarea, pero la app no les da lógica todavía. Dime qué significan para tu flujo y lo implemento.
- **"Quitar del catálogo"** borra la playlist solo de la base local; no toca Spotify.
- **Tareas atascadas:** si el proceso se corta mientras una tarea está en "Ejecutando", queda así. Puedes cambiar su estado a `pending` directamente en la base de datos para que se reintente.
- **Contraseñas y secretos:** nunca los pegues en el código ni en un chat. Van en variables de entorno.
