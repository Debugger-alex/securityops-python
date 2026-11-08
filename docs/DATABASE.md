# Datenbank

## Verbindung und Migrationen

PostgreSQL ist für den Betrieb vorgesehen. Verbindungsdaten werden über `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` gesetzt. Alembic-Migrationen liegen in `backend/migrations/versions`; normales Modell-Metadaten-`create_all` ist nur in Tests zulässig.

## Derzeitige Tabellen

- `customers`: Kundennummer, Firmenname, Status, Kontakt-E-Mail/Telefon, Rechtsform, Umsatzsteuer-ID, Steuernummer, interne Notizen, Archivierungs- sowie Erstellungs-/Änderungszeitpunkt.
- `customer_addresses`: Geschäfts- und Rechnungsanschriften eines Kunden; Kunden- und Adressdatensätze werden nicht physisch gelöscht.
- `customer_contacts`: Ansprechpartner mit Kontaktdaten und Primärkennzeichnung. Ein partieller eindeutiger Index erzwingt höchstens einen primären Ansprechpartner pro Kunde.
- `customer_history`: Kundenereignisse mit Akteur, Ereignis, Zeit und geänderten Feldnamen; keine Feldwerte.
- `objects`: kundenbezogene Objekte mit Adresse, Betriebszeiten, Soll-Besetzung, Qualifikationen, Objektleitung und Archivierungszeitpunkt.
- `object_contacts`: Objektkontakte; ein partieller eindeutiger Index erzwingt höchstens einen Primärkontakt pro Objekt.
- `object_user_assignments`: Objekt-zu-Benutzer-Zuweisungen mit Zuweisendem und UTC-Zeitpunkt.
- `object_sensitive_data`: je Objekt ein AES-GCM-Chiffrat sensibler Alarm-, Notfall-, Schlüssel- und Zutrittsangaben sowie Änderungsmetadaten.
- `object_history`: Objektänderungen mit Akteur, UTC-Zeit und geänderten Feldnamen, ohne vorherige/neue Feldwerte.
- `users`: Benutzername, E-Mail, Name, Argon2id-Passworthash, Aktivstatus und Zeitstempel.
- `roles`, `permissions`, `user_roles`, `role_permissions`: rollenbasierte Rechte.
- `user_sessions`: Hash des Sitzungstokens, CSRF-Tokenhash und Ablaufzeiten.
- `audit_logs`: Akteur, Ereignis, betroffener Datensatz, optionale Metadaten und UTC-Zeit.

## Integrität und offene Erweiterungen

UUIDs, Fremdschlüssel, eindeutige Benutzer-/Kundennummern und Status-Constraints sind vorhanden. Kunden- und Objektarchivierung verwenden Zeitstempel statt Löschungen; archivierte Kunden können keine neuen Objekte erhalten. Adressen und Ansprechpartner sind relational gebunden. Objekt-Zugriffsgrenzen werden über `object_user_assignments` umgesetzt. Sensible Felder werden vor dem Speichern in der Anwendung verschlüsselt; der Schlüssel liegt außerhalb der Datenbank in `OBJECT_DATA_ENCRYPTION_KEY`. Migration 0005 wurde lokal offline generiert; die Ausführung gegen eine echte PostgreSQL-Instanz ist durch CI vorgesehen. Personal, Dienste, Zeitbuchungen, OWKS, Dokumente, Verträge und Rechnungen fehlen. Eine Restore-Prüfung wurde nicht ausgeführt.

Jede Schemaänderung benötigt eine neue Alembic-Migration. Datenlöschungen müssen mit Aufbewahrungsregeln abgestimmt werden; produktive Downgrades mit Datenverlust dürfen nicht automatisch ausgeführt werden.
