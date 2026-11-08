# Roadmap

Die verbindliche Priorisierung, Abhängigkeiten und der aktuelle `main`-/PR-Status stehen in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) und [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Reihenfolge nach fachlichen Abhängigkeiten

1. Sicherheits- und Betriebsgrundlagen: Authentifizierung/RBAC prüfen und ausbauen, Backup/Restore, TLS/Reverse Proxy, Monitoring, Auditgrenzen und Datenschutz.
2. Fachliche Abnahme der in `main` implementierten Module und Nachverfolgung offener Akzeptanzthemen (Issues #7–#10 offen; Issue #8 laut aktueller GitHub-Abfrage OPEN).
3. OWKS (gemergter PR #23, Issue #3 geschlossen) auf Objekten, Personal und Zuweisungen fachlich weiter prüfen; statische QR/NFC-Kennungen sind kein physischer Präsenznachweis.
4. Dokumenten-/Vertragsverwaltung (gemergter PR #24) sowie geschützte Dateiablage/Vertragsregeln anhand fachlicher Akzeptanz prüfen.
5. Rechnungswesen (Issue #7, offener PR #27) auf fachlich freigegebenen Verträgen und Leistungsnachweisen; PR-Vorschlag ist nicht in `main`, Steuerrichtigkeit/Abnahme nicht belegt.
6. E2E-/Last-/Sicherheits-/Restoretests und eine eigenständige Betriebsabnahme.

PR #26 ist gemergt und hat wöchentliche Verfügbarkeiten, Dienstwünsche/Sperrzeiten und Vertretungen in `main` ergänzt; Issue #10 bleibt für fachliche Abnahme offen. PR #27 ist offen und direkt gegen `main` gerichtet. Seine vorgeschlagene Migration `0017_billing` folgt auf den gemergten Head `0016_scheduling_availability`; eine offene Stapelabhängigkeit zu #26 besteht nicht.

PR #28 ist gemergt und hat Produktions-Compose, Redis-Rate-Limiting, separate Release-Migrationen, verschlüsselte Backup-/Restorewerkzeuge und Security-Scanning ergänzt. Issue #9 bleibt offen. CI- und synthetische Restoreprüfungen sind keine produktive Betriebsabnahme oder regelmäßige Restoreübung.

Reihenfolge stellt keinen Implementierungs- oder Rechtsstatus dar. Keine Produktions-, Rechts- oder Steuerfreigabe wird behauptet.
