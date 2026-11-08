# Repository-Audit

## Umfang und Stand

Direkte Bestandsaufnahme des `main`-Quellcodes `edad05f3b3029370a62b51a6508962f1dd156592` am 08.11.2026: Routerregistrierung, Models, 18 Alembic-Revisionen, Tests, Compose, Containerdefinitionen und Workflow. Das generierte OpenAPI-Schema enthält 160 `/api/v1`-Operationen; das Modellinventar enthält 60 Tabellen. GitHub-PR-/Issue-/CI-Status stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). PRs #23, #24, #26, #27, #28, #29 und #31 sind gemergt und Teil des untersuchten Stands; nur PR #25 ist offen.

## Module und Implementierungsstand

| Bereich | Ist-Stand auf `main` | Grenzen / Abnahme |
|---|---|---|
| Identity / Rollen | Argon2id-Login, optionales TOTP-MFA, verschlüsselte Secrets, gehashte einmalige Recovery-Codes, Session-/CSRF-Schutz, Sitzungsliste/-widerruf und administrativer Passwortreset; Rollen, Berechtigungen und Audit-Lese-API | Kein E-Mail-Selbstreset/Versanddienst; Audit nicht gegen privilegierte DB-Änderungen geschützt. MFA ist optional und nicht unabhängig sicherheitsabgenommen. |
| Kunden | Kundenstammdaten, Suche/Filter, Anschriften, Kontakte, Archivierung, Historie, Website und Vertragsstatus-Feld | Vertragsverwaltung/Dokumente sind separate Funktionen; Issue #6 geschlossen. |
| Objekte | Kundenbeziehung, Suche/Filter, Adressen/Kontakte, Archivierung/Historie, Zuweisungen und getrennte Sicherheitsdaten | Implementiert; Issue #2 geschlossen. |
| Personal | Personalakten, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, sensible Daten, Zuweisungsverlauf und versionierte Qualifikationsnachweise | Dateien liegen als `BYTEA` in PostgreSQL. Kein Malware-Scan, keine Anwendungsebene-Verschlüsselung. Issue #5 geschlossen. |
| Dienstplanung | Schichten, Ansichten/Filter, Veröffentlichung/Absage, IANA-Zeitzone, Ruhezeit, Qualifikation-/Abwesenheits-/Scope-/Konfliktprüfung, wöchentliche Verfügbarkeiten, Dienstwünsche/Sperrzeiten, Vertretungen und Verlauf | In `main` implementiert; Issue #10 bleibt für fachliche Abnahme offen. Kein Nachweis rechtlicher Konformität. |
| Zeiterfassung | Arbeits-/Pausensegmente, Korrekturen/Freigaben, Historie, Berichte/CSV, Zuschlagszeitregeln, Snapshots und Periodensperren | Keine Geldbetrags-/Payrollberechnung; fehlende fachliche Rechenkonvention. Issue #4 geschlossen. |
| OWKS | Kontrollpunkte/-routen, Ereignisse/Status/Korrekturen/Anhänge, Offline-Sync, Challenge-basierte Scans und Hintergrundmonitoring | Issue #3 geschlossen. Statische QR/NFC-Kennung ist kein physischer Präsenznachweis; kein Malware-Scan für Uploads. |
| Dokumente/Verträge | Geschützte Dokumentmetadaten und Versionen, privater Dateispeicher, Freigaben/Lesebestätigungen, Verträge und manuell generierbare Erinnerungen | Migration 0015 in `main`; Issue #8 ist laut frischer GitHub-Abfrage weiterhin offen. Kein Malware-Scan und keine automatische Erinnerungszustellung. |
| Rechnungswesen | Preise, Rechnungen/Positionen und Snapshots, Freigabe/Archivierung, Folge-Korrekturbelege, Zahlungen/Mahnstatus, PDFs und versionierter JSON-Export sind in `main` (PR #27, Migration `0017_billing`) | Issue #7 bleibt offen zur fachlichen Abnahme. `Decimal`/`NUMERIC` ist implementiert, aber Steuer-/Buchhaltungsregeln sind nicht unabhängig geprüft. |
| Frontend | React/TypeScript/Vite, gemeinsame App, Kunden-/Objekt-/Personal-/Planungs-/Zeitansichten | Vite-Devserver in Compose; Produktionsauslieferung und UI-Komponententests jenseits der App-Testdatei fehlen. |
| Datenbank | PostgreSQL, 18 lineare Alembic-Migrationen bis `0018_identity_security`, 60 SQLAlchemy-Tabellen | Separater Release-Migrationsdienst und PostgreSQL-CI vorhanden; keine produktive Migration oder Restoreübung unabhängig nachgewiesen. |
| Tests / CI | Backendtests und Ruff; PostgreSQL 17-Migration/Testjob; Frontend-Build/Tests; Docker-Image-Builds, Security-Analyse und isolierter verschlüsselter Restoretest | Keine E2E-, Last-, externe Penetrations-, Malware- oder produktive Restoretests. CI ist kein Produktivitätsnachweis. |
| Betrieb | Produktions-Compose mit Nginx-Frontend, nicht privilegiertem API-Prozess, Redis-Rate-Limit und separatem Migrationdienst; Entwicklungs-Override mit Vite | TLS-Reverse-Proxy, Secret-/Rollenbetrieb, Monitoring, Incident-Prozess und regelmäßige Restoreübung müssen für die Umgebung umgesetzt und belegt werden. |

## Dateien, auf denen die Bestandsaufnahme beruht

- Router und Berechtigungen: `backend/app/main.py`, `api.py`, `identity_api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `owks_api.py`, `documents_contracts_api.py`, `billing_api.py`, `auth.py`; OpenAPI enthält 160 API-Operationen plus zwei Health-Operationen.
- Datenbank: `backend/app/models.py` und `backend/migrations/versions/0001_customers.py` bis `0018_identity_security.py`.
- Tests: Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung, Zeiterfassung, OWKS und Dokumente/Verträge; Frontendtests sowie CI-PostgreSQL-Prüfungen.
- Betrieb/CI: `.github/workflows/ci.yml`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example`, Package-/Python-Manifeste.
- PR #26 ist gemergt: Mitarbeiter-Verfügbarkeitsfenster, Dienstwünsche/Sperrzeiten und Schichtvertretungen sowie Migration `0016_scheduling_availability` sind Teil von `main`; Issue #10 bleibt offen zur fachlichen Abnahme.
- PR #28 ist gemergt: Produktions-Compose, Redis-Rate-Limit, separater Alembic-Release-Schritt, verschlüsselte Backups/Restore und SCA/SAST-CI sind implementiert. CI- und Restoreprüfungen sind kein Produktionsnachweis; Issue #9 bleibt offen.
- PR #29 ist gemergt und beschränkt Mitarbeiter-Objektzuweisungen auf den autorisierten Objektzugriff. PR #27 ist gemergt; Migration `0017_billing` folgt auf `0016_scheduling_availability`. PR #31 ist gemergt und ergänzt mit `0018_identity_security` TOTP-MFA, Recovery-Codes, Sitzungsverwaltung und administrativen Passwortreset.
- Die vollständige Tabellen-/FK-/Constraint-/Indexreferenz ist in [`DATABASE.md`](DATABASE.md), alle registrierten API-Routen in [`API.md`](API.md).

## Offene Sicherheits- und Qualitätsrisiken

Redis-gestütztes Rate-Limiting und Backup-/Restorewerkzeuge sind im Repository implementiert; produktiver Betrieb und regelmäßige Wiederherstellungsübungen sind nicht nachgewiesen. Offen bleiben unter anderem E-Mail-basierte Selbstwiederherstellung, Upload-Malwareprüfung, Schutz vor privilegierter Auditänderung, Datenschutz-/Aufbewahrungsregeln, Monitoring, Incident-Abläufe und unabhängige Sicherheits-/Rechts-/Steuerprüfung. Die priorisierte Behandlung steht in [`SECURITY.md`](SECURITY.md) und [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
