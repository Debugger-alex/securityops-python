# Benachrichtigungs-Worker

## Umfang

Der eigene Compose-Dienst `notification-worker` verarbeitet die persistierte Transactional Outbox für Aufgabenereignisse. Task-Änderung, Historieneintrag und Outbox-Ereignis werden weiterhin in derselben Datenbanktransaktion geschrieben. Der API-Prozess startet keine Hintergrundprozesse mehr. Unterstützt werden derzeit ausschließlich `task.assigned` und `task.status_changed`; daraus werden In-App-Benachrichtigungen erzeugt. Der bestehende OWKS-Prüfzyklus läuft ebenfalls im separaten Dienst weiter und behält seine PostgreSQL-Advisory-Lock-Absicherung.

Der Versand von E-Mail oder Push ist nicht konfiguriert: Es gibt keinen vorhandenen Provider. Diese Kanäle werden weder als zugestellt markiert noch durch Platzhalter simuliert.

## Betrieb

Der Dienst verwendet dasselbe Backend-Image und dieselbe PostgreSQL-Konfiguration wie die API. Er wartet auf den gesunden Datenbankdienst und besitzt einen Datenbank-/Schema-Healthcheck. Nach einer Migration wird er mit `docker compose up -d notification-worker` gestartet; für einen vollständigen Start kann er zusammen mit API und Frontend gestartet werden.

Konfigurierbare Worker-Variablen:

| Variable | Standard | Bedeutung |
|---|---:|---|
| `NOTIFICATION_WORKER_POLL_SECONDS` | `2` | Wartezeit zwischen leeren bzw. abgeschlossenen Zyklen |
| `NOTIFICATION_WORKER_BATCH_SIZE` | `25` | Höchstzahl gleichzeitig beanspruchter Ereignisse (1–100) |
| `NOTIFICATION_WORKER_LEASE_SECONDS` | `300` | Frist, nach der verwaiste `processing`-Ereignisse erneut beansprucht werden |
| `NOTIFICATION_WORKER_MAX_ATTEMPTS` | `8` | Höchstzahl beanspruchter Zustellversuche |

Der Worker kann auch direkt im Backend-Container gestartet werden:

```sh
python -m app.notification_worker run
```

`SIGTERM` und `SIGINT` beenden den Polling-Zyklus geordnet. Ein gerade laufender DB-Zyklus wird abgewartet; die Lease ermöglicht die Wiederaufnahme nach einem harten Prozessabbruch.

## Zustellung und Fehler

Mehrere Worker beanspruchen fällige Ereignisse in kurzen PostgreSQL-Transaktionen mit `FOR UPDATE SKIP LOCKED`. Eine Lease samt Token verhindert, dass ein überholter Worker den neueren Claim abschließt. Die Erstellung der In-App-Einträge und das Markieren des Outbox-Ereignisses als abgeschlossen erfolgen atomar. `uq_notifications_event_recipient` verhindert doppelte Empfänger-Einträge auch bei erneuter Ausführung.

Temporäre Fehler werden mit deterministischem exponentiellem Backoff erneut versucht: 5 Sekunden, danach Verdopplung bis maximal 1 Stunde. Nicht unterstützte oder ungültige Outbox-Nachrichten werden direkt in `dead_letter` überführt; andere Fehler nach Erreichen der maximalen Versuchsanzahl. Status, letzter Fehlercode, Versuchszähler und eine durch PostgreSQL gegen Änderung/Löschung geschützte Attempt-Historie bleiben erhalten. Fehlertexte und Payloads werden nicht in Worker-Logs geschrieben; gespeichert wird nur ein Fehlercode bzw. Exception-Klassenname.

## Operative Inspektion

Statuszählungen und fehlgeschlagene Ereignisse einschließlich ihrer bereinigten Attempt-Historie lassen sich lokal über den Worker-CLI ausgeben:

```sh
docker compose exec notification-worker \
  python -m app.notification_worker inspect --limit 50
```

Die Ausgabe enthält keine Outbox-Payload, Titel, Nachrichtenkörper, Empfänger oder Exception-Texte. Das ist eine lokale Betriebs-CLI und kein öffentlich erreichbarer Monitoring-Endpunkt.

## Noch nicht enthalten

Das Task-Modell kennt `due_at` und `priority`; es gibt aber keine festgelegten Zeitpunkte, Empfängerregeln oder Eskalationsstufen für Erinnerungen. Deshalb werden hier keine neuen Erinnerungs- oder Eskalationsregeln eingeführt. E-Mail/Push bleibt mangels konfiguriertem Provider offen. Die Zustellung dieses Ausbauschritts ist vollständig auf In-App-Aufgabenereignisse begrenzt.
