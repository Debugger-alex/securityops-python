# Priorisierte Implementierungs-Roadmap

Diese Roadmap basiert auf dem tatsächlich gemergten `main`-Stand vom 09.11.2026 (SHA `3deebd16e368733f9595cd39f7e38b6354c1a88d`) und der aktuellen GitHub-Abfrage. Statusdetails stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Priorität folgt Sicherheits- und Datenabhängigkeiten, nicht der Nummer offener Issues.

## Prioritäten

### P0 – Betriebs- und Sicherheitsrisiken vor realen Daten schließen

1. Issue #9: vorhandenes Produktions-Compose, TLS/Reverse Proxy, sichere Header/Cookies, Secrets, getrennte Datenbankrollen, Redis-Rate-Limiting, Monitoring/Alerting und Release-Migrationen für die Zielumgebung konfigurieren, testen und betreiben.
2. Verschlüsselte Backups mit getrenntem Ziel, Aufbewahrungs-/Löschregeln, dokumentiertem Wiederanlaufplan und regelmäßigen Betreiber-Restoreübungen einrichten; vorhandene Werkzeuge und der CI-Test sind kein Betriebsnachweis.
3. Authentifizierung mit MFA, sicherer Passwortwiederherstellung und aktiver Sitzungsübersicht fachlich definieren und umsetzen.
4. Sensible Daten-/Objektbereiche, Uploads, Auditgrenzen und Datenschutz unabhängig prüfen. Der derzeitige Upload hat keinen Malware-Scan; Hashing ist keine Verschlüsselung.
5. Security-/Dependency-Scanbefunde triagieren und einen Incident-Prozess mit Verantwortlichkeiten/Alarmierungsweg festlegen.

PR #28 ist gemergt und enthält Nginx-Auslieferung, einen nicht privilegierten API-Container, Redis-Rate-Limiting, getrennte Migrationen, verschlüsselte Backups/Restore und Security-Scanning. Issue #9 bleibt offen. Diese Bausteine und CI-Restoreläufe ersetzen weder eine Umgebungskonfiguration noch regelmäßige produktive Restoreübungen, Monitoring, Incident-Abläufe oder eine Betriebsfreigabe.

### P1 – Abnahme und Bestand konsolidieren

1. Issue #10: Dienstplanung fachlich abnehmen. PR #26 ist gemergt und ergänzt wöchentliche Verfügbarkeitsfenster, befristete Dienstwünsche/Sperrzeiten und nachvollziehbare Schichtvertretungen. Issue #10 bleibt offen; die Konflikt-/Ruhezeitprüfung ist keine arbeitsrechtliche Freigabe.

### P2 – Fachliche Ausbau- und Abnahmeaufgaben

1. OWKS ist in `main` (PR #23, Migration `0014`); Issue #3 ist geschlossen. Fachlich weiterhin prüfen: statische Kennungen sind keine physischen Präsenznachweise, und Uploads besitzen keinen Malware-Scan.
2. Dokumenten-/Vertragsfunktionen sind in `main` (PR #24, Migration `0015`). Issue #8 ist laut aktueller GitHub-Abfrage offen; Vertragsregeln, Dateizugriff und fachliche Akzeptanz sind vor Erledigung konkret abzugleichen. Nicht gescannte Uploads dürfen nicht als malwarefrei gelten.
3. Issue #7: PR #27 schlägt Rechnungswesen mit konfigurierbaren Preisen/Steuerwerten, Rechnungsentwürfen, Freigabe, unveränderlichen Snapshots, Korrekturbelegen, Zahlungen/Mahnstatus, PDF und Export `securityops-accounting-v1` vor. PR ist offen und basiert aktuell direkt auf `main`; Migration `0017_billing` folgt auf den gemergten Main-Head `0016_scheduling_availability`. Die frühere PR-Stapelabhängigkeit zu #26 ist durch dessen Merge aufgehoben. Preise/Steuersätze bleiben Konfigurationen, keine steuerliche oder buchhalterische Abnahme ist nachgewiesen.

### P3 – Betriebsqualität und vollständiger Nachweis

1. E2E-, Berechtigungs-, Race-/PostgreSQL-, Upload-/Malware-, Last- und Wiederherstellungstests erweitern.
2. Datenschutz-/Aufbewahrungsprozess, Auditintegrität, Incident-/Monitoringkonzept und reale Betriebsabnahme belegen.
3. Dashboard erst aus tatsächlichen freigegebenen Fachkennzahlen erweitern.

## Bestätigte GitHub-Lage

- In `main`: Identity, Kunden, Objekte, Personal/Qualifikationen, Dienstplanung einschließlich Verfügbarkeiten/Vertretungen, Zeiterfassung, OWKS und Dokumente/Verträge (Migrationen `0001`–`0016`); PRs #23, #24, #26, #28 und #29 sind gemergt.
- Offen sind PR #25 (Dokumentation) und #27 (Rechnungswesen). PR #27s zuletzt geprüfter Head `a6a3385` hatte erfolgreiche Backend/PostgreSQL/Migrations-, Frontend-, Docker-, Restore- und Security-Checks.
- PR #27 basiert direkt auf dem aktuellen `main`; Migration `0017_billing` folgt auf `0016_scheduling_availability`. Es gibt keine offene PR-Stapelabhängigkeit zu #26.
- Issues #2–#6 sind geschlossen; #7–#10 sind laut frischer GitHub-Abfrage offen. Issue #8 bleibt trotz PR #24 offen; Issue #9 bleibt trotz PR #28 offen; Issue #10 bleibt trotz PR #26 offen. Offene Issues sind keine Aussage, dass die gemergte Funktion nicht vorhanden ist, und werden hier nicht geschlossen.

## Abhängigkeiten und Abschlusskriterien

- Objekte bauen auf Kunden auf; Personalakten verknüpfen Benutzerkonten; Dienstplanung benötigt Personal/Qualifikationen, Objekte, Zuweisungen und Abwesenheiten.
- Zeiterfassung hängt an Personal, Objekten und optional veröffentlichten Schichten. OWKS benötigt Objekt-/Personalidentitäten sowie nachvollziehbare Zeit-/Kontrollereignisse. Dokumenten-/Vertragsfunktionen nutzen Kunden, Objekte und geschützte Dokumentauslieferung. Abrechnung muss nach freigegebenen Leistungsnachweisen und bestätigter Vertrags-/Tariflogik kommen.
- Jede DB-Erweiterung erhält eine Alembic-Migration und passende Schema-, API-, Recht-, UI- und Integrationstests.
- „Implementiert“, „CI-grün“, „fachlich abgenommen“ und „produktiv freigegeben“ sind unterschiedliche Zustände.
- Geld-, Arbeitszeit-, Datenschutz-, Aufbewahrungs-, Steuer- und Rechtsregeln müssen vor entsprechender Produktbehauptung fachlich bestätigt werden.
