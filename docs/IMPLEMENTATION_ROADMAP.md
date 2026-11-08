# Priorisierte Implementierungs-Roadmap

Diese Roadmap basiert auf dem tatsächlich gemergten `main`-Stand vom 08.11.2026 (SHA `6c7679a646d30da0504d8990fefeefa351a29bfe`) und der aktuellen GitHub-Abfrage. Statusdetails stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Priorität folgt Sicherheits- und Datenabhängigkeiten, nicht der Nummer offener Issues.

## Prioritäten

### P0 – Betriebs- und Sicherheitsrisiken vor realen Daten schließen

1. Issue #9: Produktionsumgebung, TLS/Reverse Proxy, sichere Header/Cookies, Secrets, getrennte Datenbankrollen, gemeinsames Rate-Limiting, Monitoring/Alerting sowie kontrollierte Migrationen planen und testen.
2. Backup/Restore mit Verschlüsselung, getesteter Wiederherstellung, Aufbewahrungs-/Löschregeln und Wiederanlaufplan einführen.
3. Authentifizierung mit MFA, sicherer Passwortwiederherstellung und aktiver Sitzungsübersicht fachlich definieren und umsetzen.
4. Sensible Daten-/Objektbereiche, Uploads, Auditgrenzen und Datenschutz unabhängig prüfen. Der derzeitige Upload hat keinen Malware-Scan; Hashing ist keine Verschlüsselung.
5. Security-/Dependency-Scanning und Incident-Prozess ergänzen, sobald Pflege/Alarmierungsweg festgelegt sind.

Der offene PR #28 (gegen `main`, Issue #9) schlägt Teile dieser Arbeiten vor: Nginx-Auslieferung, nicht privilegierten API-Container, Redis-Rate-Limiting, getrennte Migrationen sowie verschlüsselte Backups/Restore und Security-Scanning. Er ist nicht gemergt; im aktuellen CI ist der Restore-Job fehlgeschlagen, daher ist weder die Wiederherstellung noch eine Produktionsfreigabe nachgewiesen.

### P1 – Abnahme und Bestand konsolidieren

1. Issue #10: Dienstplanung fachlich abnehmen. PR #26 schlägt dazu wöchentliche Verfügbarkeitsfenster, befristete Dienstwünsche/Sperrzeiten und Schichtvertretungen vor; PR ist offen, gegen `main` (nicht Teil davon). Sein aktueller Head `7e15c71` hat grüne Backend/PostgreSQL/Migrations-, Frontend- und Docker-CI; frühere Checkfehler an einem vorherigen Head sind nicht der aktuelle Checkstatus. Die bestehende Konflikt-/Ruhezeitprüfung ist keine arbeitsrechtliche Freigabe.

### P2 – Fachliche Ausbau- und Abnahmeaufgaben

1. OWKS ist in `main` (PR #23, Migration `0014`); Issue #3 ist geschlossen. Fachlich weiterhin prüfen: statische Kennungen sind keine physischen Präsenznachweise, und Uploads besitzen keinen Malware-Scan.
2. Dokumenten-/Vertragsfunktionen sind in `main` (PR #24, Migration `0015`). Issue #8 ist laut aktueller GitHub-Abfrage offen; Vertragsregeln, Dateizugriff und fachliche Akzeptanz sind vor Erledigung konkret abzugleichen.
3. Issue #7: PR #27 schlägt Rechnungswesen mit konfigurierbaren Preisen/Steuerwerten, Rechnungsentwürfen, Freigabe, unveränderlichen Snapshots, Korrekturbelegen, Zahlungen/Mahnstatus, PDF und Export `securityops-accounting-v1` vor. PR ist offen, auf PR #26 gestapelt und nicht in `main`; seine Migration `0017_billing` folgt auf `0016_scheduling_availability`. Preise/Steuersätze bleiben Konfigurationen, keine steuerliche oder buchhalterische Abnahme ist nachgewiesen.

### P3 – Betriebsqualität und vollständiger Nachweis

1. E2E-, Berechtigungs-, Race-/PostgreSQL-, Upload-/Malware-, Last- und Wiederherstellungstests erweitern.
2. Datenschutz-/Aufbewahrungsprozess, Auditintegrität, Incident-/Monitoringkonzept und reale Betriebsabnahme belegen.
3. Dashboard erst aus tatsächlichen freigegebenen Fachkennzahlen erweitern.

## Bestätigte GitHub-Lage

- In `main`: Identity, Kunden, Objekte, Personal/Qualifikationen, Dienstplanung, Zeiterfassung, OWKS und Dokumente/Verträge (Migrationen `0001`–`0015`).
- PR #23/#24 sind gemergt. Offen sind PR #25 (Dokumentation; aktuelle Backend-CI scheitert im parallelen Dienstplan-Exclusion-Test), #26 (Dienstplanung; aktuelle CI grün), #27 (Rechnungswesen; auf #26 gestapelt, aktuelle CI grün) und #28 (Issue #9 Produktionshärtung; Restore-CI fehlgeschlagen).
- PR #26 basiert auf `main`/Revision `0015_documents_contracts`; PR #27 ist darauf gestapelt und ergänzt `0017_billing` nach `0016_scheduling_availability`. Bei Integration ist diese Abhängigkeit zu erhalten; für eine unabhängige Übernahme von #27 wären Basis und Migrationskette ausdrücklich anzupassen.
- Issues #2–#6 sind geschlossen; #7–#10 sind laut frischer GitHub-Abfrage offen. Issue #8 wird trotz PR #24 weiterhin als offen geführt. PR #28 ist Issue #9 zugeordnet, bleibt aber offen und ohne nachgewiesenen erfolgreichen Restore.

## Abhängigkeiten und Abschlusskriterien

- Objekte bauen auf Kunden auf; Personalakten verknüpfen Benutzerkonten; Dienstplanung benötigt Personal/Qualifikationen, Objekte, Zuweisungen und Abwesenheiten.
- Zeiterfassung hängt an Personal, Objekten und optional veröffentlichten Schichten. OWKS benötigt Objekt-/Personalidentitäten sowie nachvollziehbare Zeit-/Kontrollereignisse. Dokumenten-/Vertragsfunktionen nutzen Kunden, Objekte und geschützte Dokumentauslieferung. Abrechnung muss nach freigegebenen Leistungsnachweisen und bestätigter Vertrags-/Tariflogik kommen.
- Jede DB-Erweiterung erhält eine Alembic-Migration und passende Schema-, API-, Recht-, UI- und Integrationstests.
- „Implementiert“, „CI-grün“, „fachlich abgenommen“ und „produktiv freigegeben“ sind unterschiedliche Zustände.
- Geld-, Arbeitszeit-, Datenschutz-, Aufbewahrungs-, Steuer- und Rechtsregeln müssen vor entsprechender Produktbehauptung fachlich bestätigt werden.
