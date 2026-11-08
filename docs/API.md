# API-Übersicht

Die aktuelle API ist unter `/api/v1` versioniert. OpenAPI/Swagger ist während des Entwicklungsbetriebs über `/docs` erreichbar.

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/health/live` | öffentlich, Prozessstatus |
| GET | `/health/ready` | öffentlich, Datenbankverbindung |
| POST | `/api/v1/auth/login` | öffentlich, Rate-Limit 5/min pro Prozess |
| GET | `/api/v1/auth/me` | angemeldete Sitzung |
| POST | `/api/v1/auth/logout` | angemeldet + CSRF |
| POST | `/api/v1/auth/change-password` | angemeldet + CSRF; widerruft Sitzungen |
| GET | `/api/v1/users` | `users.read` |
| POST | `/api/v1/users` | `users.manage`; Administratorvergabe zusätzlich `users.manage_admin` |
| PATCH | `/api/v1/users/{user_id}` | `users.manage`; Administratoränderung zusätzlich `users.manage_admin` |
| GET | `/api/v1/roles` | `roles.read` |
| GET | `/api/v1/audit-logs` | `audit.read`; Limit 1–100 |
| GET | `/api/v1/customers` | `customers.read`; `q`, `status`, `include_archived`, `sort_by`, `sort_order`, `limit`, `offset` |
| POST | `/api/v1/customers` | `customers.create` + CSRF |
| GET | `/api/v1/customers/{customer_id}` | `customers.read` |
| PATCH | `/api/v1/customers/{customer_id}` | `customers.update` + CSRF |
| GET | `/api/v1/customers/{customer_id}/history` | `customers.read`; `limit`, `offset` |
| POST | `/api/v1/customers/{customer_id}/archive` | `customers.archive` + CSRF |
| POST | `/api/v1/customers/{customer_id}/reactivate` | `customers.archive` + CSRF |
| POST | `/api/v1/customers/{customer_id}/contacts` | `customers.update` + CSRF |
| PATCH | `/api/v1/customers/{customer_id}/contacts/{contact_id}` | `customers.update` + CSRF |
| DELETE | `/api/v1/customers/{customer_id}/contacts/{contact_id}` | `customers.update` + CSRF |
| GET | `/api/v1/dashboard` | `dashboard.read` |
| GET | `/api/v1/objects` | `objects.read`; `q`, `customer_id`, `status`, `include_archived`, `sort_by`, `sort_order`, `limit`, `offset` |
| POST | `/api/v1/objects` | `objects.create` + CSRF |
| GET | `/api/v1/objects/assignment-candidates` | `objects.assign` |
| GET | `/api/v1/objects/{object_id}` | `objects.read` + Objektzuweisung oder `objects.read_all` |
| PATCH | `/api/v1/objects/{object_id}` | `objects.manage` + Objektzuweisung oder `objects.manage_all` + CSRF |
| POST | `/api/v1/objects/{object_id}/archive` | `objects.archive` + Objektzugriff + CSRF |
| GET | `/api/v1/objects/{object_id}/history` | `objects.read` + Objektzugriff |
| GET | `/api/v1/objects/{object_id}/contacts` | `objects.read` + Objektzugriff |
| POST/PATCH/DELETE | `/api/v1/objects/{object_id}/contacts[/{contact_id}]` | `objects.manage` + Objektzuweisung oder `objects.manage_all` + CSRF |
| GET | `/api/v1/objects/{object_id}/assignments` | `objects.assign` + Objektzugriff |
| POST/DELETE | `/api/v1/objects/{object_id}/assignments[/{user_id}]` | `objects.assign` + Verwaltungszugriff + CSRF |
| GET | `/api/v1/objects/{object_id}/sensitive-data` | `objects.sensitive.read` + Objektzugriff |
| PUT | `/api/v1/objects/{object_id}/sensitive-data` | `objects.sensitive.write` + Objektzugriff + CSRF |

Kundenlisten blenden archivierte Datensätze standardmäßig aus. Die Sortierfelder sind `company_name`, `customer_number`, `created_at` und `status`; die Sortierrichtung ist `asc` oder `desc`. Die Suche berücksichtigt Kunden-, Kontakt- und Anschriftendaten.

Kunden können Geschäfts- und Rechnungsanschrift, Rechtsform, Umsatzsteuer-ID, Steuernummer und interne Notizen enthalten. Ansprechpartner werden separat verwaltet; pro Kunde kann höchstens einer als primär markiert sein. Kunden werden archiviert statt physisch gelöscht. Historieneinträge speichern Ereignis, Akteur, Zeitpunkt und geänderte Feldnamen, aber keine vorherigen/neuen Feldwerte.

Objekte sind einem nicht archivierten Kunden zugeordnet. Benutzer ohne globale Objektberechtigung sehen und verwalten nur ihnen zugewiesene Objekte; neue Objekte weisen den Ersteller automatisch zu. Alarm-, Notfall-, Schlüssel- und Zutrittsangaben werden separat AES-GCM-verschlüsselt und nur über die speziell berechtigten Endpunkte geliefert. Dafür muss `OBJECT_DATA_ENCRYPTION_KEY` als URL-sichere Base64-Kodierung eines 32-Byte-Schlüssels gesetzt sein; ohne Schlüssel schlagen diese Zugriffe ausdrücklich fehl.

Schreibzugriffe nutzen den Session-Cookie und müssen `X-CSRF-Token` senden. Archivierte Kunden und Objekte können nicht geändert werden. Nicht aufgeführte Fachmodule und Endpunkte sind nicht implementiert.
