# Änderungsprotokoll

## 2026-11-09 – Offenes Leitstellen-Dashboard als PR-Arbeit vermerkt

- Frisch geprüft: PR #38 ist offen gegen `main`; PR #25 bleibt ebenfalls offen. Issues #7–#10 sind offen, #2–#6 geschlossen.
- `main` bleibt auf `ac31bae99ee9f70026057483f303e86c69159e38`, Alembic-Head `0022_incident_management`, 73 SQLAlchemy-Tabellen und 189 `/api/v1`-Operationen.
- PR #38 beschreibt eine Leitstellenübersicht mit Recht `control_room.read`, aktiven Objekt- und Fachbereichsprüfungen und begrenzten Listen. Seine Migration `0023_control_room_permission` ist ausstehend und nicht in Main-Tabellen-, API- oder Migrationsinventaren enthalten. Die PR-Beschreibung sagt, bestehende Dashboard-API und Datenmodell blieben unverändert.
- Beim letzten Statusabruf liefen PR #38 Backend/Migration/PostgreSQL, verschlüsselter Restore, Docker und beide CodeQL-Jobs; Frontend-Checks und SCA waren erfolgreich. Der separate CodeQL-Check war neutral. CI ist kein Merge-, Fachabnahme- oder Produktionsnachweis.
- Status-, Roadmap-, Audit-, README- und Datenbanktexte aktualisiert, ohne Änderungen an Software oder Migrationen.

## 2026-11-09 – Dokumentation auf Main mit Vorfallmanagement aktualisiert

- Maßgeblicher `main`-Stand: `ac31bae99ee9f70026057483f303e86c69159e38`, Alembic-Head `0022_incident_management`, 73 SQLAlchemy-Tabellen, 189 `/api/v1`-Operationen und zwei Health-Operationen.
- PR #37 wurde am 09.11.2026 gemergt. Migration `0022_incident_management` ergänzt sechs Tabellen und zwölf API-Operationen für objektbezogene Vorfälle/Beschwerden, sensible Details, Maßnahmen, Beteiligte/Zeugen, private Anhänge und append-only Historie. Sieben abgestufte `incidents.*`-Rechte erzwingen serverseitigen Objekt-Scope und gesonderten Schutz sensibler Inhalte. Anhänge werden fail-closed mit ClamAV geprüft und privat gespeichert; kein rückwirkender Bestandsscan. Keine automatische Aufgaben-/Benachrichtigungsintegration, Fristerinnerung oder Eskalationsregeln.
- Die Merge-PR-CI war bei allen acht Checks erfolgreich. Im PR-Text gemeldet: 82 Backendtests bestanden/13 übersprungen (lokal ausgelassene PostgreSQL-spezifische Prüfungen), 39 Frontendtests bestanden, Ruff-Check/Format und Alembic-Head erfolgreich. Dies ist kein fachlicher, rechtlicher oder produktiver Nachweis.
- Frisch geprüft: PR #25 ist die einzige offene PR; Issues #7–#10 sind offen, #2–#6 geschlossen.
- API-, Datenbank-/ER-, Architektur-, Audit-, Roadmap-, Status-, Sicherheits-, README- und Incident-Dokumentation auf den integrierten Stand abgeglichen. Der Dokumentations-PR bleibt offen und wird nicht gemergt.

## 2026-11-09 – Dokumentation auf Main mit Schlüsselverwaltung aktualisiert

