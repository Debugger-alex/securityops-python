# SecurityOps – Implementierungs-Roadmap

Diese Roadmap beschreibt `main` auf Merge-Commit `d066d56b97fbd795be276b0414d6a88b8c779962` nach PR #19 und den isolierten Zeiterfassungs-Feature-Branch. PR #18: Backend/PostgreSQL, Frontend einschließlich Vitest und Docker CI grün; Issue #6 geschlossen. PR #19 (Dienstplanung) ist in `main`; Issue #10 bleibt bis zur fachlichen Abnahme offen. Issue #2 bleibt wegen ausstehender formaler Abnahme offen. Issue #4 wird ausschließlich im aktuellen Branch umgesetzt; lokale Prüfungen sind erfolgreich, PostgreSQL-CI und Review stehen noch aus. Ein Issue wird nicht ohne fachliche Abnahme geschlossen; Produktions-, Datenschutz- und Rechtsfreigaben sind hiervon getrennt.

## Statusübersicht

| Bereich | Status | Beleg / nächste Arbeit |
|---|---|---|
| Einzelmandanten-Grundgerüst | Teilweise | FastAPI, React/TypeScript, PostgreSQL, Alembic und Compose sind vorhanden; keine Mandantenstrukturen. |
| Anmeldung und Rollen | Teilweise | Argon2id, serverseitige Sitzungen, CSRF, RBAC und Admin-Bootstrap vorhanden. MFA, Passwortzurücksetzung und Sitzungsverwaltung fehlen. Objektbezogene Rechte sind im aktuellen Branch ergänzt. |
| Kunden | In `main` umgesetzt; Issue #6 geschlossen | PR #18 ergänzt Website, Vertragsstatus, Filter/Sortierung und berechtigungsgefilterte Objektzuordnungen; Backend/PostgreSQL, Frontend einschließlich Vitest und Docker CI grün. Vertrags- und Dokumentenmodule fehlen weiterhin ([#6](https://github.com/Xonni-star/securityops-python/issues/6)). |
| Objekte | In `main` umgesetzt; formale Abnahme offen | Backend/API/UI und Migrationen 0005–0007; PR #16 gemergt und CI erfolgreich. Issue #2 bleibt offen, bis die Akzeptanzkriterien formal abgenommen sind ([#2](https://github.com/Xonni-star/securityops-python/issues/2)). |
| Personal und Qualifikationen | In `main` umgesetzt | Migrationen 0008–0009, Personalakten, Qualifikationen, Abwesenheiten, sensible Daten, Historie, Objektzuweisungen und versionierte Qualifikationsdateien. PR #17 ist gemergt, CI erfolgreich; Issue #5 ist geschlossen. |
| Dienstplanung | In `main` umgesetzt; Abnahme offen | PR #19 enthält Scheduling-Kern mit UTC-Zeitpunkten, konfigurierbarer IANA-Zeitzone/Ruhezeit, PostgreSQL-Überlappungsschutz, Prüfungen, API/UI und Änderungshistorie. GitHub-CI für PostgreSQL, parallele Integrationstests, Frontend und Docker war erfolgreich; fachliche Issue-Abnahme steht aus ([#10](https://github.com/Xonni-star/securityops-python/issues/10)). |
| Zeiterfassung | Lokal umgesetzt; CI/Review ausstehend | Migration 0012, Buchungen/Segmente, Korrekturfreigaben, Rechte, Auswertungen, Fehlbuchungsübersicht und CSV. Lokale Backend-/Frontendtests, Lint/Format, Build und Offline-Up-/Downgrade erfolgreich; der PostgreSQL-spezifische Test ist mangels lokalem PostgreSQL übersprungen. PR und CI für Issue #4 stehen aus ([#4](https://github.com/Xonni-star/securityops-python/issues/4)). |
| OWKS | Nicht implementiert | Kontrollpunkte, QR/NFC, Rundgänge und Offline-Synchronisierung fehlen ([#3](https://github.com/Xonni-star/securityops-python/issues/3)). |
| Dokumente und Verträge | Nicht implementiert | Geschützte Ablage, Berechtigungen und Versionierung fehlen ([#8](https://github.com/Xonni-star/securityops-python/issues/8)). |
| Rechnungswesen | Nicht implementiert | Vertragsbasierte, freigegebene und nicht doppelt abgerechnete Leistungen fehlen ([#7](https://github.com/Xonni-star/securityops-python/issues/7)). |
| CI und Datenbankqualität | Teilweise umgesetzt | GitHub Actions definiert Python-Lint/Format, Backendtests, PostgreSQL-Migrationen, Frontend-Build und Docker-Image-Builds. Der aktuelle Stand braucht einen erneuten CI-Lauf; SCA/SAST und weitere Produktionshärtung bleiben offen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)). |

## Priorisierte Umsetzung

### P0 – Stabilisierung und Sicherheitsgrundlagen

1. **CI und PostgreSQL-Integration:** Den aktuellen Feature-Branch auf einer kurzlebigen Datenbank `securityops_test`, mit Frontend- und Docker-Build prüfen; lokale Offline-SQL-Generierung ersetzt diese Integrationsprüfung nicht ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
2. **Produktionshärtung:** Frontend nicht über den Vite-Entwicklungsserver ausliefern, TLS/Reverse Proxy und Security-Header dokumentieren, Secrets ohne Standardwerte, gemeinsames Rate-Limit für mehrere Instanzen, SCA/SAST und Wiederherstellung praktisch testen ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
3. **Zugriffsgrenzen und Audit:** Sensible Personalberechtigungen und Historien-/Audit-Trennung wurden für PR #17 in PostgreSQL-CI geprüft; Grenzen der Audit-Unveränderbarkeit und Aufbewahrung bleiben festzulegen.
4. **Datenbankverträglichkeit:** Migrationen gegen PostgreSQL validieren; SQLite bleibt für schnelle isolierte API-Tests, ersetzt aber keine Integrationstests.

### P1 – Kunden und Objekte

1. Vertrags-/Dokumentzuordnungen erst mit den noch nicht vorhandenen Modulen ergänzen; Issue #6 ist nach PR #18 geschlossen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)).
2. Akzeptanzkriterien von Issue #2 formal bewerten; Issue bis zur bestätigten Abnahme offen halten.

### P2 – Personal und Einsatzbetrieb

1. Personalverwaltung bei Bedarf nach der in `main` erfolgten Implementierung fachlich weiterentwickeln ([#5](https://github.com/Xonni-star/securityops-python/issues/5)).
2. Fachliche Abnahme der Dienstplanung und Issue #10 getrennt vom Zeiterfassungs-PR fortführen. Die Verfügbarkeit wird derzeit aus Beschäftigungszeitraum, Abwesenheiten und bestehenden Diensten abgeleitet; individuelle regelmäßige Wunsch-/Sperrzeiten sind nicht modelliert ([#10](https://github.com/Xonni-star/securityops-python/issues/10)).
3. Zeiterfassungs-Branch nach Push durch PostgreSQL-Migration, Docker-CI und Review absichern; Originalsegmente bleiben bei begründeten Korrekturen unverändert und die effektive Zeit wird versioniert. Issue #4 bis zur Abnahme offen halten ([#4](https://github.com/Xonni-star/securityops-python/issues/4)).
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
