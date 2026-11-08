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
| POST | `/api/v1/time-tracking/start` | `time_tracking.create` oder `time_tracking.manage`; ordnet den aktuellen veröffentlichten Dienst zu |
| POST | `/api/v1/time-tracking/entries/{entry_id}/pause`, `/resume`, `/stop` | Berechtigter Eigentümer oder `time_tracking.manage`; CSRF |
| POST | `/api/v1/time-tracking/entries/manual` | `time_tracking.manage`; abgeschlossene UTC-Segmente als einreichungspflichtiger Nachtrag; CSRF |
| GET | `/api/v1/time-tracking/entries` | `time_tracking.read_own` oder `time_tracking.read_all`; optionale Filter `from_date`, `to_date`, `employee_id`, `object_id`, `customer_id`, `status` |
| POST | `/api/v1/time-tracking/entries/{entry_id}/corrections` | Eigentümer mit `time_tracking.correct_own` oder berechtigter Verwalter mit `time_tracking.correct_all`; Grund und neue Segmente erforderlich; CSRF |
| GET | `/api/v1/time-tracking/corrections` | `time_tracking.read_all`; `pending_only` standardmäßig `true` |
| POST | `/api/v1/time-tracking/entries/{entry_id}/approve` oder `/reject` | `time_tracking.approve` beziehungsweise `time_tracking.reject`; Ablehnung mit Grund; keine Selbstfreigabe; CSRF |
| POST | `/api/v1/time-tracking/corrections/{correction_id}/approve` oder `/reject` | `time_tracking.approve` beziehungsweise `time_tracking.reject`; Ablehnung mit Grund; CSRF |
| POST | `/api/v1/time-tracking/entries/{entry_id}/lock` | `time_tracking.manage`; nur freigegebene Buchungen; CSRF |
| GET | `/api/v1/time-tracking/reports` | `time_tracking.read_own` oder `time_tracking.read_all`; Zeitraum sowie optionale Mitarbeiter-/Objekt-/Kunden-/Statusfilter, `group_by=employee|object|customer|day|week|month` |
| GET | `/api/v1/time-tracking/reports/missing` | `time_tracking.read_all`; `from_date`, `to_date`; veröffentlichte Schichten ohne Buchung |
| GET | `/api/v1/time-tracking/export.csv` | `time_tracking.export`; Zeitraum sowie optionale Mitarbeiter-/Objekt-/Kundenfilter; nur freigegebene oder gesperrte Buchungen |
| GET/PATCH | `/api/v1/time-tracking/settings` | `time_tracking.surcharges.read` / `time_tracking.surcharges.manage`; Bundesland für Feiertagskalender |
| GET/POST | `/api/v1/time-tracking/surcharge-rules` | `time_tracking.surcharges.read` / `time_tracking.surcharges.manage`; unveränderliche Regeln mit Gültigkeit, Wert, Priorität und Kombinationsmodus |
| POST/GET | `/api/v1/time-tracking/entries/{entry_id}/surcharge-calculations` | `time_tracking.surcharges.manage` / `time_tracking.surcharges.read` und sichtbarer Eintrag; Berechnung versionieren/einsehen |
| GET | `/api/v1/time-tracking/reports/surcharges` | `time_tracking.surcharges.read` und `time_tracking.read_all`; aktueller, nicht veralteter Berechnungsnachweis je Buchung |
| GET | `/api/v1/time-tracking/export-surcharges.csv` | `time_tracking.export` und `time_tracking.surcharges.read`; freigegebene Zuschlagsnachweise |
| GET/POST | `/api/v1/time-tracking/periods` und `/periods/lock` | `time_tracking.periods.read` / `time_tracking.periods.lock`; endgültige Abrechnungsperiodensperren |
| GET | `/api/v1/owks/objects` | `owks.read`; nur aktive, berechtigte oder zugewiesene Objekte |
| GET/POST | `/api/v1/owks/objects/{object_id}/control-points` | Lesen: `owks.read`; Anlegen: `owks.manage`; Kennung wird nur bei Anlage einmal zurückgegeben |
| GET/POST | `/api/v1/owks/objects/{object_id}/routes` | Lesen: `owks.read`; Anlegen: `owks.manage`; Route darf nur Kontrollpunkte desselben Objekts enthalten |
| POST | `/api/v1/owks/objects/{object_id}/challenges` und `/api/v1/owks/scans` | `owks.write`; kurzlebige, benutzer-/objektgebundene Einmal-Challenge und QR-/NFC-Kontrollprüfung |
| GET | `/api/v1/owks/objects/{object_id}/events` | `owks.read`; Ereignisse, Übergaben, Kontrollen, Status und Konflikte |
| POST | `/api/v1/owks/events` und `/events/sync` | `owks.write`; Ereignis mit Idempotenzschlüssel; Offline-Kontrollscans werden als sichtbare Konflikte gespeichert, nicht als verifiziert gewertet |
| POST | `/api/v1/owks/events/{event_id}/status` und `/corrections` | `owks.manage`; Statusänderungen und begründete Korrekturen werden angehängt, Originalereignisse bleiben unverändert |
| POST/GET | `/api/v1/owks/events/{event_id}/attachments` und `/attachments/{attachment_id}` | Schreiben: `owks.write`; Lesen: `owks.read`; PDF/PNG/JPEG, maximal 10 MiB, Objektzugriff serverseitig geprüft |
| POST | `/api/v1/owks/routes/{route_id}/monitor` | `owks.manage`; löst dieselbe idempotente Prüfung wie der eingebaute Minuten-Monitor aus |
| GET | `/api/v1/dashboard` | `dashboard.read` |

