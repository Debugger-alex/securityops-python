# SecurityOps – Entwicklungsstand

Modularer Start für die Verwaltungsplattform eines Sicherheitsdienstes. Enthalten sind FastAPI, PostgreSQL, Alembic, eine React-Oberfläche, Kunden-, Objekt- und Personalverwaltung sowie Benutzeranmeldung, Rollen-/Rechteprüfung und Audit-Protokoll. Dienstplanung und Zeiterfassung sind in `main`; PR #23 ergänzt das objektgebundene OWKS-Wachbuch, QR-/NFC-Kontrollgänge und Offline-Synchronisierung.

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
- `GET /api/v1/employees?q=...&status=...` – Personal suchen, filtern und paginieren (`employees.read`)
- `POST /api/v1/employees` und `GET /api/v1/employees/{id}` – Personalakte anlegen und abrufen
- `/api/v1/employees/{id}/qualifications` – Qualifikationsnachweise verwalten
- `/api/v1/employees/qualifications/expiring` – ablaufende und abgelaufene Nachweise
- `/api/v1/employees/{id}/absences` – Abwesenheiten mit eigenen Rechten verwalten
- `/api/v1/employees/{id}/sensitive` – getrennt geschützte sensible Personaldaten
- `/api/v1/scheduling/settings` – Zeitzone und Mindestruhezeit lesen/ändern
- `/api/v1/scheduling/shifts` – Schichten mit Tages-/Wochen-/Monatsfiltern lesen und verwalten
- `/api/v1/scheduling/shifts/{id}/history` – nachvollziehbaren Änderungsverlauf lesen
- `/api/v1/time-tracking/start` und `/entries/{id}/pause|resume|stop` – Arbeitsintervalle und Pausen erfassen
- `/api/v1/time-tracking/entries` – eigene oder berechtigt sichtbare Buchungen nach Zeitraum und Status abrufen
- `/api/v1/time-tracking/entries/manual` – manuelle, freigabepflichtige Nachträge für berechtigte Benutzer
- `/api/v1/time-tracking/entries/{id}/corrections` und `/corrections/{id}/approve|reject` – Korrekturen beantragen und entscheiden
- `/api/v1/time-tracking/entries/{id}/approve|reject|lock` – Einreichungen freigeben, begründet ablehnen oder sperren
- `/api/v1/time-tracking/reports` und `/reports/missing` – Soll-/Ist-, Pausen-, Abweichungs- und Fehlbuchungsübersichten
- `/api/v1/time-tracking/export.csv` – CSV-Export freigegebener Arbeitszeiten
- `/api/v1/time-tracking/surcharge-rules` und `/settings` – konfigurierbare Zuschlagsarten und Feiertags-Bundesland
- `/api/v1/time-tracking/entries/{id}/surcharge-calculations` – getrennte, versionierte Zuschlagszeit-Nachweise
- `/api/v1/time-tracking/reports/surcharges` und `/export-surcharges.csv` – Auswertung und CSV historisierter Zuschlagszeiten
- `/api/v1/time-tracking/periods/lock` – geprüfte, endgültige Abrechnungsperiodensperre

Statuswerte: `active`, `inactive`, `lead`. Kundennummern werden serverseitig eindeutig als `K-<UUID>` erzeugt. Kunden werden in dieser Ausbaustufe nicht physisch gelöscht.

Dienstplanung und Zeiterfassung speichern Zeitpunkte als UTC und verwenden die konfigurierte IANA-Zeitzone (standardmäßig `Europe/Berlin`) für lokale Tagesfilter und Anzeige. Arbeitszeitbuchungen können mehrere Arbeits- und Pausenabschnitte umfassen. Freigegebene Zeitwerte bleiben unverändert; beantragte Korrekturen werden als neue Version mit Grund und erneuter Freigabe historisiert. Ein Mitarbeiter kann nicht gleichzeitig mehrere offene Zeitbuchungen haben; parallele Prüfungen werden pro Mitarbeiter transaktionsgebunden serialisiert. Rollenrechte und Objektzuweisungen werden serverseitig kontrolliert. CSV-Zeilen werden gegen Tabellenformelinjektion abgesichert. Überstunden in der Auswertung bezeichnen ausschließlich positive Abweichungen zur geplanten Arbeitszeit, keine tarifliche oder gesetzliche Berechnung. Diese Funktionen sind keine automatische arbeitsrechtliche Konformitätsgarantie.

Zuschlagsregeln unterstützen Nacht, Samstag, Sonntag, Feiertag und betriebliche Zeitfenster mit Gültigkeit, Werttyp, Priorität und ausdrücklich gesetztem Kombinationsmodus. Feiertage folgen dem konfigurierten Bundesland. Versionierte Berechnungen speichern nur tatsächliche zuschlagsfähige Arbeitszeit und Regel-/Kalender-Snapshots; Periodensperren verhindern nachträgliche Zeitänderungen und Neuberechnungen. Geldbeträge sind bewusst nicht implementiert: Lohnbasis, Prozentbasis, Festzuschlagseinheit und Rundung sind nicht fachlich bestätigt. Die Anwendung ist kein Payroll-System und nicht produktions- oder rechtsfreigegeben.

## Datenbankserver konfigurieren

