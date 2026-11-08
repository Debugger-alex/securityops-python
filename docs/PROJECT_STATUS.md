# SecurityOps – Projektstatus

**Geprüft:** 08.11.2026, 22:30 CET · **`main`:** `5f3530463e9531c1f825f43ae4c6a6e60b9974e3`

Diese Momentaufnahme trennt gemergten Quellcode, offene PRs, CI und fachliche Abnahme. PR-Inhalt ist kein Bestandteil von `main`; grüne CI beweist weder fachliche Abnahme noch Datenschutz-, Rechts- oder Produktionsreife.

## Tatsächlich in `main`

`main` enthält die fortlaufende Alembic-Kette `0001_customers` bis `0013_time_tracking_surcharges` (Revision-Head `0013_time_tracking_surcharges`):

- FastAPI-Monolith mit SQLAlchemy/PostgreSQL, Alembic, React/TypeScript/Vite, Docker-Compose-Entwicklungsdiensten und GitHub Actions.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Schutz, Login-Limit und rollenbasierter serverseitiger Autorisierung. Benutzer, Rollen, Rechte und Anwendungs-Audit-Lesezugriff sind vorhanden.
- Kunden mit Anschriften, Ansprechpartnern, Status, Vertragsstatus-Metadatum, Suche, Archivierung und Änderungshistorie. Vertragsmanagement/-dokumente sind nicht enthalten.
- Objekte mit Kunden-FK, Ansprechpartnern/Adresse, Historie, Zuweisungen und separater Berechtigungsgrenze für Sicherheits-/Zutrittsdaten.
- Personalakten mit Qualifikationen, Abwesenheiten, sensiblen Personalangaben, Zuweisungsverlauf und versionierten Qualifikationsdateien in PostgreSQL (`BYTEA`).
- Dienstplanung mit Schichten, UTC-Speicherung, konfigurierbarer IANA-Zeitzone/Ruhezeit, Konfliktprüfungen, Verlauf und PostgreSQL-Exclusion-Constraint.
- Zeiterfassung mit Arbeits-/Pausensegmenten, Korrekturanträgen, Freigaben, Berichten/CSV, Zuschlagszeit-Regeln und versionierten Zeitnachweisen sowie endgültigen Abrechnungsperiodensperren. Es werden keine Zuschlags-Geldbeträge berechnet; Lohnbasis, Prozentbasis, Festwert-Einheit und Rundung sind fachlich nicht festgelegt.
- Es gibt keine eigenständige Frontend-Router-/Feature-Paketarchitektur; die React-Oberfläche ist eine Vite-Anwendung. Das Dashboard liefert derzeit Kundenkennzahlen, keine vollständigen operativen Kennzahlen.

## Offene Pull Requests – ausdrücklich nicht in `main`

