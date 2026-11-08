# SecurityOps – Projektstatus

Stand: 2026-11-08. Aktuelle Arbeitsgrundlage ist der Feature-Branch `feature/phase1-security-audit` und der offene [Pull Request #11](https://github.com/Xonni-star/securityops-python/pull/11). Dieser Status beschreibt implementierten Quellcode, nicht eine Produktionsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenanlage, Suche, Detailabruf, Teiländerung und datenbankbasierte Kundenkennzahlen.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Prüfung und Login-Rate-Limit.
- Serverseitige RBAC-Prüfungen, Benutzeranlage/-deaktivierung und Schutz des letzten aktiven Administrators.
- Audit-Ereignisse für An-/Abmeldung, fehlgeschlagene Anmeldungen, Passwortwechsel, Benutzer- und Kundenänderungen.
- Additive Rollen-/Rechtemigration `0003_role_permissions`; Administratorrollenvergabe erfordert `users.manage_admin`.
- Compose-Standard für Secure-Cookie ist `true`; `.env.example` setzt für lokale HTTP-Entwicklung ausdrücklich `false`.
- Das Datenbankpasswort hat keinen Standardwert in der Anwendung mehr: `POSTGRES_PASSWORD` muss gesetzt sein.
- GitHub Actions führt Backendtests auf SQLite und einer temporären PostgreSQL-Testdatenbank aus, wendet Migrationen an und baut Frontend sowie Docker-Images; erster gehosteter Workflow-Lauf ist nach dem Push zu prüfen.

## Teilweise implementiert oder offen

| Bereich | Status |
|---|---|
| Kunden | Teilweise: Ansprechpartner, Rechtsform/Anschriften, Archivierung, Historie, Vertrags- und Dokumentenzuordnung fehlen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | Nicht implementiert; Kundenbeziehung und objektbezogene Rechte fehlen ([#2](https://github.com/Xonni-star/securityops-python/issues/2)). |
| Personal/Qualifikationen | Nicht implementiert ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
| Dienstplanung | Nicht implementiert ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | Nicht implementiert ([#4](https://github.com/Xonni-star/securityops-python/issues/4)). |
| OWKS/Kontrollgänge | Nicht implementiert ([#3](https://github.com/Xonni-star/securityops-python/issues/3)). |
| Dokumente/Verträge | Nicht implementiert ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| Produktion | Nicht freigegeben: Vite-Devserver statt statischer Frontend-Auslieferung, kein TLS-Reverse-Proxy und kein gemeinsamer Rate-Limit-Speicher ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |
| Benutzerverwaltung | MFA, Passwortzurücksetzung, aktive Sitzungsübersicht und Rechteeditor fehlen. |
| Audit | App-seitig lesbar, aber nicht gegen direkte Änderungen privilegierter Datenbankrollen abgesichert. |

## Dokumentation und Prüfstatus

- Vollständige Bestandsaufnahme: [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md).
- Prioritäten und Abhängigkeiten: [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
- Sicherheitsbefunde und offene Maßnahmen: [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md).
- Architektur, Betrieb und weitere Unterlagen sind im [`README.md`](../README.md) verlinkt.
- Lokal: **9 Backend-Tests bestanden** (SQLite); Frontend-TypeScript-Prüfung und Produktionsbuild erfolgreich; Alembic 0001–0003 erfolgreich offline als PostgreSQL-SQL generiert.
- Kein lokaler Docker- oder PostgreSQL-Dienst verfügbar. Deshalb ist die reale Migration auf PostgreSQL hier nicht lokal bestätigt; der neue CI-Workflow soll diese Prüfung gehostet ausführen.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. PR #11 pushen und den ersten GitHub-Actions-Lauf einschließlich realer PostgreSQL-Migration auswerten.
2. Den Produktions- und Datenbank-Härtungsumfang aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) priorisiert schließen.
3. Danach Kundenverwaltung [#6](https://github.com/Xonni-star/securityops-python/issues/6), Objekte [#2](https://github.com/Xonni-star/securityops-python/issues/2), Personal [#5](https://github.com/Xonni-star/securityops-python/issues/5) und Einsatzmodule gemäß Roadmap angehen.

## Repository-Arbeitsstand

- Aktueller PR: [#11 – Phase 1: Rechtehärtung und Projektdokumentation](https://github.com/Xonni-star/securityops-python/pull/11).
- In diesem Update: CI mit kurzlebigem PostgreSQL (Migration und API-Tests), Frontend-/Docker-Builds, verpflichtendes Datenbank-Secret, zugehöriger Regressionstest, Implementierungs-Roadmap und statische Sicherheitsprüfung.
- Issues #2 bis #10 bestehen bereits; in diesem Update wurden keine neuen Issues angelegt.
