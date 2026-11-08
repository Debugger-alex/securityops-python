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
| GET | `/api/v1/objects` | `objects.read`; `q`, `customer_id`, `status`, `include_archived`, `sort_by`, `sort_order`, `limit`, `offset` |
| POST | `/api/v1/objects` | `objects.manage` und `objects.manage_all` + CSRF |
| GET | `/api/v1/objects/{object_id}` | `objects.read` und globales Leserecht oder Objektzuweisung |
| PATCH | `/api/v1/objects/{object_id}` | `objects.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| POST | `/api/v1/objects/{object_id}/archive` | `objects.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| POST | `/api/v1/objects/{object_id}/reactivate` | `objects.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| GET | `/api/v1/objects/{object_id}/history` | `objects.read` und globales Leserecht oder Objektzuweisung |
| POST | `/api/v1/objects/{object_id}/contacts` | `objects.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| PATCH/DELETE | `/api/v1/objects/{object_id}/contacts/{contact_id}` | `objects.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| GET | `/api/v1/objects/assignment-candidates` | `objects.assign`; aktive Mitarbeiter- und Objektleitungskonten |
| GET/PUT | `/api/v1/objects/{object_id}/assignments` | `objects.assign` und globales Verwaltungsrecht oder Objektzuweisung; PUT + CSRF |
| GET | `/api/v1/objects/{object_id}/security` | `objects.sensitive.read` und globales Leserecht oder Objektzuweisung |
| PATCH | `/api/v1/objects/{object_id}/security` | `objects.sensitive.manage` und globales Verwaltungsrecht oder Objektzuweisung + CSRF |
| GET | `/api/v1/employees` | `employees.read`; `q`, `status`, `include_archived`, `sort_by`, `sort_order`, `limit`, `offset` |
| POST | `/api/v1/employees` | `employees.manage` + CSRF |
| GET | `/api/v1/employees/{employee_id}` | `employees.read` |
| PATCH | `/api/v1/employees/{employee_id}` | `employees.manage` + CSRF |
| POST | `/api/v1/employees/{employee_id}/archive` und `/reactivate` | `employees.manage` + CSRF |
| GET | `/api/v1/employees/{employee_id}/history` | `employees.read`; `limit`, `offset` |
| GET/POST | `/api/v1/employees/{employee_id}/qualifications` | Lesen: `employees.read`; Schreiben: `employees.manage` + CSRF |
| PATCH | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}` | `employees.manage` + CSRF |
| POST | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}/archive` | `employees.manage` + CSRF |
| GET | `/api/v1/employees/qualifications/expiring` | `employees.read`; `days` |
| GET/POST | `/api/v1/employees/{employee_id}/absences` | Lesen: `employees.absences.read`; Schreiben: `employees.absences.manage` + CSRF |
| PATCH | `/api/v1/employees/{employee_id}/absences/{absence_id}` | `employees.absences.manage` + CSRF |
| GET | `/api/v1/employees/{employee_id}/sensitive` | `employees.sensitive.read` |
| PATCH | `/api/v1/employees/{employee_id}/sensitive` | `employees.sensitive.manage` + CSRF |
| GET | `/api/v1/dashboard` | `dashboard.read` |

Kundenlisten blenden archivierte Datensätze standardmäßig aus. Die Sortierfelder sind `company_name`, `customer_number`, `created_at` und `status`; die Sortierrichtung ist `asc` oder `desc`. Die Suche berücksichtigt Kunden-, Kontakt- und Anschriftendaten.

Kunden können Geschäfts- und Rechnungsanschrift, Rechtsform, Umsatzsteuer-ID, Steuernummer und interne Notizen enthalten. Ansprechpartner werden separat verwaltet; pro Kunde kann höchstens einer als primär markiert sein. Kunden werden archiviert statt physisch gelöscht. Historieneinträge speichern Ereignis, Akteur, Zeitpunkt und geänderte Feldnamen, aber keine vorherigen/neuen Feldwerte.

Objektlisten und normale Objektdetails enthalten keine Sicherheits-, Zutritts- oder Notfallangaben. Diese Felder werden ausschließlich über die getrennten `/security`-Endpunkte mit separaten Berechtigungen ausgeliefert. Objektlisten und Detail-Endpunkte wenden den Objektzugriff serverseitig an; Nutzer ohne globale Rechte sehen nur zugewiesene Objekte. Zuweisungen können derzeit aktive Konten mit Mitarbeiter- oder Objektleitungsrolle enthalten. Objektkontakte werden einzeln geändert oder gelöscht; ein allgemeines Objekt-PATCH ersetzt sie nicht.

Personalantworten enthalten keine Anschrift, Notfallkontakt- oder internen Notizfelder; diese liegen getrennt und benötigen `employees.sensitive.read` beziehungsweise `employees.sensitive.manage`. Abwesenheiten haben eigene Les-/Schreibrechte. Mitarbeiterhistorien und Audit-Einträge speichern geänderte Feldnamen, keine vertraulichen Feldwerte. Qualifikationsnachweise enthalten derzeit Metadaten, keine hochgeladenen Dateien. Mitarbeiterakten sind noch nicht mit den bestehenden Objektzuweisungen verbunden.

Schreibzugriffe nutzen den Session-Cookie und müssen `X-CSRF-Token` senden. Archivierte Kunden müssen vor Änderungen reaktiviert werden. Nicht aufgeführte Fachmodule und Endpunkte sind nicht implementiert.
