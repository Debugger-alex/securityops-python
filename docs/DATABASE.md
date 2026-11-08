# Datenbank

## Verbindung und Migrationen

PostgreSQL ist für den Betrieb vorgesehen. Verbindungsdaten werden über `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` und `POSTGRES_PASSWORD` gesetzt. Alembic-Migrationen liegen in `backend/migrations/versions`; normales Modell-Metadaten-`create_all` ist nur in Tests zulässig.

## Derzeitige Tabellen

- `customers`: Kundennummer, Firmenname, Status, Vertragsstatus, Kontakt-E-Mail/Telefon, Rechtsform, Website, Umsatzsteuer-ID, Steuernummer, interne Notizen, Archivierungs- sowie Erstellungs-/Änderungszeitpunkt.
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
- `employee_object_assignment_history`: unveränderliche Personalhistorie für Zuweisung und Beendigung bestehender Objektzuweisungen; verweist auf Mitarbeiterakte, Objekt und Benutzer.
- `employee_qualification_documents`: unveränderliche Qualifikationsnachweis-Versionen mit Dateiinhalt in PostgreSQL (`BYTEA`), Medien-/Dateimetadaten, SHA-256-Prüfsumme, Versionsnummer und hochladendem Benutzer.
- `users`: Benutzername, E-Mail, Name, Argon2id-Passworthash, Aktivstatus und Zeitstempel.
- `roles`, `permissions`, `user_roles`, `role_permissions`: rollenbasierte Rechte.
- `user_sessions`: Hash des Sitzungstokens, CSRF-Tokenhash und Ablaufzeiten.
- `audit_logs`: Akteur, Ereignis, betroffener Datensatz, optionale Metadaten und UTC-Zeit.

## Integrität und offene Erweiterungen

UUIDs, Fremdschlüssel, eindeutige Benutzer-/Kundennummern und Status-Constraints sind vorhanden. Kunden, Objekte, Mitarbeiter und Qualifikationen werden archiviert statt physisch gelöscht; FK-Constraints schützen referenzierte Datensätze. Kontakte und Adressen sind relational gebunden. Migration 0008 ergänzt Personal, Qualifikationen, Abwesenheiten, getrennte sensible Personaldaten und Historie; Migration 0009 ergänzt den Verlauf bestehender Objektzuweisungen für Personalakten, versionierte Qualifikationsdateien und separate Dokumentrechte. Migration 0010 ergänzt die optionale Kunden-Website und den Vertragsstatus additiv; vorhandene Kunden erhalten den Status `none`, bestehende Datensätze und andere Felder bleiben erhalten. Dateiinhalte liegen in der Datenbank; externe private Dateiablage und Anwendungsebene-Verschlüsselung sind nicht implementiert. Dienstplanung, Zeitbuchungen, OWKS, Vertragsverwaltung und Rechnungen fehlen. Eine Restore-Prüfung wurde nicht ausgeführt.

Jede Schemaänderung benötigt eine neue Alembic-Migration. Datenlöschungen müssen mit Aufbewahrungsregeln abgestimmt werden; produktive Downgrades mit Datenverlust dürfen nicht automatisch ausgeführt werden.
