# SecurityOps – Bestandsaufnahme und Entwicklungsbericht

Stand: 2026-11-08

## Phase 1 – Bestandsaufnahme

Ausgangsstand des Repositorys war ein einzelner Commit mit FastAPI, einem Kundenmodell samt erster Alembic-Migration, CRUD-Endpunkten für Kunden, kundendatenbasierten Dashboard-Zahlen und einer React-Oberfläche. Es gab noch keine Anmeldung, Rollen, Audit-Protokolle oder weitere Fachmodule. Docker Compose enthielt PostgreSQL, API und Frontend. Ein lokaler Docker-Daemon war für diese Arbeitsphase nicht verfügbar.

## Phase 2 – Identität, Rechte und Audit

### Fertig implementiert und getestet

- Anmeldung und Abmeldung über zufällige, serverseitig widerrufbare Sitzungs-Cookies.
- Passwort-Hashing mit Argon2id und generischer Fehlermeldung bei ungültigen Zugangsdaten.
- Idle- und absolute Sitzungsablaufzeit; Passwortwechsel widerruft alle Sitzungen.
- CSRF-Schutz für authentifizierte Schreibzugriffe über SameSite-Cookies und einen geprüften Request-Header.
- Serverseitige RBAC-Prüfungen an Kunden-, Dashboard-, Benutzer-, Rollen- und Audit-Endpunkten.
- Standardrollen für Administrator, Geschäftsführung, Einsatzleitung, Objektleitung, Personalverwaltung und Mitarbeiter samt initialen Berechtigungen.
- Benutzeranlage, Rollenvergabe, Aktivierung/Deaktivierung; letzte aktive Administratoren können nicht entfernt oder herabgestuft werden.
- Sperren häufiger Anmeldeversuche (5/min pro Backend-Prozess).
- Audit-Einträge für An-/Abmeldung, fehlgeschlagene Anmeldungen, Passwortwechsel, Benutzeränderungen sowie Kundenanlage/-änderungen.
- Admin-Bootstrap ohne eingebautes Standardpasswort.
- Login-Oberfläche mit rollenabhängiger Anzeige der Kundenfunktionen.

### Implementiert, aber betrieblich noch nicht vollständig abgesichert

- Rate-Limit-Speicher ist pro Prozess im Arbeitsspeicher; für mehrere Worker/Instanzen muss ein gemeinsamer Speicher eingerichtet werden.
- Audit-Endpunkte bieten Anwendungsschreibschutz; Datenbankadministratoren können Datenbankzeilen weiterhin direkt verändern.
- CSRF und Cookies sind implementiert; der Produktivbetrieb setzt HTTPS und `SESSION_COOKIE_SECURE=true` voraus.

### Noch nicht implementiert

- MFA, E-Mail-gestützte Passwortzurücksetzung und vollständige Sitzungsverwaltung in der Oberfläche.
- Bearbeitung von Rollen und Berechtigungsdefinitionen über eine Administrationsoberfläche.
- Objektbezogene Zugriffszuteilungen.

## Funktionsübersicht

| Bereich | Status |
|---|---|
| Kunden | Teilweise implementiert: Anlage, Suche, Detailabruf und Änderung. Ansprechpartner, Anschriften, Dokumente, Historie und Archivierung fehlen. |
| Objekte | Noch nicht implementiert |
| Personal | Noch nicht implementiert |
| Dienstplanung | Noch nicht implementiert |
| Zeiterfassung | Noch nicht implementiert |
| OWKS und Kontrollgänge | Noch nicht implementiert |
| Dienstanweisungen und Dokumente | Noch nicht implementiert |
| Verträge und Abrechnung | Noch nicht implementiert |
| Dashboard | Teilweise implementiert: Kundenkennzahlen sind datenbankbasiert. Operative Kennzahlen fehlen. |
| Identity/RBAC | Grundfunktionen implementiert und getestet; MFA, Passwortzurücksetzung und Objektzuweisungen fehlen. |
| Audit | Grundlegende Ereignisse implementiert und getestet; manipulationssichere Speicherung/Betriebskonzept fehlt. |

## Geänderte Dateien in dieser Phase

- Backend: Identity-, Rollen-, Sitzungs-, Berechtigungs- und Auditmodelle; Authentifizierungs-/Benutzer-/Rollen-/Audit-API; Argon2id; Rate-Limit; Admin-Bootstrap; Kunden- und Dashboardberechtigungen.
- Datenbank: neue Alembic-Migration `0002_identity_audit`.
- Frontend: Anmeldung, Sitzung und sichtbare Kundenaktionen nach Serverberechtigungen.
- Infrastruktur/Dokumentation: Cookie-Sicherheitskonfiguration, Installationshinweise, Erstadministrator und dieser Statusbericht.
- Tests: Anmeldung, CSRF, Sitzungswiderruf, RBAC, Benutzerverwaltung, Rate-Limit und Kundenabläufe.

## Prüfungsergebnisse

- Backend-Tests decken API- und Berechtigungsabläufe mit SQLite ab; sie ersetzen keinen Test gegen einen echten PostgreSQL-Server.
- PostgreSQL-Migrationen wurden als SQL offline generiert, aber hier nicht gegen einen laufenden PostgreSQL-Dienst ausgeführt.
- Frontend-TypeScript-Prüfung und Produktionsbuild wurden erfolgreich ausgeführt.
- Docker-Compose-Datei wurde syntaktisch geladen; Containerstart und Deployment wurden mangels Docker nicht ausgeführt.

## Nächste sinnvolle Ausbaustufe

Zuerst Kundenverwaltung abschließen (Ansprechpartner, Rechnungsanschrift, Archivierung, Auditdetails), danach Objektverwaltung mit Kundenbeziehung und objektbezogenen Zugriffsrechten. Erst auf dieser Grundlage sollten Personal- und Einsatzdatenmodule aufbauen.
