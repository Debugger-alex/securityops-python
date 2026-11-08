# SecurityOps – Implementierungs-Roadmap

Stand: 2026-11-08. Diese Roadmap beschreibt den geprüften Ist-Stand und die priorisierte Reihenfolge. Ein Issue ist geplant/offen, bis Code, Migrationen, Berechtigungsprüfungen, Tests und Dokumentation vollständig umgesetzt und geprüft sind. Der Funktionsumfang ist noch nicht produktionsreif.

## Statusübersicht

| Bereich | Status | Beleg / nächste Arbeit |
|---|---|---|
| Einzelmandanten-Grundgerüst | Teilweise | FastAPI, React/TypeScript, PostgreSQL, Alembic und Compose sind vorhanden; keine Mandantenstrukturen. |
| Anmeldung und Rollen | Teilweise | Argon2id, serverseitige Sitzungen, CSRF, RBAC, Admin-Bootstrap und objektbezogene Zuweisungsrechte vorhanden. MFA, Passwortzurücksetzung, Sitzungsverwaltung und revisionsfester Auditbetrieb fehlen. |
| Kunden | Teilweise umgesetzt | Backend/API/Migration, filter- und sortierbare Liste, Details, Anschriften, Ansprechpartner, Archivierung/Reaktivierung und Historie sind implementiert; Migration 0004 und Backendtests bestehen in gehosteter PostgreSQL-CI. Vertrags-/Dokumentzuordnung fehlt ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | Teilweise umgesetzt | Kundenbeziehung, objektbezogene Berechtigungen, Kontakte, Historie, sensible Daten, API und Oberfläche sind in Arbeit; Migration 0005 braucht noch PostgreSQL-CI und fachliche Abnahme ([#2](https://github.com/Xonni-star/securityops-python/issues/2)). |
| Personal und Qualifikationen | Nicht implementiert | Personalstammdaten, Nachweise, Verfügbarkeiten und Abwesenheiten fehlen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
| Dienstplanung | Nicht implementiert | Schichten, Besetzung, Konflikt- und Qualifikationsprüfung fehlen ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | Nicht implementiert | Nachvollziehbare Buchungen, Korrekturfreigaben und Export fehlen ([#4](https://github.com/Xonni-star/securityops-python/issues/4)). |
| OWKS | Nicht implementiert | Kontrollpunkte, QR/NFC, Rundgänge und Offline-Synchronisierung fehlen ([#3](https://github.com/Xonni-star/securityops-python/issues/3)). |
| Dokumente und Verträge | Nicht implementiert | Geschützte Ablage, Berechtigungen und Versionierung fehlen ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert | Vertragsbasierte, freigegebene und nicht doppelt abgerechnete Leistungen fehlen ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| CI und Datenbankqualität | Teilweise umgesetzt | GitHub Actions führt Python-Lint/Format, Backendtests auf SQLite und PostgreSQL, Migrationen auf PostgreSQL, Frontend-Build und Docker-Image-Builds aus. SCA/SAST und weitere Produktionshärtung bleiben offen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |

## Priorisierte Umsetzung

### P0 – Stabilisierung und Sicherheitsgrundlagen

1. **CI und PostgreSQL-Integration:** Workflow für Pull Requests; Migration und Backendtests auf einer kurzlebigen Datenbank `securityops_test`; Frontend- und Docker-Build. Gehosteter Lauf erfolgreich; regelmäßige Sicherheitsprüfungen bleiben offen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
2. **Produktionshärtung:** Frontend nicht über den Vite-Entwicklungsserver ausliefern, TLS/Reverse Proxy und Security-Header dokumentieren, Secrets ohne Standardwerte, gemeinsames Rate-Limit für mehrere Instanzen, SCA/SAST und Wiederherstellung praktisch testen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
3. **Zugriffsgrenzen und Audit:** Rollenrechte mit Regressionstests absichern; vor operativen Daten objektbezogene Autorisierung einführen; Grenzen der Audit-Unveränderbarkeit und Aufbewahrung festlegen.
4. **Datenbankverträglichkeit:** Migrationen gegen PostgreSQL validieren; SQLite bleibt für schnelle isolierte API-Tests, ersetzt aber keine Integrationstests.

### P1 – Kunden und Objekte

1. Kundenverwaltung fachlich prüfen und Vertrags-/Dokumentzuordnung planen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)).
2. Objektverwaltung [#2](https://github.com/Xonni-star/securityops-python/issues/2) gegen PostgreSQL-CI und fachliche Akzeptanzkriterien abschließen; anschließend Objektdaten und Zuweisungen als Grundlage für operative Module nutzen.

### P2 – Personal und Einsatzbetrieb

1. Personal, Qualifikationen und sensible Personalzugriffe ([#5](https://github.com/Xonni-star/securityops-python/issues/5)).
2. Dienstplanung mit Qualifikations-, Verfügbarkeits-, Ruhezeit- und Doppelbelegungsprüfungen ([#10](https://github.com/Xonni-star/securityops-python/issues/10)).
3. Arbeitszeitbuchungen mit begründeten, genehmigten Korrekturen und unverändertem Original ([#4](https://github.com/Xonni-star/securityops-python/issues/4)).
4. OWKS auf Objekte und Personal aufbauen; eindeutige Kontrollereignisse, QR/NFC und idempotente spätere Offline-Synchronisierung ([#3](https://github.com/Xonni-star/securityops-python/issues/3)).

### P3 – Dokumente, Verträge und Abrechnung

1. Sichere Dokumentenablage mit Zugriffskontrolle, Versionen und Ablaufüberwachung ([#8](https://github.com/Xonni-star/securityops-python/issues/8)).
2. Verträge und Abrechnung auf freigegebenen, nicht doppelt verrechneten Leistungsnachweisen aufbauen ([#7](https://github.com/Xonni-star/securityops-python/issues/7)).
3. Exporte erst nach fachlich verifizierter Spezifikation als DATEV-kompatibel bezeichnen; Steuer-/Rechtskonformität erfordert externe fachliche Prüfung.

### P4 – Betriebsreife

1. Dashboard ausschließlich aus echten Fachdaten speisen.
2. E2E-, Berechtigungs-, PostgreSQL-, Sicherheits- und Wiederherstellungstests erweitern.
3. Produktionsdeployment, Monitoring, Backup/Restore, Datenschutz- und Betriebsabnahme dokumentieren ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).

## Abhängigkeiten und Regeln

- Objekte bauen auf Kunden auf; Planung, OWKS und Dokumentzuordnungen bauen auf Objekten und Personal auf.
- Zeit- und Abrechnungsdaten werden nicht still überschrieben. Korrekturen müssen begründet, freigegeben und historisiert werden.
- Datenbankschemaänderungen erhalten jeweils eine Alembic-Migration.
- Kein Modul gilt als abgeschlossen, bevor Backend, Migration, API, serverseitige Rechte, UI, Tests und Dokumentation gemeinsam geprüft wurden.
- Alle Prioritäten sind technische Reihenfolge, keine Rechts- oder Steuerfreigabe. Arbeitszeit-, Datenschutz- und Abrechnungsregeln sind vor Produktiveinsatz fachlich zu bestätigen.