Kundenlisten blenden archivierte Datensätze standardmäßig aus. Sie können nach Kundenstatus (`status`) und Vertragsstatus (`contract_status`) filtern. Die Sortierfelder sind `company_name`, `customer_number`, `created_at`, `status` und `contract_status`; die Sortierrichtung ist `asc` oder `desc`. Die Suche berücksichtigt Kunden-, Kontakt-, Anschrift- und Websitedaten.

Kunden können Geschäfts- und Rechnungsanschrift, Rechtsform, Website, Vertragsstatus, Umsatzsteuer-ID, Steuernummer und interne Notizen enthalten. Websites müssen HTTP- oder HTTPS-URLs sein. Vertragsstatuswerte: `none` (kein Vertrag), `draft` (in Vorbereitung), `active` (aktiv), `expired` (abgelaufen), `terminated` (beendet). Ansprechpartner werden separat verwaltet; pro Kunde kann höchstens einer als primär markiert sein. Kunden werden archiviert statt physisch gelöscht. Historieneinträge speichern Ereignis, Akteur, Zeitpunkt und geänderte Feldnamen; das Audit-Protokoll hält dieselben geänderten Bereiche fest, aber keine vorherigen/neuen Feldwerte.

Objektlisten und normale Objektdetails enthalten keine Sicherheits-, Zutritts- oder Notfallangaben. Diese Felder werden ausschließlich über die getrennten `/security`-Endpunkte mit separaten Berechtigungen ausgeliefert. Objektlisten und Detail-Endpunkte wenden den Objektzugriff serverseitig an; Nutzer ohne globale Rechte sehen nur zugewiesene Objekte. Zuweisungen können derzeit aktive Konten mit Mitarbeiter- oder Objektleitungsrolle enthalten. Die Kunden-Detailansicht zeigt zugeordnete Objekte über die nach `objects.read` geschützte Objektliste; nicht erreichbare Objekte werden nicht offengelegt. Objektkontakte werden einzeln geändert oder gelöscht; ein allgemeines Objekt-PATCH ersetzt sie nicht.

Personalantworten enthalten keine Anschrift, Notfallkontakt- oder internen Notizfelder; diese liegen getrennt und benötigen `employees.sensitive.read` beziehungsweise `employees.sensitive.manage`. Abwesenheiten und Qualifikationsdateien haben eigene Les-/Schreibrechte. Dateien werden mit Größenlimit, Dateiendung, gemeldetem MIME-Typ und Dateisignatur geprüft, als unveränderliche Versionen in PostgreSQL gespeichert und ausschließlich über autorisierte API-Endpunkte ausgeliefert. Mitarbeiterkonten verknüpfen Personalakten mit den bestehenden `object_assignments`; beide Verwaltungswege protokollieren Zuweisungen und Beendigungen in der Personal- und Objekthistorie. Archivierung und Beendigung des Arbeitsverhältnisses beenden aktive Objektzuweisungen.

