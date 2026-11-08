# SecurityOps – Sicherheitsprüfung

Diese Prüfung fasst die bisherigen Reviews für `main` nach PR #16 und den aktuellen Feature-Branch `feature/personnel-management` zusammen. Sie ist kein Penetrationstest und keine Produktionsfreigabe. Nicht implementierte Funktionen (z. B. Datei-Uploads) wurden nicht als vorhandene Angriffsfläche bewertet. Es wurden keine echten Betriebsdaten verwendet.

## Zusammenfassung

| Kennung | Schweregrad | Status | Befund |
|---|---|---|---|
| SEC-01 | Mittel | Offen | Login-Rate-Limit liegt pro Prozess im Arbeitsspeicher; Neustarts und mehrere Instanzen schwächen die Begrenzung. |
| SEC-02 | Mittel | Offen | Compose startet Vite im Entwicklungsmodus; produktiver Webserver, TLS-Reverse-Proxy und Security-Header sind nicht Bestandteil des Deployments. |
| SEC-03 | Mittel | Offen | Audit-Protokolle sind über die App-API schreibgeschützt, aber nicht gegen direkte Änderungen privilegierter Datenbankrollen geschützt. |
| SEC-04 | Mittel | Offen | Anmeldung ohne MFA und Passwortzurücksetzungsprozess; keine aktive Sitzungsübersicht oder gezielte Einzelwiderruf-UI. |
| SEC-05 | Niedrig | Offen | Es gibt noch keine automatisierte Abhängigkeits- oder statische Sicherheitsanalyse in CI; als nächste Härtungsmaßnahme in [#9](https://github.com/Xonni-star/securityops-python/issues/9) nachzuverfolgen. |
| SEC-06 | Niedrig | Offen | API setzt keine expliziten allgemeinen Browser-Sicherheitsheader; dies muss derzeit ein vorgeschalteter Webserver übernehmen. |
| SEC-07 | Mittel | In `main` behoben | Die Anwendung verlangt `POSTGRES_PASSWORD`; Tests setzen ausschließlich einen Testwert. |
| SEC-08 | Hoch | In `main` behoben | Administratorrollenvergabe/-änderung ist serverseitig zusätzlich an `users.manage_admin` gebunden und durch Regressionstest abgedeckt. |
| SEC-09 | Hoch | In `main` behoben, PR #16 CI erfolgreich | Objektendpunkte erzwangen zuvor keine Zuweisung und erlaubten mit Modulrechten Zugriff auf fremde Objekte. Lesen, Ändern, Archivieren, Kontakte, Historie, Zuweisungen und sensible Details prüfen jetzt den Objekt-Scope serverseitig. |
| SEC-10 | Hoch | In `main` behoben, PR #16 CI erfolgreich | Allgemeine Objektantworten enthielten zuvor Sicherheits-/Zutrittsdaten. Diese Angaben liegen nun getrennt und benötigen eigene Les-/Schreibberechtigungen; Negativtests prüfen Antworttrennung und Scope. |
| SEC-11 | Mittel | Im Personal-Feature-Branch umgesetzt, CI ausstehend | Sensible Personalangaben und Abwesenheiten sind aus allgemeinen Personalantworten getrennt und durch eigene Rechte geschützt. Lokale Negativtests prüfen Zugriffstrennung; Migration und Berechtigungsmatrix müssen noch in CI/PostgreSQL bestätigt werden. |

## Geprüfte Schutzmaßnahmen

- Passwortspeicherung mit Argon2id; Login-Fehler sind für unbekannte und falsche Konten gleich.
- Sitzungen verwenden zufällige opaque Tokens; gespeichert werden Token-Hashes. Sitzungen haben Idle- und absolute Laufzeit, Logout und Passwortwechsel widerrufen Sitzungen.
- Authentifizierte schreibende Requests prüfen CSRF-Cookie, Request-Header und gespeicherten Hash.
- Cookies sind HttpOnly (Sitzung), SameSite=Strict und Secure per Konfiguration; Compose fällt auf Secure=true zurück. Lokale HTTP-Entwicklung setzt es in `.env.example` ausdrücklich auf false.
- RBAC wird serverseitig an Kunden-, Benutzer-, Rollen-, Audit- und Dashboardrouten geprüft.
- Objektzugriff wird zusätzlich zum Modulrecht global oder anhand einer Benutzerzuweisung autorisiert. Sensible Sicherheits- und Zutrittsdaten haben separate API-Routen und Berechtigungen.
- Zuweisungsendpunkte akzeptieren ausschließlich aktive Mitarbeiter- oder Objektleitungskonten; die Zuordnung selbst wird mit eindeutiger Datenbankbedingung geschützt.
- Objektänderungen werden transaktional mit Verlauf/Audit gespeichert. Historieneinträge listen geänderte Felder, nicht deren sensible Werte.
- Personalanschrift, Notfallkontakt und interne Notizen werden in einer eigenen Tabelle geführt; Personalhistorie und Audit protokollieren nur Feldnamen. Abwesenheiten haben ebenfalls eigene Lese-/Schreibrechte.
- Qualifikationsmetadaten und Abwesenheiten sind über Fremdschlüssel mit `RESTRICT` an Personalakten gebunden; Archivierung erhält verbundene Datensätze, statt sie zu löschen.
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
7. Mitarbeiterdaten-Trennung und Berechtigungsprüfungen des aktuellen Feature-Branches durch PostgreSQL-CI und Review bestätigen, bevor sie als abgeschlossen gelten.

## Grenzen und Prüfbelege

- Lokale Backend-API-Tests verwenden SQLite; aktuell bestehen 18 Tests. Ruff-Lint und Frontend-TypeScript-/Produktionsbuild sind lokal erfolgreich. Migration 0008 ist noch nicht gegen PostgreSQL validiert.
- Für den aktuellen Personal-Branch liegt noch kein echter PostgreSQL-Integrationslauf, Docker-Build oder externer Penetrationstest vor. Die CI für PR #16 war nach den Objektkorrekturen erfolgreich.
- Die Prüfung bewertet keinen konkreten Server, Reverse Proxy, Firewall, Secret Store, Backup-Speicher oder administrativen Datenbankzugang.
- Die Anwendung ist derzeit ein Entwicklungsstand. Vor öffentlichem oder produktivem Betrieb sind die offenen Punkte sowie Datenschutz-, Arbeitszeit- und Abrechnungsanforderungen fachlich und sicherheitstechnisch zu prüfen.
