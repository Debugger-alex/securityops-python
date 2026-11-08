# Priorisierte Implementierungs-Roadmap

Diese Roadmap basiert auf dem tatsächlich gemergten `main`-Stand vom 08.11.2026 (SHA `6c7679a646d30da0504d8990fefeefa351a29bfe`) und der aktuellen GitHub-Abfrage. Statusdetails stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Priorität folgt Sicherheits- und Datenabhängigkeiten, nicht der Nummer offener Issues.

## Prioritäten

### P0 – Betriebs- und Sicherheitsrisiken vor realen Daten schließen

1. Issue #9: Produktionsumgebung, TLS/Reverse Proxy, sichere Header/Cookies, Secrets, getrennte Datenbankrollen, gemeinsames Rate-Limiting, Monitoring/Alerting sowie kontrollierte Migrationen planen und testen.
2. Backup/Restore mit Verschlüsselung, getesteter Wiederherstellung, Aufbewahrungs-/Löschregeln und Wiederanlaufplan einführen.
3. Authentifizierung mit MFA, sicherer Passwortwiederherstellung und aktiver Sitzungsübersicht fachlich definieren und umsetzen.
4. Sensible Daten-/Objektbereiche, Uploads, Auditgrenzen und Datenschutz unabhängig prüfen. Der derzeitige Upload hat keinen Malware-Scan; Hashing ist keine Verschlüsselung.
5. Security-/Dependency-Scanning und Incident-Prozess ergänzen, sobald Pflege/Alarmierungsweg festgelegt sind.

### P1 – Abnahme und Bestand konsolidieren

1. Issue #10: Dienstplanung fachlich abnehmen. Die vorhandene Konflikt-/Ruhezeitprüfung ist keine arbeitsrechtliche Freigabe und bildet keine individuellen, wiederkehrenden Verfügbarkeitsfenster ab.

### P2 – Fachliche Ausbau- und Abnahmeaufgaben

1. OWKS ist in `main` (PR #23, Migration `0014`); Issue #3 ist geschlossen. Fachlich weiterhin prüfen: statische Kennungen sind keine physischen Präsenznachweise, und Uploads besitzen keinen Malware-Scan.
2. Dokumenten-/Vertragsfunktionen sind in `main` (PR #24, Migration `0015`). Issue #8 ist laut aktueller GitHub-Abfrage offen; Vertragsregeln, Dateizugriff und fachliche Akzeptanz sind vor Erledigung konkret abzugleichen.
3. Issue #7: Rechnungswesen erst auf fachlich bestätigten Verträgen und freigegebenen, nachvollziehbaren Leistungsnachweisen aufbauen. Steuer-/Buchhaltungsprüfung vor Exportbezeichnungen wie „DATEV-kompatibel“.

### P3 – Betriebsqualität und vollständiger Nachweis

1. E2E-, Berechtigungs-, Race-/PostgreSQL-, Upload-/Malware-, Last- und Wiederherstellungstests erweitern.
2. Datenschutz-/Aufbewahrungsprozess, Auditintegrität, Incident-/Monitoringkonzept und reale Betriebsabnahme belegen.
3. Dashboard erst aus tatsächlichen freigegebenen Fachkennzahlen erweitern.

## Bestätigte GitHub-Lage

- In `main`: Identity, Kunden, Objekte, Personal/Qualifikationen, Dienstplanung, Zeiterfassung, OWKS und Dokumente/Verträge (Migrationen `0001`–`0015`).
- PR #23/#24 sind gemergt. PR #25 ist offen und dokumentationsbezogen; sein aktualisierter CI-Stand wird nach Push geprüft.
- Issues #2–#6 sind geschlossen. #7–#10 sind laut frischer GitHub-Abfrage offen; insbesondere Issue #8 aktuell nicht als geschlossen dokumentieren.

## Abhängigkeiten und Abschlusskriterien

- Objekte bauen auf Kunden auf; Personalakten verknüpfen Benutzerkonten; Dienstplanung benötigt Personal/Qualifikationen, Objekte, Zuweisungen und Abwesenheiten.
- Zeiterfassung hängt an Personal, Objekten und optional veröffentlichten Schichten. OWKS benötigt Objekt-/Personalidentitäten sowie nachvollziehbare Zeit-/Kontrollereignisse. Dokumenten-/Vertragsfunktionen nutzen Kunden, Objekte und geschützte Dokumentauslieferung. Abrechnung muss nach freigegebenen Leistungsnachweisen und bestätigter Vertrags-/Tariflogik kommen.
- Jede DB-Erweiterung erhält eine Alembic-Migration und passende Schema-, API-, Recht-, UI- und Integrationstests.
- „Implementiert“, „CI-grün“, „fachlich abgenommen“ und „produktiv freigegeben“ sind unterschiedliche Zustände.
- Geld-, Arbeitszeit-, Datenschutz-, Aufbewahrungs-, Steuer- und Rechtsregeln müssen vor entsprechender Produktbehauptung fachlich bestätigt werden.
