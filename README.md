# SecurityOps – Entwicklungsstand

Modularer Start für die Verwaltungsplattform eines Sicherheitsdienstes. Enthalten sind FastAPI, PostgreSQL, Alembic, eine React-Oberfläche, Kundenstammdaten sowie Benutzeranmeldung, Rollen-/Rechteprüfung und Audit-Protokoll.

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

Die `SESSION_COOKIE_SECURE`-Einstellung ist im lokalen HTTP-Beispiel deaktiviert. Für jeden Betrieb hinter HTTPS muss sie auf `true` gesetzt werden. `POSTGRES_PASSWORD` ist erforderlich; ändere das Beispielpasswort vor dem Start und verwende für jeden Server ein eigenes Secret.

## Erstes Administratorkonto

Nach dem Start legt Alembic die Systemrollen und Berechtigungen an. Erstelle danach ein erstes Administratorkonto. Setze die vier Variablen in deiner lokalen Shell (nicht in Git) und führe aus:

```sh
export BOOTSTRAP_ADMIN_USERNAME=admin
export BOOTSTRAP_ADMIN_EMAIL=admin@deine-domain.de
export BOOTSTRAP_ADMIN_NAME="System Administration"
export BOOTSTRAP_ADMIN_PASSWORD='ein-einmaliges-lang-passwort'
docker compose exec \
  -e BOOTSTRAP_ADMIN_USERNAME \
  -e BOOTSTRAP_ADMIN_EMAIL \
  -e BOOTSTRAP_ADMIN_NAME \
  -e BOOTSTRAP_ADMIN_PASSWORD \
  api python -m app.bootstrap_admin
unset BOOTSTRAP_ADMIN_USERNAME BOOTSTRAP_ADMIN_EMAIL BOOTSTRAP_ADMIN_NAME BOOTSTRAP_ADMIN_PASSWORD
```

Das Passwort muss mindestens 12 Zeichen lang sein. Der Bootstrapping-Befehl erstellt kein Standardpasswort und verweigert doppelte Benutzernamen oder E-Mail-Adressen. Melde dich anschließend an und erstelle weitere Benutzer über `POST /api/v1/users`.

## API

- `GET /health/live` – Prozessstatus
- `GET /health/ready` – Datenbankverbindung prüfen
- `GET /api/v1/dashboard` – Kundenkennzahlen
- `POST /api/v1/auth/login` – Anmeldung und sichere Sitzung starten
- `GET /api/v1/auth/me` – angemeldeten Benutzer und Berechtigungen abrufen
- `POST /api/v1/auth/logout` – Sitzung beenden (CSRF-Token erforderlich)
- `POST /api/v1/auth/change-password` – Passwort ändern und Sitzungen widerrufen
- `GET /api/v1/users` / `POST /api/v1/users` – Benutzerverwaltung (entsprechende Berechtigung erforderlich)
- `GET /api/v1/roles` – Standardrollen und Rechte einsehen
- `GET /api/v1/audit-logs` – jüngste Audit-Einträge einsehen
- `GET /api/v1/customers?q=...&limit=25&offset=0` – Kunden suchen und paginieren
- `POST /api/v1/customers` – Kunde anlegen
- `GET /api/v1/customers/{id}` – Kundendetails abrufen
- `PATCH /api/v1/customers/{id}` – Kundendaten ändern
- `GET /api/v1/objects?q=...&status=...&customer_id=...` – Objekte suchen, filtern und paginieren
- `POST /api/v1/objects` – Objekt mit Kundenbeziehung anlegen
- `GET /api/v1/objects/{id}` / `PATCH /api/v1/objects/{id}` – Objekt abrufen oder ändern
- `POST /api/v1/objects/{id}/archive` und `/reactivate` – Objekt archivieren oder reaktivieren
- `GET /api/v1/objects/{id}/history` – Objektänderungen einsehen
- `/api/v1/objects/{id}/contacts` – Ansprechpartner einzeln verwalten
- `/api/v1/objects/{id}/assignments` – Objektmitarbeiter zuweisen (separate Berechtigung)
- `/api/v1/objects/{id}/security` – sensible Sicherheits- und Zutrittsdaten (separate Berechtigungen)