- Diese Momentaufnahme beschreibt den vor dem Merge von PR #37 geltenden Main-Stand; der neuere Eintrag oben ist maßgeblich.
- Maßgeblicher `main`-Stand: `744eff7c4c747d089a2fa6da2aeadab4840c5ef8`, Alembic-Head `0021_key_management`, 67 SQLAlchemy-Tabellen, 177 `/api/v1`-Operationen und zwei Health-Operationen.
- PR #36 wurde am 09.11.2026 gemergt. Migration `0021_key_management` ergänzt `physical_keys` und append-only `key_movements`, drei `keys.*`-Rechte und acht API-Operationen. Ausgabe erfordert eine aktive, dem Objekt zugewiesene Person und Quittierungsbestätigung. Diese ist keine qualifizierte elektronische Signatur oder ein Nachweis physischer Verwahrung; bestehende Freitext-Zutrittsangaben werden nicht migriert.
- Die PR-CI war für alle acht Checks erfolgreich (Backend/Migrationen/PostgreSQL, Frontend-Typprüfung/Build, Docker-Images, verschlüsselter PostgreSQL-17-Restore, SCA, CodeQL Python, CodeQL JavaScript/TypeScript und zusätzlicher CodeQL-Check). Der PR meldete 78 Backendtests bestanden/12 übersprungen, 36 Frontendtests bestanden, Ruff-Check/Format und Alembic-Head erfolgreich. CI ist keine fachliche oder produktive Abnahme.
- Lokale Prüfung dieses Updates: Schlüsseltests 5 bestanden/2 übersprungen; interne Markdown-Links/Anker und Codefences in 19 Markdown-Dateien geprüft.
- Frisch geprüft: PR #25 ist die einzige offene PR; Issues #7–#10 sind offen, #2–#6 geschlossen.
- API-, Datenbank-/ER-, Architektur-, Audit-, Roadmap-, Status-, Sicherheits-, Task-, README- und Schlüsselverwaltungsdokumentation auf den integrierten Stand abgeglichen. Der Dokumentations-PR bleibt offen und wird nicht gemergt.

## 2026-11-09 – Dokumentation auf Main mit Benachrichtigungen aktualisiert

- Diese Momentaufnahme beschreibt den vor dem Merge von PR #36 geltenden Main-Stand; der neuere Eintrag oben ist maßgeblich.
- Maßgeblicher `main`-Stand: `881ba0873f616f8b6ab9b5a13ba5fd8e6f81f704`, Alembic-Head `0020_notifications`, 65 SQLAlchemy-Tabellen, 169 `/api/v1`-Operationen und zwei Health-Operationen.
- PR #35 ist gemergt. `0020_notifications` folgt auf `0019_tasks` und ergänzt eine Inbox sowie dauerhafte Outbox für Aufgaben-Neuzuweisungen und Statuswechsel. Einträge werden transaktional erzeugt; Outbox-Ereignisse werden nicht verarbeitet. Worker, Retry-Verarbeitung, E-Mail/Push und Ereignisse aus anderen Modulen fehlen.
- Frisch geprüft: PR #25 ist die einzige offene PR; Issues #7–#10 sind offen, #2–#6 geschlossen.
- API-, Datenbank-/ER-, Architektur-, Audit-, Roadmap-, Status-, Task-, Sicherheits- und README-Dokumentation auf den integrierten Stand abgeglichen. Der Dokumentations-PR bleibt offen und wurde nicht gemergt.

## 2026-11-09 – Dokumentation auf Main mit Uploadscan und Aufgaben aktualisiert

Diese Momentaufnahme dokumentiert den Stand vor Merge PR #35; der anschließende Eintrag beschreibt den aktuellen Main-Stand.

- Maßgeblicher `main`-Stand: `d47efae7b58e4f78f60bede783bc3655ab03297c`, Alembic-Head `0019_tasks`, 63 SQLAlchemy-Tabellen, 167 `/api/v1`-Operationen und zwei Health-Operationen.
- PR #33 ist gemergt: neue Dokument-/Vertragsdateien, neue Dokumentversionen, OWKS-Anhänge und Personal-Qualifikationsdateien werden vor Speicherung fail-closed mit ClamAV geprüft. Es gibt keinen rückwirkenden Bestandsscan; Scanner-Mocks sind kein Produktionsnachweis.
- PR #34 ist gemergt: Migration `0019_tasks` ergänzt drei Aufgaben-Tabellen und sieben API-Operationen. Es gibt keine automatische Kopplung an Fachmodule, Anhänge, Benachrichtigungszustellung, Hintergrundjobs oder Eskalationen.
- Frisch geprüft: PR #25 ist die einzige offene PR; Issues #7–#10 sind offen, #2–#6 geschlossen. CI für den vorherigen PR-Head `63c644a` war grün; neue Commits benötigen neue Checks.
- Status-, API-, Datenbank-/ER-, Architektur-, Audit-, Roadmap-, Sicherheits-, Betriebs-, README-, AGENTS- und Task-Dokumentation gegen Quellcode und Live-GitHub-Status abgeglichen. Nur Markdown/`AGENTS.md` geändert.

