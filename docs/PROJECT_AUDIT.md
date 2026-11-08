# Repository-Audit

## Umfang und Stand

Direkte Bestandsaufnahme des `main`-Quellcodes `3deebd16e368733f9595cd39f7e38b6354c1a88d` am 09.11.2026: Routerregistrierung, Models, 16 Alembic-Revisionen, Tests, Compose, Containerdefinitionen und Workflow. Das generierte OpenAPI-Schema enthält 140 `/api/v1`-Operationen; das Modellinventar enthält 54 Tabellen. GitHub-PR-/Issue-/CI-Status stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). PRs #23, #24, #26, #28 und #29 sind gemergt und Teil des untersuchten Stands; offene PRs #25 und #27 sind nicht Teil von `main`.

## Module und Implementierungsstand

| Bereich | Ist-Stand auf `main` | Grenzen / Abnahme |
|---|---|---|
| Identity / Rollen | Passwortlogin, Argon2id, Session-/CSRF-Schutz, Benutzer-/Rollenzuordnung, Berechtigungen und Audit-Lese-API | Kein MFA, Passwortreset, Rolleneditor oder Sitzungsübersicht. Audit nicht gegen DB-Owner geschützt. |
| Kunden | Kundenstammdaten, Suche/Filter, Anschriften, Kontakte, Archivierung, Historie, Website und Vertragsstatus-Feld | Vertragsverwaltung/Dokumente sind separate Funktionen; Issue #6 geschlossen. |
| Objekte | Kundenbeziehung, Suche/Filter, Adressen/Kontakte, Archivierung/Historie, Zuweisungen und getrennte Sicherheitsdaten | Implementiert; Issue #2 geschlossen. |
| Personal | Personalakten, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, sensible Daten, Zuweisungsverlauf und versionierte Qualifikationsnachweise | Dateien liegen als `BYTEA` in PostgreSQL. Kein Malware-Scan, keine Anwendungsebene-Verschlüsselung. Issue #5 geschlossen. |
| Dienstplanung | Schichten, Ansichten/Filter, Veröffentlichung/Absage, IANA-Zeitzone, Ruhezeit, Qualifikation-/Abwesenheits-/Scope-/Konfliktprüfung, wöchentliche Verfügbarkeiten, Dienstwünsche/Sperrzeiten, Vertretungen und Verlauf | In `main` implementiert; Issue #10 bleibt für fachliche Abnahme offen. Kein Nachweis rechtlicher Konformität. |
| Zeiterfassung | Arbeits-/Pausensegmente, Korrekturen/Freigaben, Historie, Berichte/CSV, Zuschlagszeitregeln, Snapshots und Periodensperren | Keine Geldbetrags-/Payrollberechnung; fehlende fachliche Rechenkonvention. Issue #4 geschlossen. |
| OWKS | Kontrollpunkte/-routen, Ereignisse/Status/Korrekturen/Anhänge, Offline-Sync, Challenge-basierte Scans und Hintergrundmonitoring | Issue #3 geschlossen. Statische QR/NFC-Kennung ist kein physischer Präsenznachweis; kein Malware-Scan für Uploads. |
| Dokumente/Verträge | Geschützte Dokumentmetadaten und Versionen, privater Dateispeicher, Freigaben/Lesebestätigungen, Verträge und manuell generierbare Erinnerungen | Migration 0015 in `main`; Issue #8 ist laut frischer GitHub-Abfrage weiterhin offen. Kein Malware-Scan und keine automatische Erinnerungszustellung. |
| Rechnungswesen | Nicht in `main` implementiert | Offener PR #27 schlägt Preisstammdaten, Rechnungsentwürfe und Snapshots, Freigabe, Folge-/Stornobelege, Zahlungen/Mahnstatus, PDF und versionierten JSON-Export vor; zuletzt geprüfte CI auf dem direkten `main`-Head ist grün. Keine fachliche/steuerliche Abnahme. Migration `0017_billing` folgt auf Main-Revision `0016_scheduling_availability`; #27 ist aktuell nicht auf einem offenen PR gestapelt. |
| Frontend | React/TypeScript/Vite, gemeinsame App, Kunden-/Objekt-/Personal-/Planungs-/Zeitansichten | Vite-Devserver in Compose; Produktionsauslieferung und UI-Komponententests jenseits der App-Testdatei fehlen. |
| Datenbank | PostgreSQL, 16 lineare Alembic-Migrationen bis `0016_scheduling_availability`, 54 SQLAlchemy-Tabellen | Separater Release-Migrationsdienst und PostgreSQL-CI vorhanden; keine produktive Migration oder Restoreübung unabhängig nachgewiesen. |
| Tests / CI | Backendtests und Ruff; PostgreSQL 17-Migration/Testjob; Frontend-Build/Tests; Docker-Image-Builds, Security-Analyse und isolierter verschlüsselter Restoretest | Keine E2E-, Last-, externe Penetrations-, Malware- oder produktive Restoretests. CI ist kein Produktivitätsnachweis. |
| Betrieb | Produktions-Compose mit Nginx-Frontend, nicht privilegiertem API-Prozess, Redis-Rate-Limit und separatem Migrationdienst; Entwicklungs-Override mit Vite | TLS-Reverse-Proxy, Secret-/Rollenbetrieb, Monitoring, Incident-Prozess und regelmäßige Restoreübung müssen für die Umgebung umgesetzt und belegt werden. |

