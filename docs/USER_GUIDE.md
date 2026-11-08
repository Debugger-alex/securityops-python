# Kurzanleitung

## Administratorkonto

Nach Migrationen legt `python -m app.bootstrap_admin` ein Administratorkonto aus den explizit gesetzten `BOOTSTRAP_ADMIN_*`-Variablen an. Ein Standardpasswort existiert nicht. Zugangsdaten sicher verwahren und den Bootstrap nicht mit wiederverwendeten oder öffentlich gespeicherten Passwörtern ausführen.

## Anmeldung und Kunden

Im aktuellen Webfrontend mit Benutzername und Passwort anmelden. Berechtigungen werden vom Backend geprüft. Benutzer mit passenden Kundenrechten können Kunden anlegen, suchen und Kundenstatus, Vertragsstatus, Website, Anschriften, Rechtsform, Notizen und Ansprechpartner pflegen. Websites werden als HTTP-/HTTPS-Adresse validiert. Der Vertragsstatus beschreibt den Stand der Vertragsbeziehung; Vertragsdokumente oder Vertragsverwaltung sind noch nicht verfügbar. Das Dashboard zeigt nur implementierte Kundenkennzahlen. „Abmelden“ widerruft die aktuelle Sitzung.

## Objektverwaltung

Benutzer mit Objektleserecht können die Objektliste suchen, nach Kunde und Status filtern, sortieren und Details zu erreichbaren Objekten öffnen. Objekte können mit einem vorhandenen Kunden angelegt, bearbeitet, archiviert und reaktiviert werden. Anschriften und mehrere Ansprechpartner lassen sich in der Detailansicht pflegen; Änderungen an einem Ansprechpartner löschen keine weiteren Kontakte. Die Historie zeigt Ereignisse und geänderte Feldnamen.

In einer Kundendetailansicht zeigt die Liste „Zugeordnete Objekte“ nur Objekte, die das angemeldete Konto auch über die Objektberechtigungen erreichen darf. Archivierte Kunden bleiben über die Archivfilter und ihre Historie nachvollziehbar. Dokumenten- und Vertragsmodule sind noch nicht implementiert.

Objektzugriff ist zusätzlich zum Modulrecht an eine Objektzuweisung gebunden, sofern das Konto kein globales Lese- oder Verwaltungsrecht besitzt. Objektzuweisungen werden durch berechtigte Benutzerkonten mit Mitarbeiter- oder Objektleitungsrolle vorgenommen. Sicherheits-, Zutritts- und Notfallinformationen erscheinen nicht in der Objektliste oder normalen Detailansicht und benötigen eigene Les-/Schreibberechtigungen.

## Dienstplanung

Berechtigte Einsatzleitungen können Schichtentwürfe mit Mitarbeiter, Objekt, lokaler Start-/Endzeit, Pause und optionaler Qualifikation anlegen, bearbeiten, veröffentlichen oder absagen. Tages-, Wochen- und Monatsansichten lassen sich nach Zeitraum, Mitarbeiter und Objekt filtern; der Verlauf zeigt geänderte Felder. Schreibzugriffe und der sichtbare Objekt-/Personalbereich werden serverseitig kontrolliert.

Zeitzone und Mindestabstand zwischen Diensten werden in den Planungseinstellungen festgelegt. Lokale Eingaben werden anhand der IANA-Zeitzone in UTC umgerechnet; nicht existierende Uhrzeiten bei einer Zeitumstellung werden abgewiesen und doppelte Uhrzeiten sind über die Auswahl des ersten/zweiten Auftretens unterscheidbar. Bei Zeitkonflikten, fehlender Qualifikation, unpassendem Beschäftigungszeitraum, Abwesenheit oder fehlender Objektzuweisung wird die Änderung mit einem Konflikthinweis abgelehnt. PostgreSQL verhindert überlappende aktive Schichten auch bei parallelen Schreibzugriffen.

Die aktuelle Verfügbarkeitsprüfung nutzt aktiven Beschäftigungszeitraum, Abwesenheiten und bereits geplante Dienste. Individuelle wiederkehrende Verfügbarkeitsfenster sind nicht modelliert. Die konfigurierbare Ruhezeit ist keine automatische Rechtsprüfung und garantiert keine gesetzliche Konformität. Die Dienstplanung ist in `main` integriert; vor betrieblicher Nutzung bleiben unabhängige fachliche und rechtliche Prüfungen erforderlich.

## Zeiterfassung

Mitarbeiter mit den Rechten `time_tracking.read_own` und `time_tracking.create` öffnen im Modul „Zeiterfassung“ den aktuellen veröffentlichten Dienst mit „Arbeitszeit starten“. Wenn kein passender veröffentlichter Dienst vorliegt, kann die Anwendung keine Dienst-/Objektzuordnung erraten; eine berechtigte Verwaltung kann dann einen manuellen Nachtrag anlegen. Ein Mitarbeiter kann gleichzeitig nur eine offene Buchung haben. „Pause starten“ und „Pause beenden“ erzeugen getrennte, fortlaufende Pausen- und Arbeitsabschnitte; „Dienst beenden“ reicht die Buchung zur Prüfung ein.

