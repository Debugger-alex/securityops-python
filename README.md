# SecurityOps – erste Ausbaustufe

Ein lokal startbares Grundgerüst für die Verwaltungsplattform eines Sicherheitsdienstes. Enthalten sind ein FastAPI-Backend, PostgreSQL, Datenbankmigrationen, eine versionierte Kunden-API und eine React-Oberfläche für Kundenstammdaten.

## Start mit Docker Compose

Voraussetzung ist Docker mit Compose. Im Projektordner:

```sh
cp .env.example .env
```

Ändere in `.env` das Datenbankpasswort und starte anschließend:

```sh
docker compose up --build
```

Die Anwendung ist danach unter <http://localhost:5173> erreichbar. Die API-Dokumentation befindet sich unter <http://localhost:8000/docs>. Die Ports sind standardmäßig nur an `localhost` gebunden.

## API

- `GET /health/live` – Prozessstatus
- `GET /health/ready` – Datenbankverbindung prüfen
- `GET /api/v1/dashboard` – Kundenkennzahlen
- `GET /api/v1/customers?q=...&limit=25&offset=0` – Kunden suchen und paginieren
- `POST /api/v1/customers` – Kunde anlegen
- `GET /api/v1/customers/{id}` – Kundendetails abrufen
- `PATCH /api/v1/customers/{id}` – Kundendaten ändern

Statuswerte: `active`, `inactive`, `lead`. Kundennummern werden serverseitig eindeutig als `K-<UUID>` erzeugt. Kunden werden in dieser Ausbaustufe nicht physisch gelöscht.

## Datenbankserver konfigurieren

Das Backend liest `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` aus der Umgebung. Compose setzt `POSTGRES_HOST=db` für den enthaltenen PostgreSQL-Dienst. Für einen externen PostgreSQL-Server können diese Werte in der `.env` auf dessen Verbindungsdaten gesetzt werden. `CORS_ORIGINS` steuert die erlaubte Browser-Origin. Der Datenbankport wird absichtlich nicht öffentlich freigegeben.

Bei direktem Backend-Start außerhalb von Docker: Python 3.12+, `cd backend`, `pip install '.[test]'`, die PostgreSQL-Variablen setzen, `alembic upgrade head` und danach `uvicorn app.main:app --reload`. `POSTGRES_PASSWORD` sollte nicht in Quellcode oder Versionsverwaltung abgelegt werden.

## Tests

```sh
cd backend
pip install '.[test]'
pytest
```

Die API-Tests verwenden eine isolierte SQLite-Testdatenbank; der Produktivbetrieb verwendet PostgreSQL.

## Umfang und Sicherheit

Dies ist ein lauffähiger Startpunkt, kein produktionsreifes Gesamtsystem. Benutzeranmeldung, Rollen-/Objektberechtigungen, MFA, Audit-Protokoll, OWKS, Personal, Verträge und Abrechnung sind noch nicht implementiert. Deshalb darf diese Version nicht öffentlich oder mit echten schutzbedürftigen Kunden- oder Personaldaten betrieben werden. Vor einem Serverbetrieb müssen insbesondere Authentifizierung, Autorisierung, Auditierung, TLS/Reverse-Proxy, Geheimnisverwaltung, Backups und Wiederherstellung ergänzt und geprüft werden.
