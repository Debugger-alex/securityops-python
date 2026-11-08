# Sicherheitsstatus und Betriebshinweise

## Bereits vorhanden

- Argon2id-Passwort-Hashes und generische Login-Fehler.
- Serverseitige opaque Sitzungen mit gleitender und absoluter Ablaufzeit.
- HttpOnly, SameSite=Strict Sitzungscookie; CSRF-Tokenprüfung für authentifizierte Schreibzugriffe.
- Server-RBAC und Schutz vor unberechtigter Administratorrollenvergabe.
- Login-Rate-Limit, derzeit nur im In-Memory-Speicher eines Prozesses.
- Keine Passworthashes in API-Antworten.
- Audit-Einträge für implementierte Anmelde-, Benutzer-, Kunden- und Objektänderungen.
- Objektzugriff serverseitig nach globalen Rechten oder Objektzuweisung; Sicherheits- und Zutrittsdaten sind getrennt und zusätzlich berechtigt.
- OWKS-Endpunkte prüfen das OWKS-Recht und zusätzlich den Objekt-Scope; Anhangabruf ist nicht öffentlich und der Upload validiert Dateiendung, MIME-Typ, Signatur und 10-MiB-Grenze.
- OWKS-Ereignisse, Statusverläufe und Anhänge sind in PostgreSQL append-only. Statusänderungen und Korrekturen werden als neue Datensätze protokolliert.
- Kontrollscans benötigen eine kurzlebige, benutzer- und objektgebundene Einmal-Challenge; PostgreSQL koordiniert den Versäumnis-Monitor zwischen Instanzen und verhindert doppelte generierte Meldungen.
- Statische QR-/NFC-Kennungstreffer werden als `presence_verified=false` protokolliert, bleiben offen und zählen nicht als erledigter Besuch. Sie belegen keine physische Anwesenheit.
- `POSTGRES_PASSWORD` ist als Umgebungsvariable erforderlich; es gibt keinen impliziten Datenbankpasswort-Standardwert.

## Vor jedem produktiven Betrieb

- TLS/HTTPS und Reverse Proxy einrichten; `SESSION_COOKIE_SECURE=true` erzwingen.
- Rate-Limit-Speicher für alle Instanzen zentralisieren; Proxy-IP nur aus vertrauenswürdiger Infrastruktur übernehmen.
- Secrets sicher außerhalb von Git und Image-Layern bereitstellen.
- Produktions-Frontend als statische Assets über einen gehärteten Webserver ausliefern; Vite-Devserver nicht öffentlich nutzen.
- Datenbankrollen mit minimalen Rechten definieren; Audit-Schreibschutz/externes unveränderliches Archiv bewerten.
- Backups verschlüsseln, getrennt aufbewahren und Wiederherstellungen regelmäßig praktisch testen.
- Sicherheits- und Datenschutzprüfung, Aufbewahrungs-/Löschregeln, Monitoring und Incident-Abläufe definieren.
- OWKS-Downgrade nicht ausführen, solange Betriebsdaten vorliegen; Migration 0014 verweigert den Downgrade dann explizit. Für sichere Rollbacks müssen Datenaufbewahrung und Exportverfahren vorher festgelegt werden.
- Statische OWKS-QR-Codes und NFC-Tags sind kopierbar. Web-NFC, Challenge und serverseitige Replay-Prüfungen beweisen keine physische Anwesenheit; dynamische kryptografische Tags oder verwaltete Standort-/Gerätenachweise sind nicht integriert.
- Keine echten Kunden-/Personal-/Einsatzdaten verwenden, solange fachliche Berechtigungen und Produktionshärtung fehlen.

## Offene Sicherheitsfunktionen

MFA, Passwortzurücksetzung per geprüftem Einmalprozess, aktive Sitzungsverwaltung, zentrale Rate-Limits und revisionsfester Auditbetrieb fehlen. Die Objektberechtigungen und Datentrennung des aktuellen Feature-Branches müssen noch durch PostgreSQL-CI und Review bestätigt werden. Das implementierte System ist nicht sicherheitszertifiziert und noch kein vollständiges Produkt.
