# Änderungsprotokoll

## 2026-11-08 – Sicherheitsbasis und Bestandsaudit

- Bestandsaufnahme der vorhandenen Kunden-, Identity-, RBAC-, Audit-, Frontend- und Compose-Funktionen dokumentiert.
- Gefährliche Vergabe der Administratorrolle über allgemeines `users.manage` erkannt und auf zusätzliche Berechtigung `users.manage_admin` begrenzt.
- Standardrollen um Verwaltung, Buchhaltung und Auditor erweitert; zusätzliche fachliche Berechtigungen angelegt.
- Compose-Secure-Cookie-Fallback auf `true` gesetzt.
- Dokumentation zu Architektur, Datenbank, API, Sicherheit, Installation, Deployment, Backup/Restore, Benutzerführung und Roadmap ergänzt.
- Backend-Tests, Frontend-Build und Migration-SQL-Generierung werden nach Ausführung im PR vermerkt; kein Docker-/PostgreSQL-Produktionslauf behauptet.
