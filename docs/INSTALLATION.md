# Lokale Installation

## Docker Compose (Entwicklung)

1. Docker Engine und Compose installieren.
2. `cp .env.example .env` ausführen und ein eigenes Datenbankpasswort eintragen.
3. `SESSION_COOKIE_SECURE=false` nur für lokales HTTP belassen.
4. Für sensible Objektangaben einen eigenen, stabil zu sichernden 32-Byte-Schlüssel für `OBJECT_DATA_ENCRYPTION_KEY` erzeugen und setzen. Ohne ihn sind diese Angaben nicht lesbar oder speicherbar.
5. `docker compose up --build` starten.
6. Nach erfolgreicher API-/Datenbankinitialisierung den Admin-Bootstrap-Befehl aus der README mit einmaligen Shell-Umgebungsvariablen ausführen.
7. Oberfläche unter `http://localhost:5173`, API-Dokumentation unter `http://localhost:8000/docs` öffnen.

## Ohne Container

Backend: Python 3.12+, `cd backend`, `pip install '.[test]'`, PostgreSQL-Umgebung setzen, `alembic upgrade head`, `uvicorn app.main:app --reload`. Frontend: `cd frontend`, `npm ci`, `npm run dev`. Die Vite-Proxykonfiguration verweist auf `http://api:8000` und ist außerhalb von Docker lokal auf `localhost` anzupassen.

## Status

Der lokale Installationspfad wurde nicht in einer Docker-Umgebung ausgeführt. Der erste Administrator benötigt gültige Umgebungsvariablen; es gibt kein fest eingebautes Standardkonto oder Passwort.
