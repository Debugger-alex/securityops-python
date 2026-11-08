# Sicherheitsprüfung – Ist-Stand und offene Maßnahmen

## Charakter und Scope

Dies ist eine statische, dokumentarische Zusammenfassung sichtbarer Kontrollen im `main`-Code (`edad05f3b3029370a62b51a6508962f1dd156592`), keine unabhängige Sicherheitsprüfung, kein Penetrationstest und keine Zertifizierung. Es wurden für diese Dokumentationsarbeit keine Angriffe ausgeführt und keine realen Daten verwendet. OWKS, Dokumente/Verträge, Dienstplan-Verfügbarkeiten, Rechnungswesen, MFA/Sitzungsverwaltung und Produktionshärtung aus den gemergten PRs #23, #24, #26, #27, #28 und #31 sowie Objekt-Scope aus #29 sind im `main`-Befund eingerechnet.

## Befundübersicht

| Bereich | Status | Beleg / verbleibendes Risiko |
|---|---|---|
| Passwort- und Session-Schutz | Teilweise vorhanden | Argon2id, generische Loginfehler, gehashte opaque Session-/CSRF-Tokens, Idle-/Absolute-Timeout, optionales TOTP-MFA mit verschlüsseltem Secret, Replay-Schutz, gehashte einmalige Recovery-Codes, eigene Sitzungsliste/-widerruf und administrative Sitzungsverwaltung. Admin-Passwortreset setzt Passwortwechselpflicht und widerruft Sessions. Kein nutzerinitiierter E-Mail-Reset; keine unabhängige Sicherheitsabnahme. |
| CSRF / Cookies | Vorhanden, Umgebung abhängig | CSRF-Doppelübermittlung und HttpOnly/SameSite=Strict; Secure konfigurierbar, Compose default `true`. Lokale HTTP-Ausnahme darf nicht produktiv werden. |
| RBAC / Scoping | Serverseitig implementiert | Modulrechte, Admin-Zuweisungsschutz sowie Objekt- und Sensitivitätsgrenzen. Mitarbeiter-Objektzuweisungen berücksichtigen serverseitig den autorisierten Objektzugriff. Abdeckung muss in jeder neuen Route und allen Aggregaten erhalten bleiben; UI ist keine Schutzgrenze. |
| Rate-Limit | Implementiert, Betrieb abhängig | Login `5/minute` über SlowAPI und Client-IP; Redis wird in Produktion als geteilter Speicher verlangt und Readiness prüft Redis. Proxy-Vertrauen muss passend zur realen Netzwerktopologie konfiguriert und geprüft werden. |
| Audit | Teilweise | App-API erlaubt Lesen mit `audit.read`; schreibt Events für implementierte Abläufe. Kein DB-seitiger Append-only-Schutz/externes unveränderliches Archiv, keine vollständige Abdeckung aller Vorgänge. |
| Personal-/Objektdaten | Getrennte Endpunkte | Sensible Werte und Datei-/Abwesenheitsdaten haben gesonderte Rechte. Datenschutz, Verschlüsselung at rest und Aufbewahrung sind nicht vollständig nachgewiesen. |
| Uploads | Eingabeprüfung, aber kein Malware-Schutz | Qualifikationsnachweise und OWKS-Anhänge: PDF/PNG/JPEG, max. 10 MiB, in PostgreSQL (`BYTEA`). Dokumente: PDF/PNG/JPEG/DOCX/XLSX im privaten Dateispeicher, Standardgrenze 20 MiB. Typ-/Signaturprüfung, aber kein Malware-Scan, Quarantäne, KMS oder Anwendungsebene-Verschlüsselung. |
| OWKS-Protokoll | Teilweise geschützt | Migration 0014 ergänzt Append-only-Trigger gegen UPDATE/DELETE an Ereignissen, Statushistorien und Anhängen. Direkte privilegierte DB-Änderungen außerhalb der Triggerberechtigung, Backup/Restore und unabhängige Integritätsprüfung sind nicht nachgewiesen. |
| Dokumente / Verträge | Autorisierte API und privater lokaler Speicher | Dateiabruf erfolgt über Rechte-Endpunkte; private Verzeichnis-/Dateimodi. Malware-Scan, Verschlüsselung, externer geschützter Speicher und automatische Erinnerungszustellung fehlen. |
| Rechnungswesen | Rollen-/Audit-kontrollierte API und transaktionale Datenbankänderungen | Rechnungen speichern Kunden-/Eingabe-Snapshots; Korrekturen erzeugen Folgebelege statt Originalüberschreibung. Geldfelder sind `NUMERIC`/`Decimal`; Steuer-/Buchhaltungsregeln, Integrationen und fachliche Abnahme sind nicht unabhängig geprüft. Issue #7 bleibt offen. |
| Transport / Deployment | Teilweise umgesetzt, Umgebung abhängig | Produktions-Compose mit statischem Nginx-Frontend, Sicherheitsheadern, nicht privilegiertem API-Prozess und Secure-Cookie-Anforderung. TLS wird von einem separat zu betreibenden Reverse Proxy terminiert; dessen Konfiguration und produktiver Betrieb sind nicht nachgewiesen. |
| Abhängigkeiten / CI | Implementierte Automatisierung | Ruff, Backend, PostgreSQL-Migrationen, Frontend-Build/-Tests, Docker-Builds, Security-Analyse und Abhängigkeitsprüfung. CI-Erfolg ist kein unabhängiger Sicherheitsnachweis; Secret-Handling und produktive Updateprozesse bleiben zu prüfen. |
| Backup / Wiederherstellung | Werkzeuge und synthetischer CI-Test vorhanden | Verschlüsselte Datenbank-/Dokumentenbackups und isolierter PostgreSQL-17-Restoretest in CI. Es gibt keinen Beleg für einen produktiven Backupbestand, Betreiber-Restore-Drill, Aufbewahrung oder externes Backupziel. |
| Datenschutz / Incident | Nicht nachgewiesen | Kein vollständiger Lösch-/Aufbewahrungs-/Betroffenenprozess, keine Datenschutzfolgenprüfung oder Incident-Ablaufdokumentation für Produktion. |

