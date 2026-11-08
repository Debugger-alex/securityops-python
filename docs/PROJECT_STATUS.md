# SecurityOps – Projektstatus

Arbeitsstand: Feature-Branch `feature/personnel-management`, aufgebaut auf dem aktuellen `main` nach dem Merge von PR #16. Die Personalverwaltung wird für Issue #5 ergänzt; Änderungen sind noch nicht gepusht und ein Pull Request wurde noch nicht erstellt. Dieser Status beschreibt den Quellcode und lokale Prüfungen, nicht eine Produktionsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenanlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung und Historie.
- Objektverwaltung mit Kunden-FK, Suche/Filter/Sortierung/Paginierung, Detailbearbeitung, Anschrift, mehreren einzeln bearbeitbaren Ansprechpartnern, Archivierung/Reaktivierung und Historie.
- Objektmitarbeiter-Zuweisungen auf aktive Mitarbeiter-/Objektleitungskonten; serverseitiger Objektzugriff anhand globaler Rechte oder Zuweisung. Sensible Sicherheits-/Zutrittsdaten liegen in eigener Tabelle und eigenen API-Endpunkten mit separaten Berechtigungen.
- Personalakten mit Personalnummer, Stammdaten, optionalem Benutzerkonto, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, Archivierung/Reaktivierung und Historie. Anschrift, Notfallkontakt und interne Notizen sind getrennt und zusätzlich berechtigt.
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
| Objekte | Backend/API/UI und Migrationen 0005–0007 in `main` implementiert; PR #16 und dessen CI sind abgeschlossen. Objektzuweisungen bleiben technisch an Benutzerkonten gebunden; Personalakten werden über dasselbe Zuweisungsmodell und eine zusätzliche Personalhistorie integriert. Issue #2 bleibt bis zur fachlichen Bestätigung der Akzeptanzkriterien offen. |
| Personal/Qualifikationen | Migration 0008 und 0009, Personalakten, Abwesenheiten, sensible Daten, Historie, Zuweisungen und versionierte Qualifikationsdateien sind implementiert. 21 Backendtests, Ruff und Frontend-TypeScript/Produktionsbuild bestehen lokal; Offline-SQL wurde für Migration 0009 erzeugt. PostgreSQL-/Docker-CI muss die neuesten Negativtests noch prüfen. PR #17 ist zur Review bereit; Issue #5 bleibt bis zur vollständigen Abnahme offen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
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
- Personalverwaltungs-Branch: **21 lokale Backendtests bestanden**; Ruff-Lint/Format und Frontend-TypeScript/Produktionsbuild bestanden. Alembic-Upgrade bis 0009 und Downgrade 0009→0008 wurden offline gerendert. Die vorherigen GitHub-CI-Ergebnisse auf PR #17 waren erfolgreich; der jüngste Commit mit zusätzlichen Negativtests wartet auf CI.
- Lokales PostgreSQL und Docker sind in der Entwicklungsumgebung nicht verfügbar; die tatsächliche PostgreSQL- und Docker-Prüfung erfolgte in CI.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Aktuelle Personalverwaltungsänderungen gegen PostgreSQL und Docker in CI prüfen und Review sowie Akzeptanzkriterien von Issue #5 abschließen.
2. Danach Dienstplanung [#10](https://github.com/Xonni-star/securityops-python/issues/10), Zeiterfassung [#4](https://github.com/Xonni-star/securityops-python/issues/4) und weitere Module gemäß Roadmap angehen.
3. Produktionshärtung, Monitoring und Backup/Restore aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) bleiben separat offen.

## Repository-Arbeitsstand

- Der aktuelle Arbeitsbranch ist `feature/personnel-management`; PR #17 ist als Draft offen. Die hier dokumentierten Folgeänderungen müssen noch gepusht und auf dem PR geprüft werden.
- Issue #5 bleibt offen, bis sämtliche Akzeptanzkriterien, CI-/PostgreSQL-Prüfungen und Review abgeschlossen sind.
- Die bereits in `main` gemergte Objektverwaltung wurde nicht neu entwickelt; Personalakten greifen über ihr verknüpftes Benutzerkonto auf die bestehende Zuweisungstabelle zu.
