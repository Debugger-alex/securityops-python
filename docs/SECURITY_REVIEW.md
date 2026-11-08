# SecurityOps – Sicherheitsprüfung

Stand: 2026-11-08. Diese Prüfung ist eine statische Bestandsaufnahme des versionierten Quellcodes und der Konfiguration, keine Penetrationstest- oder Produktionsfreigabe. Nicht implementierte Funktionen (z. B. Datei-Uploads) wurden nicht als vorhandene Angriffsfläche bewertet. Es wurden keine echten Betriebsdaten verwendet.

## Zusammenfassung

| Kennung | Schweregrad | Status | Befund |
|---|---|---|---|
| SEC-01 | Mittel | Offen | Login-Rate-Limit liegt pro Prozess im Arbeitsspeicher; Neustarts und mehrere Instanzen schwächen die Begrenzung. |
| SEC-02 | Mittel | Offen | Compose startet Vite im Entwicklungsmodus; produktiver Webserver, TLS-Reverse-Proxy und Security-Header sind nicht Bestandteil des Deployments. |
| SEC-03 | Mittel | Offen | Audit-Protokolle sind über die App-API schreibgeschützt, aber nicht gegen direkte Änderungen privilegierter Datenbankrollen geschützt. |
| SEC-04 | Mittel | Offen | Anmeldung ohne MFA und Passwortzurücksetzungsprozess; keine aktive Sitzungsübersicht oder gezielte Einzelwiderruf-UI. |
| SEC-05 | Niedrig | Offen | Es gibt noch keine automatisierte Abhängigkeits- oder statische Sicherheitsanalyse in CI; als nächste Härtungsmaßnahme in [#9](https://github.com/Xonni-star/securityops-python/issues/9) nachzuverfolgen. |
| SEC-06 | Niedrig | Offen | API setzt keine expliziten allgemeinen Browser-Sicherheitsheader; dies muss derzeit ein vorgeschalteter Webserver übernehmen. |
| SEC-07 | Mittel | In diesem PR behoben | Ein implizites Datenbankpasswort in der Anwendungskonfiguration erlaubte einen Start ohne bewusst gesetztes Secret. Die Anwendung verlangt jetzt `POSTGRES_PASSWORD`; Tests setzen nur einen Testwert. |
| SEC-08 | Hoch | In diesem PR behoben | Die Geschäftsführungsrolle konnte über `users.manage` Administratorrechte zuweisen. Die serverseitige Vergabe/Änderung ist jetzt zusätzlich an `users.manage_admin` gebunden und durch einen Regressionstest abgedeckt. |

## Geprüfte Schutzmaßnahmen

- Passwortspeicherung mit Argon2id; Login-Fehler sind für unbekannte und falsche Konten gleich.
- Sitzungen verwenden zufällige opaque Tokens; gespeichert werden Token-Hashes. Sitzungen haben Idle- und absolute Laufzeit, Logout und Passwortwechsel widerrufen Sitzungen.
- Authentifizierte schreibende Requests prüfen CSRF-Cookie, Request-Header und gespeicherten Hash.
- Cookies sind HttpOnly (Sitzung), SameSite=Strict und Secure per Konfiguration; Compose fällt auf Secure=true zurück. Lokale HTTP-Entwicklung setzt es in `.env.example` ausdrücklich auf false.
- RBAC wird serverseitig an Kunden-, Benutzer-, Rollen-, Audit- und Dashboardrouten geprüft.
- ORM-Abfragen verwenden gebundene Parameter; React escaped Textausgaben standardmäßig. Keine Upload- oder Datei-Auslieferungsfunktion ist aktuell implementiert.
- CORS stammt aus einer expliziten Origin-Konfiguration und erlaubt keine beliebigen Origins.
- Compose verlangt ein gesetztes Datenbankpasswort; Anwendungskonfiguration enthält keinen Produktions-Standardwert.

## Offene Maßnahmen

1. Gemeinsamen Rate-Limit-Speicher (z. B. Redis) und vertrauenswürdige Proxy-IP-Konfiguration einführen; Login- und weitere sensible Endpunkte prüfen.
2. Produktionsfrontend als statische Assets ausliefern und TLS, HSTS, CSP sowie weitere passende Header am vertrauenswürdigen Reverse Proxy konfigurieren. Den Devserver nicht öffentlich bereitstellen.
3. Laufzeit-, Migrations- und Backup-Datenbankrollen nach minimalen Rechten trennen. Audit-Protokoll extern oder append-only sichern; direkte privilegierte Datenbankänderungen bleiben sonst außerhalb des App-Schutzes.
4. MFA, sicheren Passwort-Reset und Sitzungsanzeige/-widerruf mit Abuse- und Berechtigungstests umsetzen.
5. CI um verwaltete SCA-/SAST-Prüfungen ergänzen und deren Pflege/Alarmierungsweg festlegen.
6. Security-Header, TLS, Datenschutz-/Aufbewahrung und Incident-Abläufe für die konkrete Serverumgebung festlegen und prüfen.
7. Objektbezogene Autorisierung vor Einsatz-, Personal-, Dokument- und Kontrollfunktionen implementieren.

## Grenzen und Prüfbelege

- Lokale Backend-API-Tests verwenden SQLite. CI ist für Migrationen und API-Tests gegen eine kurzlebige PostgreSQL-Testdatenbank eingerichtet; der erste gehostete Lauf muss noch abgewartet werden.
- Der lokale Arbeitslauf hat keine Docker-/PostgreSQL-Integration und keinen externen Penetrationstest ausgeführt.
- Die Prüfung bewertet keinen konkreten Server, Reverse Proxy, Firewall, Secret Store, Backup-Speicher oder administrativen Datenbankzugang.
- Die Anwendung ist derzeit ein Entwicklungsstand. Vor öffentlichem oder produktivem Betrieb sind die offenen Punkte sowie Datenschutz-, Arbeitszeit- und Abrechnungsanforderungen fachlich und sicherheitstechnisch zu prüfen.
