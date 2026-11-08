# SecurityOps – Projektstatus

**Geprüft:** 08.11.2026, 23:26 CET · **`main`:** `6c7679a646d30da0504d8990fefeefa351a29bfe`

Diese Momentaufnahme trennt gemergten Quellcode, offene PRs, CI und fachliche Abnahme. PR-Inhalt ist kein Bestandteil von `main`; grüne CI beweist weder fachliche Abnahme noch Datenschutz-, Rechts- oder Produktionsreife.

## Tatsächlich in `main`

`main` enthält die lineare Alembic-Kette `0001_customers` bis `0015_documents_contracts` (Revision-Head `0015_documents_contracts`), 52 SQLAlchemy-Tabellen und 136 API-Operationen unter `/api/v1`:

- FastAPI-Monolith mit SQLAlchemy/PostgreSQL, Alembic, React/TypeScript/Vite, Docker-Compose-Entwicklungsdiensten und GitHub Actions.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Schutz, Login-Limit und rollenbasierter serverseitiger Autorisierung. Benutzer, Rollen, Rechte und Anwendungs-Audit-Lesezugriff sind vorhanden.
- Kunden mit Anschriften, Ansprechpartnern, Status, Vertragsstatus-Metadatum, Suche, Archivierung und Änderungshistorie. Vertragsmanagement und Dokumentakten sind als separate, unten aufgeführte Module vorhanden.
- Objekte mit Kunden-FK, Ansprechpartnern/Adresse, Historie, Zuweisungen und separater Berechtigungsgrenze für Sicherheits-/Zutrittsdaten.
- Personalakten mit Qualifikationen, Abwesenheiten, sensiblen Personalangaben, Zuweisungsverlauf und versionierten Qualifikationsdateien in PostgreSQL (`BYTEA`).
- Dienstplanung mit Schichten, UTC-Speicherung, konfigurierbarer IANA-Zeitzone/Ruhezeit, Konfliktprüfungen, Verlauf und PostgreSQL-Exclusion-Constraint.
- Zeiterfassung mit Arbeits-/Pausensegmenten, Korrekturanträgen, Freigaben, Berichten/CSV, Zuschlagszeit-Regeln und versionierten Zeitnachweisen sowie endgültigen Abrechnungsperiodensperren. Es werden keine Zuschlags-Geldbeträge berechnet; Lohnbasis, Prozentbasis, Festwert-Einheit und Rundung sind fachlich nicht festgelegt.
- OWKS mit objektspezifischen Kontrollpunkten und Routen, Wachbuchereignissen, Offline-Synchronisation, Challenges für Scans, Statushistorie, Korrekturverweisen, Anhängen und Minutentakt-Monitoring. Statische QR-/NFC-Kennungen belegen keine physische Anwesenheit; Anhänge werden nicht auf Malware gescannt.
- Geschützte Dokumenten- und Vertragsverwaltung mit Versionen, Freigaben, Lesebestätigungen, Historien und manuell generierbaren Erinnerungen. Dokumentdateien werden in einem konfigurierten privaten Dateispeicher abgelegt und über autorisierte API-Endpunkte ausgeliefert; Malware-Scan, E-Mail-/Push-Zustellung und automatische tägliche Erinnerungsplanung sind nicht enthalten.
- Es gibt keine eigenständige Frontend-Router-/Feature-Paketarchitektur; die React-Oberfläche ist eine Vite-Anwendung. Das Dashboard liefert derzeit Kundenkennzahlen, keine vollständigen operativen Kennzahlen.

## Offene Pull Requests – nicht Bestandteil von `main`

