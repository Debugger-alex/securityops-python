# Änderungsprotokoll

## 2026-11-08 – Sicherheitsbasis und Bestandsaudit

- Bestandsaufnahme der vorhandenen Kunden-, Identity-, RBAC-, Audit-, Frontend- und Compose-Funktionen dokumentiert.
- Gefährliche Vergabe der Administratorrolle über allgemeines `users.manage` erkannt und auf zusätzliche Berechtigung `users.manage_admin` begrenzt.
- Standardrollen um Verwaltung, Buchhaltung und Auditor erweitert; zusätzliche fachliche Berechtigungen angelegt.
- Compose-Secure-Cookie-Fallback auf `true` gesetzt.
- Dokumentation zu Architektur, Datenbank, API, Sicherheit, Installation, Deployment, Backup/Restore, Benutzerführung und Roadmap ergänzt.
- Backend-Tests, Frontend-Build und Migration-SQL-Generierung werden nach Ausführung im PR vermerkt; kein Docker-/PostgreSQL-Produktionslauf behauptet.

## 2026-11-08 – Phase 1: CI und Konfigurationshärtung

- GitHub Actions prüft Backendtests auf SQLite und PostgreSQL, wendet Migrationen auf einem kurzlebigen PostgreSQL-17-Dienst an und baut Frontend- sowie Docker-Images.
- Das Datenbankpasswort hat keinen impliziten Anwendung-Standardwert mehr; Regressionstest und expliziter Testwert ergänzt.
- Vollständige priorisierte Implementierungs-Roadmap und statische Sicherheitsprüfung hinzugefügt.
- Lokale Prüfung: 9 Backend-Tests, Frontend-TypeScript-/Produktionsbuild und Offline-Migration erfolgreich. Kein Docker-/PostgreSQL-Dienst lokal verfügbar. Erster CI-Lauf bestätigte Migrationen und Image-Builds, deckte einen Konflikt der PostgreSQL-Test-Fixture mit migrierten Rollen auf; Fixture korrigiert, Wiederholung ausstehend.
