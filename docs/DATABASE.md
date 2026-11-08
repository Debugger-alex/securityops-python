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
- `employees`: Personalnummer, optionales eindeutiges Benutzerkonto, Stammdaten, Beschäftigungsstatus, Vertragsart, Wochenstunden und Archivierungszeitpunkt.
- `employee_qualifications`: Qualifikationsmetadaten und Gültigkeits-/Ablaufdaten; Qualifikationen werden archiviert statt physisch gelöscht.
- `employee_absences`: Abwesenheitstyp, Zeitraum, Status und erstellendes Benutzerkonto; Constraints sichern erlaubte Typen, Statuswerte und Datumsbereiche.
- `employee_sensitive_details`: getrennte Anschrift, Notfallkontakt und interne Notizen mit eigener Berechtigungsgrenze.
- `employee_history`: Akteur, Ereignis, Zeit und geänderte Feldnamen ohne sensible Feldwerte.
- `users`: Benutzername, E-Mail, Name, Argon2id-Passworthash, Aktivstatus und Zeitstempel.
- `roles`, `permissions`, `user_roles`, `role_permissions`: rollenbasierte Rechte.
- `user_sessions`: Hash des Sitzungstokens, CSRF-Tokenhash und Ablaufzeiten.
- `audit_logs`: Akteur, Ereignis, betroffener Datensatz, optionale Metadaten und UTC-Zeit.

## Integrität und offene Erweiterungen

UUIDs, Fremdschlüssel, eindeutige Benutzer-/Kundennummern und Status-Constraints sind vorhanden. Kunden, Objekte, Mitarbeiter und Qualifikationen werden archiviert statt physisch gelöscht; FK-Constraints schützen referenzierte Datensätze. Kontakte und Adressen sind relational gebunden. Migration 0008 ergänzt Personal, Qualifikationen, Abwesenheiten, getrennte sensible Personaldaten und Historie. Upgrade bis 0008 sowie Downgrade 0008→0007 wurden offline für PostgreSQL gerendert; ein lokaler PostgreSQL-Integrationslauf ist nicht belegt. Dienste, Zeitbuchungen, OWKS, Dokumente, Verträge und Rechnungen fehlen. Eine Restore-Prüfung wurde nicht ausgeführt.

Jede Schemaänderung benötigt eine neue Alembic-Migration. Datenlöschungen müssen mit Aufbewahrungsregeln abgestimmt werden; produktive Downgrades mit Datenverlust dürfen nicht automatisch ausgeführt werden.
