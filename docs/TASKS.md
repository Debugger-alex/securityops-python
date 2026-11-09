# Zentrales Aufgabenmanagement

## Umfang

Der Aufgaben-Kern stellt generische Aufgaben mit Titel, Beschreibung, verantwortlichem Benutzer, Ersteller, optionalem Kunden und Objekt, Fälligkeit, Priorität, Status und Erledigungsnachweis bereit. Kommentare und ein fortlaufend erfasster Aufgabenverlauf ergänzen die zentrale Audit-Protokollierung. Änderungen an Aufgabe, Zuweisung und Abschluss werden gemeinsam mit dem fachlichen Schreibvorgang persistiert.

Die Revision `0019_tasks` folgt auf `0018_identity_security`. Aufgaben verwenden die Statuswerte `open`, `in_progress`, `blocked`, `completed` und `cancelled`; Prioritäten sind `low`, `normal`, `high` und `urgent`. Zum erstmaligen Abschließen ist ein Erledigungsnachweis erforderlich. Ein Fälligkeitszeitpunkt muss eine Zeitzone enthalten und wird in UTC gespeichert.

## API

- `GET /api/v1/tasks`: paginierte Liste mit Suche, Status-, Prioritäts-, Verantwortlichen-, Kunden-, Objekt- und Überfälligkeitsfilter.
- `POST /api/v1/tasks`: Aufgabe anlegen; ohne explizite Verantwortlichkeit wird der Ersteller eingetragen.
- `GET /api/v1/tasks/{id}`: Aufgabendetails einschließlich Kommentaren und Verlauf.
- `PATCH /api/v1/tasks/{id}`: validierte Änderungen, Zuweisung und Statuswechsel.
- `POST /api/v1/tasks/{id}/comments`: Kommentar anfügen.
- `GET /api/v1/tasks/locations` und `GET /api/v1/tasks/assignees`: datensparsame Auswahlwerte für berechtigte Aufgabenersteller und Zuweisende.

Schreibvorgänge verwenden Datenbanktransaktionen; Aufgaben-, Kommentar-, Verlauf- und Audit-Einträge werden gemeinsam committed. Nicht sichtbare Aufgaben werden bei Einzelabrufen als nicht gefunden behandelt, damit IDs nicht als Auskunftskanal dienen.

## Berechtigungen

- `tasks.read_own`: eigene Aufgaben sowie Aufgaben zu persönlich zugewiesenen Objekten einsehen.
- `tasks.read_all`: Aufgaben übergreifend einsehen.
- `tasks.create`: Aufgaben anlegen, wobei Objekt- und Kundenzuordnungen dem eigenen Objektbereich entsprechen müssen.
- `tasks.update_own`: eigene oder auf eigene Objekte bezogene Aufgaben bearbeiten.
- `tasks.manage`: sichtbare Aufgaben verwalten.
- `tasks.assign`: Aufgaben anderen aktiven Benutzern zuweisen.
- `tasks.manage_all`: Aufgaben und Zuordnungen unabhängig vom Objektbereich verwalten.

Die Migration weist alle Aufgabenberechtigungen der Administratorrolle zu, Lese-/Bearbeitungsrechte im eigenen Bereich den Rollen `operations` und `employee` und bereichsübergreifende Verwaltungsrechte der Geschäftsführung. Die Berechtigungsprüfung findet ausschließlich im Backend statt.

## Grenzen und Folgeintegration

Der Aufgaben-Kern erzeugt noch keine automatischen Aufgaben aus Vorfällen, Objektprüfungen, Kontrollgängen, Dienstplanproblemen, Qualifikations- oder Vertragsabläufen, Materialprüfungen, Rechnungsfreigaben oder Kundenanfragen. Diese Module veröffentlichen derzeit keine vereinbarte Task-Event-Schnittstelle; sie werden daher nicht direkt gekoppelt.

Anhänge, Erinnerungszustellung, Hintergrundjobs und automatisierte Eskalationen sind nicht Bestandteil dieser Einheit. Es werden weder E-Mail- noch sonstige Benachrichtigungsdienste gestartet. Eine Folgeintegration sollte fachliche Ereignisse über explizite, versionierte Schnittstellen oder transaktionale Outbox-Einträge auslösen und dann eine deduplizierte Aufgabenanlage bereitstellen. Erinnerungen und Eskalationen benötigen eigene Laufzeit-, Zustell-, Wiederholungs- und Auditregeln. Anhänge müssen über autorisierte Backend-Endpunkte und mit dem bestehenden Malware-Scan geschützt werden.
