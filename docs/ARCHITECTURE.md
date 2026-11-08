# Architektur

## Ziel und aktueller Stand

SecurityOps ist als modularer Monolith mit Python/FastAPI, SQLAlchemy, PostgreSQL, Alembic und React/TypeScript/Vite angelegt. Der aktuelle Code umfasst Identity/RBAC, Kunden-API und eine einzelne React-Oberfläche. Objekte, Personal, Planung, Zeiterfassung, OWKS, Dokumente, Verträge und Rechnungen sind noch nicht implementiert.

## Laufzeitkomponenten

- `backend/app/main.py`: FastAPI-Anwendung, Middleware und Router.
- `backend/app/identity_api.py`: Anmeldung, Benutzer, Rollen und Audit-Lesezugriff.
- `backend/app/api.py`: Kunden- und Dashboard-Endpunkte.
- `backend/app/auth.py`: Sitzungen, CSRF und Rechteabhängigkeiten.
- `backend/app/models.py`: SQLAlchemy-Modelle.
- `backend/migrations`: Alembic-Schemaänderungen.
- `frontend/src`: React-Anwendung und zentrale API-Aufrufe.
- `docker-compose.yml`: lokale Entwicklungsdienste PostgreSQL, API und Vite.

## Request- und Sicherheitsfluss

Der Browser authentifiziert sich mit einem zufälligen, HttpOnly-Session-Cookie. Der Server speichert nur den Hash des Session-Tokens. Schreibzugriffe erfordern einen CSRF-Cookie, den das Frontend als `X-CSRF-Token` wiederholt; der Server vergleicht Cookie, Header und gespeicherten Hash. Geschützte Endpunkte laden Benutzerrollen und Berechtigungen serverseitig. UI-Sichtbarkeit ist nur UX und keine Zugriffsgrenze.

## Fachmodule (Ziel)

Kunden → Objekte → Verträge und Dienste → Personal und Qualifikationen → Dienstplanung → Zeiterfassung → OWKS/Nachweise → Abrechnung. Gemeinsame Identity-, Dokumenten- und Audit-Funktionen dienen diesen Modulen. Objektzuweisungen müssen vor operativen Datenmodulen als serverseitige Zugriffsbeschränkung eingeführt werden.

## Betrieb

Compose dient derzeit der lokalen Entwicklung. Das Frontend läuft über Vite; Produktionsauslieferung, TLS-Reverse-Proxy und gemeinsamer Rate-Limit-Speicher sind noch offen. Migrationen werden derzeit beim API-Containerstart ausgeführt und sollen für Mehrfachreplikate in einen kontrollierten Deploy-Schritt verlagert werden.