Das Backend liest `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` aus der Umgebung. Compose setzt `POSTGRES_HOST=db` für den enthaltenen PostgreSQL-Dienst. Für einen externen PostgreSQL-Server können diese Werte in der `.env` auf dessen Verbindungsdaten gesetzt werden. `CORS_ORIGINS` steuert die erlaubte Browser-Origin. Der Datenbankport wird absichtlich nicht öffentlich freigegeben. Sitzungen verwenden zufällige opaque Cookies; der Datenbankeintrag speichert nur den Token-Hash. Schreibzugriffe erfordern einen CSRF-Header. Passwort-Hashes werden mit Argon2id erzeugt.

Bei direktem Backend-Start außerhalb von Docker: Python 3.12+, `cd backend`, `pip install '.[test]'`, die PostgreSQL-Variablen setzen, für lokale HTTP-Entwicklung `SESSION_COOKIE_SECURE=false` einstellen, `alembic upgrade head` und danach `uvicorn app.main:app --reload`. `POSTGRES_PASSWORD` sollte nicht in Quellcode oder Versionsverwaltung abgelegt werden.

## Tests

```sh
cd backend
pip install '.[test]'
pytest
```

Die lokalen API-Tests verwenden standardmäßig eine isolierte SQLite-Testdatenbank. Die GitHub-CI wendet alle Alembic-Migrationen zusätzlich auf PostgreSQL 17 an und führt die Backendtests gegen diese Datenbank aus; der produktive Betrieb verwendet PostgreSQL.

## Projektstatus und Sicherheit

Die Bestandsaufnahme und offenen Module sind in [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md), [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) und der [priorisierten Implementierungs-Roadmap](docs/IMPLEMENTATION_ROADMAP.md) dokumentiert. Weitere technische Informationen: [Architektur](docs/ARCHITECTURE.md), [Datenbank](docs/DATABASE.md), [API](docs/API.md), [Sicherheitsstatus](docs/SECURITY.md), [Sicherheitsprüfung](docs/SECURITY_REVIEW.md), [Installation](docs/INSTALLATION.md), [Deployment](docs/DEPLOYMENT.md), [Backup/Restore](docs/BACKUP_RESTORE.md), [Benutzeranleitung](docs/USER_GUIDE.md), [Changelog](docs/CHANGELOG.md) und [Roadmap](docs/ROADMAP.md).

Die Objektverwaltung umfasst Backend, API und Frontend mit Suche, Filtern, Details, Anschriften, Ansprechpartnern, Archivierung, Historie, Zuweisungen und getrennt geschützten Sicherheitsdaten. Objektzugriff wird serverseitig anhand globaler Rechte oder einer Objektzuweisung geprüft. Personalakten, Qualifikationen, Abwesenheiten, getrennte sensible Daten und versionierte Qualifikationsdateien sind in `main`. PR #18 ist mit Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033` gemergt; Backend/PostgreSQL, Frontend einschließlich Vitest und Docker CI waren grün, Issue #6 ist geschlossen. Issue #2 bleibt bis zur formalen Abnahme seiner Akzeptanzkriterien offen. Dienstplanung ist mit PR #19 in `main`; Zeiterfassung wurde mit PR #22 gemergt. PR #23 ergänzt OWKS mit objektspezifischen QR-/NFC-Kontrollpunkten und -Routen, einem append-only Wachbuch, geschützten Anhängen und Offline-Synchronisierung mit sichtbaren Konflikten. QR-Codes werden erzeugt und können per Kamera gescannt werden; Web-NFC liest/beschreibt NDEF-Textkennungen nur bei sicherem Kontext und kompatiblem Browser/Gerät. Der eingebaute PostgreSQL-Minutenmonitor prüft versäumte Kontrollen auch über mehrere API-Instanzen. Statische QR-/NFC-Treffer bleiben `presence_verified=false`, gelten nicht als erledigter Besuch und beweisen keine physische Anwesenheit; dynamische kryptografische Tags oder Geräte-/Standortnachweise sind nicht integriert. Issue #3 bleibt bis zur fachlichen Abnahme offen. MFA, Passwortzurücksetzung, Vertragsverwaltung und Rechnungswesen sind noch nicht implementiert. Das Audit-Protokoll ist über die Anwendung schreibgeschützt, aber noch nicht durch getrennte Datenbankrollen gegen privilegierte Datenbankänderungen abgesichert.

Die Anwendung ist ein Entwicklungsstand, keine Produktionsfreigabe. Für Zeiterfassung und die gestapelte Ergänzung mit Zuschlagszeitnachweisen sind Backend-, Ruff-, Frontend- und Offline-Migrationsprüfungen dokumentiert; Live-PostgreSQL- und Docker-Prüfungen sind separat in CI auszuführen. Vor öffentlichem Betrieb müssen unter anderem HTTPS/Reverse-Proxy, `SESSION_COOKIE_SECURE=true`, zentralisiertes Rate-Limiting, Backup/Wiederherstellung, Sicherheitsprüfung und Datenschutz-/Aufbewahrungsvorgaben eingerichtet sein. Ruhezeitregeln sind keine automatische Rechtsprüfung; gesetzliche Konformität wird nicht behauptet und erfordert unabhängige fachliche Prüfung.
