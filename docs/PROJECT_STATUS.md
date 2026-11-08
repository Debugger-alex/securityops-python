# SecurityOps – Projektstatus

Arbeitsstand: Feature-Branch `feature/object-management-completion`, ausgehend vom aktuellen `main`. PRs #11, #12, #14 und #15 sind laut Aufgabenstand in `main` gemergt. Issue #2 bleibt offen; für diesen Branch wurde noch kein Pull Request erstellt. Dieser Status beschreibt den Quellcode und lokale Prüfungen, nicht eine Produktionsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenanlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung und Historie.
- Objektverwaltung mit Kunden-FK, Suche/Filter/Sortierung/Paginierung, Detailbearbeitung, Anschrift, mehreren einzeln bearbeitbaren Ansprechpartnern, Archivierung/Reaktivierung und Historie.
- Objektmitarbeiter-Zuweisungen auf aktive Mitarbeiter-/Objektleitungskonten; serverseitiger Objektzugriff anhand globaler Rechte oder Zuweisung. Sensible Sicherheits-/Zutrittsdaten liegen in eigener Tabelle und eigenen API-Endpunkten mit separaten Berechtigungen.
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
| Kunden | Kernverwaltung vorhanden: Backend, Migration 0004, API, Filter-/Detail-/Kontakt-/Archivierungsoberflächen und Regressionstests. Vertrags- und Dokumentenzuordnung fehlen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | Backend/API/UI und Migrationen 0005–0007 implementiert. Objektzuweisungen sind Benutzerkonten, keine Personalakten. Lokale Tests/Ruff/Frontendbuild bestanden; echter PostgreSQL-Lauf, Docker-Builds, CI und Review für diesen Branch stehen aus. Issue #2 daher noch nicht abschließen. |
| Personal/Qualifikationen | Nicht implementiert ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
| Dienstplanung | Nicht implementiert ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | Nicht implementiert ([#4](https://github.com/Xonni-star/securityops-python/issues/4)). |
| OWKS/Kontrollgänge | Nicht implementiert ([#3](https://github.com/Xonni-star/securityops-python/issues/3)). |
| Dokumente/Verträge | Nicht implementiert ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| Produktion | Nicht freigegeben: Vite-Devserver statt statischer Frontend-Auslieferung, kein TLS-Reverse-Proxy und kein gemeinsamer Rate-Limit-Speicher ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |
| Benutzerverwaltung | MFA, Passwortzurücksetzung, aktive Sitzungsübersicht und Rechteeditor fehlen. |
| Audit | App-seitig lesbar; Objektänderungen protokollieren Aktion und geänderte Feldnamen ohne sensible Werte. Nicht gegen direkte Änderungen privilegierter Datenbankrollen abgesichert. |

## Dokumentation und Prüfstatus

- Vollständige Bestandsaufnahme: [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md).
- Prioritäten und Abhängigkeiten: [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
- Sicherheitsbefunde und offene Maßnahmen: [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md).
- Architektur, Betrieb und weitere Unterlagen sind im [`README.md`](../README.md) verlinkt.
- Objektverwaltungs-Branch: **16 Backendtests bestanden**, Ruff-Lint und Formatprüfung bestanden, Frontend-TypeScript-Prüfung und Produktionsbuild bestanden. Alembic-Upgrade bis Revision 0007 sowie Downgrade 0007→0006 wurden als PostgreSQL-SQL offline gerendert.
- Kein lokaler PostgreSQL- oder Docker-Dienst verfügbar; echte PostgreSQL-Integration und Docker-Builds für diesen Branch sind nicht belegt. Vorherige CI-Ergebnisse für andere Branches ersetzen diese Prüfung nicht.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Objektverwaltungs-Branch gegen PostgreSQL und Docker in CI prüfen, Review abschließen und danach die Akzeptanzkriterien von [Issue #2](https://github.com/Xonni-star/securityops-python/issues/2) bewerten.
2. Erst nach vollständigem Abschluss Personal/Qualifikationen [#5](https://github.com/Xonni-star/securityops-python/issues/5), Dienstplanung [#10](https://github.com/Xonni-star/securityops-python/issues/10), Zeiterfassung [#4](https://github.com/Xonni-star/securityops-python/issues/4) und weitere Module gemäß Roadmap beginnen.
3. Produktionshärtung, Monitoring und Backup/Restore aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) bleiben separat offen.

## Repository-Arbeitsstand

- Der aktuelle Arbeitsbranch ist `feature/object-management-completion`; Änderungen sind noch nicht gepusht und ein PR wurde noch nicht erstellt.
- Issue #2 bleibt offen bis PostgreSQL-/CI-Prüfung, Review und Abnahme der Akzeptanzkriterien.
- Keine abgeschlossene Fachfunktion wurde absichtlich entfernt; Anpassungen an Kontaktänderungen erhalten nicht übermittelte Kontakte.
