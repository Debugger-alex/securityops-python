# Repository-Audit

## Umfang und Stand

Direkte Bestandsaufnahme des `main`-Quellcodes `5f3530463e9531c1f825f43ae4c6a6e60b9974e3` am 08.11.2026: Routerregistrierung, Models, 13 Alembic-Revisionen, Tests, Compose, Containerdefinitionen und Workflow. GitHub-PR-/Issue-/CI-Status stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Offene PR-Änderungen sind nicht als Teil des Audits von `main` gezählt.

## Module und Implementierungsstand

| Bereich | Ist-Stand auf `main` | Grenzen / Abnahme |
|---|---|---|
| Identity / Rollen | Passwortlogin, Argon2id, Session-/CSRF-Schutz, Benutzer-/Rollenzuordnung, Berechtigungen und Audit-Lese-API | Kein MFA, Passwortreset, Rolleneditor oder Sitzungsübersicht. Audit nicht gegen DB-Owner geschützt. |
| Kunden | Kundenstammdaten, Suche/Filter, Anschriften, Kontakte, Archivierung, Historie, Website und Vertragsstatus-Feld | Vertragsverwaltung und Vertragsdateien fehlen. Issue #6 geschlossen; #2 ist nicht für Kunden, sondern Objekte offen. |
| Objekte | Kundenbeziehung, Suche/Filter, Adressen/Kontakte, Archivierung/Historie, Zuweisungen und getrennte Sicherheitsdaten | Implementiert; Issue #2 bleibt bis formaler Abnahme offen. |
| Personal | Personalakten, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, sensible Daten, Zuweisungsverlauf und versionierte Qualifikationsnachweise | Dateien liegen als `BYTEA` in PostgreSQL. Kein Malware-Scan, keine Anwendungsebene-Verschlüsselung. Issue #5 geschlossen. |
| Dienstplanung | Schichten, Ansichten/Filter, Veröffentlichung/Absage, IANA-Zeitzone, Ruhezeit, Qualifikation-/Abwesenheits-/Scope-/Konfliktprüfung und Verlauf | Individuelle Wiederholungsverfügbarkeit nicht modelliert; kein Nachweis rechtlicher Konformität. Issue #10 offen bis Abnahme. |
| Zeiterfassung | Arbeits-/Pausensegmente, Korrekturen/Freigaben, Historie, Berichte/CSV, Zuschlagszeitregeln, Snapshots und Periodensperren | Keine Geldbetrags-/Payrollberechnung; fehlende fachliche Rechenkonvention. Issue #4 offen bis Abnahme. |
| OWKS | Nicht in `main` | PR #23 offen, Migration 0014 nicht gemergt. |
| Dokumente/Verträge | Nur Qualifikationsdateien; allgemeine Dokumenten-/Vertragsverwaltung fehlt | PR #24 offen auf #23 gestapelt, Migration 0015 nicht gemergt. |
| Rechnungswesen | Nicht implementiert | Issue #7 offen; fachliche Vertrags-/Leistungs-/Steuerregeln fehlen. |
| Frontend | React/TypeScript/Vite, gemeinsame App, Kunden-/Objekt-/Personal-/Planungs-/Zeitansichten | Vite-Devserver in Compose; Produktionsauslieferung und UI-Komponententests jenseits der App-Testdatei fehlen. |
| Datenbank | PostgreSQL, 13 lineare Alembic-Migrationen bis `0013_time_tracking_surcharges` | PostgreSQL CI vorhanden; kein Schema-Deployprozess für Produktion oder Restore-Nachweis. |
| Tests / CI | Backendtests und Ruff; PostgreSQL 17-Migration/Testjob; Frontend-Build/Tests; zwei Docker-Image-Builds | Keine E2E-, Last-, SCA/SAST-, externe Penetrations-, Malware- oder Restoretests. CI ist kein Produktivitätsnachweis. |
| Betrieb | Compose für lokale Entwicklung, Loopback-Ports, DB-Healthcheck und explizites Passwort | Kein TLS/Reverse Proxy, kein Monitoring, verteiltes Rate-Limit, Secret Store, automatische Backups oder produktive Vite-Alternative. |

## Dateien, auf denen die Bestandsaufnahme beruht

- Router und Berechtigungen: `backend/app/main.py`, `api.py`, `identity_api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `auth.py`.
- Datenbank: `backend/app/models.py` und `backend/migrations/versions/0001_customers.py` bis `0013_time_tracking_surcharges.py`.
- Tests: `backend/tests/test_config.py`, `test_customer_management.py`, `test_customers.py`, `test_identity.py`, `test_objects.py`, `test_personnel.py`, `test_scheduling.py`, `test_time_tracking.py`, `frontend/src/App.test.tsx`.
- Betrieb/CI: `.github/workflows/ci.yml`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example`, Package-/Python-Manifeste.
- Die vollständige Tabellen-/FK-/Constraint-/Indexreferenz ist in [`DATABASE.md`](DATABASE.md), alle registrierten API-Routen in [`API.md`](API.md).

## Offene Sicherheits- und Qualitätsrisiken

Verteiltes Rate-Limiting, sichere externe Bereitstellung, MFA/Account Recovery, Upload-Malwareprüfung, Schutz vor privilegierter Auditänderung, Datenschutz-/Aufbewahrungsregeln, verschlüsselte Backup-/Restorepraxis, Monitoring, Incident-Abläufe und unabhängige Sicherheits-/Rechtsprüfung sind nicht nachgewiesen. Die priorisierte Behandlung steht in [`SECURITY.md`](SECURITY.md) und [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
