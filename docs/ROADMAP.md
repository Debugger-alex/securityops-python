# Roadmap

Die priorisierte und mit Status versehene Umsetzungsliste steht in [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md). Die Phasen unten sind langfristige Zielbereiche, keine Behauptung, dass diese Funktionen bereits existieren.

PR #18 ist in `main` gemergt (Merge-Commit `c8d4fbe203d179b7c4b620d604409c7217478033`); Backend/PostgreSQL, Frontend einschließlich Vitest und Docker CI waren grün, Issue #6 ist geschlossen. Issue #2 bleibt bis zur formalen Abnahme offen. Der Feature-Branch `satan1800de-eng-dienstplanung-besetzung-konfliktpruefung` bearbeitet Issue #10; PostgreSQL-CI und Review stehen aus. Issues werden nicht vor geprüfter Akzeptanz geschlossen, und Produktions-/Rechtsprüfungen bleiben separat.

1. **Phase 1 – Sicherheit und Grundlagen:** RBAC-Rechteausweitung schließen, sichere Cookie-Standards, vollständiger Ist-Audit und Dokumentation; PostgreSQL-/Betriebsprüfungen [#9](https://github.com/Xonni-star/securityops-python/issues/9).
2. **Phase 2 – Kunden:** Anschriften, Ansprechpartner, Archivierung, Historie, Filter, Sortierung und vollständige Oberfläche sind in `main`; Issue #6 ist nach PR #18 geschlossen.
3. **Phase 3 – Objekte:** Backend, API und Frontend für kundenbezogene Objekte, Anschriften, Kontakte, Archivierung, Historie, Zuweisungen und separate Sicherheitsdaten sind in `main`. Issue #2 bleibt bis zur formalen Abnahme der Akzeptanzkriterien offen.
4. **Phase 4 – Personal:** Stammdaten, Qualifikationen, Ablaufwarnungen, Abwesenheiten und sensible Berechtigungsgrenzen sind in `main`; Issue #5 ist geschlossen.
5. **Phase 5 – Dienstplanung:** Issue #10 wird auf einem Feature-Branch bearbeitet. Der Scope umfasst Ansichten, Besetzung, Konfliktprüfung, Qualifikationen, konfigurierbare Zeitzonen/Ruhezeit und Änderungshistorie; CI und Review sind noch erforderlich.
6. **Phase 6 – Zeiterfassung:** Buchungen, Pausen, Korrekturfreigaben und konfigurierbare Zuschläge [#4](https://github.com/Xonni-star/securityops-python/issues/4).
7. **Phase 7 – OWKS:** Wachbuch, Kontrollen, QR/NFC, Anhänge, Offline-Warteschlange und Konfliktbehandlung [#3](https://github.com/Xonni-star/securityops-python/issues/3).
8. **Phase 8 – Dokumente/Verträge:** geschützter Dateispeicher, Versionierung, Ablaufüberwachung und Freigaben [#8](https://github.com/Xonni-star/securityops-python/issues/8).
9. **Phase 9 – Abrechnung:** Verträge, Rechnungskalkulation, unveränderbare Freigabe/Archivierung und Buchhaltungsexport [#7](https://github.com/Xonni-star/securityops-python/issues/7).
10. **Phase 10/11 – Dashboard und Qualität:** echte fachliche Kennzahlen, PostgreSQL-/E2E-/Sicherheitstests, Produktionsdeployment, Backup/Restore und Betriebsabnahme [#9](https://github.com/Xonni-star/securityops-python/issues/9).

Gesetzliche Arbeitszeit- und Steuerregeln dürfen nicht als automatische Rechtsfreigabe ausgewiesen werden; Konfiguration und fachliche Prüfung sind erforderlich.
