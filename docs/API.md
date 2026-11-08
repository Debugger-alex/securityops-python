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
| GET | `/api/v1/employees/linked-user-candidates` | `employees.manage`; `employee_id` optional for editing the current link |
| GET | `/api/v1/employees/object-assignment-candidates` | `employees.manage` + `objects.assign`; only objects within the caller's write scope |
| GET | `/api/v1/employees/{employee_id}/objects` | `employees.read`; active assignments through the linked user account |
| GET | `/api/v1/employees/{employee_id}/object-assignment-history` | `employees.read`; `limit`, `offset` |
| POST/DELETE | `/api/v1/employees/{employee_id}/objects/{object_id}` | `employees.manage` + `objects.assign` and object write scope; CSRF; POST assigns, DELETE ends |
| GET/POST | `/api/v1/employees/{employee_id}/qualifications` | Lesen: `employees.read`; Schreiben: `employees.manage` + CSRF |
| PATCH | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}` | `employees.manage` + CSRF |
| POST | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}/archive` | `employees.manage` + CSRF |
| GET | `/api/v1/employees/{employee_id}/qualification-documents` | `employees.documents.read` |
| POST | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}/documents` | `employees.documents.manage` + CSRF; PDF/PNG/JPEG, max. 10 MiB |
| GET | `/api/v1/employees/{employee_id}/qualifications/{qualification_id}/documents/{document_id}` | `employees.documents.read`; `download=true` forces attachment |
| GET | `/api/v1/employees/qualifications/expiring` | `employees.read`; `days` |
| GET/POST | `/api/v1/employees/{employee_id}/absences` | Lesen: `employees.absences.read`; Schreiben: `employees.absences.manage` + CSRF |
| PATCH | `/api/v1/employees/{employee_id}/absences/{absence_id}` | `employees.absences.manage` + CSRF |
| GET | `/api/v1/employees/{employee_id}/sensitive` | `employees.sensitive.read` |
| PATCH | `/api/v1/employees/{employee_id}/sensitive` | `employees.sensitive.manage` + CSRF |
| GET | `/api/v1/scheduling/settings` | `scheduling.read` |
| PATCH | `/api/v1/scheduling/settings` | `scheduling.manage` + CSRF |
| GET | `/api/v1/scheduling/shifts` | `scheduling.read`; `from_date`, `to_date`, `employee_id`, `object_id`, `include_cancelled`, `limit`, `offset` |
| POST | `/api/v1/scheduling/shifts` | `scheduling.manage` + Objektzugriff + CSRF; legt einen Entwurf an |
| PATCH | `/api/v1/scheduling/shifts/{shift_id}` | `scheduling.manage` + Objektzugriff + CSRF |
| POST | `/api/v1/scheduling/shifts/{shift_id}/publish` oder `/cancel` | `scheduling.manage` + Objektzugriff + CSRF |
| GET | `/api/v1/scheduling/shifts/{shift_id}/history` | `scheduling.read` und sichtbarer Objekt-/Personalbereich |
| GET | `/api/v1/dashboard` | `dashboard.read` |

Kundenlisten blenden archivierte Datensätze standardmäßig aus. Sie können nach Kundenstatus (`status`) und Vertragsstatus (`contract_status`) filtern. Die Sortierfelder sind `company_name`, `customer_number`, `created_at`, `status` und `contract_status`; die Sortierrichtung ist `asc` oder `desc`. Die Suche berücksichtigt Kunden-, Kontakt-, Anschrift- und Websitedaten.

Kunden können Geschäfts- und Rechnungsanschrift, Rechtsform, Website, Vertragsstatus, Umsatzsteuer-ID, Steuernummer und interne Notizen enthalten. Websites müssen HTTP- oder HTTPS-URLs sein. Vertragsstatuswerte: `none` (kein Vertrag), `draft` (in Vorbereitung), `active` (aktiv), `expired` (abgelaufen), `terminated` (beendet). Ansprechpartner werden separat verwaltet; pro Kunde kann höchstens einer als primär markiert sein. Kunden werden archiviert statt physisch gelöscht. Historieneinträge speichern Ereignis, Akteur, Zeitpunkt und geänderte Feldnamen; das Audit-Protokoll hält dieselben geänderten Bereiche fest, aber keine vorherigen/neuen Feldwerte.

Objektlisten und normale Objektdetails enthalten keine Sicherheits-, Zutritts- oder Notfallangaben. Diese Felder werden ausschließlich über die getrennten `/security`-Endpunkte mit separaten Berechtigungen ausgeliefert. Objektlisten und Detail-Endpunkte wenden den Objektzugriff serverseitig an; Nutzer ohne globale Rechte sehen nur zugewiesene Objekte. Zuweisungen können derzeit aktive Konten mit Mitarbeiter- oder Objektleitungsrolle enthalten. Die Kunden-Detailansicht zeigt zugeordnete Objekte über die nach `objects.read` geschützte Objektliste; nicht erreichbare Objekte werden nicht offengelegt. Objektkontakte werden einzeln geändert oder gelöscht; ein allgemeines Objekt-PATCH ersetzt sie nicht.

Personalantworten enthalten keine Anschrift, Notfallkontakt- oder internen Notizfelder; diese liegen getrennt und benötigen `employees.sensitive.read` beziehungsweise `employees.sensitive.manage`. Abwesenheiten und Qualifikationsdateien haben eigene Les-/Schreibrechte. Dateien werden mit Größenlimit, Dateiendung, gemeldetem MIME-Typ und Dateisignatur geprüft, als unveränderliche Versionen in PostgreSQL gespeichert und ausschließlich über autorisierte API-Endpunkte ausgeliefert. Mitarbeiterkonten verknüpfen Personalakten mit den bestehenden `object_assignments`; beide Verwaltungswege protokollieren Zuweisungen und Beendigungen in der Personal- und Objekthistorie. Archivierung und Beendigung des Arbeitsverhältnisses beenden aktive Objektzuweisungen.

Dienstzeiten werden als lokale, offsetfreie `starts_at_local`-/`ends_at_local`-Werte in der konfigurierten IANA-Zeitzone angefragt und als UTC-Zeitpunkte gespeichert/zurückgegeben. Bei doppelten Ortszeiten kann `starts_at_fold` beziehungsweise `ends_at_fold` den ersten oder zweiten Zeitpunkt wählen; nicht existierende Ortszeiten bei der Zeitumstellung werden abgewiesen. Filter `from_date`/`to_date` sind inklusive lokale Kalendertage in der eingestellten Zeitzone. `scheduling.read`-Antworten beachten zusätzlich Personal- und Objektzugriff; Konten ohne globales Leserecht sehen nur eigene Personal- und/oder zugewiesene Objektbereiche.

Anlage, Änderung und Veröffentlichung prüfen Beschäftigungsstatus/-zeitraum, aktive Objektzuweisung, offene oder genehmigte Abwesenheiten, geforderte gültige Qualifikationen, zeitliche Überschneidungen und den konfigurierten Mindestabstand. Konflikte liefern HTTP 409; bei Konflikten enthält `detail.conflicts` Codes und deutsche Meldungen. PostgreSQL schützt zusätzlich mit einem partiellen GiST-Exclusion-Constraint vor überlappenden Schichten desselben Mitarbeiters (abgesagte Schichten ausgenommen); transaktionsgebundene Advisory Locks serialisieren die API-Konfliktprüfung pro Mitarbeiter. Diese Regeln sind Planungsprüfungen, keine automatische arbeitsrechtliche Konformitätsprüfung. Individuelle regelmäßige Verfügbarkeitsfenster sind nicht Teil des vorhandenen Personalmodells; Verfügbarkeit wird aus Beschäftigungszeitraum, Abwesenheiten und bereits geplanten Diensten abgeleitet.

Schreibzugriffe nutzen den Session-Cookie und müssen `X-CSRF-Token` senden. Archivierte Kunden müssen vor Änderungen reaktiviert werden. Nicht aufgeführte Fachmodule und Endpunkte sind nicht implementiert.
