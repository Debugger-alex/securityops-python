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

MFA, Passwortzurücksetzung per geprüftem Einmalprozess, aktive Sitzungsverwaltung, zentrale Rate-Limits und revisionsfester Auditbetrieb fehlen. Die Objektberechtigungen und Datentrennung des aktuellen Feature-Branches müssen noch durch PostgreSQL-CI und Review bestätigt werden. Das implementierte System ist nicht sicherheitszertifiziert und noch kein vollständiges Produkt.

## Dokumenten- und Vertragsverwaltung

- Dokumentdateien liegen im Compose-Volume `document_storage` unter `/var/lib/securityops/documents`, außerhalb aller Frontend-/Static-Verzeichnisse. Im lokalen Betrieb kann `DOCUMENT_STORAGE_PATH` auf ein privates Verzeichnis gesetzt werden; Zugriffsschutz des Datenträgers und Backups liegen beim Betreiber.
- Dateien erhalten eine zufällige 128-Bit-hex Storage-ID; Originalnamen werden nie als Pfad verwendet. Pfade akzeptieren ausschließlich die erwartete ID-Form und werden innerhalb des aufgelösten Root-Verzeichnisses geprüft. Dateien werden exklusiv mit Modus `0600`, Verzeichnis mit `0700` angelegt.
- Unterstützt werden PDF, PNG, JPEG, DOCX und XLSX. Endung, deklarierter MIME-Typ und serverseitige Signatur beziehungsweise OOXML-ZIP-Struktur müssen zusammenpassen. Uploadgrenze: Standard 20 MiB, konfigurierbar bis maximal 100 MiB. Bei erfolgreichem Upload werden SHA-256 und Größe gespeichert.
- Download erfolgt nur über eine authentifizierte, berechtigungs- und objektgeprüfte API-Route; Antworten sind `attachment`, `private, no-store` und `nosniff`. Upload, Download, Änderung, Archivierung, Freigabe und Lesebestätigung erzeugen Audit-Einträge. Versionen werden nicht überschrieben; Archivierung löscht nicht dauerhaft.
- Mitarbeiterdokumente benötigen HR-Sensitivberechtigung oder die eigene Personalzuordnung; Objektakten erfordern globale Objektberechtigung oder passende Objektzuweisung. Kundendatensätze benötigen Kundenrechte. Diese Prüfungen gelten auch für Download, Freigabe und Erinnerungsansichten.
- Der MIME-/Signaturtest ersetzt keinen Virenscanner, vollständigen Office-Parser oder Inhaltssicherheitsdienst. Dokumentfreigabe ist ein interner Status und keine elektronische Signatur. Verschlüsselung im Ruhezustand wird nicht auf Anwendungsebene bereitgestellt.
- Erinnerungen werden aktiv durch berechtigte API/UI ausgelöst und datenbankseitig dedupliziert. Es gibt keinen Zeitplan-Worker und keine Mail-/Push-Integration. Bis ein vertrauenswürdiger Scheduler und ein Virenscanner eingerichtet, die PostgreSQL-/Docker-Integration ausgeführt und Backup/Restore praktisch getestet wurden, darf die Funktion nicht als produktionsgehärtet gelten.
