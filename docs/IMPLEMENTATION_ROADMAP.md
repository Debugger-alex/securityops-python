# Priorisierte Implementierungs-Roadmap

Diese Roadmap basiert auf dem tatsächlich gemergten `main`-Stand vom 08.11.2026 (SHA `5f3530463e9531c1f825f43ae4c6a6e60b9974e3`) und der aktuellen GitHub-Abfrage. Statusdetails stehen in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Priorität folgt Sicherheits- und Datenabhängigkeiten, nicht der Nummer offener Issues.

## Prioritäten

### P0 – Betriebs- und Sicherheitsrisiken vor realen Daten schließen

1. Issue #9: Produktionsumgebung, TLS/Reverse Proxy, sichere Header/Cookies, Secrets, getrennte Datenbankrollen, gemeinsames Rate-Limiting, Monitoring/Alerting sowie kontrollierte Migrationen planen und testen.
2. Backup/Restore mit Verschlüsselung, getesteter Wiederherstellung, Aufbewahrungs-/Löschregeln und Wiederanlaufplan einführen.
3. Authentifizierung mit MFA, sicherer Passwortwiederherstellung und aktiver Sitzungsübersicht fachlich definieren und umsetzen.
4. Sensible Daten-/Objektbereiche, Uploads, Auditgrenzen und Datenschutz unabhängig prüfen. Der derzeitige Upload hat keinen Malware-Scan; Hashing ist keine Verschlüsselung.
5. Security-/Dependency-Scanning und Incident-Prozess ergänzen, sobald Pflege/Alarmierungsweg festgelegt sind.

### P1 – Abnahme und Bestand konsolidieren

1. Issue #2: Objektverwaltung anhand der verbliebenen Akzeptanzkriterien formal abnehmen; Implementation ist bereits in `main`, Issue offen.
2. Issue #10: Dienstplanung fachlich abnehmen. Die vorhandene Konflikt-/Ruhezeitprüfung ist keine arbeitsrechtliche Freigabe und bildet keine individuellen, wiederkehrenden Verfügbarkeitsfenster ab.
3. Issue #4: Zeiterfassung gegen Fachanforderungen abnehmen. Korrekturen und Periodensperren sind vorhanden; Geldbeträge/Payroll bleiben mangels bestätigter Basis und Rundungsregeln außen vor.

### P2 – Offene Fachmodule in Abhängigkeitsreihenfolge

1. PR #23 / Issue #3: OWKS auf Objekte, Personal und bestehende Rechte aufsetzen. Der PR ist offen, Migration `0014_owks_wachbuch` ist nicht in `main`; Review und fachliche Abnahme fehlen trotz grüner CI.
2. PR #24 / Issue #8: Dokumente/Verträge baut auf PR #23 auf; Migration `0015_documents_contracts` ist nicht in `main`. Den Basiswechsel, Uploadschutz, Berechtigungen und Vertragsregeln getrennt prüfen und abnehmen.
3. Issue #7: Rechnungswesen erst auf bestätigten Verträgen und freigegebenen, nachvollziehbaren Leistungsnachweisen aufbauen. Fachliche Buchhaltungs-/Steuerprüfung vor Exportbezeichnungen wie „DATEV-kompatibel“.

### P3 – Betriebsqualität und vollständiger Nachweis

1. E2E-, Berechtigungs-, Race-/PostgreSQL-, Upload-/Malware-, Last- und Wiederherstellungstests erweitern.
2. Datenschutz-/Aufbewahrungsprozess, Auditintegrität, Incident-/Monitoringkonzept und reale Betriebsabnahme belegen.
3. Dashboard erst aus tatsächlichen freigegebenen Fachkennzahlen erweitern.

## Bestätigte GitHub-Lage

- In `main`: Identity, Kunden, Objekte, Personal/Qualifikationen, Dienstplanung und Zeiterfassung mit Zuschlagszeit-Snapshots (Migrationen `0001`–`0013`).
- Offen, nicht in `main`: PR #23 OWKS gegen `main`, PR #24 Dokumente/Verträge als Folgebranch von #23. Beide hatten am Prüfzeitpunkt grüne Backend/PostgreSQL/Migrationen-, Frontend- und Docker-CI. Dies ersetzt weder Review noch fachliche Abnahme.
- PR #20/#22 gemergt; PR #21 geschlossen, da relevante Commits in `main` sind. Issues #5/#6 geschlossen; #2/#4/#10 trotz Funktion offen bis Abnahme.
- Weitere offene Issues: #3, #7, #8 und #9. Nicht schließen oder als erledigt darstellen, ohne die fachlichen Kriterien tatsächlich zu prüfen.

## Abhängigkeiten und Abschlusskriterien

- Objekte bauen auf Kunden auf; Personalakten verknüpfen Benutzerkonten; Dienstplanung benötigt Personal/Qualifikationen, Objekte, Zuweisungen und Abwesenheiten.
- Zeiterfassung hängt an Personal, Objekten und optional veröffentlichten Schichten. OWKS benötigt Objekt-/Personalidentitäten sowie nachvollziehbare Zeit-/Kontrollereignisse. Dokumenten-/Vertragsfunktionen nutzen Kunden, Objekte und geschützte Dokumentauslieferung. Abrechnung muss nach freigegebenen Leistungsnachweisen und bestätigter Vertrags-/Tariflogik kommen.
- Jede DB-Erweiterung erhält eine Alembic-Migration und passende Schema-, API-, Recht-, UI- und Integrationstests.
- „Implementiert“, „CI-grün“, „fachlich abgenommen“ und „produktiv freigegeben“ sind unterschiedliche Zustände.
- Geld-, Arbeitszeit-, Datenschutz-, Aufbewahrungs-, Steuer- und Rechtsregeln müssen vor entsprechender Produktbehauptung fachlich bestätigt werden.
