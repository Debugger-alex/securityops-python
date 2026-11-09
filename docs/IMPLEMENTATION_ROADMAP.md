# Priorisierte Implementierungs-Roadmap

Diese Roadmap basiert auf dem tatsächlich gemergten `main`-Stand vom 09.11.2026 (SHA `ac31bae99ee9f70026057483f303e86c69159e38`) und der aktuellen GitHub-Abfrage. Statusdetails stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Priorität folgt Sicherheits- und Datenabhängigkeiten, nicht der Nummer offener Issues.

## Prioritäten

### P0 – Betriebs- und Sicherheitsrisiken vor realen Daten schließen

1. Issue #9: vorhandenes Produktions-Compose, TLS/Reverse Proxy, sichere Header/Cookies, Secrets, getrennte Datenbankrollen, Redis-Rate-Limiting, Monitoring/Alerting und Release-Migrationen für die Zielumgebung konfigurieren, testen und betreiben.
2. Verschlüsselte Backups mit getrenntem Ziel, Aufbewahrungs-/Löschregeln, dokumentiertem Wiederanlaufplan und regelmäßigen Betreiber-Restoreübungen einrichten; vorhandene Werkzeuge und der CI-Test sind kein Betriebsnachweis.
3. Optionales TOTP-MFA, Recovery-Codes, Sitzungsliste/-widerruf und administrativen Passwortreset aus PR #31 unabhängig sicherheitsprüfen. Ein nutzerinitiierter E-Mail-Passwortreset ist mangels Zustellprovider nicht implementiert; dessen Bedarf und Ablauf sind fachlich zu entscheiden.
4. Sensible Daten-/Objektbereiche, Uploads, Auditgrenzen und Datenschutz unabhängig prüfen. ClamAV scannt neue Uploads fail-closed; dies ersetzt weder unabhängige Prüfung noch rückwirkenden Bestandsscan. Hashing ist keine Verschlüsselung.
5. Security-/Dependency-Scanbefunde triagieren und einen Incident-Prozess mit Verantwortlichkeiten/Alarmierungsweg festlegen.

PR #28 ist gemergt und enthält Nginx-Auslieferung, einen nicht privilegierten API-Container, Redis-Rate-Limiting, getrennte Migrationen, verschlüsselte Backups/Restore und Security-Scanning. PR #31 ist gemergt und ergänzt TOTP-MFA sowie Sitzungsverwaltung. Issue #9 bleibt offen. Diese Bausteine und CI-Restoreläufe ersetzen weder eine Umgebungskonfiguration noch regelmäßige produktive Restoreübungen, Monitoring, Incident-Abläufe oder eine Betriebsfreigabe.

PR #33 hat die Malwareprüfung neuer Dokument-/Vertragsdateien, Dokumentversionen, OWKS-Anhänge und Personal-Qualifikationsdateien integriert. Bereits gespeicherte Dateien werden nicht rückwirkend geprüft. PR #34 hat mit Migration `0019_tasks` einen generischen Aufgaben-Kern integriert. Er ist nicht automatisch mit Fachmodulen verbunden und enthält keine Anhänge, Zustellbenachrichtigungen, Hintergrundjobs oder Eskalationen; diese Ausbaupunkte erfordern eine separat abgestimmte Ereignis-/Integrationssemantik.

PR #35 ist inzwischen gemergt und ergänzt mit `0020_notifications` In-App-Benachrichtigungen für Aufgaben-Zuweisungen und Statuswechsel. Outbox- und Inbox-Einträge werden transaktional gespeichert, aber es gibt keinen Worker, Retry-Verarbeitung, E-Mail-/Push-Versand oder Modulereignisse außerhalb der Aufgaben. Der Betrieb eines Workers und zusätzliche Kanäle bleiben Folgearbeit, keine bereits verfügbare Funktion.

PR #36 ist mit Migration `0021_key_management` gemergt und ergänzt ein objektgebundenes Schlüsselregister mit Ausgabe, Rückgabe, Verlust-/Defektmeldung, Inventur und append-only Bewegungsverlauf. Ausgabe erfordert eine aktive, dem Objekt zugewiesene Person und eine digitale Quittierung. Die Quittierung ist keine qualifizierte elektronische Signatur oder ein Nachweis physischer Verwahrung; bestehende Freitext-Zutrittsangaben werden nicht als Schlüsselbestand migriert. Betriebsprozesse für tatsächliche Schlüsselübergabe und physische Sicherung bleiben erforderlich.

PR #37 ist mit Migration `0022_incident_management` gemergt und ergänzt objektbezogene Vorfälle/Beschwerden, Maßnahmen, Fristen, Statusübergänge und Abschlussbericht. Separate Sensitivitätsrechte schützen Hergang, Abschlussbericht, Beteiligte/Zeugen und Dateizugriff; alle Endpunkte prüfen zusätzlich Objekt-Scope. Vorfallanhänge werden fail-closed mit ClamAV geprüft, privat gespeichert und nur autorisiert abgerufen; vorhandene Dateien werden nicht rückwirkend geprüft. Maßnahmen, Fristen und Eskalationen bleiben manuell: es gibt keine automatische Aufgaben-/Benachrichtigungsintegration, Fristerinnerung oder Eskalationsregel.

### P1 – Abnahme und Bestand konsolidieren