## 2026-11-08 – Dokumentation auf Billing-/MFA-Main synchronisiert

Diese Momentaufnahme bezieht sich auf den damaligen Stand vor PR #33 und #34; aktueller Status und aktuelle Inventare stehen im Eintrag vom 09.11.2026 sowie in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

- Maßgeblicher `main`-Stand: `edad05f3b3029370a62b51a6508962f1dd156592`, Alembic-Head `0018_identity_security`, 60 SQLAlchemy-Tabellen und 160 `/api/v1`-Operationen.
- PR #27 (Rechnungswesen, Migration `0017_billing`) und PR #31 (MFA/Sitzungsverwaltung, Migration `0018_identity_security`) sind gemergt. Rechnungswesen ist implementiert, aber nicht steuerlich/buchhalterisch abgenommen; TOTP-MFA ist optional, E-Mail-Selbstreset fehlt.
- Frisch geprüft: PR #25 ist die einzige offene PR; Issues #7–#10 sind offen, #2–#6 geschlossen. Issue #8 bleibt trotz Merge der Dokumentenfunktionen offen.
- `PROJECT_STATUS`, Architektur-, API-, Datenbank-, Audit-, Roadmap-, Sicherheits- und README-Dokumentation auf den tatsächlichen Main-Stand abgeglichen; kein Anwendungscode, Schema oder Migration geändert.

## Vorangegangene Synchronisierung auf Zwischenstand (überholt)

Die folgenden Angaben dokumentieren den damaligen Stand vor Billing-/MFA-Merge und sind kein aktueller Repository-Status.

- `main` auf SHA `3deebd16e368733f9595cd39f7e38b6354c1a88d`, Alembic-Head `0016_scheduling_availability`, 54 Tabellen und 140 `/api/v1`-Operationen aktualisiert; Verfügbarkeitsfenster, Anträge und Schichtvertretungen in API-/Datenbankinventar ergänzt.
- PRs #26, #28 und #29 als gemergt und in `main` aufgenommen dokumentiert. PR #27 bleibt offen und zielt nach dem Merge von #26 direkt auf `main`; `0017_billing` folgt eindeutig auf `0016_scheduling_availability`.
- Frischer GitHub-Status: PRs #25 und #27 offen; Issues #7–#10 offen. Issue #8 bleibt offen bis zur fachlichen Bestätigung; Issue #9 bleibt trotz Merge von #28 offen, ebenso Issue #10 trotz Merge von #26.
- Produktions-Compose, Redis-Rate-Limiting, getrennte Release-Migrationen, verschlüsselte Backup-/Restorewerkzeuge, Security-Analyse und synthetischen CI-Restore als vorhanden dokumentiert, ohne daraus Produktionsfreigabe abzuleiten.
- Ausschließlich Dokumentationen und `AGENTS.md` geändert; keine Anwendung, Schema- oder Migrationsdatei. Ältere Einträge weiter unten sind zeitgebundene Entwicklungsnotizen; die aktuelle Momentaufnahme steht in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## 2026-11-08 – Gestapelte Ergänzung zu Zeiterfassung/Zuschlägen

