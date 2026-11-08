# Architektur

## Ist-Architektur auf `main`

SecurityOps ist ein modular gedachter, derzeit noch zentral organisierter Monolith. Die API-Router sind nach fachlichen Dateien getrennt, die SQLAlchemy-Modelle liegen jedoch gemeinsam in `backend/app/models.py`, und das Frontend ist eine gemeinsame React-Anwendung ohne eigenständige Modul-Bundles. PostgreSQL ist die Betriebsdatenbank; Alembic verwaltet Schemaänderungen. Docker Compose umfasst ein Produktionssetup und ein getrenntes Entwicklungs-Override.

```mermaid
flowchart LR
    Browser["Browser / React UI"]
    UI["React / TypeScript / Vite<br/>statisches Frontend"]
    Web["Nginx<br/>unprivilegierter Webserver"]
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
    Redis[("Redis<br/>Rate-Limit-Speicher")]
    Migrations["Alembic-Release-Schritt<br/>0001–0016 auf main"]
    CI["GitHub Actions<br/>PostgreSQL · Tests · Build · Docker · Security · Restore"]
    Browser -->|"HTTP(S)"| Web
    Web -->|"statischer Build"| Browser
    Browser -->|"/api/v1 · Session-Cookie · CSRF-Header"| Web
    Web -->|"Reverse Proxy /api/"| API
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
    API --> Redis
    Migrations --> DB
    CI --> API
    CI --> UI
    CI --> DB
```

## Request- und Berechtigungsfluss

`main.py` registriert Router aus `api.py`, `personnel_api.py`, `scheduling_api.py`, `time_tracking_api.py`, `time_tracking_surcharges.py`, `documents_contracts_api.py`, `identity_api.py` und `owks_api.py` unter `/api/v1`; die Health-Endpunkte liegen außerhalb des Präfixes. Authentifizierte Requests lesen ein zufälliges opaque Session-Cookie. Gespeichert wird der Hash des Session-Tokens; Berechtigungen werden aus Benutzerrollen und Rollenrechten serverseitig ermittelt. Für zustandsändernde authentifizierte Requests müssen CSRF-Cookie und `X-CSRF-Token` übereinstimmen und der gespeicherte Tokenhash passen. Objekt-/Personal-Scope ist zusätzlich zu Modulrechten relevant; Mitarbeiter-Objektzuweisungen werden gegen den Objektzugriff geprüft. Frontend-Sichtbarkeit ist keine Sicherheitsgrenze.

`/health/live` prüft nur den Prozess. `/health/ready` prüft Datenbank und in Produktion Redis und liefert bei Nichtverfügbarkeit HTTP 503. Das Produktions-Compose-Setup liefert statische Frontenddateien über Nginx; TLS wird von einem separat zu betreibenden Reverse Proxy terminiert. Nginx setzt Security-Header. Der API-Prozess nutzt in Produktion Redis für gemeinsam geteilte Rate-Limit-Zähler; Proxy-Header werden nur von konfigurierten vertrauenswürdigen Hops übernommen.

## Daten- und Integritätsgrenzen

Geschäftsdaten und Benutzerrechte liegen in PostgreSQL. Die fachlichen Tabellen, Beziehungen und Constraints stehen in [`DATABASE.md`](DATABASE.md). Migrationen sind eine lineare Alembic-Kette bis Revision `0016_scheduling_availability` auf `main`. Revision `0014_owks_wachbuch` ergänzt OWKS, `0015_documents_contracts` darauf aufbauend Dokumente und Verträge, `0016_scheduling_availability` Mitarbeiter-Verfügbarkeiten und Dienstwünsche. PRs #23, #24 und #26 sind gemergt.

Mehrere Datenbereiche haben separate sensitive Tabellen und Endpunkte. Qualifikationsdateien und OWKS-Anhänge werden in PostgreSQL gespeichert; allgemeine Dokumentversionen liegen in einem konfigurierten privaten lokalen Dateispeicher und werden über geschützte Endpunkte gelesen. Ein externer Datei-/Objektspeicher, KMS/Schlüsselrotation und Malware-Prüfung sind nicht vorhanden. Für Planungs- und Zeiterfassungsoperationen bestehen Datenbankconstraints und PostgreSQL-Advisory-Locks; OWKS nutzt zusätzlich einen Hintergrundmonitor und Advisory-Locks. Details stehen in der Datenbank-, API- und Sicherheitsdokumentation.

## Deployment und CI

Das Produktions-Compose-Setup startet PostgreSQL, Redis, einen separaten einmaligen Alembic-Release-Schritt, API und Nginx für statische Frontenddateien. Ein separates Compose-Override stellt den lokalen Vite-Entwicklungsserver und HTTP-spezifische Einstellungen bereit. GitHub Actions prüft Backend und Migrationen auf PostgreSQL, Frontend-Build/Tests, Containerimages, Sicherheitsanalyse und einen isolierten synthetischen Backup-/Restorelauf. CI-Erfolg belegt weder reale Betriebsfähigkeit noch Produktionsfreigabe.

## Modulgrenzen und offene Arbeit

OWKS-Wachbuch, Dokumenten-/Vertragsfunktionen, Dienstplan-Verfügbarkeiten und Teile der Produktionshärtung sind in `main` integriert. Rechnungswesen ist nicht implementiert; offener PR #27 ergänzt es als Änderung auf aktuellem `main` mit `0017_billing` nach `0016_scheduling_availability`. Das ist keine unabhängige fachliche, steuerliche oder produktive Abnahme. Der modulare Monolith ist nicht in getrennte Services aufgeteilt und das ist keine stillschweigende Zielanforderung.
