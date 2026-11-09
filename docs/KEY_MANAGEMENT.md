# Schlüsselverwaltung

Die Schlüsselverwaltung ergänzt ein eigenes Register für physische Schlüssel. Die vorhandenen Freitextangaben unter `objects.security_information.access_information` werden nicht migriert, verändert oder als Schlüsselbestand interpretiert.

## Daten und Zustände

Jeder Schlüssel hat eine eindeutige Schlüsselnummer, eine Beschreibung und genau ein Pflichtobjekt. Der Registerstatus ist `available`, `issued`, `lost`, `defective` oder `archived`. Schlüsselnummer und Objekt sind nach dem Anlegen unveränderlich; die Beschreibung kann geändert werden. Archivieren ist nur möglich, wenn der Schlüssel nicht ausgegeben ist.

Ausgaben, Rückgaben, Verlust- und Defektmeldungen sowie Inventurbestätigungen werden als Schlüsselbewegungen protokolliert. Eine Ausgabe setzt einen aktiven, nicht archivierten Mitarbeiter mit aktivem Benutzerkonto voraus, der dem Schlüsselobjekt zugewiesen ist. Sie benötigt außerdem eine bestätigte Empfangsquittierung. Rückgabe ist nur für ausgegebene Schlüssel zulässig. Verlust- und Defektmeldungen benötigen eine Notiz und übernehmen bei ausgegebenen Schlüsseln den bisherigen Mitarbeiter in den Historieneintrag. Eine Inventurbestätigung bedeutet, dass der Schlüssel physisch gesehen wurde; ein fehlender Schlüssel muss separat als Verlust gemeldet werden.

Die Zustandsänderung, der Bewegungsdatensatz und der Eintrag im Audit-Protokoll werden gemeinsam in einer Datenbanktransaktion gespeichert. Zeilen werden bei Bewegungen gesperrt, damit parallele Ausgaben nicht denselben verfügbaren Schlüssel vergeben. Bewegungseinträge sind über API und PostgreSQL-Trigger unveränderlich. Korrekturen erfolgen als neue nachvollziehbare Bewegung statt durch Überschreiben.

## Berechtigungen und Objektzugriff

| Berechtigung | Zweck |
| --- | --- |
| `keys.read` | Register, Status und Historie lesen |
| `keys.manage` | Schlüssel anlegen, Beschreibung ändern und archivieren |
| `keys.move` | Ausgabe, Rückgabe, Meldungen und Inventur erfassen |

Administrator, Geschäftsführung und Operations erhalten alle drei Berechtigungen; Objektleitungen erhalten Lese- und Bewegungsrechte. Zusätzlich begrenzt der Backendzugriff alle Schlüssel auf Objekte mit Benutzerzuweisung, sofern kein `objects.read_all`-Zugriff besteht. Stammdaten dürfen nur mit `objects.manage_all` oder mit `objects.manage` für ein zugewiesenes Objekt geändert werden. Mitarbeiterzuweisungen werden serverseitig gegen die aktive Objektzuweisung des verknüpften Benutzerkontos geprüft.

Die digitale Quittierung dokumentiert die Bestätigung im angemeldeten Benutzerkontext; sie ist keine qualifizierte elektronische Signatur. Eine Datenbank-ID ist kein physischer Verwahrnachweis und ersetzt weder ein Schlüsselübergabeprotokoll noch die tatsächliche Sicherung eines Schlüssels.

## API

- `GET /api/v1/keys`: Suche (`q`), Status-, Objekt- und Mitarbeiterfilter sowie begrenzte Pagination (`limit`, `offset`)
- `POST /api/v1/keys`, `PATCH /api/v1/keys/{id}`, `POST /api/v1/keys/{id}/archive`: Registerverwaltung
- `GET /api/v1/keys/objects`, `GET /api/v1/keys/eligible-employees?object_id=…`: objektgebundene Auswahlwerte
- `POST /api/v1/keys/{id}/movements`: `issued`, `returned`, `lost`, `defective` oder `inventory`
- `GET /api/v1/keys/{id}/movements`: unveränderliche, paginierte Historie

Die Migration `0021_key_management` folgt linear auf `0020_notifications`. Ein Downgrade wird abgelehnt, sobald Schlüssel, Bewegungsdaten oder benutzerdefinierte Schlüsselberechtigungen vorhanden sind, damit betriebliche Historie nicht stillschweigend gelöscht wird.