- Migration 0013 ergänzt Bundeslandseinstellung, unveränderliche Zuschlagsregeln, versionierte Berechnungssnapshots und endgültige Abrechnungsperiodensperren mit getrennten Rechten.
- Zuschlagszeit wird ausschließlich auf tatsächliche Arbeitssegmente verteilt; Nacht-/Betriebszeitfenster, Samstage, Sonntage, gesetzliche Feiertage nach Bundesland, Prioritäten, ausdrücklich freigegebene Kombinationen und `Europe/Berlin`-DST werden berücksichtigt.
- Verwaltungsoberfläche, getrennte Zuschlagsauswertung und formelsicherer CSV-Nachweis ergänzt. Periodensperren verlangen freigegebene Buchungen, vollständige Dienstabdeckung und keine grenzüberschreitenden Buchungen.
- Geldbeträge bleiben bewusst unberechnet: Lohnbasis, Prozentbasis, Festzuschlagseinheit und Rundung sind nicht festgelegt. Snapshots speichern Regelwert und Arbeitszeit, nicht Payroll-Beträge.
- Lokale Prüfung: zielgerichtete Zeiterfassungstests `4 passed`, Frontendtests `4 passed`, TypeScript-/Produktionsbuild, Ruff und PostgreSQL-Offline-Upgrade/-Downgrade erfolgreich. Vollständige Backend-, Live-PostgreSQL- und Dockerprüfungen folgen vor Veröffentlichung.

## 2026-11-08 – Zeiterfassung für Issue #4

