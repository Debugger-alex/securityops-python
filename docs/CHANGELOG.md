# Änderungsprotokoll

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
