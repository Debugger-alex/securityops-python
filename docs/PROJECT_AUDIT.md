# Repository-Audit

## Umfang und Stand

Direkte Bestandsaufnahme des `main`-Quellcodes `6c7679a646d30da0504d8990fefeefa351a29bfe` am 08.11.2026: Routerregistrierung, Models, 15 Alembic-Revisionen, Tests, Compose, Containerdefinitionen und Workflow. GitHub-PR-/Issue-/CI-Status stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). PR #23/#24 sind gemergt und Teil des untersuchten Stands; offene PRs #25–#27 sind nicht Teil von `main`.

## Module und Implementierungsstand

| Bereich | Ist-Stand auf `main` | Grenzen / Abnahme |
|---|---|---|
| Identity / Rollen | Passwortlogin, Argon2id, Session-/CSRF-Schutz, Benutzer-/Rollenzuordnung, Berechtigungen und Audit-Lese-API | Kein MFA, Passwortreset, Rolleneditor oder Sitzungsübersicht. Audit nicht gegen DB-Owner geschützt. |
| Kunden | Kundenstammdaten, Suche/Filter, Anschriften, Kontakte, Archivierung, Historie, Website und Vertragsstatus-Feld | Vertragsverwaltung/Dokumente sind separate Funktionen; Issue #6 geschlossen. |
| Objekte | Kundenbeziehung, Suche/Filter, Adressen/Kontakte, Archivierung/Historie, Zuweisungen und getrennte Sicherheitsdaten | Implementiert; Issue #2 geschlossen. |
| Personal | Personalakten, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, sensible Daten, Zuweisungsverlauf und versionierte Qualifikationsnachweise | Dateien liegen als `BYTEA` in PostgreSQL. Kein Malware-Scan, keine Anwendungsebene-Verschlüsselung. Issue #5 geschlossen. |
| Dienstplanung | Schichten, Ansichten/Filter, Veröffentlichung/Absage, IANA-Zeitzone, Ruhezeit, Qualifikation-/Abwesenheits-/Scope-/Konfliktprüfung und Verlauf | Individuelle Wiederholungsverfügbarkeit nicht modelliert; kein Nachweis rechtlicher Konformität. Issue #10 offen. |
| Zeiterfassung | Arbeits-/Pausensegmente, Korrekturen/Freigaben, Historie, Berichte/CSV, Zuschlagszeitregeln, Snapshots und Periodensperren | Keine Geldbetrags-/Payrollberechnung; fehlende fachliche Rechenkonvention. Issue #4 geschlossen. |
| OWKS | Kontrollpunkte/-routen, Ereignisse/Status/Korrekturen/Anhänge, Offline-Sync, Challenge-basierte Scans und Hintergrundmonitoring | Issue #3 geschlossen. Statische QR/NFC-Kennung ist kein physischer Präsenznachweis; kein Malware-Scan für Uploads. |
| Dokumente/Verträge | Geschützte Dokumentmetadaten und Versionen, privater Dateispeicher, Freigaben/Lesebestätigungen, Verträge und manuell generierbare Erinnerungen | Migration 0015 in `main`; Issue #8 ist laut frischer GitHub-Abfrage weiterhin offen. Kein Malware-Scan und keine automatische Erinnerungszustellung. |
| Rechnungswesen | Nicht in `main` implementiert | Offener PR #27 schlägt Preisstammdaten, Rechnungsentwürfe und Snapshots, Freigabe, Folge-/Stornobelege, Zahlungen/Mahnstatus, PDF und versionierten JSON-Export vor; aktuelle CI am gestapelten Head ist grün. Keine fachliche/steuerliche Abnahme. Migration `0017_billing` ist auf PR #26s `0016_scheduling_availability` gestapelt; beide nicht als Main-Schema erfasst. |
| Frontend | React/TypeScript/Vite, gemeinsame App, Kunden-/Objekt-/Personal-/Planungs-/Zeitansichten | Vite-Devserver in Compose; Produktionsauslieferung und UI-Komponententests jenseits der App-Testdatei fehlen. |
| Datenbank | PostgreSQL, 15 lineare Alembic-Migrationen bis `0015_documents_contracts`, 52 SQLAlchemy-Tabellen | PostgreSQL CI vorhanden; kein Schema-Deployprozess für Produktion oder Restore-Nachweis. |
| Tests / CI | Backendtests und Ruff; PostgreSQL 17-Migration/Testjob; Frontend-Build/Tests; zwei Docker-Image-Builds | Keine E2E-, Last-, SCA/SAST-, externe Penetrations-, Malware- oder Restoretests. CI ist kein Produktivitätsnachweis. |
| Betrieb | Compose für lokale Entwicklung, Loopback-Ports, DB-Healthcheck und explizites Passwort | Kein TLS/Reverse Proxy, kein Monitoring, verteiltes Rate-Limit, Secret Store, automatische Backups oder produktive Vite-Alternative. |

## Dateien, auf denen die Bestandsaufnahme beruht

- Router und Berechtigungen: `backend/app/main.py`, `api.py`, `identity_api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `owks_api.py`, `documents_contracts_api.py`, `auth.py`.
- Datenbank: `backend/app/models.py` und `backend/migrations/versions/0001_customers.py` bis `0015_documents_contracts.py`.
- Tests: Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung, Zeiterfassung, OWKS und Dokumente/Verträge; Frontendtests sowie CI-PostgreSQL-Prüfungen.
- Betrieb/CI: `.github/workflows/ci.yml`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example`, Package-/Python-Manifeste.
- PR #26 (gegen `main`) schlägt Mitarbeiter-Verfügbarkeitsfenster, Dienstwünsche/Sperrzeiten und Schichtvertretungen vor; seine aktuelle CI ist grün. PR #27 baut darauf auf und ergänzt `0017_billing` nach `0016_scheduling_availability`. Die gestapelte Reihenfolge ist linear; #27 muss mit seiner Basisabhängigkeit integriert werden oder vor unabhängiger Übernahme neu basieren und migrationsseitig angepasst werden. Beide bleiben außerhalb des Main-Inventars.
- Die vollständige Tabellen-/FK-/Constraint-/Indexreferenz ist in [`DATABASE.md`](DATABASE.md), alle registrierten API-Routen in [`API.md`](API.md).

## Offene Sicherheits- und Qualitätsrisiken

Verteiltes Rate-Limiting, sichere externe Bereitstellung, MFA/Account Recovery, Upload-Malwareprüfung, Schutz vor privilegierter Auditänderung, Datenschutz-/Aufbewahrungsregeln, verschlüsselte Backup-/Restorepraxis, Monitoring, Incident-Abläufe und unabhängige Sicherheits-/Rechtsprüfung sind nicht nachgewiesen. Die priorisierte Behandlung steht in [`SECURITY.md`](SECURITY.md) und [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