| PR | Aktueller Status | Inhalt/Abhängigkeit | CI (zuletzt frisch geprüft) |
|---|---|---|---|
| [#23](https://github.com/Xonni-star/securityops-python/pull/23) | Offen, Ziel `main`, Head `5bcbdbe5fab3be20d5b52b3cde432539ebf5f2a0` | OWKS-Wachbuch, Kontrollgänge, QR/NFC, Migration `0014_owks_wachbuch`; nicht gemergt und nicht fachlich abgenommen. | Backend/Migration/PostgreSQL, Frontend und Docker jeweils erfolgreich. |
| [#24](https://github.com/Xonni-star/securityops-python/pull/24) | Offen, Zielbranch PR #23, Head `a405530635a67cecb5cb223dadc59e3e16432c1a` | Dokumente/Verträge, Migration `0015_documents_contracts`; baut auf #23 auf und ist daher ebenfalls nicht in `main`. | Backend/Migration/PostgreSQL, Frontend und Docker jeweils erfolgreich nach dem Basiswechsel. |

Die PR-Köpfe, Basen, Dateien und CI wurden am obigen Prüfzeitpunkt über GitHub erneut abgefragt. Für die Funktions- und Schema-Dokumentation dieses Repositories gelten allein die Dateien auf `main`; PR-Änderungen sind nur als getrennte Vorschau aufgeführt.

## Vollständiger PR- und Issue-Index

| PR | Status am Prüftag | Titel |
|---|---|---|
| [#24](https://github.com/Xonni-star/securityops-python/pull/24) | Offen | Geschützte Dokumenten- und Vertragsverwaltung |
| [#23](https://github.com/Xonni-star/securityops-python/pull/23) | Offen | OWKS-Wachbuch und QR/NFC-Kontrollgänge integrieren |
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
| [#8](https://github.com/Xonni-star/securityops-python/issues/8) | Offen | Geschützte Dokumenten- und Vertragsverwaltung entwickeln |
| [#7](https://github.com/Xonni-star/securityops-python/issues/7) | Offen | Rechnungswesen, Freigaben und Buchhaltungsexport implementieren |
| [#6](https://github.com/Xonni-star/securityops-python/issues/6) | Geschlossen | Kundenverwaltung um Ansprechpartner, Anschriften und Archivierung ergänzen |
| [#5](https://github.com/Xonni-star/securityops-python/issues/5) | Geschlossen | Personalverwaltung und Qualifikationsnachweise entwickeln |
| [#4](https://github.com/Xonni-star/securityops-python/issues/4) | Offen | Zeiterfassung mit Korrekturfreigaben und Änderungsverlauf ergänzen |
| [#3](https://github.com/Xonni-star/securityops-python/issues/3) | Offen | OWKS-Wachbuch und QR/NFC-Kontrollgänge integrieren |
| [#2](https://github.com/Xonni-star/securityops-python/issues/2) | Offen | Objektverwaltung mit Kundenbeziehung und Objektzugriffsrechten implementieren |

## PR- und Issue-Verlauf

- PR #20 und PR #22 sind gemergt; der aktuelle `main`-SHA ist der Merge-Commit von #22.
- PR #21 ist geschlossen, weil seine relevanten Commits bereits in #22/`main` enthalten sind. Er ist kein offener Feature-Branch.
- PR #17 Personal, #18 Kunden und #19 Dienstplanung sind gemergt. Die jeweiligen GitHub-CI-Läufe auf den Merge-Commits waren erfolgreich.
- Die jüngsten `main`-CI-Läufe zu #22 (`5f35304`), #19 (`d066d56`), #18 (`c8d4fbe`), #17 (`fc8c7e8`) und #16 (`6cda443`) wurden als erfolgreich verzeichnet. Der ältere Lauf für #14 war fehlgeschlagen; spätere Korrektur-/Merge-Läufe sind erfolgreich. Ein früherer Fehler wird nicht als aktueller Main-Fehler interpretiert.
- Offene Issues laut letzter GitHub-Abfrage: #2 Objektverwaltung, #3 OWKS, #4 Zeiterfassung, #7 Rechnungswesen, #8 Dokumente/Verträge, #9 Produktionshärtung und #10 Dienstplanung.
- Geschlossene Issues: #5 Personal/Qualifikationen und #6 Kundenverwaltung.
- #2, #4 und #10 bleiben trotz implementierter Main-Funktionen bis zur formalen fachlichen Abnahme offen. #3 und #8 sind durch offene PRs in Arbeit, nicht integriert. #7 und #9 sind nicht abgeschlossen. Kein Issue wurde durch diese Dokumentationsarbeit verändert oder geschlossen.

## Tests, Betrieb und Abnahme

Im Repository vorhanden sind Backendtests für Konfiguration, Kunden, Identität, Objekte, Personal, Planung und Zeiterfassung sowie ein Frontend-Test für die App; die GitHub-CI prüft zusätzlich Python-Lint/Format, Migrationen und Tests auf temporärem PostgreSQL 17, Frontend-Build/-Tests und Backend-/Frontend-Docker-Images. Es gibt keine dokumentierten E2E-, Last-, Restore-, externen Penetrations- oder unabhängigen Datenschutz-/Rechts-/Steuerprüfungen.

Compose bindet API und Vite an Loopback, stellt aber kein Produktionsdeployment bereit. Nicht umgesetzt bzw. nicht nachgewiesen sind unter anderem MFA, Passwortzurücksetzung, Sitzungsübersicht, zentral verteilter Rate-Limit-Speicher, TLS-Reverse-Proxy, produktive statische Frontendauslieferung, Malware-Scan, Anwendungsebene-Verschlüsselung, automatisierte verschlüsselte Backups mit Restore-Nachweis, Monitoring und Incident-Prozess. Auditdaten sind nicht gegen direkte Änderungen privilegierter Datenbankrollen geschützt.

**Gesamturteil:** ein fortgeschrittener Entwicklungsstand mit CI-geprüften Funktionsbereichen, keine Produktionsfreigabe. Arbeitszeit-/Dienstplanungskonfiguration ist keine Rechtskonformitätsgarantie; Geldbeträge werden nicht berechnet. Datenschutz, Aufbewahrung und Betrieb müssen für eine reale Umgebung eigenständig geprüft und umgesetzt werden.

## Verweise

- [Architektur](ARCHITECTURE.md) · [Datenbank/Migrationen](DATABASE.md) · [API](API.md)
- [Sicherheit](SECURITY.md) · [Deployment](DEPLOYMENT.md) · [Backup/Restore](BACKUP_RESTORE.md)
- [Audit](PROJECT_AUDIT.md) · [Sicherheitsprüfung](SECURITY_REVIEW.md) · [Roadmap](IMPLEMENTATION_ROADMAP.md)