| PR | Status / CI (frisch geprüft) | Basis | Inhalt, Abhängigkeit und Abgrenzung |
|---|---|---|---|
| [#25](https://github.com/Xonni-star/securityops-python/pull/25) | Offen; letzter hier dokumentierter Head `2422922b` mit Backend/PostgreSQL/Migrationen, Frontend und Docker erfolgreich; aktuelle head-spezifische CI am PR prüfen | `main` | Diese Dokumentationssynchronisierung. Nur Dokumentation und `AGENTS.md`; nicht gemergt. |
| [#26](https://github.com/Xonni-star/securityops-python/pull/26) | Offen; aktueller Head `7e15c71d539249a5888382ebb7e80ff46a7ebca2`; Backend/PostgreSQL/Migrationen, Frontend und Docker erfolgreich | `main` | Dienstplan-Verfügbarkeitsfenster, befristete Dienstwünsche/Sperrzeiten und nachvollziehbare Schichtvertretungen; Migration `0016_scheduling_availability`. Issue #10 bleibt offen. Ein vorheriger Head hatte einen fehlgeschlagenen Backend-Lauf (u. a. Deadlock/`401` in parallelen Scheduling-Tests); das ist nicht der Checkstatus des aktuellen Heads und kein Beleg fachlicher Abnahme. |
| [#27](https://github.com/Xonni-star/securityops-python/pull/27) | Offen; aktueller gestapelter Head `ee81a6cf2560c415bb942c713d685b9d3a566e8b`; Backend/PostgreSQL/Migrationen, Frontend und Docker erfolgreich | [#26](https://github.com/Xonni-star/securityops-python/pull/26) | Rechnungswesen-Vorschlag: konfigurierbare Preise/Steuerwerte, Rechnungsentwürfe und unveränderliche Snapshots, Freigabe/Archivierung, Folge-/Stornobelege, Zahlungen/Mahnstatus, geschützte PDFs und idempotenter Export `securityops-accounting-v1`. Migration `0017_billing` folgt auf #26s `0016_scheduling_availability`. Issue #7 bleibt offen; CI-Grün ist weder fachliche noch steuerliche/buchhalterische Abnahme. |
| [#28](https://github.com/Xonni-star/securityops-python/pull/28) | Offen; aktueller Head `57650bdb98e68a20f1a4ceb34064f0b8bd26665c`; Backend/PostgreSQL/Migrationen, Frontend, Docker, Restore und Security-Analyse erfolgreich | `main` | Produktionshärtungs-Vorschlag zu statischer Nginx-Auslieferung, nicht privilegiertem API-Container, Redis-Rate-Limit, getrenntem Alembic-Release-Schritt, verschlüsselten Backups/Restoretest sowie SCA/SAST. Keine Migration; Issue #9 bleibt offen. Ein vorheriger Head scheiterte beim Restore mit `tar: This does not look like a tar archive`; grünes CI ist keine Betriebs- oder Produktionsabnahme. |

PR #23 (OWKS) und #24 (Dokumente/Verträge) sind gemergt und in `main` enthalten. Ihre Migrationen `0014` und `0015` sind Teil des aktuellen Quell-/Schema-Inventars. PR #26 zielt direkt auf `main`, PR #27 ist aktuell auf #26 gestapelt. Ihre Vorschläge bilden die lineare Kette `0015_documents_contracts` → `0016_scheduling_availability` → `0017_billing`; #27 hängt daher von #26 ab. Falls #27 unabhängig von #26 integriert werden soll, müssen Basis und Migration ausdrücklich angepasst und anschließend in PostgreSQL geprüft werden. PR #28 zielt separat auf `main` und schlägt Betriebs-/Sicherheitsänderungen ohne Migration vor; diese Änderungen sind ebenfalls nicht Teil des unten dokumentierten `main`-Stands.

## Vollständiger PR- und Issue-Index

| PR | Status am Prüftag | Titel |
|---|---|---|
| [#25](https://github.com/Xonni-star/securityops-python/pull/25) | Offen | Dokumentation mit aktuellem main- und PR-Stand synchronisieren |
| [#28](https://github.com/Xonni-star/securityops-python/pull/28) | Offen | Produktionshärtung und PostgreSQL-Integrationsprüfungen |
| [#27](https://github.com/Xonni-star/securityops-python/pull/27) | Offen, gestapelt auf #26 | Rechnungswesen, Freigaben und Buchhaltungsexport |
| [#26](https://github.com/Xonni-star/securityops-python/pull/26) | Offen | Add missing scheduling availability and replacements |
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

- PR #23 und #24 sind gemergt. Offen sind #25 bis #28; #26 (Dienstplanung, Issue #10) und #28 (Produktionshärtung, Issue #9) zielen auf `main`, #27 (Rechnungswesen, Issue #7) ist auf #26 gestapelt.
- PR #21 ist geschlossen, nicht gemergt; die enthaltenen Änderungen sind laut Verlauf in #22/`main` enthalten.
- Issues #2, #3, #4, #5 und #6 sind geschlossen; #7, #8, #9 und #10 sind laut frischer GitHub-Abfrage offen. Issue #8 wird trotz des gemergten PR #24 als OPEN geführt und bleibt bis zur Bestätigung offen. Keine Issue wurde durch diese Dokumentationsänderung verändert.
- Issue #9 Produktionshärtung bleibt offen; PR #28 schlägt dazu Betriebs- und Sicherheitsänderungen sowie CI- und Restoreprüfungen vor, ist aber nicht gemergt und sein verschlüsselter Restore-Job schlägt fehl. Daraus wird keine Produktionsreife oder fachliche Abnahme abgeleitet.
- PR #25-Head `2422922b242b744da3825c87c2f590dfeb8a804c` hatte im Lauf 42527761972 erfolgreiche Backend/PostgreSQL/Migrations-, Frontend- und Docker-Checks. Dieser historische Nachweis gilt nur für diesen Head; aktuelle Checkstände stehen am jeweiligen PR. CI ist kein fachlicher Abnahmenachweis.

## Tests, Betrieb und Abnahme

Im `main`-Stand vorhanden sind Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung, Zeiterfassung, OWKS sowie Dokumente/Verträge und Frontendtests; die Main-GitHub-CI prüft zusätzlich Python-Lint/Format, Migrationen und Tests auf temporärem PostgreSQL 17, Frontend-Build/-Tests und Backend-/Frontend-Docker-Images. Für `main` sind keine E2E-, Last-, Restore-, externen Penetrations- oder unabhängigen Datenschutz-/Rechts-/Steuerprüfungen nachgewiesen. PR #28 schlägt Restore- und Sicherheitsprüfungen vor, ist aber offen und sein aktueller verschlüsselter Restore-Job fehlgeschlagen.

Compose bindet API und Vite an Loopback, stellt aber kein Produktionsdeployment bereit. Nicht umgesetzt bzw. nicht nachgewiesen sind unter anderem MFA, Passwortzurücksetzung, Sitzungsübersicht, zentral verteilter Rate-Limit-Speicher, TLS-Reverse-Proxy, produktive statische Frontendauslieferung, Malware-Scan, Anwendungsebene-Verschlüsselung, automatisierte verschlüsselte Backups mit Restore-Nachweis, Monitoring und Incident-Prozess. Auditdaten sind nicht gegen direkte Änderungen privilegierter Datenbankrollen geschützt.

**Gesamturteil:** ein fortgeschrittener Entwicklungsstand mit CI-geprüften Funktionsbereichen, keine Produktionsfreigabe. Arbeitszeit-/Dienstplanungskonfiguration ist keine Rechtskonformitätsgarantie; Geldbeträge werden nicht berechnet. Datenschutz, Aufbewahrung und Betrieb müssen für eine reale Umgebung eigenständig geprüft und umgesetzt werden.

## Verweise

- [Architektur](ARCHITECTURE.md) · [Datenbank/Migrationen](DATABASE.md) · [API](API.md)
- [Sicherheit](SECURITY.md) · [Deployment](DEPLOYMENT.md) · [Backup/Restore](BACKUP_RESTORE.md)
- [Audit](PROJECT_AUDIT.md) · [Sicherheitsprüfung](SECURITY_REVIEW.md) · [Roadmap](IMPLEMENTATION_ROADMAP.md)
