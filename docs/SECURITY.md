# Sicherheitsstatus und Betriebshinweise

## Bereits vorhanden

- Argon2id-Passwort-Hashes und generische Login-Fehler.
- Serverseitige opaque Sitzungen mit gleitender und absoluter Ablaufzeit.
- HttpOnly, SameSite=Strict Sitzungscookie; CSRF-Tokenprüfung für authentifizierte Schreibzugriffe.
- Server-RBAC und Schutz vor unberechtigter Administratorrollenvergabe.
- Login-Rate-Limit, derzeit nur im In-Memory-Speicher eines Prozesses.
- Keine Passworthashes in API-Antworten.
- Audit-Einträge für implementierte Anmelde-, Benutzer- und Kundenänderungen.
- `POSTGRES_PASSWORD` ist als Umgebungsvariable erforderlich; es gibt keinen impliziten Datenbankpasswort-Standardwert.

## Vor jedem produktiven Betrieb

- TLS/HTTPS und Reverse Proxy einrichten; `SESSION_COOKIE_SECURE=true` erzwingen.
- Rate-Limit-Speicher für alle Instanzen zentralisieren; Proxy-IP nur aus vertrauenswürdiger Infrastruktur übernehmen.
- Secrets sicher außerhalb von Git und Image-Layern bereitstellen.
- Produktions-Frontend als statische Assets über einen gehärteten Webserver ausliefern; Vite-Devserver nicht öffentlich nutzen.
- Datenbankrollen mit minimalen Rechten definieren; Audit-Schreibschutz/externes unveränderliches Archiv bewerten.
- Backups verschlüsseln, getrennt aufbewahren und Wiederherstellungen regelmäßig praktisch testen.
- Sicherheits- und Datenschutzprüfung, Aufbewahrungs-/Löschregeln, Monitoring und Incident-Abläufe definieren.
- Keine echten Kunden-/Personal-/Einsatzdaten verwenden, solange fachliche Berechtigungen und Produktionshärtung fehlen.

## Offene Sicherheitsfunktionen

MFA, Passwortzurücksetzung per geprüftem Einmalprozess, aktive Sitzungsverwaltung, objektbezogene Rechte, zentrale Rate-Limits und revisionsfester Auditbetrieb fehlen. CI ist für PostgreSQL-Migrationen und API-Tests auf einer kurzlebigen Testdatenbank eingerichtet; der erste gehostete Lauf ist noch auszuwerten. Das implementierte System ist nicht sicherheitszertifiziert und noch kein vollständiges Produkt.
