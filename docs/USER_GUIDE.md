# Kurzanleitung

## Administratorkonto

Nach Migrationen legt `python -m app.bootstrap_admin` ein Administratorkonto aus den explizit gesetzten `BOOTSTRAP_ADMIN_*`-Variablen an. Ein Standardpasswort existiert nicht. Zugangsdaten sicher verwahren und den Bootstrap nicht mit wiederverwendeten oder öffentlich gespeicherten Passwörtern ausführen.

## Anmeldung und Kunden

Im aktuellen Webfrontend mit Benutzername und Passwort anmelden. Berechtigungen werden vom Backend geprüft. Benutzer mit passenden Kundenrechten können Kunden anlegen, suchen und den Kundenstatus ändern. Das Dashboard zeigt nur implementierte Kundenkennzahlen. „Abmelden“ widerruft die aktuelle Sitzung.

## Objekte

Benutzer mit Objektleserecht können im Modul „Objekte“ ihnen zugewiesene oder global freigegebene Objekte suchen und filtern. Objekte sind immer einem aktiven Kunden zugeordnet. Berechtigte Benutzer können Stammdaten, Betriebszeiten, Kontakte und Zuweisungen verwalten sowie Objekte archivieren; Änderungen werden in der Objektchronik festgehalten. Alarm-, Notfall-, Schlüssel- und Zutrittsdaten sind separat berechtigt. Zu ihrer Nutzung muss der Betreiber `OBJECT_DATA_ENCRYPTION_KEY` als URL-sichere Base64-Kodierung eines 32-Byte-Schlüssels sicher konfigurieren und sichern. Schlüsselverlust verhindert den Zugriff auf bereits gespeicherte sensible Daten.

## Noch nicht verfügbare Bereiche

Personal, Schichten, Arbeitszeiterfassung, Wachbuch, Kontrollgänge, Dokumente, Verträge und Rechnungen sind noch nicht implementiert. Die Anwendung nicht als Ersatz dieser Betriebsprozesse verwenden.
