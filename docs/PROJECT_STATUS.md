# SecurityOps – Projektstatus

**Geprüft:** 09.11.2026 · **`main`:** `3deebd16e368733f9595cd39f7e38b6354c1a88d`

Diese Momentaufnahme trennt gemergten Quellcode, offene PRs, CI und fachliche Abnahme. PR-Inhalt ist kein Bestandteil von `main`; grüne CI beweist weder fachliche Abnahme noch Datenschutz-, Rechts- oder Produktionsreife.

## Tatsächlich in `main`

`main` enthält die lineare Alembic-Kette `0001_customers` bis `0016_scheduling_availability` (Revision-Head `0016_scheduling_availability`), 54 SQLAlchemy-Tabellen und 140 API-Operationen unter `/api/v1`:

- FastAPI-Monolith mit SQLAlchemy/PostgreSQL, Alembic, React/TypeScript/Vite, getrenntem Produktions-/Entwicklungs-Compose und GitHub Actions.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Schutz, Login-Limit und rollenbasierter serverseitiger Autorisierung. Benutzer, Rollen, Rechte und Anwendungs-Audit-Lesezugriff sind vorhanden.
- Kunden mit Anschriften, Ansprechpartnern, Status, Vertragsstatus-Metadatum, Suche, Archivierung und Änderungshistorie. Vertragsmanagement und Dokumentakten sind als separate, unten aufgeführte Module vorhanden.
- Objekte mit Kunden-FK, Ansprechpartnern/Adresse, Historie, Zuweisungen und separater Berechtigungsgrenze für Sicherheits-/Zutrittsdaten. Mitarbeiter-Objektzuweisungen berücksichtigen serverseitig den Objektzugriff.
- Personalakten mit Qualifikationen, Abwesenheiten, sensiblen Personalangaben, Zuweisungsverlauf und versionierten Qualifikationsdateien in PostgreSQL (`BYTEA`).
- Dienstplanung mit Schichten, UTC-Speicherung, konfigurierbarer IANA-Zeitzone/Ruhezeit, wöchentlichen Verfügbarkeitsfenstern, Dienstwünschen/Sperrzeiten, nachvollziehbaren Schichtvertretungen, Konfliktprüfungen, Verlauf und PostgreSQL-Exclusion-Constraint.
- Zeiterfassung mit Arbeits-/Pausensegmenten, Korrekturanträgen, Freigaben, Berichten/CSV, Zuschlagszeit-Regeln und versionierten Zeitnachweisen sowie endgültigen Abrechnungsperiodensperren. Es werden keine Zuschlags-Geldbeträge berechnet; Lohnbasis, Prozentbasis, Festwert-Einheit und Rundung sind fachlich nicht festgelegt.
- OWKS mit objektspezifischen Kontrollpunkten und Routen, Wachbuchereignissen, Offline-Synchronisation, Challenges für Scans, Statushistorie, Korrekturverweisen, Anhängen und Minutentakt-Monitoring. Statische QR-/NFC-Kennungen belegen keine physische Anwesenheit; Anhänge werden nicht auf Malware gescannt.
- Geschützte Dokumenten- und Vertragsverwaltung mit Versionen, Freigaben, Lesebestätigungen, Historien und manuell generierbaren Erinnerungen. Dokumentdateien werden in einem konfigurierten privaten Dateispeicher abgelegt und über autorisierte API-Endpunkte ausgeliefert; Malware-Scan, E-Mail-/Push-Zustellung und automatische tägliche Erinnerungsplanung sind nicht enthalten.
- Produktions-Compose enthält statische Nginx-Auslieferung, nicht privilegierten API-Prozess, Redis-Rate-Limit-Speicher und separaten Release-Migrationsdienst. Verschlüsselte Backup-/Restore-Skripte, PostgreSQL-Restore-CI und Security-Analyse sind vorhanden; keine davon weist einen produktiven Rollout oder eine betriebliche Abnahme nach.
- Es gibt keine eigenständige Frontend-Router-/Feature-Paketarchitektur; die React-Oberfläche ist eine Vite-Anwendung. Das Dashboard liefert derzeit Kundenkennzahlen, keine vollständigen operativen Kennzahlen.

## Offene Pull Requests – nicht Bestandteil von `main`

