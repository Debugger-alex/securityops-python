# SecurityOps – Projektstatus

Stand: 2026-11-08. Die Phase-1-Grundlage ist der Feature-Branch `feature/phase1-security-audit` mit offenem [Pull Request #11](https://github.com/Xonni-star/securityops-python/pull/11). Die Kundenverwaltung wird isoliert auf `feature/customer-management` darauf aufgebaut; PR #11 wird dadurch nicht verändert. Dieser Status beschreibt implementierten Quellcode, nicht eine Produktionsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenanlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung und Historie.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Prüfung und Login-Rate-Limit.
- Serverseitige RBAC-Prüfungen, Benutzeranlage/-deaktivierung und Schutz des letzten aktiven Administrators.
- Audit-Ereignisse für An-/Abmeldung, fehlgeschlagene Anmeldungen, Passwortwechsel, Benutzer- und Kundenänderungen.
- Additive Rollen-/Rechtemigration `0003_role_permissions`; Administratorrollenvergabe erfordert `users.manage_admin`.
- Compose-Standard für Secure-Cookie ist `true`; `.env.example` setzt für lokale HTTP-Entwicklung ausdrücklich `false`.
- Das Datenbankpasswort hat keinen Standardwert in der Anwendung mehr: `POSTGRES_PASSWORD` muss gesetzt sein.
- GitHub Actions führt Python-Lint/Format, Backendtests auf SQLite und einer temporären PostgreSQL-Testdatenbank, Migrationen, Frontendbuild und Docker-Image-Builds aus. Der erste Lauf zeigte einen Test-Fixture-Konflikt; nach Korrektur waren alle Jobs erfolgreich.

## Teilweise implementiert oder offen

| Bereich | Status |
|---|---|
| Kunden | Teilweise umgesetzt: Backend, Migration 0004, API, Filter-/Detail-/Kontakt-/Archivierungsoberflächen und Regressionstests vorhanden. Vertrags- und Dokumentenzuordnung sowie umfassende UX-Prüfung fehlen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
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
- Kundenverwaltungs-Branch lokal: **11 Backend-Tests bestanden** (SQLite); Ruff-Lint und Formatprüfung, Frontend-TypeScript-/Produktionsbuild sowie Offline-PostgreSQL-SQL-Generierung einschließlich Migration 0004 erfolgreich.
- Kein lokaler Docker- oder PostgreSQL-Dienst verfügbar. Im korrigierten gehosteten Lauf waren PostgreSQL-Migration und API-Tests sowie Frontend- und beide Docker-Builds erfolgreich.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Phase-2-Frontendbuild und gehostete PostgreSQL-CI einschließlich Migration 0004 ausführen.
2. Kundenverwaltung [#6](https://github.com/Xonni-star/securityops-python/issues/6) fachlich vervollständigen und den Kunden-Branch als gestapelten PR auf Phase 1 prüfen.
3. Den Produktions- und Datenbank-Härtungsumfang aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) schließen und danach Objekte [#2](https://github.com/Xonni-star/securityops-python/issues/2), Personal [#5](https://github.com/Xonni-star/securityops-python/issues/5) und Einsatzmodule gemäß Roadmap angehen.

## Repository-Arbeitsstand

- Aktueller PR: [#11 – Phase 1: Rechtehärtung und Projektdokumentation](https://github.com/Xonni-star/securityops-python/pull/11).
- Kundenverwaltungsänderungen auf `feature/customer-management` sind lokal und noch nicht committet oder gepusht; PR #11 bleibt offen und unverändert.
- Issues #2 bis #10 bestehen bereits; in diesem Update wurden keine neuen Issues angelegt.
