# Kurzanleitung

## Administratorkonto

Nach Migrationen legt `python -m app.bootstrap_admin` ein Administratorkonto aus den explizit gesetzten `BOOTSTRAP_ADMIN_*`-Variablen an. Ein Standardpasswort existiert nicht. Zugangsdaten sicher verwahren und den Bootstrap nicht mit wiederverwendeten oder öffentlich gespeicherten Passwörtern ausführen.

## Anmeldung und Kunden

Im aktuellen Webfrontend mit Benutzername und Passwort anmelden. Berechtigungen werden vom Backend geprüft. Benutzer mit passenden Kundenrechten können Kunden anlegen, suchen und Kundenstatus, Vertragsstatus, Website, Anschriften, Rechtsform, Notizen und Ansprechpartner pflegen. Websites werden als HTTP-/HTTPS-Adresse validiert. Der Vertragsstatus beschreibt den Stand der Vertragsbeziehung; Vertragsdokumente oder Vertragsverwaltung sind noch nicht verfügbar. Das Dashboard zeigt nur implementierte Kundenkennzahlen. „Abmelden“ widerruft die aktuelle Sitzung.

## Objektverwaltung

Benutzer mit Objektleserecht können die Objektliste suchen, nach Kunde und Status filtern, sortieren und Details zu erreichbaren Objekten öffnen. Objekte können mit einem vorhandenen Kunden angelegt, bearbeitet, archiviert und reaktiviert werden. Anschriften und mehrere Ansprechpartner lassen sich in der Detailansicht pflegen; Änderungen an einem Ansprechpartner löschen keine weiteren Kontakte. Die Historie zeigt Ereignisse und geänderte Feldnamen.

In einer Kundendetailansicht zeigt die Liste „Zugeordnete Objekte“ nur Objekte, die das angemeldete Konto auch über die Objektberechtigungen erreichen darf. Archivierte Kunden bleiben über die Archivfilter und ihre Historie nachvollziehbar. Dokumenten- und Vertragsmodule sind noch nicht implementiert.

Objektzugriff ist zusätzlich zum Modulrecht an eine Objektzuweisung gebunden, sofern das Konto kein globales Lese- oder Verwaltungsrecht besitzt. Objektzuweisungen werden durch berechtigte Benutzerkonten mit Mitarbeiter- oder Objektleitungsrolle vorgenommen. Sicherheits-, Zutritts- und Notfallinformationen erscheinen nicht in der Objektliste oder normalen Detailansicht und benötigen eigene Les-/Schreibberechtigungen.

## Noch nicht verfügbare Bereiche

Eine eigenständige Personalverwaltung, Qualifikationen, Schichten, Arbeitszeiterfassung, Wachbuch, Kontrollgänge, Dokumente, Verträge und Rechnungen sind noch nicht implementiert. Objektzuweisungen ersetzen keine Personalakte oder Dienstplanung. Die Anwendung nicht als Ersatz dieser Betriebsprozesse verwenden.
