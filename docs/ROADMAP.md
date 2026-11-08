# Roadmap

Die priorisierte und mit Status versehene Umsetzungsliste steht in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md). Die Phasen unten sind langfristige Zielbereiche, keine Behauptung, dass diese Funktionen bereits existieren.

Derzeit wird die Objektverwaltung auf dem aktuellen `main`-Stand vervollständigt. Die Stufen unten sind Langfristziele; nur die Kundenverwaltung und die vorhandene Objektverwaltung sind bereits im Quellcode umgesetzt. Objektfunktionen in Arbeit gelten erst nach erfolgreicher PostgreSQL-/CI-Prüfung und Review als abgeschlossen.

1. **Phase 1 – Sicherheit und Grundlagen:** RBAC-Rechteausweitung schließen, sichere Cookie-Standards, vollständiger Ist-Audit und Dokumentation; PostgreSQL-/Betriebsprüfungen [#9](https://github.com/Xonni-star/securityops-python/issues/9).
2. **Phase 2 – Kunden:** Anschriften, Ansprechpartner, Archivierung, Historie, Filter, Sortierung und vollständige Oberfläche [#6](https://github.com/Xonni-star/securityops-python/issues/6).
3. **Phase 3 – Objekte:** Backend, API und Frontend für kundenbezogene Objekte, Anschriften, Kontakte, Archivierung, Historie, Zuweisungen und separate Sicherheitsdaten sind auf dem Feature-Branch umgesetzt. PostgreSQL-Integrationsprüfung, CI und Review sind noch ausstehend; erst danach Issue #2 als abgeschlossen bewerten.
4. **Phase 4 – Personal:** Stammdaten, Qualifikationen, Ablaufwarnungen, Abwesenheiten und sensible Berechtigungsgrenzen [#5](https://github.com/Xonni-star/securityops-python/issues/5).
5. **Phase 5 – Dienstplanung:** Ansichten, Besetzung, Konfliktprüfung, Qualifikationen, nachvollziehbare Regeln und Änderungshistorie [#10](https://github.com/Xonni-star/securityops-python/issues/10).
6. **Phase 6 – Zeiterfassung:** Buchungen, Pausen, Korrekturfreigaben und konfigurierbare Zuschläge [#4](https://github.com/Xonni-star/securityops-python/issues/4).
7. **Phase 7 – OWKS:** Wachbuch, Kontrollen, QR/NFC, Anhänge, Offline-Warteschlange und Konfliktbehandlung [#3](https://github.com/Xonni-star/securityops-python/issues/3).
8. **Phase 8 – Dokumente/Verträge:** geschützter Dateispeicher, Versionierung, Ablaufüberwachung und Freigaben [#8](https://github.com/Xonni-star/securityops-python/issues/8).
9. **Phase 9 – Abrechnung:** Verträge, Rechnungskalkulation, unveränderbare Freigabe/Archivierung und Buchhaltungsexport [#7](https://github.com/Xonni-star/securityops-python/issues/7).
10. **Phase 10/11 – Dashboard und Qualität:** echte fachliche Kennzahlen, PostgreSQL-/E2E-/Sicherheitstests, Produktionsdeployment, Backup/Restore und Betriebsabnahme [#9](https://github.com/Xonni-star/securityops-python/issues/9).

Gesetzliche Arbeitszeit- und Steuerregeln dürfen nicht als automatische Rechtsfreigabe ausgewiesen werden; Konfiguration und fachliche Prüfung sind erforderlich.
