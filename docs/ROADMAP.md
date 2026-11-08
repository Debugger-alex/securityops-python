# Roadmap

Die verbindliche Priorisierung, Abhängigkeiten und der aktuelle `main`-/PR-Status stehen in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) und [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Reihenfolge nach fachlichen Abhängigkeiten

1. Sicherheits- und Betriebsgrundlagen: Authentifizierung/RBAC prüfen und ausbauen, Backup/Restore, TLS/Reverse Proxy, Monitoring, Auditgrenzen und Datenschutz.
2. Formale Abnahme der bereits in `main` implementierten Module Kunden/Objekte/Personal/Planung/Zeiterfassung (offene Issues #2, #4, #10 nicht vor Abnahme schließen).
3. OWKS (Issue #3, offener PR #23) auf Objekten, Personal und Zuweisungen; erst nach Review/Merge Bestandteil von `main`.
4. Dokumente und Verträge (Issue #8, offener Folge-PR #24) nach Prüfung der PR-#23-Abhängigkeit und des Datei-/Datenschutzkonzepts.
5. Rechnungswesen (Issue #7) auf fachlich freigegebenen Verträgen und Leistungsnachweisen.
6. E2E-/Last-/Sicherheits-/Restoretests und eine eigenständige Betriebsabnahme.

Reihenfolge stellt keinen Implementierungs- oder Rechtsstatus dar. Keine Produktions-, Rechts- oder Steuerfreigabe wird behauptet.
