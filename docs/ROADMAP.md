# Roadmap

Die verbindliche Priorisierung, Abhängigkeiten und der aktuelle `main`-/PR-Status stehen in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) und [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Reihenfolge nach fachlichen Abhängigkeiten

1. Sicherheits- und Betriebsgrundlagen: Authentifizierung/RBAC prüfen und ausbauen, Backup/Restore, TLS/Reverse Proxy, Monitoring, Auditgrenzen und Datenschutz.
2. Fachliche Abnahme der in `main` implementierten Module und Nachverfolgung offener Akzeptanzthemen (Issues #7–#10 offen; Issue #8 laut aktueller GitHub-Abfrage OPEN).
3. OWKS (gemergter PR #23, Issue #3 geschlossen) auf Objekten, Personal und Zuweisungen fachlich weiter prüfen; statische QR/NFC-Kennungen sind kein physischer Präsenznachweis.
4. Dokumenten-/Vertragsverwaltung (gemergter PR #24) sowie geschützte Dateiablage/Vertragsregeln anhand fachlicher Akzeptanz prüfen.
5. Rechnungswesen (Issue #7, offener PR #27) auf fachlich freigegebenen Verträgen und Leistungsnachweisen; PR-Vorschlag ist nicht in `main`, Steuerrichtigkeit/Abnahme nicht belegt.
6. E2E-/Last-/Sicherheits-/Restoretests und eine eigenständige Betriebsabnahme.

PR #26 schlägt zusätzliche Dienstplan-Verfügbarkeiten/Vertretungen vor und ist offen; sein aktueller CI-Lauf ist grün. PR #27 ist auf #26 gestapelt und ergänzt Rechnungswesen nachgelagert mit `0017_billing` nach `0016_scheduling_availability`; die gestapelte Migrationenkette ist linear, die Abhängigkeit muss bei Integration erhalten bleiben.

PR #28 ist ein offener, direkt auf `main` basierter Vorschlag für Produktionshärtung (Issue #9), einschließlich verschlüsseltem Backup-/Restore-Test und Security-Scanning. Der aktuelle Restore-CI-Job ist fehlgeschlagen; das ist weder Teil von `main` noch ein nachgewiesener Restore-/Produktionsstatus.

Reihenfolge stellt keinen Implementierungs- oder Rechtsstatus dar. Keine Produktions-, Rechts- oder Steuerfreigabe wird behauptet.