| PR | Status / CI (frisch geprüft) | Basis | Inhalt, Abhängigkeit und Abgrenzung |
|---|---|---|---|
| [#25](https://github.com/Xonni-star/securityops-python/pull/25) | Offen; Checks gelten jeweils nur für den aktuellen GitHub-Head | `main` | Diese Dokumentationssynchronisierung. Ausschließlich Markdown und `AGENTS.md`; kein Merge, keine Issue-Änderung. |
| [#27](https://github.com/Xonni-star/securityops-python/pull/27) | Offen; Head `a6a33851ab1ac8cdf06a55222ecf528227a5fa76`; Backend/PostgreSQL/Migrationen, Frontend, Docker, Restore und Security-Analyse erfolgreich | `main` | Rechnungswesen-Vorschlag: konfigurierbare Preise/Steuerwerte, Rechnungsentwürfe und unveränderliche Snapshots, Freigabe/Archivierung, Folge-/Stornobelege, Zahlungen/Mahnstatus, geschützte PDFs und idempotenter Export `securityops-accounting-v1`. Migration `0017_billing` folgt auf Main-Revision `0016_scheduling_availability`; nicht mehr auf einem offenen PR gestapelt. Issue #7 bleibt offen; CI-Grün ist weder fachliche noch steuerliche/buchhalterische Abnahme. |

PR #23, #24, #26, #28 und #29 sind gemergt und in `main` enthalten. Die Main-Migrationskette endet bei `0016_scheduling_availability`. PR #27 zielt nach dem Merge von #26 direkt auf `main`; seine vorgeschlagene `0017_billing` folgt auf `0016`. Es besteht aktuell keine offene PR-Stapelabhängigkeit.

## Vollständiger PR- und Issue-Index

| PR | Status am Prüftag | Titel |
|---|---|---|
| [#25](https://github.com/Xonni-star/securityops-python/pull/25) | Offen | Dokumentation mit aktuellem main- und PR-Stand synchronisieren |
| [#27](https://github.com/Xonni-star/securityops-python/pull/27) | Offen, direkt gegen `main` | Rechnungswesen, Freigaben und Buchhaltungsexport |
| [#29](https://github.com/Xonni-star/securityops-python/pull/29) | Gemergt | Beschränke Mitarbeiter-Objektzuweisungen auf Objektzugriff |
| [#28](https://github.com/Xonni-star/securityops-python/pull/28) | Gemergt | Produktionshärtung und PostgreSQL-Integrationsprüfungen |
| [#26](https://github.com/Xonni-star/securityops-python/pull/26) | Gemergt | Add missing scheduling availability and replacements |
| [#24](https://github.com/Xonni-star/securityops-python/pull/24) | Gemergt | Geschützte Dokumenten- und Vertragsverwaltung |
| [#23](https://github.com/Xonni-star/securityops-python/pull/23) | Gemergt | OWKS-Wachbuch und QR/NFC-Kontrollgänge integrieren |
| [#22](https://github.com/Xonni-star/securityops-python/pull/22) | Gemergt | Complete time tracking surcharges and approval controls |
| [#21](https://github.com/Xonni-star/securityops-python/pull/21) | Geschlossen, nicht gemergt | Complete time tracking surcharges and period locking |
| [#20](https://github.com/Xonni-star/securityops-python/pull/20) | Gemergt | Implement complete time tracking module |
| [#19](https://github.com/Xonni-star/securityops-python/pull/19) | Gemergt | Dienstplanung mit Besetzungs- und Konfliktprüfung |
| [#18](https://github.com/Xonni-star/securityops-python/pull/18) | Gemergt | Kundenverwaltung in Issue #6 vervollständigen |
| [#17](https://github.com/Xonni-star/securityops-python/pull/17) | Gemergt | Personalverwaltung und Qualifikationen ergänzen |
| [#16](https://github.com/Xonni-star/securityops-python/pull/16) | Gemergt | Objektverwaltung vervollständigen und Zugriff absichern |
| [#15](https://github.com/Xonni-star/securityops-python/pull/15) | Gemergt | Behebt Backend-CI-Lintfehler für Objektverwaltung |
| [#14](https://github.com/Xonni-star/securityops-python/pull/14) | Gemergt | Add object management backend and tests |
| [#13](https://github.com/Xonni-star/securityops-python/pull/13) | Gemergt | Objektverwaltung ergänzen |
| [#12](https://github.com/Xonni-star/securityops-python/pull/12) | Gemergt | Phase 2: Complete customer management |
| [#11](https://github.com/Xonni-star/securityops-python/pull/11) | Gemergt | Phase 1: CI, Rechtehärtung und Projektdokumentation |
| [#1](https://github.com/Xonni-star/securityops-python/pull/1) | Gemergt | Add authentication, RBAC, and audit foundation |

### Issues

| Issue | Status am Prüftag | Thema |
|---|---|---|
| [#10](https://github.com/Xonni-star/securityops-python/issues/10) | Offen | Dienstplanung mit Besetzungs- und Konfliktprüfung implementieren |
| [#9](https://github.com/Xonni-star/securityops-python/issues/9) | Offen | Produktionshärtung und PostgreSQL-Integrationsprüfungen einrichten |
| [#8](https://github.com/Xonni-star/securityops-python/issues/8) | Offen (frische GitHub-Abfrage) | Geschützte Dokumenten- und Vertragsverwaltung entwickeln |
| [#7](https://github.com/Xonni-star/securityops-python/issues/7) | Offen | Rechnungswesen, Freigaben und Buchhaltungsexport implementieren |
| [#6](https://github.com/Xonni-star/securityops-python/issues/6) | Geschlossen | Kundenverwaltung um Ansprechpartner, Anschriften und Archivierung ergänzen |
| [#5](https://github.com/Xonni-star/securityops-python/issues/5) | Geschlossen | Personalverwaltung und Qualifikationsnachweise entwickeln |
| [#4](https://github.com/Xonni-star/securityops-python/issues/4) | Geschlossen | Zeiterfassung mit Korrekturfreigaben und Änderungsverlauf ergänzen |
| [#3](https://github.com/Xonni-star/securityops-python/issues/3) | Geschlossen | OWKS-Wachbuch und QR/NFC-Kontrollgänge integrieren |
| [#2](https://github.com/Xonni-star/securityops-python/issues/2) | Geschlossen | Objektverwaltung mit Kundenbeziehung und Objektzugriffsrechten implementieren |

## PR- und Issue-Verlauf

- PRs #26, #28 und #29 wurden nach #23/#24 ebenfalls gemergt. Offen sind PR #25 (Dokumentation) und #27 (Rechnungswesen); #27 basiert direkt auf dem aktualisierten `main`.
- PR #21 ist geschlossen, nicht gemergt; die enthaltenen Änderungen sind laut Verlauf in #22/`main` enthalten.
- Issues #2, #3, #4, #5 und #6 sind geschlossen; #7, #8, #9 und #10 sind laut frischer GitHub-Abfrage offen. Issue #8 wird trotz des gemergten PR #24 als OPEN geführt und bleibt bis zur Bestätigung offen. Keine Issue wurde durch diese Dokumentationsänderung verändert.
- Issue #9 bleibt trotz des gemergten PR #28 offen. Der Merge enthält Betriebswerkzeuge und CI-Prüfungen, aber keinen Nachweis eines realen produktiven Rollouts, Restore-Drills, Monitorings oder Incident-Prozesses.
- Issue #10 bleibt trotz des gemergten PR #26 offen; eine fachliche Abnahme der Dienstplanergänzungen ist nicht belegt. Issue #8 bleibt nach aktueller Abfrage offen und wird nicht durch diese Dokumentationsänderung geschlossen.
- PR #27s zuletzt geprüfter Head `a6a3385` hatte erfolgreiche Backend/PostgreSQL/Migrations-, Frontend-, Docker-, Restore- und Security-Checks. Checkresultate gelten nur für den bezeichneten Head und sind keine fachliche oder steuerliche Abnahme.

## Tests, Betrieb und Abnahme

Im `main`-Stand vorhanden sind Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung, Zeiterfassung, OWKS sowie Dokumente/Verträge und Frontendtests. Die GitHub-CI prüft Python-Lint/Format, Migrationen und Tests auf temporärem PostgreSQL 17, Frontend-Build/-Tests, Backend-/Frontend-Docker-Images, Security-Analyse sowie einen isolierten synthetischen Backup-/Restorelauf. Nicht nachgewiesen sind E2E-/Lastprüfungen, externe Penetrationstests, produktive Restoreübungen oder unabhängige Datenschutz-/Rechts-/Steuerprüfungen.

Das Produktions-Compose enthält Nginx für statische Dateien, Redis-gestütztes Rate-Limiting, separate Release-Migrationen und verschlüsselte Backup-/Restore-Skripte. TLS, vertrauenswürdige Proxykonfiguration, Secrets, Rollen, Backupaufbewahrung und Restoreübungen bleiben für die konkrete Betriebsumgebung einzurichten und nachzuweisen. Nicht umgesetzt bzw. nicht nachgewiesen sind unter anderem MFA, Passwortzurücksetzung, Sitzungsübersicht, Upload-Malware-Scan, Anwendungsebene-Verschlüsselung, produktives Monitoring und Incident-Prozess. Auditdaten sind nicht gegen direkte Änderungen privilegierter Datenbankrollen geschützt.

**Gesamturteil:** ein fortgeschrittener Entwicklungsstand mit CI-geprüften Funktionsbereichen, keine Produktionsfreigabe. Arbeitszeit-/Dienstplanungskonfiguration ist keine Rechtskonformitätsgarantie; Geldbeträge werden nicht berechnet. Datenschutz, Aufbewahrung und Betrieb müssen für eine reale Umgebung eigenständig geprüft und umgesetzt werden.

## Verweise

- [Architektur](ARCHITECTURE.md) · [Datenbank/Migrationen](DATABASE.md) · [API](API.md)
- [Sicherheit](SECURITY.md) · [Deployment](DEPLOYMENT.md) · [Backup/Restore](BACKUP_RESTORE.md)
- [Audit](PROJECT_AUDIT.md) · [Sicherheitsprüfung](SECURITY_REVIEW.md) · [Roadmap](IMPLEMENTATION_ROADMAP.md)
