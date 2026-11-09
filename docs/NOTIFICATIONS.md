# In-App-Benachrichtigungen

## Umfang

Der Benachrichtigungskern speichert derzeit ausschließlich In-App-Ereignisse für den vorhandenen Aufgaben-Kern. Er erzeugt Einträge, wenn eine Aufgabe einer anderen Person zugewiesen oder ihr Status tatsächlich geändert wird. Eine unveränderte PATCH-Anfrage erzeugt kein neues Ereignis. Die Ereignis- und Empfängerzeilen werden zusammen mit Aufgabenhistorie und Audit-Eintrag in derselben Datenbanktransaktion geschrieben.

Neue Zuweisungen benachrichtigen die neue verantwortliche Person, nicht die zuvor verantwortliche Person. Eine Statusänderung benachrichtigt die aktuelle verantwortliche Person und die erstellende Person, soweit sie nicht selbst handelnde Person sind. Beim Abschluss bleibt ein bereits erzeugter Eintrag erhalten. Ein Empfänger kann ihn jedoch nur sehen, solange die bestehende Aufgabenberechtigung den Zugriff auf die Aufgabe erlaubt. Nach einer Neuzuweisung verliert eine frühere verantwortliche Person ohne anderweitigen Aufgabenzugriff auch die Sichtbarkeit zugehöriger Benachrichtigungen; die gespeicherten Einträge werden dadurch nicht gelöscht.

## API und Berechtigungen

- `GET /api/v1/notifications?limit=25&offset=0&unread_only=false` liefert eine paginierte Empfängersicht mit Gesamtzahl und ungelesener Anzahl. `limit` ist auf 100 begrenzt.
- `PATCH /api/v1/notifications/{id}/read` markiert eine eigene, sichtbare Benachrichtigung als gelesen. Wiederholte Aufrufe sind idempotent. Fremde, nicht mehr sichtbare oder unbekannte IDs antworten einheitlich mit `404`.
- Beide Endpunkte verlangen eine gültige Sitzung und `notifications.read_own`. Zusätzlich wird die Empfänger-ID mit der Aufgaben-Sichtbarkeit des Aufgaben-Kerns verknüpft; die Client-Oberfläche ersetzt diese Prüfung nicht.

Die Migration `0020_notifications` vergibt die Berechtigung an die vorhandenen Standardrollen. Berechtigungen, Lesestatus und Aufgabenereignisse werden nicht über Frontend-Daten autorisiert oder aus Benutzereingaben übernommen.

## Outbox und Folgearbeit

`notification_outbox` wird in derselben Transaktion wie das Aufgabenereignis und dessen In-App-Einträge geschrieben. Ein eindeutiger Schlüssel auf der Aufgabenhistorienzeile und eine eindeutige Kombination aus Outbox-Ereignis und Empfänger verhindern doppelte Einträge. Das Outbox-Schema hält Status-, Verfügbarkeits-, Versuchs- und Fehlerfelder für eine spätere Verarbeitung bereit.

Es gibt in diesem Umfang **keinen Outbox-Worker, Scheduler, Retry-Lauf, Job-Monitor, E-Mail- oder Push-Provider**. Offene Outbox-Ereignisse werden daher nicht automatisch abgearbeitet; die In-App-Einträge selbst sind bereits dauerhaft verfügbar. Für den produktiven Ausbau sind ein unabhängig vom Browser laufender Worker, konkurrenzsichere Jobübernahme, Retry- und Backoff-Regeln, eine nachvollziehbare Versuchshistorie, Fehler-/Dead-Letter-Behandlung, Metriken und Betriebsalarme erforderlich. Erst dann sollten weitere Kanäle und Ereignisse aus anderen Modulen angeschlossen werden.

PR #39 ist offen und schlägt einen solchen Worker sowie Migration `0024_notification_outbox_worker` vor. Die PR-Beschreibung umfasst idempotente Verarbeitung der Aufgabenereignisse, konkurrierende Claims, Lease-Wiederaufnahme, konfigurierbare Versuche mit Backoff und Dead-Letter-/Attempt-Historie. Diese Änderungen sind nicht in `main` enthalten; E-Mail/Push und Task-Erinnerungen/Eskalationen sind laut PR-Beschreibung weiterhin nicht vorgesehen.

## Migration und Rückbau

`0020_notifications` folgt linear auf `0019_tasks`. Ein Downgrade wird abgelehnt, sobald Outbox- oder Benachrichtigungsdaten oder Berechtigungszuordnungen zu benutzerdefinierten Rollen vorhanden sind. Diese Daten müssen vor einem Rückbau ausdrücklich gesichert beziehungsweise fachlich behandelt werden.
