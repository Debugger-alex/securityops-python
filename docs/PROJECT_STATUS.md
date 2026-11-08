# SecurityOps – Projektstatus

Arbeitsstand: PR #20 ergänzt Zeiterfassung auf dem `main`-Stand `d066d56b97fbd795be276b0414d6a88b8c779962`; die gestapelte Folgeänderung [PR #21](https://github.com/Xonni-star/securityops-python/pull/21) baut isoliert auf PR-20-Head `d3315bbc995a3fabe1d37ad6aa8be24f3744f470` auf und zielt nicht auf `main`. PR #20 und Issue #4 bleiben offen. PR #19 (Dienstplanung) ist in diesem Ausgangsstand integriert; Issue #10 bleibt bis zur fachlichen Abnahme offen. PR #18 ist mit Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033` integriert, seine Backend/PostgreSQL-, Frontend-/Vitest- und Docker-CI war erfolgreich; Issue #6 ist geschlossen. Issue #2 bleibt bis zur formalen Abnahme seiner Akzeptanzkriterien offen. Die offenen PRs #23 (OWKS) und #24 (Dokumenten-/Vertragsverwaltung) werden als Folgeänderung integriert; PR #24 hängt nach der Umstellung auf der OWKS-Migration 0014 und enthält Migration 0015. Der kombinierte PostgreSQL-17-CI-Lauf steht für diesen Integrationsstand noch aus. Dieser Status beschreibt Quellcode und tatsächlich ausgeführte Prüfungen, nicht eine Produktions- oder Rechtsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenkern in `main`: Anlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Rechtsform, Website, Vertragsstatus, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung, Historie und erreichbare Objektzuordnungen. PR #18 ist gemergt; Issue #6 ist geschlossen.
- Objektverwaltung mit Kunden-FK, Suche/Filter/Sortierung/Paginierung, Detailbearbeitung, Anschrift, mehreren einzeln bearbeitbaren Ansprechpartnern, Archivierung/Reaktivierung und Historie.
- Objektmitarbeiter-Zuweisungen auf aktive Mitarbeiter-/Objektleitungskonten; serverseitiger Objektzugriff anhand globaler Rechte oder Zuweisung. Sensible Sicherheits-/Zutrittsdaten liegen in eigener Tabelle und eigenen API-Endpunkten mit separaten Berechtigungen.
- Personalakten mit Personalnummer, Stammdaten, optionalem Benutzerkonto, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, Archivierung/Reaktivierung und Historie. Anschrift, Notfallkontakt und interne Notizen sind getrennt und zusätzlich berechtigt.
- Dienstplan-Kern in `main` (PR #19): Schichtanlage/-änderung, Tages-/Wochen-/Monatsansichten, Mitarbeiter-/Objekt-/Datumsfilter, Entwurf/Veröffentlichung/Absage, Verlauf, Konfliktprüfung und konfigurierbare IANA-Zeitzone/Mindestruhezeit. UTC-Zeitpunkte, Abwesenheiten, aktiver Beschäftigungszeitraum, Qualifikation, Objektzuweisung, bestehende Schichten und Ruhezeit werden geprüft. Die persönliche Verfügbarkeit hat im aktuellen Datenmodell keine eigenständigen Wunsch-/Sperrzeitfenster; es wird die Verfügbarkeit aus Beschäftigungsstatus, Abwesenheiten und bestehenden Diensten abgeleitet.
- Zeiterfassung in PR #20 (Migration 0012) und gestapelte Erweiterung (Migration 0013): Live-Start/-Stopp mit Arbeits-/Pausensegmenten, Korrekturversionen, Freigaben, Soll-Ist, Fehlbuchungsübersicht, Zuschlagsregeln, regionale Feiertage, priorisierte/Kombinationsregeln, versionierte Zuschlagszeitnachweise, endgültige Periodensperren sowie getrennte CSV-Exporte. Geldbeträge werden mangels bestätigter Lohn-/Prozentbasis, Festzuschlagseinheit und Rundung nicht errechnet. Lokale Gesamtprüfung: Backend 31 bestanden/1 PostgreSQL-spezifischer Test übersprungen; Frontend 4 bestanden, Produktionsbuild, Ruff/Format und Offline-Upgrade/-Downgrade erfolgreich. GitHub-CI für PR #21 (Backend/PostgreSQL/Migrationen, Frontend, Docker) erfolgreich; lokale Docker- und Live-PostgreSQL-Werkzeuge sind nicht verfügbar.
- Anmeldung mit Argon2id, serverseitig widerrufbaren opaque Sitzungen, Idle-/Absolute-Timeout, CSRF-Prüfung und Login-Rate-Limit.
- Serverseitige RBAC-Prüfungen, Benutzeranlage/-deaktivierung und Schutz des letzten aktiven Administrators.
- Audit-Ereignisse für An-/Abmeldung, fehlgeschlagene Anmeldungen, Passwortwechsel, Benutzer- und Kundenänderungen.
- Additive Rollen-/Rechtemigration `0003_role_permissions`; Administratorrollenvergabe erfordert `users.manage_admin`.
- Compose-Standard für Secure-Cookie ist `true`; `.env.example` setzt für lokale HTTP-Entwicklung ausdrücklich `false`.
- Das Datenbankpasswort hat keinen Standardwert in der Anwendung mehr: `POSTGRES_PASSWORD` muss gesetzt sein.
- GitHub Actions führt Python-Lint/Format, Backendtests auf SQLite und einer temporären PostgreSQL-Testdatenbank, Migrationen, Frontendtests/-build und Docker-Image-Builds aus. PR #17 und der Issue-#6-PR #18 bestanden Backend/PostgreSQL, Frontend und Docker.

## Teilweise implementiert oder offen

| Bereich | Status |
|---|---|
| Kunden | PR #18 mit Migration 0010, Website, Vertragsstatus, Suche/Filter/Sortierung und geschützten Objektzuordnungen ist gemergt; CI Backend/PostgreSQL, Frontend/Vitest und Docker war grün. Issue #6 ist geschlossen. Vertrags- und Dokumentenmodule fehlen weiterhin ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | Backend/API/UI und Migrationen 0005–0007 in `main` implementiert; PR #16 und dessen CI sind abgeschlossen. Issue #2 bleibt offen, da die formale Abnahme der Akzeptanzkriterien noch aussteht. |
| Personal/Qualifikationen | Migrationen 0008–0009, Personalakten, Abwesenheiten, sensible Daten, Historie, Zuweisungen und versionierte Qualifikationsdateien sind in `main`. PR #17 wurde gemergt; PostgreSQL-/Backend-, Frontend- und Docker-CI war grün und Issue #5 ist geschlossen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
| Dienstplanung | Scheduling-Kern in PR [#19](https://github.com/Xonni-star/securityops-python/pull/19) ist im Ausgangsstand `main` enthalten; GitHub-CI für Backend/Migration/PostgreSQL, Frontend und Docker war erfolgreich. Formale Akzeptanz von Issue #10 steht noch aus ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | PR #20 offen; gestapelte Ergänzung mit Migration 0013 und Zuschlagszeit-/Periodensperren baut auf PR-20-Head auf. Issue #4 bleibt offen; Geldbetragsberechnung ist mangels bestätigter Abrechnungskonvention bewusst nicht enthalten. |
| OWKS/Kontrollgänge | In offenem PR #23; seine Migration 0014 ist die Vorgängermigration von PR #24. Issue #3 bleibt bis zur fachlichen Abnahme offen. |
| Dokumente/Verträge | In offenem PR #24, gestapelt auf PR #23; die kombinierte Migration- und PostgreSQL-17-CI ist für den Integrationsstand noch nicht bestätigt ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| Produktion | Nicht freigegeben: Vite-Devserver statt statischer Frontend-Auslieferung, kein TLS-Reverse-Proxy und kein gemeinsamer Rate-Limit-Speicher ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |
| Benutzerverwaltung | MFA, Passwortzurücksetzung, aktive Sitzungsübersicht und Rechteeditor fehlen. |
| Audit | App-seitig lesbar; Objektänderungen protokollieren Aktion und geänderte Feldnamen ohne sensible Werte. Nicht gegen direkte Änderungen privilegierter Datenbankrollen abgesichert. |

## Dokumentation und Prüfstatus

- Vollständige Bestandsaufnahme: [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md).
- Prioritäten und Abhängigkeiten: [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md).
- Sicherheitsbefunde und offene Maßnahmen: [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md).
- Architektur, Betrieb und weitere Unterlagen sind im [`README.md`](../README.md) verlinkt.
- PR #18 (Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033`): GitHub-CI für Backend/PostgreSQL, Frontend einschließlich Vitest und Docker erfolgreich; Issue #6 geschlossen.
- PR #19: GitHub-CI für Backend/Migration/PostgreSQL, Frontend einschließlich Vitest und Docker erfolgreich. Der PostgreSQL-Job deckt Live-Migration und den parallelen Schreibzugriffstest ab.
- PR #20: Backend `29 passed, 1 skipped` (PostgreSQL-spezifischer Scheduling-Constraint-Test); Frontend `4 passed`, Produktionsbuild, Ruff und Offline-Migration erfolgreich. Seine GitHub-CI war zuletzt für Backend/PostgreSQL, Frontend und Docker grün.
- Gestapelte Zeiterfassungsergänzung [PR #21](https://github.com/Xonni-star/securityops-python/pull/21): Backend `31 passed, 1 skipped` (lokal übersprungener PostgreSQL-spezifischer Constraint-Test), Frontend `4 passed`, Produktionsbuild, Ruff/Format und Offline-Alembic-Upgrade/-Downgrade durch Migration 0013 erfolgreich. GitHub-CI für Backend/PostgreSQL/Migrationen, Frontend und Docker erfolgreich. Die Docker-CLI und lokale PostgreSQL-Prüfwerkzeuge sind nicht verfügbar; Offline-SQL-Rendering allein wäre kein Live-PostgreSQL-Test.
- Die CI-Ergebnisse stellen keine Produktions- oder Rechtsfreigabe dar. Issue #10 bleibt bis zur fachlichen Abnahme offen.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Gestapelte Zeiterfassungsergänzung gegen den PR-20-Branch fachlich reviewen; CI für PostgreSQL/Migrationen, Frontend und Docker ist für PR #21 grün. PR #20 weder ändern noch mergen und Issue #4 bis zur fachlichen Abnahme offen halten.
2. Issue #10 und Issue #2 bleiben bis zur jeweiligen formalen Abnahme offen; keine geschlossenen Issues erneut öffnen.
3. OWKS und weitere Module gemäß Roadmap getrennt angehen.
4. Produktionshärtung, Monitoring, unabhängige Rechtsprüfung und Backup/Restore aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) bleiben separat offen.

## Repository-Arbeitsstand

- Der aktuelle Folgebranch baut isoliert auf PR-20-Head auf und zielt gegen den PR-20-Branch, nicht gegen `main`.
- PR #18 und PR #19 sind im Ausgangsstand integriert; Issue #6 ist geschlossen. PR #20 ist offen und nicht gemergt; Issue #4 bleibt ebenfalls offen. Issue #10 bleibt bis fachlicher Akzeptanz offen. Issue #2 bleibt bis zur formalen Akzeptanz offen.
- Die bereits in `main` gemergte Objektverwaltung wurde nicht neu entwickelt; Personalakten greifen über ihr verknüpftes Benutzerkonto auf die bestehende Zuweisungstabelle zu.
