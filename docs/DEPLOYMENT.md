# Deployment

## Laufzeitaufbau

Das Produktions-Compose-Setup baut das Frontend als statische Vite-Dateien und liefert sie über einen unprivilegierten Nginx-Prozess auf Port 8080 im Container aus. Nginx leitet `/api/` intern an FastAPI weiter; PostgreSQL und Redis liegen in einem internen Compose-Netz ohne veröffentlichte Ports. Nur Frontend und API sind am Host-Loopback gebunden. Die API erzwingt im Produktionsmodus Secure-Cookies und Redis als gemeinsamen Rate-Limit-Speicher. Ein eigener `migrate`-Dienst ist nur über das Profil `release` verfügbar und wird nicht automatisch von API-Replikaten gestartet.

Für den ersten Start oder ein Release:

```sh
docker compose up -d db redis
docker compose --profile release run --rm migrate
docker compose up --build -d api frontend
```

Die Migration muss erfolgreich abgeschlossen sein, bevor API-Replikate aktualisiert oder skaliert werden. Bei einem Rollback darf ein destruktiver Downgrade nicht ungeprüft ausgeführt werden. Nach dem Start `GET /health/ready` prüfen; in Produktion umfasst die Readiness Datenbank und Redis. API-Prozesse führen keine Migration aus.

Beim Upgrade vom bisherigen root-basierten API-Image muss das private Dokumentenvolume einmalig auf den neuen Containerbenutzer übertragen werden. Zuerst ein Backup erstellen und die alte API stoppen, dann gezielt nur das Dokumentenvolume anpassen:

```sh
docker compose stop api
docker compose run --rm --no-deps --user 0 --entrypoint chown api \
  -R 10001:10001 /var/lib/securityops/documents
```

Der Befehl ändert Dateieigentümer, nicht Dokumentinhalte. Bei Neuinstallationen mit leerem Volume ist er nicht erforderlich.

## TLS-Reverse-Proxy und vertrauenswürdige Header

TLS wird von einem separat verwalteten Reverse Proxy terminiert. Beispiel für Nginx auf demselben Host; Zertifikatspfade, Hostname und TLS-Parameter müssen an die Betriebsumgebung angepasst werden:

```nginx
server {
    listen 443 ssl;
    server_name securityops.example.invalid;

    ssl_certificate /etc/letsencrypt/live/securityops.example.invalid/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/securityops.example.invalid/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        # Eingehenden, nicht vertrauenswürdigen X-Forwarded-For-Wert ersetzen.
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

HSTS nur aktivieren, wenn die Domain dauerhaft ausschließlich über HTTPS erreichbar ist; `includeSubDomains` nur setzen, wenn ausnahmslos alle Subdomains HTTPS unterstützen. Der statische Nginx-Webserver setzt `nosniff`, Frame-Schutz, Referrer-Policy, eine restriktive Content-Security-Policy und eine Kamera-erlaubende Permissions-Policy. Der TLS-Proxy muss eingehende `X-Forwarded-*`-Header überschreiben, statt sie ungeprüft von Clients zu übernehmen.

Uvicorn vertraut ausschließlich den in `FORWARDED_ALLOW_IPS` aufgelisteten Adressen; Wildcards sind verboten und werden im Produktionsmodus abgelehnt. Standard ist die feste Frontend-Container-IP `172.28.0.10`, die der API als unmittelbarer Proxy-Hop bekannt ist. `APP_NETWORK_SUBNET` und `APP_FRONTEND_IP` müssen zusammenpassen und dürfen keine bestehenden Host-/Docker-Netze überlappen. Läuft ein TLS-Proxy vor dem veröffentlichten Frontend-Port, anhand der Nginx-Logs die von der Frontend-Instanz tatsächlich beobachtete Proxy-/Bridge-IP ermitteln und nur diese zusätzlich in `FORWARDED_ALLOW_IPS` aufnehmen; die Frontend-Container-IP muss enthalten bleiben. Keine beliebigen Client-Adressen oder `*` vertrauen. Der TLS-Proxy muss `X-Forwarded-For` mit der ermittelten Client-IP neu setzen, damit die Weitergabe an FastAPI eine kontrollierte Kette bildet. Die Rate-Limit-IP wird nur aus dieser vertrauenswürdigen Proxy-Kette abgeleitet.

## Secrets und Betrieb

- `POSTGRES_PASSWORD`, TLS-Schlüssel und Backup-Identitäten aus einem Secret-Manager bereitstellen; nicht in `.env`, Git oder Images veröffentlichen.
- Die Beispielkonfiguration nutzt eine lokale PostgreSQL-Rolle. Für Produktion eine dedizierte Rolle mit minimalen Datenbankrechten und getrennte Migrationsberechtigungen einrichten.
- Redis ist nur im internen Compose-Netz erreichbar und speichert flüchtige Rate-Limit-Zähler. Für externe Redis-Installationen `rediss://` und die dafür erforderlichen Zugriffsdaten sicher bereitstellen.
- Dokumente liegen im privaten Volume und niemals im statischen Webroot. Volume-Verschlüsselung, Zugriff, Aufbewahrung und Backup sind Betreiberaufgaben.
- Images, OS-Pakete und Abhängigkeiten regelmäßig aktualisieren; CI-Images bauen keine Images mit festgeschriebenem Digest. Für den produktiven Rollout geprüfte Images/Digests freigeben und einen Rollback-Ablauf erproben.
- Monitoring, Protokollaufbewahrung ohne Tokens/Passwörter, Alarmierung, Datenbankrechte, Datenschutz und Incident-Verfahren vor öffentlichem Betrieb festlegen.

## Grenzen und Nachweise

CI baut die Container, prüft die Migrationen und API-Tests auf PostgreSQL 17 und führt einen verschlüsselten Backup-/Restore-Zyklus für Datenbank und Dokumentenvolume in isolierten Testressourcen aus. Der CI-Restore ist kein Restore einer Produktionssicherung. TLS-Zertifikate, DNS, produktive Proxy-IP, Secret-Manager, Produktionsrechte, Verfügbarkeit und Wiederherstellung im Betreiberumfeld wurden dadurch nicht eingerichtet oder nachgewiesen. Es wird keine Produktionsfreigabe behauptet.