Dienstzeiten werden als lokale, offsetfreie `starts_at_local`-/`ends_at_local`-Werte in der konfigurierten IANA-Zeitzone angefragt und als UTC-Zeitpunkte gespeichert/zurückgegeben. Bei doppelten Ortszeiten kann `starts_at_fold` beziehungsweise `ends_at_fold` den ersten oder zweiten Zeitpunkt wählen; nicht existierende Ortszeiten bei der Zeitumstellung werden abgewiesen. Filter `from_date`/`to_date` sind inklusive lokale Kalendertage in der eingestellten Zeitzone. `scheduling.read`-Antworten beachten zusätzlich Personal- und Objektzugriff; Konten ohne globales Leserecht sehen nur eigene Personal- und/oder zugewiesene Objektbereiche.

Anlage, Änderung und Veröffentlichung prüfen Beschäftigungsstatus/-zeitraum, aktive Objektzuweisung, offene oder genehmigte Abwesenheiten, geforderte gültige Qualifikationen, zeitliche Überschneidungen und den konfigurierten Mindestabstand. Konflikte liefern HTTP 409; bei Konflikten enthält `detail.conflicts` Codes und deutsche Meldungen. PostgreSQL schützt zusätzlich mit einem partiellen GiST-Exclusion-Constraint vor überlappenden Schichten desselben Mitarbeiters (abgesagte Schichten ausgenommen); transaktionsgebundene Advisory Locks serialisieren die API-Konfliktprüfung pro Mitarbeiter. Diese Regeln sind Planungsprüfungen, keine automatische arbeitsrechtliche Konformitätsprüfung. Individuelle regelmäßige Verfügbarkeitsfenster sind nicht Teil des vorhandenen Personalmodells; Verfügbarkeit wird aus Beschäftigungszeitraum, Abwesenheiten und bereits geplanten Diensten abgeleitet.

Schreibzugriffe nutzen den Session-Cookie und müssen `X-CSRF-Token` senden. Archivierte Kunden müssen vor Änderungen reaktiviert werden. Nicht aufgeführte Fachmodule und Endpunkte sind nicht implementiert.

## Zeiterfassung

`POST /time-tracking/start` startet eine offene Buchung für die verknüpfte Personalakte. Ohne `shift_id` wird ein gerade laufender veröffentlichter Dienst gesucht; mehrere passende Dienste werden abgewiesen. Ein Dienst ohne Dienstplan oder eine manuelle historische Buchung erfordert `time_tracking.manage` sowie Mitarbeiter-, Objekt- und Zeitraumangaben. Mitarbeiter und Objekt müssen aktiv und einander zugewiesen sein. Pro Mitarbeiter darf nur eine Buchung offen sein. PostgreSQL-Transaktions-Advisory-Locks serialisieren gleichzeitige Buchungsänderungen; partielle eindeutige Indizes schützen offene Einträge und Segmente zusätzlich.

`pause` beendet den aktuellen Arbeitsabschnitt und startet eine Pause; `resume` beendet diese Pause und startet einen neuen Arbeitsabschnitt. `stop` schließt den aktiven Abschnitt und reicht die Buchung ein. Arbeits-/Pausensegmente müssen in UTC mit Offset geliefert werden, sich abwechseln und lückenlos aufeinanderfolgen. Die Berechnung verwendet die gespeicherten Zeitpunkte ohne Rundung. Das Zeitkonto liefert Soll-/Ist-Sekunden, tatsächliche Pausendauer, geplante Pausen, Start-/Endabweichung und Zeitdifferenz. Berichte können nach Mitarbeiter, Objekt, Kunde, Tag, ISO-Kalenderwoche oder Monat gruppiert werden. „Mehrzeit gegenüber Dienstplan“ summiert nur positive Soll-/Ist-Abweichungen pro Schicht; eine tarifliche Überstunden- oder Zuschlagsberechnung ist nicht enthalten.

