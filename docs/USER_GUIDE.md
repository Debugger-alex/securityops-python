# Kurzanleitung

## Administratorkonto

Nach Migrationen legt `python -m app.bootstrap_admin` ein Administratorkonto aus den explizit gesetzten `BOOTSTRAP_ADMIN_*`-Variablen an. Ein Standardpasswort existiert nicht. Zugangsdaten sicher verwahren und den Bootstrap nicht mit wiederverwendeten oder öffentlich gespeicherten Passwörtern ausführen.

## Anmeldung und Kunden

Im aktuellen Webfrontend mit Benutzername und Passwort anmelden. Berechtigungen werden vom Backend geprüft. Benutzer mit passenden Kundenrechten können Kunden anlegen, suchen und den Kundenstatus ändern. Das Dashboard zeigt nur implementierte Kundenkennzahlen. „Abmelden“ widerruft die aktuelle Sitzung.

## Noch nicht verfügbare Bereiche

Objekte, Personal, Schichten, Arbeitszeiterfassung, Wachbuch, Kontrollgänge, Dokumente, Verträge und Rechnungen sind noch nicht implementiert. Die Anwendung nicht als Ersatz dieser Betriebsprozesse verwenden.
