# Änderungsprotokoll

## 2026-11-08 – Dienstplanung (in Bearbeitung)

- Alembic-Migration 0011 ergänzt Schichten, Planungseinstellungen, Verlauf und einen PostgreSQL-Exclusion-Constraint gegen zeitliche Doppelbelegung; API-Konfliktprüfungen werden pro Mitarbeiter per Transaktions-Advisory-Lock serialisiert.
- Geschützte Scheduling-API und React-Oberfläche mit Tages-/Wochen-/Monatsansichten, Filtern, Entwurf/Veröffentlichung/Absage, Änderungsverlauf und konfigurierbarer IANA-Zeitzone/Ruhezeit ergänzt.
- Backendtests für Zeitumrechnung einschließlich doppelter Ortszeit, Konflikte, Qualifikation, Abwesenheiten, Objektzuweisung, Berechtigungen und parallele PostgreSQL-Schreibzugriffe ergänzt. Lokal: 27 Backendtests bestanden, PostgreSQL-Parallelitätstest mangels PostgreSQL übersprungen; Ruff, Frontend-Build/Vitest und Offline-Migrationsupgrade/-downgrade erfolgreich. Live-PostgreSQL-Prüfung und GitHub-CI ausstehend.
- PR #18 ist in `main` (Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033`), CI Backend/PostgreSQL, Frontend einschließlich Vitest und Docker grün; Issue #6 geschlossen. Issue #2 bleibt bis zur formalen Abnahme offen; Issue #10 wird bearbeitet.

## Kundenverwaltung erweitert

- Website und validierter Vertragsstatus in Kundendaten, Suche und Formularen ergänzt; Migration 0010 (`0010_customer_fields`) übernimmt Bestandskunden ohne Datenverlust.
- Kunden-Detailansicht zeigt vorhandene, serverseitig nach Objektberechtigung gefilterte Objektzuordnungen.
- API-Validierungs-, Berechtigungs- und Frontendtests für Vertragsstatus, Website und Fehlerfälle ergänzt.

## Objektverwaltung – Feature-Branch

- React-Objektverwaltung mit Kundenbeziehung, Suche, Filtern, Sortierung, Paginierung und Detailansicht ergänzt.
- Objektanschriften und Ansprechpartner einschließlich Einzelbearbeitung, Archivierung/Reaktivierung und Änderungshistorie integriert.
- Objektbezogene Mitarbeiterzuweisungen und serverseitige Scope-Prüfungen ergänzt.
- Sicherheits-/Zutrittsdaten in eigene Tabelle und API-Berechtigungen getrennt; Migration 0007 übernimmt vorhandene Werte.
- Lokale Prüfung: 16 Backendtests, Ruff-Lint/Format und Frontend-TypeScript-/Produktionsbuild bestanden. PostgreSQL-Offline-SQL bis 0007 sowie Downgrade 0007→0006 gerendert; echte PostgreSQL-Integration und Docker-Builds dieses Branches ausstehend.

## 2026-11-08 – Sicherheitsbasis und Bestandsaudit

- Bestandsaufnahme der vorhandenen Kunden-, Identity-, RBAC-, Audit-, Frontend- und Compose-Funktionen dokumentiert.
- Gefährliche Vergabe der Administratorrolle über allgemeines `users.manage` erkannt und auf zusätzliche Berechtigung `users.manage_admin` begrenzt.
- Standardrollen um Verwaltung, Buchhaltung und Auditor erweitert; zusätzliche fachliche Berechtigungen angelegt.
- Compose-Secure-Cookie-Fallback auf `true` gesetzt.
- Dokumentation zu Architektur, Datenbank, API, Sicherheit, Installation, Deployment, Backup/Restore, Benutzerführung und Roadmap ergänzt.
- Backend-Tests, Frontend-Build und Migration-SQL-Generierung werden nach Ausführung im PR vermerkt; kein Docker-/PostgreSQL-Produktionslauf behauptet.

## 2026-11-08 – Phase 1: CI und Konfigurationshärtung

- GitHub Actions prüft Backendtests auf SQLite und PostgreSQL, wendet Migrationen auf einem kurzlebigen PostgreSQL-17-Dienst an und baut Frontend- sowie Docker-Images.
- Python-Linting und Formatprüfung mit Ruff sind in CI eingebunden.
- Das Datenbankpasswort hat keinen impliziten Anwendung-Standardwert mehr; Regressionstest und expliziter Testwert ergänzt.
- Vollständige priorisierte Implementierungs-Roadmap und statische Sicherheitsprüfung hinzugefügt.
- Lokale Prüfung: 9 Backend-Tests, Frontend-TypeScript-/Produktionsbuild und Offline-Migration erfolgreich. Kein Docker-/PostgreSQL-Dienst lokal verfügbar. Der gehostete CI-Lauf bestand nach Behebung eines Test-Fixture-Konflikts mit migrierten Rollen einschließlich PostgreSQL-Migration/API-Tests sowie Frontend- und Docker-Builds.
