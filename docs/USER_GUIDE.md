# Kurzanleitung

## Administratorkonto

Nach Migrationen legt `python -m app.bootstrap_admin` ein Administratorkonto aus den explizit gesetzten `BOOTSTRAP_ADMIN_*`-Variablen an. Ein Standardpasswort existiert nicht. Zugangsdaten sicher verwahren und den Bootstrap nicht mit wiederverwendeten oder öffentlich gespeicherten Passwörtern ausführen.

## Anmeldung und Kunden

Im aktuellen Webfrontend mit Benutzername und Passwort anmelden. Berechtigungen werden vom Backend geprüft. Benutzer mit passenden Kundenrechten können Kunden anlegen, suchen und Kundenstatus, Vertragsstatus, Website, Anschriften, Rechtsform, Notizen und Ansprechpartner pflegen. Websites werden als HTTP-/HTTPS-Adresse validiert. Der Vertragsstatus beschreibt den Stand der Vertragsbeziehung; Vertragsdokumente oder Vertragsverwaltung sind noch nicht verfügbar. Das Dashboard zeigt nur implementierte Kundenkennzahlen. „Abmelden“ widerruft die aktuelle Sitzung.

## Objektverwaltung

Benutzer mit Objektleserecht können die Objektliste suchen, nach Kunde und Status filtern, sortieren und Details zu erreichbaren Objekten öffnen. Objekte können mit einem vorhandenen Kunden angelegt, bearbeitet, archiviert und reaktiviert werden. Anschriften und mehrere Ansprechpartner lassen sich in der Detailansicht pflegen; Änderungen an einem Ansprechpartner löschen keine weiteren Kontakte. Die Historie zeigt Ereignisse und geänderte Feldnamen.

In einer Kundendetailansicht zeigt die Liste „Zugeordnete Objekte“ nur Objekte, die das angemeldete Konto auch über die Objektberechtigungen erreichen darf. Archivierte Kunden bleiben über die Archivfilter und ihre Historie nachvollziehbar. Dokumenten- und Vertragsmodule sind noch nicht implementiert.

Objektzugriff ist zusätzlich zum Modulrecht an eine Objektzuweisung gebunden, sofern das Konto kein globales Lese- oder Verwaltungsrecht besitzt. Objektzuweisungen werden durch berechtigte Benutzerkonten mit Mitarbeiter- oder Objektleitungsrolle vorgenommen. Sicherheits-, Zutritts- und Notfallinformationen erscheinen nicht in der Objektliste oder normalen Detailansicht und benötigen eigene Les-/Schreibberechtigungen.

## Dienstplanung (Feature-Branch)

Im aktuellen Feature-Branch können berechtigte Einsatzleitungen Schichtentwürfe mit Mitarbeiter, Objekt, lokaler Start-/Endzeit, Pause und optionaler Qualifikation anlegen, bearbeiten, veröffentlichen oder absagen. Tages-, Wochen- und Monatsansichten lassen sich nach Zeitraum, Mitarbeiter und Objekt filtern; der Verlauf zeigt geänderte Felder. Schreibzugriffe und der sichtbare Objekt-/Personalbereich werden serverseitig kontrolliert.

Zeitzone und Mindestabstand zwischen Diensten werden in den Planungseinstellungen festgelegt. Lokale Eingaben werden anhand der IANA-Zeitzone in UTC umgerechnet; nicht existierende Uhrzeiten bei einer Zeitumstellung werden abgewiesen und doppelte Uhrzeiten sind über die Auswahl des ersten/zweiten Auftretens unterscheidbar. Bei Zeitkonflikten, fehlender Qualifikation, unpassendem Beschäftigungszeitraum, Abwesenheit oder fehlender Objektzuweisung wird die Änderung mit einem Konflikthinweis abgelehnt. PostgreSQL verhindert überlappende aktive Schichten auch bei parallelen Schreibzugriffen.

Die aktuelle Verfügbarkeitsprüfung nutzt aktiven Beschäftigungszeitraum, Abwesenheiten und bereits geplante Dienste. Individuelle wiederkehrende Verfügbarkeitsfenster sind nicht modelliert. Die konfigurierbare Ruhezeit ist keine automatische Rechtsprüfung und garantiert keine gesetzliche Konformität. Der Scheduling-Kern ist noch nicht in `main` geprüft/gemergt; vor betrieblicher Nutzung sind Review, CI sowie fachliche und rechtliche Prüfung erforderlich.

Arbeitszeiterfassung, Wachbuch, Kontrollgänge, Dokumente, Verträge und Rechnungen sind noch nicht implementiert. Objektzuweisungen ersetzen keine Personalakte oder Dienstplanung. Die Anwendung nicht als Ersatz dieser Betriebsprozesse verwenden.
