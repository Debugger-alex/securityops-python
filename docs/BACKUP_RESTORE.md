# Backup und Wiederherstellung

## Status

Automatisierte Backups und ein erfolgreicher Restore-Test sind im Repository noch nicht eingerichtet. PostgreSQL-Daten liegen in Compose im persistenten Volume `postgres_data`; ein Volume allein ist kein Backup.

## Manueller PostgreSQL-Dump

Für einen geschützten, zugriffsbeschränkten Zielpfad und nachdem ein `.env` mit korrekter Datenbankkonfiguration eingerichtet ist:

```sh
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > securityops-$(date +%F).dump
```

In einer Shell, in der diese Variablen nicht gesetzt sind, die Benutzernamen/-datenbank aus `.env` kontrolliert setzen. Das Dump enthält vertrauliche Daten; verschlüsselt und getrennt vom Server aufbewahren. Zugangsdaten nicht in Shell-Historie oder Logs schreiben.

## Wiederherstellungstest

Restore ausschließlich in eine eigens dafür angelegte Testdatenbank ausführen, nie unaufgefordert in die produktive Datenbank. Mit `pg_restore --clean` können bestehende Tabellen und Daten gelöscht werden. Nach Restore Migrationstand, Benutzerzugriff, Kundenanzahl und fachliche Beziehungen prüfen und den Test dokumentieren.

Dieses Dokument beschreibt ein Verfahren, meldet aber keinen bereits ausgeführten Backup- oder Restore-Test.
