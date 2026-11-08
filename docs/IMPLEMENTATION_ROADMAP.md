# SecurityOps – Implementierungs-Roadmap

Diese Roadmap beschreibt `main` nach dem Merge von PR #16 sowie den aktuellen Arbeitsstand im Branch `feature/personnel-management`. Ein Issue bleibt offen, bis Code, Migrationen, Berechtigungsprüfungen, Tests, Dokumentation und CI vollständig geprüft sind. Der Funktionsumfang ist nicht produktionsreif.

## Statusübersicht

| Bereich | Status | Beleg / nächste Arbeit |
|---|---|---|
| Einzelmandanten-Grundgerüst | Teilweise | FastAPI, React/TypeScript, PostgreSQL, Alembic und Compose sind vorhanden; keine Mandantenstrukturen. |
| Anmeldung und Rollen | Teilweise | Argon2id, serverseitige Sitzungen, CSRF, RBAC und Admin-Bootstrap vorhanden. MFA, Passwortzurücksetzung und Sitzungsverwaltung fehlen. Objektbezogene Rechte sind im aktuellen Branch ergänzt. |
| Kunden | Teilweise umgesetzt | Backend/API/Migration, filter- und sortierbare Liste, Details, Anschriften, Ansprechpartner, Archivierung/Reaktivierung und Historie sind implementiert; Migration 0004 und Backendtests bestehen in gehosteter PostgreSQL-CI. Vertrags-/Dokumentzuordnung fehlt ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | In `main` umgesetzt; Abnahme offen | Backend/API/UI und Migrationen 0005–0007; PR #16 gemergt und CI erfolgreich. Akzeptanzkriterien von Issue #2 sind noch formal zu bestätigen ([#2](https://github.com/Xonni-star/securityops-python/issues/2)). |
| Personal und Qualifikationen | Teilweise umgesetzt, Feature-Branch | Migration 0008, Personalakten, Qualifikationen/Ablaufübersicht, Abwesenheiten, sensible Daten, Historie, API, Berechtigungen, UI und lokale Tests vorhanden. PostgreSQL-/Docker-CI, Dokumentuploads und Objektzuweisungsintegration fehlen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)). |
| Dienstplanung | Nicht implementiert | Schichten, Besetzung, Konflikt- und Qualifikationsprüfung fehlen ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | Nicht implementiert | Nachvollziehbare Buchungen, Korrekturfreigaben und Export fehlen ([#4](https://github.com/Xonni-star/securityops-python/issues/4)). |
| OWKS | Nicht implementiert | Kontrollpunkte, QR/NFC, Rundgänge und Offline-Synchronisierung fehlen ([#3](https://github.com/Xonni-star/securityops-python/issues/3)). |
| Dokumente und Verträge | Nicht implementiert | Geschützte Ablage, Berechtigungen und Versionierung fehlen ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert | Vertragsbasierte, freigegebene und nicht doppelt abgerechnete Leistungen fehlen ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| CI und Datenbankqualität | Teilweise umgesetzt | GitHub Actions definiert Python-Lint/Format, Backendtests, PostgreSQL-Migrationen, Frontend-Build und Docker-Image-Builds. Der aktuelle Branch wurde noch nicht in CI geprüft; SCA/SAST und weitere Produktionshärtung bleiben offen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |

## Priorisierte Umsetzung

### P0 – Stabilisierung und Sicherheitsgrundlagen

1. **CI und PostgreSQL-Integration:** Den aktuellen Feature-Branch auf einer kurzlebigen Datenbank `securityops_test`, mit Frontend- und Docker-Build prüfen; lokale Offline-SQL-Generierung ersetzt diese Integrationsprüfung nicht ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
2. **Produktionshärtung:** Frontend nicht über den Vite-Entwicklungsserver ausliefern, TLS/Reverse Proxy und Security-Header dokumentieren, Secrets ohne Standardwerte, gemeinsames Rate-Limit für mehrere Instanzen, SCA/SAST und Wiederherstellung praktisch testen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
3. **Zugriffsgrenzen und Audit:** Sensible Personalberechtigungen und Historien-/Audit-Trennung in PostgreSQL-CI bestätigen; Grenzen der Audit-Unveränderbarkeit und Aufbewahrung festlegen.
4. **Datenbankverträglichkeit:** Migrationen gegen PostgreSQL validieren; SQLite bleibt für schnelle isolierte API-Tests, ersetzt aber keine Integrationstests.

### P1 – Kunden und Objekte

1. Kundenverwaltung fachlich prüfen und Vertrags-/Dokumentzuordnung planen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)).
2. Akzeptanzkriterien von Issue #2 nach dem Merge von PR #16 formal bewerten; Issue bis zur bestätigten Abnahme offen halten.

### P2 – Personal und Einsatzbetrieb

1. Personal-Branch gegen Migration, PostgreSQL, Docker und CI prüfen; Abnahme von Issue #5 erst nach Review. Mitarbeiterakten und bestehende Objektzuweisungen nachvollziehbar verknüpfen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)).
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