Zuschlagsregeln sind eigene, unveränderliche Datensätze mit Kategorie (Nacht, Samstag, Sonntag, gesetzlicher Feiertag oder betriebliche Regel), lokalem Zeitfenster, Gültigkeitsdaten, Prozent- oder Festwert, frei beschriebener Bezugs-/Einheit, Priorität und Kombinationsmodus. Feiertage verwenden den konfigurierten deutschen Ländercode und den `holidays`-Kalender; ohne Bundesland kann keine Feiertagsregel angelegt oder berechnet werden. Nachträgliche Änderungen werden als neue Regel angelegt. Pro Intervall gewinnt grundsätzlich die höchste Priorität. Gleichrangige exklusive Treffer führen zu HTTP 409; gleichrangig kombinierbare Regeln werden gemeinsam ausgewiesen. Eine Regel mit Modus `combine` kombiniert weitere passende kombinierbare Regeln; ein höher priorisierter exklusiver Treffer bleibt exklusiv. Nicht geleistete Pausenzeit ist nie zuschlagsfähig. Zeitfenstergrenzen, Mitternacht und DST-Offsetwechsel werden in `Europe/Berlin` (oder der konfigurierten Scheduling-Zeitzone) aufgeteilt. Die Berechnung speichert Arbeitssekunden, Regelkonfiguration, Zeitzone, Bundesland und Quellsegmente als Version; Korrekturen machen alte Nachweise im Zeitraumbericht als veraltet unsichtbar, erhalten sie aber in der Historie.

**Abrechnungsgrenze:** Es wird bewusst kein Geldbetrag errechnet. Das Modul enthält weder Mitarbeiter-Lohnbasis noch eine fachlich bestätigte Prozentbasis, Festzuschlagseinheit oder Rundungsregel. Bezugs-/Einheitenbeschreibung und konfigurierte Werte werden gespeichert; `calculated_amount` bleibt `null` und weist den Grund aus. Damit sind die gespeicherten Zuschlagszeiten und CSV-Nachweise nachvollziehbar, aber kein payroll-/abrechnungsfertiges Ergebnis. Diese Konventionen müssen vor einer Geldberechnung fachlich festgelegt werden.

Eine Abrechnungsperiode kann erst nach ihrem vollständigen Ablauf endgültig gesperrt werden, wenn alle enthaltenen Buchungen freigegeben/gesperrt sind, keine Buchung die Periodengrenze überschreitet und alle veröffentlichten Dienste eine freigegebene Buchung haben. Beim Sperren werden Berechnungssnapshots für die Buchungen angelegt. Es gibt keinen Entsperr-Endpunkt; Korrekturen und neue Berechnungen in gesperrten Zeiträumen werden abgewiesen. Die Zeitwerte werden unter einem transaktionsgebundenen PostgreSQL-Advisory-Lock gegen gleichzeitige Periodensperren und Änderungen geschützt.

## OWKS-Wachbuch

`owks.read` liefert nur Objekte, die global lesbar oder dem Benutzer zugewiesen sind. `owks.write` erlaubt Wachbucheinträge, Übergaben, Meldungen, Abweichungen und Kontrollen; die aktive Personalakte wird aus dem angemeldeten Konto ermittelt. Kontrollpunkte erhalten bei Anlage eine zufällige QR-/NFC-Kennung; gespeichert wird ausschließlich deren SHA-256-Hash. Die Kennung wird genau einmal in der Antwort ausgegeben und muss sicher auf einem passenden QR-/NFC-Träger hinterlegt werden. Eine Route kann nur Kontrollpunkte desselben Objekts enthalten.

Für eine Online-Kontrolle fordert die App zuerst eine fünf Minuten gültige, benutzer- und objektgebundene Challenge an. Der Server prüft Kennung, Objektzuweisung, Route, Einmalverwendung und Zeitstempel (maximal fünf Minuten Abweichung), ordnet den Scan der verknüpften Personalakte zu und protokolliert Wiederholungen, fremde Objektkennungen und Zeitabweichungen als kritische Manipulationsereignisse. Verspätete Scans werden als Warnung festgehalten. Ein eingebauter Hintergrundprozess prüft aktive Routen einmal pro Minute und protokolliert fällige Versäumnisse. PostgreSQL-Transaktions-Advisory-Locks koordinieren Monitoraufrufe und Hintergrundprozesse über mehrere API-Instanzen; ein partieller eindeutiger Index schützt zusätzlich vor doppelten Versäumnisereignissen. Fällt ein Prozess aus, läuft die Prüfung nach seinem Neustart beziehungsweise durch eine andere Instanz weiter. Das manuelle `POST /owks/routes/{route_id}/monitor` bleibt für berechtigte Betreiber verfügbar.