Statuswerte: `active`, `inactive`, `lead`. Kundennummern werden serverseitig eindeutig als `K-<UUID>` erzeugt. Kunden werden in dieser Ausbaustufe nicht physisch gelöscht.

## Datenbankserver konfigurieren

Das Backend liest `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` aus der Umgebung. Compose setzt `POSTGRES_HOST=db` für den enthaltenen PostgreSQL-Dienst. Für einen externen PostgreSQL-Server können diese Werte in der `.env` auf dessen Verbindungsdaten gesetzt werden. `CORS_ORIGINS` steuert die erlaubte Browser-Origin. Der Datenbankport wird absichtlich nicht öffentlich freigegeben. Sitzungen verwenden zufällige opaque Cookies; der Datenbankeintrag speichert nur den Token-Hash. Schreibzugriffe erfordern einen CSRF-Header. Passwort-Hashes werden mit Argon2id erzeugt.

Bei direktem Backend-Start außerhalb von Docker: Python 3.12+, `cd backend`, `pip install '.[test]'`, die PostgreSQL-Variablen setzen, für lokale HTTP-Entwicklung `SESSION_COOKIE_SECURE=false` einstellen, `alembic upgrade head` und danach `uvicorn app.main:app --reload`. `POSTGRES_PASSWORD` sollte nicht in Quellcode oder Versionsverwaltung abgelegt werden.

## Tests

```sh
cd backend
pip install '.[test]'
pytest
```

Die API-Tests verwenden eine isolierte SQLite-Testdatenbank; der Produktivbetrieb verwendet PostgreSQL.

## Projektstatus und Sicherheit

Die Bestandsaufnahme und offenen Module sind in [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md), [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) und der [priorisierten Implementierungs-Roadmap](docs/IMPLEMENTATION_ROADMAP.md) dokumentiert. Weitere technische Informationen: [Architektur](docs/ARCHITECTURE.md), [Datenbank](docs/DATABASE.md), [API](docs/API.md), [Sicherheitsstatus](docs/SECURITY.md), [Sicherheitsprüfung](docs/SECURITY_REVIEW.md), [Installation](docs/INSTALLATION.md), [Deployment](docs/DEPLOYMENT.md), [Backup/Restore](docs/BACKUP_RESTORE.md), [Benutzeranleitung](docs/USER_GUIDE.md), [Changelog](docs/CHANGELOG.md) und [Roadmap](docs/ROADMAP.md).

Die Objektverwaltung umfasst Backend, API und eine Frontend-Oberfläche mit Suche, Filterung, Sortierung, Details, Anschriften, Ansprechpartnern, Archivierung, Historie, Zuweisungen und getrennt geschützten Sicherheitsdaten. Objektzugriff wird serverseitig anhand globaler Rechte oder einer Objektzuweisung geprüft. Zuweisungen referenzieren derzeit aktive Benutzerkonten mit Mitarbeiter- oder Objektleitungsrolle; eine eigenständige Personalverwaltung ist noch nicht vorhanden. MFA, Passwortzurücksetzung, Dienstplanung, Zeiterfassung, OWKS, Dokumente und Rechnungswesen sind noch nicht implementiert. Das Audit-Protokoll ist über die Anwendung schreibgeschützt, aber noch nicht durch getrennte Datenbankrollen gegen privilegierte Datenbankänderungen abgesichert.

Die Anwendung ist ein Entwicklungsstand, keine Produktionsfreigabe. Lokal wurden Backendtests, Ruff und Frontendbuild ausgeführt; die PostgreSQL-Migrationen wurden offline für den PostgreSQL-Dialekt gerendert. Ein lokaler PostgreSQL-Integrationslauf und Docker-Builds waren in dieser Umgebung nicht verfügbar. Vor öffentlichem Betrieb müssen unter anderem HTTPS/Reverse-Proxy, `SESSION_COOKIE_SECURE=true`, zentralisiertes Rate-Limiting, Backup/Wiederherstellung, Sicherheitsprüfung und die Datenschutz-/Aufbewahrungsvorgaben für den konkreten Betrieb eingerichtet sein.
