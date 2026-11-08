# Architektur

## Ziel und aktueller Stand

SecurityOps ist als modularer Monolith mit Python/FastAPI, SQLAlchemy, PostgreSQL, Alembic und React/TypeScript/Vite angelegt. Der aktuelle Code umfasst Identity/RBAC, Kunden-, Objekt-, Personal-, Planungs- und Zeiterfassungsverwaltung, das OWKS-Wachbuch sowie Dokumenten- und Vertragsverwaltung mit getrennten Verwaltungsansichten. Rechnungswesen ist nicht implementiert.

## Laufzeitkomponenten

- `backend/app/main.py`: FastAPI-Anwendung, Middleware und Router.
- `backend/app/identity_api.py`: Anmeldung, Benutzer, Rollen und Audit-Lesezugriff.
- `backend/app/api.py`: Kunden-, Objekt- und Dashboard-Endpunkte einschließlich objektbezogener Zugriffskontrolle.
- `backend/app/documents_contracts_api.py`: geschützte Dokument-, Freigabe-, Vertrags- und Erinnerungsrouten.
- `backend/app/document_storage.py`: Upload-Prüfung sowie privater Dateispeicher ohne öffentliche Dateipfade.
- `backend/app/auth.py`: Sitzungen, CSRF und Rechteabhängigkeiten.
- `backend/app/models.py`: SQLAlchemy-Modelle.
- `backend/migrations`: Alembic-Schemaänderungen.
- `frontend/src`: React-Anwendung mit Kunden-, Objekt-, Personal-, Planungs-, Zeiterfassungs-, OWKS- und Dokumenten-/Vertragsverwaltung.
- `docker-compose.yml`: lokale Entwicklungsdienste PostgreSQL, API, Vite und persistenter privater Dokumentenspeicher.
- `.github/workflows/ci.yml`: Backendtests, Migrationen auf einem temporären PostgreSQL-Dienst und Frontend-Build bei Pull Requests und Änderungen an `main`.

## Request- und Sicherheitsfluss

Der Browser authentifiziert sich mit einem zufälligen, HttpOnly-Session-Cookie. Der Server speichert nur den Hash des Session-Tokens. Schreibzugriffe erfordern einen CSRF-Cookie, den das Frontend als `X-CSRF-Token` wiederholt; der Server vergleicht Cookie, Header und gespeicherten Hash. Geschützte Endpunkte laden Benutzerrollen und Berechtigungen serverseitig. UI-Sichtbarkeit ist nur UX und keine Zugriffsgrenze.

Dokumentdateien werden nicht als statische Ressourcen oder öffentliche API-Pfade gemountet. Uploads werden begrenzt in Speicher gelesen, anhand Endung, deklarierter MIME-Angabe und Dateisignatur geprüft, mit zufälliger Storage-ID in einem privaten Verzeichnis abgelegt und ausschließlich nach serverseitiger Berechtigungs-/Objektprüfung als Download-Response ausgegeben. Dateiversion, Metadaten, Auditereignis und Historie werden innerhalb derselben Datenbanktransaktion gespeichert; bei fehlgeschlagenem Commit wird die neu geschriebene Datei entfernt. Bereits gespeicherte Versionen werden nicht überschrieben.

Die Erinnerungsplanung persistiert Fristdatensätze in PostgreSQL. Ein eindeutiger Schlüssel und `ON CONFLICT DO NOTHING` machen die manuelle Generierung mehrprozesssicher. Ein periodischer Worker, Mail-/Push-Versand und ein Virenscanner sind nicht Bestandteil der Architektur.

## Fachmodule (Ziel)

Kunden → Objekte → Verträge und Dienste → Personal und Qualifikationen → Dienstplanung → Zeiterfassung → OWKS/Nachweise → Abrechnung. Gemeinsame Identity-, Dokumenten- und Audit-Funktionen dienen diesen Modulen. Die Objektverwaltung besitzt bereits serverseitige Zugriffsprüfungen und Zuweisungen auf Benutzerkonten; diese ersetzen noch keine Personalverwaltung.

## Betrieb

Compose dient derzeit der lokalen Entwicklung. Das Frontend läuft über Vite; Produktionsauslieferung, TLS-Reverse-Proxy und gemeinsamer Rate-Limit-Speicher sind noch offen. Migrationen werden derzeit beim API-Containerstart ausgeführt und sollen für Mehrfachreplikate in einen kontrollierten Deploy-Schritt verlagert werden. CI führt die Migrationen unabhängig davon auf einem kurzlebigen PostgreSQL-17-Dienst aus; dies ersetzt keine Prüfung in der Zielbetriebsumgebung.
