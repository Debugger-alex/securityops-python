# Sicherheitsprüfung – Ist-Stand und offene Maßnahmen

## Charakter und Scope

Dies ist eine statische, dokumentarische Zusammenfassung sichtbarer Kontrollen im `main`-Code (`6c7679a646d30da0504d8990fefeefa351a29bfe`), keine unabhängige Sicherheitsprüfung, kein Penetrationstest und keine Zertifizierung. Es wurden für diese Dokumentationsarbeit keine Angriffe ausgeführt und keine realen Daten verwendet. OWKS und Dokumente/Verträge aus den gemergten PRs #23/#24 sind in den `main`-Befund eingerechnet.

## Befundübersicht

| Bereich | Status | Beleg / verbleibendes Risiko |
|---|---|---|
| Passwort- und Session-Schutz | Teilweise vorhanden | Argon2id, generische Loginfehler, gehashte opaque Session-/CSRF-Tokens, Idle-/Absolute-Timeout, Logout/Widerruf. Kein MFA, Resetprozess oder Sitzungsübersicht. |
| CSRF / Cookies | Vorhanden, Umgebung abhängig | CSRF-Doppelübermittlung und HttpOnly/SameSite=Strict; Secure konfigurierbar, Compose default `true`. Lokale HTTP-Ausnahme darf nicht produktiv werden. |
| RBAC / Scoping | Serverseitig implementiert | Modulrechte, Admin-Zuweisungsschutz sowie Objekt- und Sensitivitätsgrenzen. Abdeckung muss in jeder neuen Route und allen Aggregaten erhalten bleiben; UI ist keine Schutzgrenze. |
| Rate-Limit | Unvollständig | Login `5/minute` über SlowAPI und Client-IP; kein geteilter Speicher/Mehrinstanznachweis. Proxy-Header-Trust nicht eingerichtet. |
| Audit | Teilweise | App-API erlaubt Lesen mit `audit.read`; schreibt Events für implementierte Abläufe. Kein DB-seitiger Append-only-Schutz/externes unveränderliches Archiv, keine vollständige Abdeckung aller Vorgänge. |
| Personal-/Objektdaten | Getrennte Endpunkte | Sensible Werte und Datei-/Abwesenheitsdaten haben gesonderte Rechte. Datenschutz, Verschlüsselung at rest und Aufbewahrung sind nicht vollständig nachgewiesen. |
| Uploads | Eingabeprüfung, aber kein Malware-Schutz | Qualifikationsnachweise und OWKS-Anhänge: PDF/PNG/JPEG, max. 10 MiB, in PostgreSQL (`BYTEA`). Dokumente: PDF/PNG/JPEG/DOCX/XLSX im privaten Dateispeicher, Standardgrenze 20 MiB. Typ-/Signaturprüfung, aber kein Malware-Scan, Quarantäne, KMS oder Anwendungsebene-Verschlüsselung. |
| OWKS-Protokoll | Teilweise geschützt | Migration 0014 ergänzt Append-only-Trigger gegen UPDATE/DELETE an Ereignissen, Statushistorien und Anhängen. Direkte privilegierte DB-Änderungen außerhalb der Triggerberechtigung, Backup/Restore und unabhängige Integritätsprüfung sind nicht nachgewiesen. |
| Dokumente / Verträge | Autorisierte API und privater lokaler Speicher | Dateiabruf erfolgt über Rechte-Endpunkte; private Verzeichnis-/Dateimodi. Malware-Scan, Verschlüsselung, externer geschützter Speicher und automatische Erinnerungszustellung fehlen. |
| Transport / Deployment | Nicht umgesetzt | Kein TLS-Reverse-Proxy, HSTS/CSP oder Produktions-Webserver im Compose-Setup; Vite läuft als Entwicklungsserver. |
| Abhängigkeiten / CI | Grundlegende CI | Ruff, Backend, PostgreSQL-Migrationen, Frontend-Build/-Tests, Docker-Build. Kein SCA/SAST/Secret-Scanning-Job. |
| Backup / Wiederherstellung | Nicht nachgewiesen | Keine automatisierten verschlüsselten Backups oder erfolgreich durchgeführte Restoreprobe im Repository belegt. |
| Datenschutz / Incident | Nicht nachgewiesen | Kein vollständiger Lösch-/Aufbewahrungs-/Betroffenenprozess, keine Datenschutzfolgenprüfung oder Incident-Ablaufdokumentation für Produktion. |

## Frühere behobene Findings

In vorherigen Änderungen wurden eine unbeschränkte Administratorrollenvergabe über allgemeines `users.manage` begrenzt (`users.manage_admin`), Objektzugriff nach globalem Recht oder Zuweisung umgesetzt und sensible Zutrittsdaten aus allgemeinen Objektantworten getrennt. Merge-PRs #16 und #17 wurden mit GitHub-CI gemergt. Das beschreibt konkrete behobene Codepfade, nicht eine Gesamtfreigabe des Produkts.

## Maßnahmen vor produktivem Einsatz

1. Bedrohungsmodell und unabhängigen Sicherheitstest auf aktuellem Release durchführen; alle Objekt-/Personal- und Schreibendpunkte einschließlich Listen/Aggregaten testen.
2. MFA, Passwortwiederherstellung, Sitzungssicht/-widerruf sowie Abuse-Schutz spezifizieren und prüfen.
3. Reverse Proxy, TLS, Secure-Cookie, vertrauenswürdige Proxy-IP, HSTS/CSP und verteiltes Rate-Limit produktiv implementieren und testen.
4. Minimal privilegierte Rollen für Laufzeit, Migration und Backups; Audit-Append-only/externen Nachweis, Verschlüsselung und Schlüsselrotation umsetzen.
5. Uploads malwareprüfen oder quarantänisieren; nicht gescannte Dokumente nicht als sicher deklarieren.
6. Datenschutz-/Aufbewahrung-/Löschung, Monitoring, Alerting, Incident-Response, verschlüsselte Backups und Restore-Übungen mit Verantwortlichen festlegen.
7. Arbeitszeit-, Zuschlags- und Abrechnungsregeln fachlich prüfen. Aktuelle Zeiterfassung berechnet keine Beträge und garantiert keine Rechtskonformität.

Siehe [`SECURITY.md`](SECURITY.md) für Maßnahmenbeschreibung und [`PROJECT_STATUS.md`](PROJECT_STATUS.md) für aktuelle PR-/Issue-/CI-Grenzen. Eine Produktionsfreigabe ist nicht erteilt.
