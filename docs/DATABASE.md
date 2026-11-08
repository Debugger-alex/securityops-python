# Datenbank

## Verbindung und Migrationen

PostgreSQL ist für den Betrieb vorgesehen. Verbindungsdaten werden über `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` gesetzt. Alembic-Migrationen liegen in `backend/migrations/versions`; normales Modell-Metadaten-`create_all` ist nur in Tests zulässig.

## Derzeitige Tabellen

- `customers`: Kundennummer, Firmenname, Status, Kontakt-E-Mail/Telefon, Rechtsform, Umsatzsteuer-ID, Steuernummer, interne Notizen, Archivierungs- sowie Erstellungs-/Änderungszeitpunkt.
- `customer_addresses`: Geschäfts- und Rechnungsanschriften eines Kunden; Kunden- und Adressdatensätze werden nicht physisch gelöscht.
- `customer_contacts`: Ansprechpartner mit Kontaktdaten und Primärkennzeichnung. Ein partieller eindeutiger Index erzwingt höchstens einen primären Ansprechpartner pro Kunde.
- `customer_history`: Kundenereignisse mit Akteur, Ereignis, Zeit und geänderten Feldnamen; keine Feldwerte.
- `objects`: eindeutiger Objektcode, Kunde (FK mit RESTRICT), Status, Betriebs-/Personalangaben sowie Archivierungs- und Zeitstempel.
- `object_addresses`: optionale 1:1-Anschrift; `object_contacts`: mehrere Ansprechpartner mit partiellem eindeutigem Index für höchstens einen Primärkontakt.
- `object_history`: Akteur, Aktion, Zeit und geänderte Feldnamen; sensible Werte werden nicht in der Historie gespeichert.
- `object_assignments`: eindeutige Objekt-/Benutzerzuweisung mit Zuordnungszeit und zuordnendem Benutzer.
- `object_security_details`: getrennte Tabelle für Sicherheitsanforderungen, Zutrittsinformation und Notfallkontakt.
- `users`: Benutzername, E-Mail, Name, Argon2id-Passworthash, Aktivstatus und Zeitstempel.
- `roles`, `permissions`, `user_roles`, `role_permissions`: rollenbasierte Rechte.
- `user_sessions`: Hash des Sitzungstokens, CSRF-Tokenhash und Ablaufzeiten.
- `audit_logs`: Akteur, Ereignis, betroffener Datensatz, optionale Metadaten und UTC-Zeit.

## Integrität und offene Erweiterungen

UUIDs, Fremdschlüssel, eindeutige Benutzer-/Kundennummern und Status-Constraints sind vorhanden. Kunden und Objekte werden archiviert statt physisch gelöscht; FK-Constraints verhindern das Löschen referenzierter Kunden und Objekte. Kontakte und Adressen sind relational gebunden. Migrationen 0005 bis 0007 ergänzen Objekte, Zuweisungen und sensible Sicherheitsdaten mit Datenübernahme. In dieser Arbeitsumgebung wurden Upgrade- und Downgrade-SQL für PostgreSQL offline gerendert; ein lokaler PostgreSQL-Integrationslauf ist nicht belegt. Mitarbeiterstammdaten, Dienste, Zeitbuchungen, OWKS, Dokumente, Verträge und Rechnungen fehlen. Eine Restore-Prüfung wurde nicht ausgeführt.

Jede Schemaänderung benötigt eine neue Alembic-Migration. Datenlöschungen müssen mit Aufbewahrungsregeln abgestimmt werden; produktive Downgrades mit Datenverlust dürfen nicht automatisch ausgeführt werden.