Kontrollintervalle sind verstrichene Minutenabstände, keine lokale Uhrzeitplanung. Die Fälligkeit wird aus zeitzonenbewussten UTC-Zeitpunkten berechnet; Sommerzeitwechsel verschieben die Dauer nicht und erzeugen weder doppelte noch nicht existierende Ortszeiten. Die Anzeige kann die Zeiten in der jeweiligen Browserzeitzone darstellen.

Wachbuchereignisse, Statusänderungen, Korrekturen und Anhänge sind in PostgreSQL durch Trigger gegen UPDATE/DELETE geschützt. Statusfortschritt wird als zusätzlicher Verlaufseintrag gespeichert; eine Korrektur verweist auf das Original und überschreibt es nicht. Offline-Ereignisse werden per UUID-Idempotenzschlüssel synchronisiert; erneute identische Übertragung ist idempotent, abweichende Wiederverwendung liefert einen sichtbaren Konflikt. Offline notierte QR-/NFC-Kontrollen werden ausdrücklich nicht nachträglich als verifiziert ausgegeben, sondern als zu prüfende Abweichung gespeichert. Anhänge werden in der Datenbank gehalten, nach Endung, MIME-Typ, Signatur und 10-MiB-Grenze geprüft und nur mit Objektberechtigung über private, nicht cachebare Antworten bereitgestellt. Das Frontend erzeugt QR-Bilder, scannt per Kamera über ZXing und liest/beschreibt NDEF-Textkennungen über `NDEFReader`, sofern HTTPS/lokaler sicherer Kontext, Browser und Gerät dies unterstützen. Kamera- und NFC-Berechtigungsfehler, Scanabbruch und fehlende APIs führen auf manuelle Eingabe beziehungsweise externes QR-Scannen zurück. Die gelesene Kennung ist nicht selbst autoritativ: Challenge, Objektzugriff, Wiederverwendung und Gültigkeit werden ausschließlich serverseitig geprüft. Treffer mit statischen Kennungen erhalten `presence_verified=false`, bleiben im Status offen und zählen nicht als erledigter Besuch für den Versäumnis-Monitor.

**Sicherheitsgrenze:** Ein statischer QR-Code oder einfacher NFC-Tag ist kopierbar. Einmal-Challenge schützt vor dem erneuten Absenden eines bereits akzeptierten Scan-Requests, kann aber das Kopieren eines statischen Trägers nicht technisch ausschließen. Web-NFC-Unterstützung hängt vom konkreten Browser und Gerät ab und ist keine kryptografische Klonprüfung. Für einen belastbaren physischen Klonschutz sind dynamische, kryptografisch prüfbare NFC-Tags oder ein verwalteter Geräte-/Standortnachweis erforderlich; diese Hardware- und Geräteintegration ist nicht Teil dieses Moduls. Issue #3 bleibt bis zu fachlicher Abnahme offen.

Statuswechsel sind serverseitig begrenzt: `open → submitted → approved|rejected`; nur abgeschlossene, nicht gesperrte Buchungen können Korrekturen erhalten. Korrekturanträge erfordern einen Grund und vollständige Ersatzsegmente. Sie schreiben die ursprünglichen Segmentwerte nicht um: genehmigte Segmente werden als eigene Korrekturversion gespeichert und für die effektive Anzeige/Auswertung verwendet. Ablehnung stellt den vorherigen Status wieder her und verlangt eine Begründung. Freigebende dürfen ihre eigenen Arbeitszeiten nicht freigeben. `locked` kann nur aus `approved` gesetzt werden und ist endgültig.

`time_tracking.read_own` beschränkt Buchungen auf die mit der angemeldeten Person verknüpfte Personalakte. `time_tracking.read_all` erlaubt die Verwaltungssicht; ohne `objects.read_all` wird diese zusätzlich auf zugewiesene Objekte beschränkt. Berechtigungen für Erfassung, Korrektur, Freigabe, Ablehnung, Export und Verwaltung sind getrennt. CSV enthält ausschließlich freigegebene/gesperrte Buchungen, verwendet UTF-8 und Semikolon als Trennzeichen und maskiert potenzielle Tabellenformeln.