## Dateien, auf denen die Bestandsaufnahme beruht

- Router und Berechtigungen: `backend/app/main.py`, `api.py`, `identity_api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `owks_api.py`, `documents_contracts_api.py`, `auth.py`; OpenAPI enthält 140 API-Operationen plus zwei Health-Operationen.
- Datenbank: `backend/app/models.py` und `backend/migrations/versions/0001_customers.py` bis `0016_scheduling_availability.py`.
- Tests: Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung, Zeiterfassung, OWKS und Dokumente/Verträge; Frontendtests sowie CI-PostgreSQL-Prüfungen.
- Betrieb/CI: `.github/workflows/ci.yml`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example`, Package-/Python-Manifeste.
- PR #26 ist gemergt: Mitarbeiter-Verfügbarkeitsfenster, Dienstwünsche/Sperrzeiten und Schichtvertretungen sowie Migration `0016_scheduling_availability` sind Teil von `main`; Issue #10 bleibt offen zur fachlichen Abnahme.
- PR #28 ist gemergt: Produktions-Compose, Redis-Rate-Limit, separater Alembic-Release-Schritt, verschlüsselte Backups/Restore und SCA/SAST-CI sind implementiert. CI- und Restoreprüfungen sind kein Produktionsnachweis; Issue #9 bleibt offen.
- PR #29 ist gemergt und beschränkt Mitarbeiter-Objektzuweisungen auf den autorisierten Objektzugriff. PR #27 bleibt offen und basiert aktuell direkt auf `main`; sein Vorschlag `0017_billing` folgt auf `0016_scheduling_availability`.
- Die vollständige Tabellen-/FK-/Constraint-/Indexreferenz ist in [`DATABASE.md`](DATABASE.md), alle registrierten API-Routen in [`API.md`](API.md).

## Offene Sicherheits- und Qualitätsrisiken

Redis-gestütztes Rate-Limiting und Backup-/Restorewerkzeuge sind im Repository implementiert; produktiver Betrieb und regelmäßige Wiederherstellungsübungen sind nicht nachgewiesen. Offen bleiben unter anderem MFA/Account Recovery, Upload-Malwareprüfung, Schutz vor privilegierter Auditänderung, Datenschutz-/Aufbewahrungsregeln, Monitoring, Incident-Abläufe und unabhängige Sicherheits-/Rechtsprüfung. Die priorisierte Behandlung steht in [`SECURITY.md`](SECURITY.md) und [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
