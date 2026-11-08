# Datenbank

## Verbindung und Migrationen

PostgreSQL ist für den Betrieb vorgesehen. Verbindungsdaten werden über `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` gesetzt. Alembic-Migrationen liegen in `backend/migrations/versions`; normales Modell-Metadaten-`create_all` ist nur in Tests zulässig.

## Derzeitige Tabellen

- `customers`: Kundennummer, Firmenname, Status, Kontakt-E-Mail/Telefon, Rechtsform, Umsatzsteuer-ID, Steuernummer, interne Notizen, Archivierungs- sowie Erstellungs-/Änderungszeitpunkt.
- `customer_addresses`: Geschäfts- und Rechnungsanschriften eines Kunden; Kunden- und Adressdatensätze werden nicht physisch gelöscht.
- `customer_contacts`: Ansprechpartner mit Kontaktdaten und Primärkennzeichnung. Ein partieller eindeutiger Index erzwingt höchstens einen primären Ansprechpartner pro Kunde.
- `customer_history`: Kundenereignisse mit Akteur, Ereignis, Zeit und geänderten Feldnamen; keine Feldwerte.
- `users`: Benutzername, E-Mail, Name, Argon2id-Passworthash, Aktivstatus und Zeitstempel.
- `roles`, `permissions`, `user_roles`, `role_permissions`: rollenbasierte Rechte.
- `user_sessions`: Hash des Sitzungstokens, CSRF-Tokenhash und Ablaufzeiten.
- `audit_logs`: Akteur, Ereignis, betroffener Datensatz, optionale Metadaten und UTC-Zeit.

## Integrität und offene Erweiterungen

UUIDs, Fremdschlüssel, eindeutige Benutzer-/Kundennummern und Status-Constraints sind vorhanden. Kundenarchivierung ist ein Zeitstempel statt einer Löschung; archivierte Kunden werden standardmäßig aus Listen und Dashboard ausgeschlossen. Adressen und Ansprechpartner sind relational an Kunden gebunden. Objekte, Mitarbeiter, Dienste, Zeitbuchungen, OWKS, Dokumente, Verträge und Rechnungen fehlen. Migration 0004 wurde lokal offline und in der gehosteten PostgreSQL-CI erfolgreich geprüft. Eine Restore-Prüfung wurde nicht ausgeführt.

Jede Schemaänderung benötigt eine neue Alembic-Migration. Datenlöschungen müssen mit Aufbewahrungsregeln abgestimmt werden; produktive Downgrades mit Datenverlust dürfen nicht automatisch ausgeführt werden.
