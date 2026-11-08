# Architektur

## Ist-Architektur auf `main`

SecurityOps ist ein modular gedachter, derzeit noch zentral organisierter Monolith. Die API-Router sind nach fachlichen Dateien getrennt, die SQLAlchemy-Modelle liegen jedoch gemeinsam in `backend/app/models.py`, und das Frontend ist eine gemeinsame React-Anwendung ohne eigenständige Modul-Bundles. PostgreSQL ist die Betriebsdatenbank; Alembic verwaltet Schemaänderungen. Docker Compose ist für lokale Entwicklung ausgelegt.

```mermaid
flowchart LR
    Browser["Browser"]
    UI["React / TypeScript / Vite<br/>Frontend"]
    API["FastAPI-Prozess<br/>app/main.py"]
    Identity["Identity / RBAC / Audit<br/>identity_api.py · auth.py"]
    Customer["Kunden / Objekte<br/>api.py"]
    People["Personal / Qualifikationen<br/>personnel_api.py"]
    Scheduling["Dienstplanung<br/>scheduling_api.py"]
    Time["Zeiterfassung / Zuschlagszeit<br/>time_tracking_api.py · time_tracking_surcharges.py"]
    OWKS["OWKS / Kontrollgänge<br/>owks_api.py · owks_scheduler.py"]
    Docs["Dokumente / Verträge<br/>documents_contracts_api.py"]
    Models["Gemeinsame SQLAlchemy-Modelle<br/>models.py"]
    DB[("PostgreSQL")]
    Migrations["Alembic-Migrationen<br/>0001–0015 auf main"]
    CI["GitHub Actions<br/>PostgreSQL · Tests · Build · Docker"]
    Browser --> UI
    UI -->|"HTTP /api/v1 · Session-Cookie · CSRF-Header"| API
    API --> Identity
    API --> Customer
    API --> People
    API --> Scheduling
    API --> Time
    API --> OWKS
    API --> Docs
    Identity --> Models
    Customer --> Models
    People --> Models
    Scheduling --> Models
    Time --> Models
    OWKS --> Models
    Docs --> Models
    Models --> DB
    Migrations --> DB
    CI --> API
    CI --> UI
    CI --> DB
```

## Request- und Berechtigungsfluss

`main.py` registriert Router aus `api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `documents_contracts_api.py`, `identity_api.py` und `owks_api.py` unter `/api/v1`; die Health-Endpunkte liegen außerhalb des Präfixes. Authentifizierte Requests lesen ein zufälliges opaque Session-Cookie. Gespeichert wird der Hash des Session-Tokens; Berechtigungen werden aus Benutzerrollen und Rollenrechten serverseitig ermittelt. Für zustandsändernde authentifizierte Requests müssen CSRF-Cookie und `X-CSRF-Token` übereinstimmen und der gespeicherte Tokenhash passen. Objekt-/Personal-Scope ist zusätzlich zu Modulrechten relevant. Frontend-Sichtbarkeit ist keine Sicherheitsgrenze.

`/health/live` prüft nur den Prozess. `/health/ready` versucht eine Datenbankabfrage und liefert bei nicht verfügbarer Datenbank HTTP 503. CORS wird aus `CORS_ORIGINS` geladen. Ein allgemeines Security-Header-/TLS-Middleware-Setup ist nicht vorhanden.

## Daten- und Integritätsgrenzen

Geschäftsdaten und Benutzerrechte liegen in PostgreSQL. Die fachlichen Tabellen, Beziehungen und Constraints stehen in [`DATABASE.md`](DATABASE.md). Migrationen sind eine lineare Alembic-Kette bis Revision `0015_documents_contracts` auf `main`. Revision `0014_owks_wachbuch` ergänzt OWKS, `0015_documents_contracts` darauf aufbauend Dokumente, Verträge und Erinnerungen; PR #23 und #24 sind gemergt.

Mehrere Datenbereiche haben separate sensitive Tabellen und Endpunkte. Qualifikationsdateien und OWKS-Anhänge werden in PostgreSQL gespeichert; allgemeine Dokumentversionen liegen in einem konfigurierten privaten lokalen Dateispeicher und werden über geschützte Endpunkte gelesen. Ein externer Datei-/Objektspeicher, KMS/Schlüsselrotation und Malware-Prüfung sind nicht vorhanden. Für Planungs- und Zeiterfassungsoperationen bestehen Datenbankconstraints und PostgreSQL-Advisory-Locks; OWKS nutzt zusätzlich einen Hintergrundmonitor und Advisory-Locks. Details stehen in der Datenbank-, API- und Sicherheitsdokumentation.

## Lokale Entwicklung und CI

Compose startet PostgreSQL 17, API und Vite-Devserver. Der API-Container führt Migrationen bei Start aus. Das ist kein koordinierter Release-Migrationsschritt für mehrere Replikate. CI führt Migrationen einmal auf temporärem PostgreSQL 17 aus, dann Backendtests; zusätzlich prüft sie Ruff, `npm run build`, `npm test` und baut beide Container-Images. CI-Erfolg belegt keine Produktionsfähigkeit.

## Modulgrenzen und offene Arbeit

OWKS-Wachbuch, Dokumenten-/Vertragsfunktionen sind in `main` integriert. Rechnungswesen ist nicht implementiert; ebenso bleibt die Produktionshärtung außerhalb einer bereitgestellten Produktionsarchitektur. Der modulare Monolith ist nicht in getrennte Services aufgeteilt und das ist keine stillschweigende Zielanforderung.