1. Issue #10: Dienstplanung fachlich abnehmen. PR #26 ist gemergt und ergänzt wöchentliche Verfügbarkeitsfenster, befristete Dienstwünsche/Sperrzeiten und nachvollziehbare Schichtvertretungen. Issue #10 bleibt offen; die Konflikt-/Ruhezeitprüfung ist keine arbeitsrechtliche Freigabe.

### P2 – Fachliche Ausbau- und Abnahmeaufgaben

1. OWKS ist in `main` (PR #23, Migration `0014`); Issue #3 ist geschlossen. Fachlich weiterhin prüfen: statische Kennungen sind keine physischen Präsenznachweise. Neue Anhänge werden durch PR #33 fail-closed gescannt; vorhandene Dateien nicht rückwirkend.
2. Dokumenten-/Vertragsfunktionen sind in `main` (PR #24, Migration `0015`). Issue #8 ist laut aktueller GitHub-Abfrage offen; Vertragsregeln, Dateizugriff und fachliche Akzeptanz sind vor Erledigung konkret abzugleichen. Neue Uploads werden fail-closed geprüft, der Bestand nicht rückwirkend.
3. Issue #7: das mit PR #27 gemergte Rechnungswesen fachlich abnehmen: Preise/Steuerwerte, Rechnungssnapshots, Korrekturbelege, Zahlungen/Mahnstatus, PDF und Export `securityops-accounting-v1`. Migration `0017_billing` ist in `main`; Preise/Steuersätze bleiben konfigurierte Eingaben, keine steuerliche oder buchhalterische Abnahme ist nachgewiesen. Issue #7 bleibt offen.

### P3 – Betriebsqualität und vollständiger Nachweis

1. E2E-, Berechtigungs-, Race-/PostgreSQL-, Upload-/Malware-, Last- und Wiederherstellungstests erweitern.
2. Datenschutz-/Aufbewahrungsprozess, Auditintegrität, Incident-/Monitoringkonzept und reale Betriebsabnahme belegen.
3. Dashboard erst aus tatsächlichen freigegebenen Fachkennzahlen erweitern.

## Bestätigte GitHub-Lage

- In `main`: Identity inklusive MFA/Sitzungsverwaltung, Kunden, Objekte, Personal/Qualifikationen, Dienstplanung einschließlich Verfügbarkeiten/Vertretungen, Zeiterfassung, OWKS, Dokumente/Verträge, Rechnungswesen, Upload-Scan, Aufgaben, In-App-Aufgabenbenachrichtigungen, Schlüssel- und Vorfallmanagement (Migrationen `0001`–`0022`); PRs #23, #24, #26, #27, #28, #29, #31, #33, #34, #35, #36 und #37 sind gemergt.
- PR #33 ergänzt fail-closed ClamAV-Scan neuer relevanter Uploads; PR #34 ergänzt den generischen Aufgaben-Kern, der nicht automatisch mit Fachmodulen gekoppelt ist. PR #35 ergänzt transaktionale In-App-Benachrichtigungen für Aufgabenereignisse; die Outbox wird nicht von einem Worker verarbeitet und es gibt keine Retries oder externe Kanäle.
- Offen ist nur PR #25 (Dokumentation); aktuelle CI-Ergebnisse sind pro PR-Head zu prüfen.
- Migration `0017_billing` folgt auf `0016_scheduling_availability`; `0018_identity_security` folgt auf `0017_billing`, `0019_tasks` auf `0018_identity_security`, `0020_notifications` auf `0019_tasks`, `0021_key_management` auf `0020_notifications` und `0022_incident_management` auf `0021_key_management`. Issues #7–#10 sind offen, #2–#6 geschlossen; PR #25 ist die einzige offene PR.
- Issues #2–#6 sind geschlossen; #7–#10 sind laut frischer GitHub-Abfrage offen. Issue #8 bleibt trotz PR #24 offen; Issue #9 trotz PR #28, Issue #10 trotz PR #26 und Issue #7 trotz PR #27. Offene Issues sind keine Aussage, dass die gemergte Funktion nicht vorhanden ist; keine Issue wurde durch diese Dokumentationsänderung geändert.

## Abhängigkeiten und Abschlusskriterien

- Objekte bauen auf Kunden auf; Personalakten verknüpfen Benutzerkonten; Dienstplanung benötigt Personal/Qualifikationen, Objekte, Zuweisungen und Abwesenheiten.
- Zeiterfassung hängt an Personal, Objekten und optional veröffentlichten Schichten. OWKS benötigt Objekt-/Personalidentitäten sowie nachvollziehbare Zeit-/Kontrollereignisse. Dokumenten-/Vertragsfunktionen nutzen Kunden, Objekte und geschützte Dokumentauslieferung. Die Abrechnungsfunktion ist in `main`, ihre fachliche Vertrags-/Tarif-/Steuerlogik muss jedoch unabhängig bestätigt werden.
- Jede DB-Erweiterung erhält eine Alembic-Migration und passende Schema-, API-, Recht-, UI- und Integrationstests.
- „Implementiert“, „CI-grün“, „fachlich abgenommen“ und „produktiv freigegeben“ sind unterschiedliche Zustände.
- Geld-, Arbeitszeit-, Datenschutz-, Aufbewahrungs-, Steuer- und Rechtsregeln müssen vor entsprechender Produktbehauptung fachlich bestätigt werden.
