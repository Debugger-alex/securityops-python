# SecurityOps – Projektstatus

Arbeitsstand: Zeiterfassungs-Feature-Branch auf `main` bei Merge-Commit `d066d56b97fbd795be276b0414d6a88b8c779962`. PR #19 (Dienstplanung) ist in diesem Ausgangsstand integriert; Issue #10 bleibt bis zur fachlichen Abnahme offen. PR #18 ist mit Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033` integriert, seine Backend/PostgreSQL-, Frontend-/Vitest- und Docker-CI war erfolgreich; Issue #6 ist geschlossen. Issue #2 bleibt bis zur formalen Abnahme seiner Akzeptanzkriterien offen. Der aktuelle Branch ergänzt ausschließlich Zeiterfassung für Issue #4; PR [#20](https://github.com/Xonni-star/securityops-python/pull/20) ist offen, die PostgreSQL-/Docker-CI läuft. Dieser Status beschreibt Quellcode und tatsächlich ausgeführte Prüfungen, nicht eine Produktions- oder Rechtsfreigabe.

## Implementierter Stand

- Modularer FastAPI-Monolith mit SQLAlchemy, PostgreSQL, Alembic sowie React/TypeScript/Vite.
- Kundenkern in `main`: Anlage, Filterung, Sortierung, Suche, Detailabruf/-änderung, Geschäfts- und Rechnungsanschriften, Rechtsform, Website, Vertragsstatus, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung, Historie und erreichbare Objektzuordnungen. PR #18 ist gemergt; Issue #6 ist geschlossen. Dokumenten- und Vertragsverwaltung fehlen weiterhin.
- Objektverwaltung mit Kunden-FK, Suche/Filter/Sortierung/Paginierung, Detailbearbeitung, Anschrift, mehreren einzeln bearbeitbaren Ansprechpartnern, Archivierung/Reaktivierung und Historie.
- Objektmitarbeiter-Zuweisungen auf aktive Mitarbeiter-/Objektleitungskonten; serverseitiger Objektzugriff anhand globaler Rechte oder Zuweisung. Sensible Sicherheits-/Zutrittsdaten liegen in eigener Tabelle und eigenen API-Endpunkten mit separaten Berechtigungen.
- Personalakten mit Personalnummer, Stammdaten, optionalem Benutzerkonto, Beschäftigungsstatus, Qualifikationen, Ablaufübersicht, Abwesenheiten, Archivierung/Reaktivierung und Historie. Anschrift, Notfallkontakt und interne Notizen sind getrennt und zusätzlich berechtigt.
- Dienstplan-Kern in `main` (PR #19): Schichtanlage/-änderung, Tages-/Wochen-/Monatsansichten, Mitarbeiter-/Objekt-/Datumsfilter, Entwurf/Veröffentlichung/Absage, Verlauf, Konfliktprüfung und konfigurierbare IANA-Zeitzone/Mindestruhezeit. UTC-Zeitpunkte, Abwesenheiten, aktiver Beschäftigungszeitraum, Qualifikation, Objektzuweisung, bestehende Schichten und Ruhezeit werden geprüft. Die persönliche Verfügbarkeit hat im aktuellen Datenmodell keine eigenständigen Wunsch-/Sperrzeitfenster; es wird die Verfügbarkeit aus Beschäftigungsstatus, Abwesenheiten und bestehenden Diensten abgeleitet.
- Zeiterfassung im aktuellen Feature-Branch (Migration 0012): Live-Start/-Stopp mit mehreren Arbeits-/Pausensegmenten, automatische Dienst-/Objektzuordnung, manuelle Nachträge, Korrekturanträge als unveränderliche Versionen, serverseitig kontrollierte Freigaben/Ablehnungen, Tages-/Wochen-/Monatsgruppen, Soll-/Ist-/Pausenauswertungen, Fehlbuchungsübersicht und formelsicherer CSV-Export. Lokal geprüft: Backend 29 bestanden/1 PostgreSQL-Constraint-Test übersprungen, Ruff-Lint/Format, Frontend 4 bestanden, Produktionsbuild sowie Offline-Upgrade/-Downgrade. Live-PostgreSQL, Docker-CI und PR-Review stehen noch aus; siehe unten.
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
| Zeiterfassung | In Umsetzung im aktuellen Feature-Branch ([#4](https://github.com/Xonni-star/securityops-python/issues/4)); Freigabe und CI-Abnahme ausstehend. |
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
- PR #18 (Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033`): GitHub-CI für Backend/PostgreSQL, Frontend einschließlich Vitest und Docker erfolgreich; Issue #6 geschlossen.
- PR #19: GitHub-CI für Backend/Migration/PostgreSQL, Frontend einschließlich Vitest und Docker erfolgreich. Der PostgreSQL-Job deckt Live-Migration und den parallelen Schreibzugriffstest ab.
- Zeiterfassung: Backend `29 passed, 1 skipped` (übersprungen: PostgreSQL-Constraint-Test in `tests/test_scheduling.py`), Frontend `4 passed`, `npm run build`, Ruff-Lint/Format sowie Alembic-Offline-Upgrade und -Downgrade erfolgreich. Docker und lokale PostgreSQL-Werkzeuge stehen in dieser Umgebung nicht zur Verfügung; PR [#20](https://github.com/Xonni-star/securityops-python/pull/20) führt die Live-Migration und den PostgreSQL-Constraint-Test aus. Ein Offline-SQL-Render gilt nicht als Live-PostgreSQL-Migrationstest.
- Die CI-Ergebnisse stellen keine Produktions- oder Rechtsfreigabe dar. Issue #10 bleibt bis zur fachlichen Abnahme offen.
- Derzeit keine E2E-, Last-, Restore-, externe Penetrations- oder unabhängige Datenschutz-/Steuerprüfung.

## Nächste Schritte

1. Zeiterfassungs-Branch durch PostgreSQL-/Docker-CI und Review prüfen; Issue #4 bleibt bis zur fachlichen Abnahme offen.
2. Issue #10 und Issue #2 bleiben bis zur jeweiligen formalen Abnahme offen; keine geschlossenen Issues erneut öffnen.
3. OWKS und weitere Module gemäß Roadmap getrennt angehen.
4. Produktionshärtung, Monitoring, unabhängige Rechtsprüfung und Backup/Restore aus [Issue #9](https://github.com/Xonni-star/securityops-python/issues/9) bleiben separat offen.

## Repository-Arbeitsstand

- Der aktuelle Arbeitsbranch ist der isolierte Zeiterfassungs-Feature-Branch, ausgehend von `main` nach Merge von PR #19.
- PR #18 und PR #19 sind im Ausgangsstand integriert; Issue #6 ist geschlossen. PR #20 ist offen und nicht gemergt; Issue #4 bleibt ebenfalls offen. Issue #10 bleibt bis fachlicher Akzeptanz offen. Issue #2 bleibt bis zur formalen Akzeptanz offen.
- Die bereits in `main` gemergte Objektverwaltung wurde nicht neu entwickelt; Personalakten greifen über ihr verknüpftes Benutzerkonto auf die bestehende Zuweisungstabelle zu.