- Migration 0012 ergänzt UTC-Arbeitszeitbuchungen, Arbeits-/Pausensegmente, getrennte Korrekturversionen, Verlauf, Constraints und rollenbasierte Rechte.
- Geschützte API ergänzt Start, Pause, Fortsetzen, Einreichen, manuelle Nachträge, Korrekturen, Freigaben/Ablehnungen, Sperren, gruppierte Auswertungen, Fehlbuchungsübersicht und formelsicheren CSV-Export.
- Deutsche Mitarbeiter- und Verwaltungsoberfläche mit Zeitsteuerung, Filtern, Korrektur-/Freigabeablauf und CSV-Download ergänzt. Freigegebene Originalsegmente werden bei Korrekturen nicht überschrieben.
- Lokal erfolgreich: Backend `29 passed, 1 skipped`, Frontend `4 passed`, Produktionsbuild, Ruff-Lint/Format und Alembic-Offline-Upgrade/-Downgrade. Der übersprungene Test benötigt PostgreSQL; Live-PostgreSQL-/Docker-CI läuft für PR [#20](https://github.com/Xonni-star/securityops-python/pull/20). Issue #4 bleibt bis zur fachlichen Abnahme offen; kein Merge oder Issue-Abschluss.

## 2026-11-08 – Dienstplanung (in `main`)

- Alembic-Migration 0011 ergänzt Schichten, Planungseinstellungen, Verlauf und einen PostgreSQL-Exclusion-Constraint gegen zeitliche Doppelbelegung; API-Konfliktprüfungen werden pro Mitarbeiter per Transaktions-Advisory-Lock serialisiert.
- Geschützte Scheduling-API und React-Oberfläche mit Tages-/Wochen-/Monatsansichten, Filtern, Entwurf/Veröffentlichung/Absage, Änderungsverlauf und konfigurierbarer IANA-Zeitzone/Ruhezeit ergänzt.
- Backendtests für Zeitumrechnung einschließlich doppelter Ortszeit, Konflikte, Qualifikation, Abwesenheiten, Objektzuweisung, Berechtigungen und parallele PostgreSQL-Schreibzugriffe ergänzt. Lokal: 27 Backendtests bestanden, PostgreSQL-Parallelitätstest mangels PostgreSQL übersprungen; Ruff, Frontend-Build/Vitest und Offline-Migrationsupgrade/-downgrade erfolgreich. GitHub-CI für Backend/Migration/PostgreSQL, Frontend und Docker erfolgreich.
- PR [#19](https://github.com/Xonni-star/securityops-python/pull/19) ist in `main`; Issue #10 bleibt bis fachlicher Akzeptanz offen. Issue #2 bleibt bis zur formalen Abnahme offen; Issue #6 wird nicht erneut geöffnet.
- PR #18 ist in `main` (Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033`), CI Backend/PostgreSQL, Frontend einschließlich Vitest und Docker grün; Issue #6 geschlossen. Issue #2 bleibt bis zur formalen Abnahme offen.

## Kundenverwaltung erweitert

- Website und validierter Vertragsstatus in Kundendaten, Suche und Formularen ergänzt; Migration 0010 (`0010_customer_fields`) übernimmt Bestandskunden ohne Datenverlust.
- Kunden-Detailansicht zeigt vorhandene, serverseitig nach Objektberechtigung gefilterte Objektzuordnungen.
- API-Validierungs-, Berechtigungs- und Frontendtests für Vertragsstatus, Website und Fehlerfälle ergänzt.

## Objektverwaltung – Feature-Branch

- React-Objektverwaltung mit Kundenbeziehung, Suche, Filtern, Sortierung, Paginierung und Detailansicht ergänzt.
- Objektanschriften und Ansprechpartner einschließlich Einzelbearbeitung, Archivierung/Reaktivierung und Änderungshistorie integriert.
- Objektbezogene Mitarbeiterzuweisungen und serverseitige Scope-Prüfungen ergänzt.
- Sicherheits-/Zutrittsdaten in eigene Tabelle und API-Berechtigungen getrennt; Migration 0007 übernimmt vorhandene Werte.
- Lokale Prüfung: 16 Backendtests, Ruff-Lint/Format und Frontend-TypeScript-/Produktionsbuild bestanden. PostgreSQL-Offline-SQL bis 0007 sowie Downgrade 0007→0006 gerendert; echte PostgreSQL-Integration und Docker-Builds dieses Branches ausstehend.

## 2026-11-08 – Sicherheitsbasis und Bestandsaudit

- Bestandsaufnahme der vorhandenen Kunden-, Identity-, RBAC-, Audit-, Frontend- und Compose-Funktionen dokumentiert.
- Gefährliche Vergabe der Administratorrolle über allgemeines `users.manage` erkannt und auf zusätzliche Berechtigung `users.manage_admin` begrenzt.
- Standardrollen um Verwaltung, Buchhaltung und Auditor erweitert; zusätzliche fachliche Berechtigungen angelegt.
- Compose-Secure-Cookie-Fallback auf `true` gesetzt.
- Dokumentation zu Architektur, Datenbank, API, Sicherheit, Installation, Deployment, Backup/Restore, Benutzerführung und Roadmap ergänzt.
- Backend-Tests, Frontend-Build und Migration-SQL-Generierung werden nach Ausführung im PR vermerkt; kein Docker-/PostgreSQL-Produktionslauf behauptet.

## 2026-11-08 – Phase 1: CI und Konfigurationshärtung

- GitHub Actions prüft Backendtests auf SQLite und PostgreSQL, wendet Migrationen auf einem kurzlebigen PostgreSQL-17-Dienst an und baut Frontend- sowie Docker-Images.
- Python-Linting und Formatprüfung mit Ruff sind in CI eingebunden.
- Das Datenbankpasswort hat keinen impliziten Anwendung-Standardwert mehr; Regressionstest und expliziter Testwert ergänzt.
- Vollständige priorisierte Implementierungs-Roadmap und statische Sicherheitsprüfung hinzugefügt.
- Lokale Prüfung: 9 Backend-Tests, Frontend-TypeScript-/Produktionsbuild und Offline-Migration erfolgreich. Kein Docker-/PostgreSQL-Dienst lokal verfügbar. Der gehostete CI-Lauf bestand nach Behebung eines Test-Fixture-Konflikts mit migrierten Rollen einschließlich PostgreSQL-Migration/API-Tests sowie Frontend- und Docker-Builds.
