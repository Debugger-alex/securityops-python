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
| GET | `/api/v1/customers` | `customers.read`; `q`, `limit`, `offset` |
| POST | `/api/v1/customers` | `customers.create` + CSRF |
| GET | `/api/v1/customers/{customer_id}` | `customers.read` |
| PATCH | `/api/v1/customers/{customer_id}` | `customers.update` + CSRF |
| GET | `/api/v1/dashboard` | `dashboard.read` |

Schreibzugriffe nutzen den Session-Cookie und müssen `X-CSRF-Token` senden. Nicht aufgeführte Fachmodule und Endpunkte sind nicht implementiert.
