# Roadmap

Die verbindliche Priorisierung, Abhängigkeiten und der aktuelle `main`-/PR-Status stehen in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) und [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Reihenfolge nach fachlichen Abhängigkeiten

1. Sicherheits- und Betriebsgrundlagen: Authentifizierung/RBAC prüfen und ausbauen, Backup/Restore, TLS/Reverse Proxy, Monitoring, Auditgrenzen und Datenschutz.
2. Fachliche Abnahme der in `main` implementierten Module und Nachverfolgung offener Akzeptanzthemen (Issues #7–#10 offen; Issue #8 laut aktueller GitHub-Abfrage OPEN).
3. OWKS (gemergter PR #23, Issue #3 geschlossen) auf Objekten, Personal und Zuweisungen fachlich weiter prüfen; statische QR/NFC-Kennungen sind kein physischer Präsenznachweis.
4. Dokumenten-/Vertragsverwaltung (gemergter PR #24) sowie geschützte Dateiablage/Vertragsregeln anhand fachlicher Akzeptanz prüfen.
5. Rechnungswesen (Issue #7, PR #27 gemergt) auf fachlich freigegebenen Verträgen und Leistungsnachweisen fachlich abnehmen; Steuer-/Buchhaltungsrichtigkeit ist nicht belegt.
6. E2E-/Last-/Sicherheits-/Restoretests und eine eigenständige Betriebsabnahme.

PR #26 ist gemergt und hat wöchentliche Verfügbarkeiten, Dienstwünsche/Sperrzeiten und Vertretungen in `main` ergänzt; Issue #10 bleibt für fachliche Abnahme offen. PR #27 ist gemergt; Migration `0017_billing` folgt auf `0016_scheduling_availability` und Rechnungswesen ist in `main`. Issue #7 bleibt trotz Merge offen, bis die fachlichen Kriterien abgeglichen sind.

PR #28 ist gemergt und hat Produktions-Compose, Redis-Rate-Limiting, separate Release-Migrationen, verschlüsselte Backup-/Restorewerkzeuge und Security-Scanning ergänzt. PR #31 ist ebenfalls gemergt und ergänzt optionales TOTP-MFA, Recovery-Codes, Sitzungsliste/-widerruf und administrativen Passwortreset. Issue #9 bleibt offen. CI- und synthetische Restoreprüfungen sind keine produktive Betriebsabnahme oder regelmäßige Restoreübung; MFA ist keine unabhängige Sicherheitsabnahme.

Reihenfolge stellt keinen Implementierungs- oder Rechtsstatus dar. Keine Produktions-, Rechts- oder Steuerfreigabe wird behauptet.
