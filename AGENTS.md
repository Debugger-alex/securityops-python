# Arbeitsanweisungen für KI-Agenten

## Projektziel

SecurityOps ist eine deutschsprachige, modulare Verwaltungsplattform für einen Sicherheitsdienst. Die Zielarchitektur ist ein modularer Monolith mit Python/FastAPI, React/TypeScript und PostgreSQL. Die Anwendung wird schrittweise erweitert; bestehende Module und Daten müssen bei Änderungen funktionsfähig bleiben.

## Verbindliche Arbeitsweise

- Benutzeroberfläche, Fehlermeldungen und Dokumentation sind auf Deutsch.
- Geschäftslogik und Berechtigungsprüfungen gehören ins Backend; Frontend-Prüfungen ersetzen keine serverseitigen Kontrollen.
- Datenbankänderungen erfolgen ausschließlich über Alembic-Migrationen. Modelle, Schemas, API und Migrationen müssen zusammenpassen.
- Eingaben werden serverseitig validiert. Geschäftskritische Änderungen müssen transaktional und nachvollziehbar sein.
- Geldbeträge verwenden später Decimal/NUMERIC, Zeitpunkte UTC; lokale Zeitzonen sind bei Dienstplänen ausdrücklich zu behandeln.
- Geheimnisse gehören in Umgebungsvariablen, nie in Quellcode oder Git.
- Änderungen bleiben eng am Auftrag. Keine Fachmodule, Datenfelder oder externen Dienste ohne fachlichen Grund ergänzen.
- Tests für geändertes Verhalten ergänzen und passende Backend-Tests sowie Frontend-Build ausführen.

## Sicherheits- und Datenschutzanforderungen

- Keine echten Kunden-, Personal- oder Einsatzdaten in Tests, Beispielen oder Logs.
- Keine geschützte API ohne serverseitige Authentifizierung und Autorisierung nach außen freigeben.
- Zugriffe sind nach Rolle und bei operativen Daten zusätzlich nach Objektzuweisung zu prüfen.
- Kritische Wachbuch- und Abrechnungsdaten nicht stillschweigend überschreiben; Korrekturen müssen nachvollziehbar sein.
- Sensible Dokumente ausschließlich über autorisierte Backend-Endpunkte bereitstellen.
- Vor produktivem Einsatz sind mindestens Login, RBAC, Audit-Protokoll, TLS, Backups/Wiederherstellung und Sicherheitsprüfungen erforderlich.

## Ausbaureihenfolge

Das aktuelle Grundgerüst enthält PostgreSQL, die Kundenverwaltung und ein Dashboard. Darauf aufbauend zuerst Identity/Rollen und Auditierung ergänzen, danach Objekte und Ansprechpartner. Verträge, Aufträge, Personal, Dienstplanung, OWKS, Dokumente, Abrechnung und Integrationen folgen als getrennte Fachmodule.
