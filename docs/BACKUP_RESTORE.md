# Backup und Wiederherstellung

## Ist-Zustand

Automatisierte Backups, definierte RPO/RTO, verschlüsselte externe Aufbewahrung und ein erfolgreicher Restore-Test sind in diesem Repository nicht implementiert bzw. nicht belegt. Das Compose-Volume `postgres_data` ist persistenter Speicher, kein Backup. Dateien von Personalqualifikationen liegen in der Datenbank (`BYTEA`) und müssen in einem konsistenten Datenbankbackup enthalten sein.

## Manueller PostgreSQL-Dump (Beispiel)

Nur für eine lokale Test-/Betriebsübung und nur in einen zugriffsbeschränkten Zielpfad verwenden. Die Shellvariablen `POSTGRES_USER` und `POSTGRES_DB` müssen auf dem aufrufenden Host gesetzt sein; nicht aus unkontrollierten oder fremden `.env`-Dateien laden.

```sh
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > securityops-$(date +%F).dump
```

Der Dump kann Kunden-, Personal-, Abwesenheits- und Sicherheitsdaten enthalten. Zugriff beschränken, vor Speicherung außerhalb des Hosts verschlüsseln, Prüfsummen/Integrität erfassen und Aufbewahrung sowie sichere Vernichtung festlegen. Zugangsdaten nicht in Befehlsargumenten, Shell-Historie, CI-Logs oder Backupnamen ablegen. Dieses Beispiel allein erfüllt keine Backupkontrolle.

## Restore-Übung

1. Restore ausschließlich in eine eigens dafür isolierte Testdatenbank durchführen; nie ungefragt in eine produktive Datenbank.
2. Ziel und Backupversion prüfen. `pg_restore --clean` löscht Objekte im Ziel und darf nicht auf einer produktiven Datenbank eingesetzt werden.
3. Restore mit minimal privilegiertem, passenden PostgreSQL-Konto durchführen.
4. Alembic-Revision, Tabellen/Fremdschlüssel, Benutzerzugriff und anonymisierte fachliche Konsistenz prüfen.
5. Wiederherstellung von `BYTEA`-Dokumenten, benötigten Verschlüsselungsschlüsseln/Secrets und Datenbankrollen in einem dokumentierten Ablauf berücksichtigen.
6. Dauer, Fehler, Prüfergebnis und erreichte RPO/RTO protokollieren; echte Betriebsdaten nicht in Entwicklungslogs kopieren.

Es wurde kein Backup- oder Restorelauf behauptet. Vor produktivem Einsatz ist ein automatisierter, verschlüsselter und regelmäßig praktisch getesteter Prozess einzurichten.
