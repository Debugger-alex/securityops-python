# SecurityOps – Projektstatus

Arbeitsstand: Issue-#6-Branch `satan1800de-eng-issue-6-customer-completion`, aufgebaut auf `main` nach Merge von PR #17. PR #17 ist gemergt, seine PostgreSQL-/Backend-, Frontend- und Docker-CI war erfolgreich; Issue #5 ist geschlossen. Issue #6 wird in diesem Branch vervollständigt. Dieser Status beschreibt den Quellcode und lokale Prüfungen, nicht eine Produktionsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenkern in `main`: Anlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Rechtsform, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung und Historie. Der Issue-#6-Branch ergänzt Website, Vertragsstatus, Filter/Sortierung danach und erreichbare Objektzuordnungen. Dokumenten- und Vertragsverwaltung fehlen weiterhin.
- Objektverwaltung mit Kunden-FK, Suche/Filter/Sortierung/Paginierung, Detailbearbeitung, Anschrift, mehreren einzeln bearbeitbaren Ansprechpartnern, Archivierung/Reaktivierung und Historie.
- Objektmitarbeiter-Zuweisungen auf aktive Mitarbeiter-/Objektleitungskonten; serverseitiger Objektzugriff anhand globaler Rechte oder Zuweisung. Sensible Sicherheits-/Zutrittsdaten liegen in eigener Tabelle und eigenen API-Endpunkten mit separaten Berechtigungen.
- Personalakten mit Personalnummer, Stammdaten, optionalem Benutzerkonto, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, Archivierung/Reaktivierung und Historie. Anschrift, Notfallkontakt und interne Notizen sind getrennt und zusätzlich berechtigt.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Prüfung und Login-Rate-Limit.
- Serverseitige RBAC-Prüfungen, Benutzeranlage/-deaktivierung und Schutz des letzten aktiven Administrators.
- Audit-Ereignisse für An-/Abmeldung, fehlgeschlagene Anmeldungen, Passwortwechsel, Benutzer- und Kundenänderungen.
- Additive Rollen-/Rechtemigration `0003_role_permissions`; Administratorrollenvergabe erfordert `users.manage_admin`.
- Compose-Standard für Secure-Cookie ist `true`; `.env.example` setzt für lokale HTTP-Entwicklung ausdrücklich `false`.
- Das Datenbankpasswort hat keinen Standardwert in der Anwendung mehr: `POSTGRES_PASSWORD` muss gesetzt sein.
- GitHub Actions führt Python-Lint/Format, Backendtests auf SQLite und einer temporären PostgreSQL-Testdatenbank, Migrationen, Frontendtests/-build und Docker-Image-Builds aus. PR #17 bestand Backend/PostgreSQL, Frontend und Docker; der CI-Lauf für Issue #6 steht noch aus.

## Teilweise implementiert oder offen

| Bereich | Status |
|---|---|
| Kunden | Issue #6 wird in diesem Branch vervollständigt: additive Alembic-Migration 0010, Website, Vertragsstatus, Validierung, Suche/Filter/Sortierung sowie geschützte Objektzuordnungen. Vertrags- und Dokumentenmodule/Zuordnungen fehlen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | Backend/API/UI und Migrationen 0005–0007 in `main` implementiert; PR #16 und dessen CI sind abgeschlossen. Objektzuweisungen bleiben technisch an Benutzerkonten gebunden; Personalakten werden über dasselbe Zuweisungsmodell und eine zusätzliche Personalhistorie integriert. Issue #2 bleibt bis zur fachlichen Bestätigung der Akzeptanzkriterien offen. |
| Personal/Qualifikationen | Migrationen 0008–0009, Personalakten, Abwesenheiten, sensible Daten, Historie, Zuweisungen und versionierte Qualifikationsdateien sind in `main`. PR #17 wurde gemergt; PostgreSQL-/Backend-, Frontend- und Docker-CI war grün und Issue #5 ist geschlossen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
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
- PR #17: GitHub-CI für Backend/PostgreSQL, Frontend und Docker erfolgreich; Issue #5 geschlossen.
- Issue #6: 23 Backendtests, Ruff-Lint/Format, 2 Frontendtests und Frontend-TypeScript-/Produktionsbuild bestanden. Alembic-Upgrade bis 0010 und Downgrade 0010→0009 wurden für PostgreSQL offline gerendert. PostgreSQL-Integrations- und Docker-Build-CI stehen nach Erstellung des PRs aus.
- Lokales PostgreSQL und Docker sind in der Entwicklungsumgebung nicht verfügbar; die tatsächliche PostgreSQL- und Docker-Prüfung erfolgt in CI.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Issue #6 lokal validieren, PR erstellen und PostgreSQL-/Docker-CI prüfen.
2. Danach Dienstplanung [#10](https://github.com/Xonni-star/securityops-python/issues/10), Zeiterfassung [#4](https://github.com/Xonni-star/securityops-python/issues/4) und weitere Module gemäß Roadmap angehen.
3. Produktionshärtung, Monitoring und Backup/Restore aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) bleiben separat offen.

## Repository-Arbeitsstand

- Der aktuelle Arbeitsbranch ist `satan1800de-eng-issue-6-customer-completion`; er enthält nur die Folgearbeiten zu Issue #6 auf dem aktuellen `main`.
- PR #17 ist gemergt; Issue #5 ist geschlossen.
- Die bereits in `main` gemergte Objektverwaltung wurde nicht neu entwickelt; Personalakten greifen über ihr verknüpftes Benutzerkonto auf die bestehende Zuweisungstabelle zu.
