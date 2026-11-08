# Prüfung hochgeladener Dateien

## Abgedeckte Uploads

Das Backend prüft vor jeder dauerhaften Speicherung und Freigabe:

- `POST /api/v1/documents` – neue private Dokument-/Vertragsdatei
- `POST /api/v1/documents/{document_id}/versions` – neue Dokumentversion
- `POST /api/v1/owks/events/{event_id}/attachments` – OWKS-Anhang
- `POST /api/v1/employees/{employee_id}/qualifications/{qualification_id}/documents` – Personal-Qualifikationsnachweis

Der gemeinsame Adapter spricht das ClamAV-`INSTREAM`-Protokoll über TCP an. Er überträgt den Dateiinhalt in begrenzten Blöcken und akzeptiert nur eine eindeutige `stream: OK`-Antwort. Eine erkannte Signatur oder jede Scanner-, Protokoll-, Größen- oder Timeout-Störung führt nicht zur Speicherung. Infizierte Dateien erhalten HTTP 422, Dateien über dem Scanlimit HTTP 413 und ein fehlgeschlagener oder nicht erreichbarer Scanner HTTP 503. Es gibt keinen unsicheren Fallback und keine öffentliche Scanner-Schnittstelle.

Ablehnungen werden mit einem Audit-Eintrag protokolliert, der nur Upload-Oberfläche, Ergebnis und gegebenenfalls einen festen Fehlergrund enthält. Dateiname, Inhalt, Signaturname und Datei-Hash werden dafür nicht protokolliert. Ein Audit-Datenbankfehler wird zusätzlich über eine statische, nicht sensitive Servermeldung erfasst; der Upload bleibt in jedem Fall abgelehnt.

## Betrieb und Grenzwerte

Compose verwendet das mehrplattformfähige Image `clamav/clamav-debian:1.4.3`, gepinnt auf den OCI-Manifest-Digest `sha256:1d261f9c83ef2bbeef3915c7792f125e5707500fde0019d53547461747b90374`, im internen Datennetz und veröffentlicht Port 3310 nicht am Host. Der Compose-Healthcheck verlangt `PONG` und eine `VERSION`-Antwort mit positiver ClamAV-Datenbankversion. Das Startfenster von 30 Minuten deckt den ersten Datenbankdownload ab. ClamAV aktualisiert seine Virendefinitionen zur Laufzeit; die Scanner-Software bleibt durch den Digest reproduzierbar festgelegt, die Malwaredefinitionen sind bewusst nicht eingefroren. Digest-Aktualisierungen müssen geprüft und explizit übernommen werden.

`MALWARE_SCANNER_TIMEOUT_SECONDS` ist standardmäßig 30 Sekunden und darf höchstens 300 betragen. `MALWARE_SCAN_MAX_BYTES` ist standardmäßig 100 MiB und darf höchstens 100 MiB betragen. ClamAV ist auf 100 MiB Stream-/Dateigröße und 200 MiB Scan-Größe gesetzt. OWKS- und Personalanhänge sind weiterhin auf 10 MiB begrenzt; private Dokumente folgen `DOCUMENT_MAX_UPLOAD_BYTES` (Standard 20 MiB, höchstens 100 MiB). Ein abweichend niedriger konfiguriertes Scannerlimit lehnt größere Dateien ebenfalls ab.

Bei direktem Backendbetrieb müssen Host, Port, Timeout und Größenlimit über `MALWARE_SCANNER_HOST`, `MALWARE_SCANNER_PORT`, `MALWARE_SCANNER_TIMEOUT_SECONDS` und `MALWARE_SCAN_MAX_BYTES` auf einen erreichbaren ClamAV-Dienst gesetzt sein. `clamav` als Hostname ist nur im Compose-Netz auflösbar. Ein fehlender oder fehlerhafter Scanner verhindert Uploads, nicht aber den Start der API außerhalb des Compose-Stacks.

## Grenzen

Der Scan gilt nur für neue Uploads, die durch diese Backend-Endpunkte laufen. Bereits gespeicherte Dateien werden weder automatisch gescannt noch als sauber bestätigt; es gibt keinen rückwirkenden Bestandsscan. Der Virenscanner kann nicht jede Schadsoftware oder jedes passwortgeschützte/verschlüsselte Dateiformat erkennen und ersetzt keine sichere Parser-Konfiguration, Isolation, Patchpflege, TLS, Backups oder fachliche Prüfung. Tests verwenden ausschließlich deterministische Scanner-Mocks und keine Malware-Proben.
