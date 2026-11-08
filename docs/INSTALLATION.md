# Lokale Installation

## Docker Compose (Entwicklung)

1. Docker Engine und Compose installieren.
2. `cp .env.example .env` ausführen und ein eigenes Datenbankpasswort eintragen.
3. Für lokales HTTP den Override `docker-compose.dev.yml` verwenden; er deaktiviert Secure-Cookies ausschließlich in der Entwicklungsumgebung.
4. PostgreSQL und Redis starten und die Migration einmalig ausführen:

   ```sh
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db redis
   docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile release run --rm migrate
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
   ```

5. Den Admin-Bootstrap-Befehl aus der README mit einmaligen Shell-Umgebungsvariablen ausführen.
6. Statische Oberfläche unter `http://localhost:5173`, API-Dokumentation unter `http://localhost:8000/docs` öffnen.

## Ohne Container

Backend: Python 3.12+, `cd backend`, `pip install '.[test]'`, PostgreSQL-Umgebung setzen, Migrationen einmalig mit `alembic upgrade head` ausführen und `uvicorn app.main:app --reload` starten. Für lokale HTTP-Entwicklung `APP_ENV=development` und `SESSION_COOKIE_SECURE=false` ausdrücklich setzen. Frontend-Entwicklung: `cd frontend`, `npm ci`, `npm run dev`.

## Status

Der lokale Installationspfad wurde nicht in einer Docker-Umgebung ausgeführt. Die PostgreSQL-17-CI prüft Migrationen, API-Tests und einen separaten verschlüsselten Backup-/Restore-Zyklus. Der erste Administrator benötigt gültige Umgebungsvariablen; es gibt kein fest eingebautes Standardkonto oder Passwort.