Eigene Buchungen zeigen tatsächliche Start-/Endzeiten, Arbeits- und Pausendauer, den zugehörigen Dienst und die Soll-/Ist-Abweichung. Zeiten werden intern in UTC gespeichert und in der konfigurierten Dienstplanzeitzone (standardmäßig `Europe/Berlin`) dargestellt. Buchungen ohne Dienstplan benötigen eine manuelle Berechtigung und eine aktive Mitarbeiter-/Objektzuweisung.

Eine freigegebene Buchung kann nicht direkt überschrieben werden. Über „Korrektur beantragen“ werden ein Grund und die vollständigen Arbeits-/Pausensegmente als neuer Vorschlag eingereicht; die editierbaren Zeitfelder sind ausdrücklich UTC. Eine berechtigte, andere Person kann den Antrag freigeben oder mit Begründung ablehnen. Der ursprüngliche Zeitverlauf bleibt erhalten. Für die Freigabe und Ablehnung von Zeiteinreichungen gelten getrennte Rechte; eine Person kann ihre eigene Buchung nicht selbst freigeben.

Vorgesetzte sehen abhängig von ihrer Berechtigung und Objektzuweisung Arbeitszeiten, offene Korrekturen und veröffentlichte Dienste ohne Buchung. Zeitraum, Mitarbeiter, Objekt, Kunde und Status sind filterbar. Die Übersicht gruppiert nach Mitarbeiter, Objekt, Kunde, Tag, ISO-Kalenderwoche oder Monat und zeigt Soll-/Ist-Zeit, Pausen, Abweichungen sowie offene Freigaben. „Mehrzeit gegenüber Dienstplan“ ist die positive Differenz zur geplanten Arbeitszeit; tarifliche Überstunden, Zuschläge und Rundungen werden nicht berechnet. Der CSV-Export ist auf freigegebene oder gesperrte Buchungen beschränkt und maskiert Tabellenformeln.

Korrekturanträge nach der Freigabe ändern nur die effektive, separat versionierte Ansicht. Gesperrte Einträge sind endgültig und können nicht mehr korrigiert werden. Arbeitszeitberechnung, Zeitzonen und Dienstplanabgleich ersetzen keine fachliche oder arbeitsrechtliche Prüfung. Wachbuch, Kontrollgänge, Dokumente, Verträge und Rechnungen sind weiterhin nicht implementiert; die Anwendung nicht als Ersatz dieser Betriebsprozesse verwenden.

### Zuschläge und Abrechnungsperioden

Benutzer mit `time_tracking.surcharges.manage` legen im Bereich „Zuschläge und Abrechnungszeiträume“ Regeln für Nacht-, Samstag-, Sonntag-, Feiertags- oder individuelle Betriebszeiten an. Regeln erfordern Gültigkeitsbeginn, Wert, Bezugs-/Einheitenbeschreibung, Priorität und Kombinationsmodus; Nacht- und Betriebsregeln benötigen zusätzlich ein lokales Zeitfenster. Für betriebliche Regeln können Wochentage gewählt werden. Die Regeln sind unveränderlich; eine fachliche Änderung wird als neue Regel mit neuem Code und Gültigkeitszeitraum dokumentiert. Das für Feiertage verwendete Bundesland muss vorher ausdrücklich eingestellt werden.

Für freigegebene Buchungen kann die Verwaltung einen versionierten Zuschlagsnachweis erzeugen und einsehen. Die Auswertung zählt ausschließlich tatsächliche Arbeitssegmente; Pausen bleiben ausgeschlossen. Lokalzeitfenster, Feiertage, Mitternacht und die doppelte/fehlende Stunde bei Zeitumstellungen werden in der konfigurierten Zeitzone behandelt. Priorität und Kombinationsmodus sind maßgeblich; gleich priorisierte exklusive Überschneidungen werden nicht geraten, sondern abgewiesen. Die Zuschlagsübersicht und der separate CSV-Export enthalten Regelwert und zuschlagsfähige Arbeitszeit.

**Wichtig:** Das Modul berechnet derzeit keine Geldbeträge. Es gibt keine bestätigte Mitarbeiter-Lohnbasis und keine fachliche Festlegung zur Prozentbasis, Einheit eines Festzuschlags oder Rundung. Der Nachweis weist den Geldbetrag daher ausdrücklich als nicht berechnet aus. Er ist kein abrechnungsfertiger Lohn- oder Payroll-Export.

Eine Periode kann nach vollständigem Ablauf endgültig gesperrt werden, wenn jede Buchung freigegeben ist, keine Buchung die Periodengrenze schneidet und jeder veröffentlichte Dienst eine freigegebene Zeiterfassung besitzt. Beim Sperren werden Berechnungssnapshots gesichert. Nach der Sperre sind Korrektur und Neuberechnung ausgeschlossen; es gibt keine Entsperr-Funktion.