## Frühere behobene Findings

In vorherigen Änderungen wurden eine unbeschränkte Administratorrollenvergabe über allgemeines `users.manage` begrenzt (`users.manage_admin`), Objektzugriff nach globalem Recht oder Zuweisung umgesetzt und sensible Zutrittsdaten aus allgemeinen Objektantworten getrennt. PR #29 schränkt Mitarbeiter-Objektzuweisungen serverseitig nach Objektzugriff ein. Merge-PRs #16, #17 und #29 wurden mit GitHub-CI gemergt. Das beschreibt konkrete Codepfade, nicht eine Gesamtfreigabe des Produkts.

## Maßnahmen vor produktivem Einsatz

1. Bedrohungsmodell und unabhängigen Sicherheitstest auf aktuellem Release durchführen; alle Objekt-/Personal- und Schreibendpunkte einschließlich Listen/Aggregaten testen.
2. MFA-/Recovery-Code-, Sitzungs- und administrativen Resetablauf unabhängig testen; Bedarf und Anforderungen für nutzerinitiierten Passwortreset ohne vorhandenen E-Mail-Zustelldienst klären.
3. Reverse Proxy, TLS, Secure-Cookie, vertrauenswürdige Proxy-IP, HSTS/CSP und Redis-Rate-Limit für die konkrete Produktionsumgebung konfigurieren, testen und überwachen.
4. Minimal privilegierte Rollen für Laufzeit, Migration und Backups; Audit-Append-only/externen Nachweis, Verschlüsselung und Schlüsselrotation umsetzen.
5. Uploads malwareprüfen oder quarantänisieren; nicht gescannte Dokumente nicht als sicher deklarieren.
6. Datenschutz-/Aufbewahrung-/Löschung, Monitoring, Alerting, Incident-Response, Backupziele und regelmäßige Restore-Übungen mit Verantwortlichen festlegen; die CI-Restoreprobe ersetzt diese Betreiberverantwortung nicht.
7. Arbeitszeit-, Zuschlags- und Rechnungs-/Steuerregeln fachlich prüfen. Das Billing-Modul berechnet Geldbeträge, ist aber keine nachgewiesene steuerliche oder buchhalterische Freigabe und garantiert keine Rechtskonformität.

Siehe [`SECURITY.md`](SECURITY.md) für Maßnahmenbeschreibung und [`PROJECT_STATUS.md`](PROJECT_STATUS.md) für aktuelle PR-/Issue-/CI-Grenzen. Eine Produktionsfreigabe ist nicht erteilt.
