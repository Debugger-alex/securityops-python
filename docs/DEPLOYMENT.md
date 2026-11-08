# Deployment-Status

## Derzeit

`docker-compose.yml` beschreibt PostgreSQL, FastAPI und einen Vite-Entwicklungsserver. Die Ports der API und Oberfläche sind an Loopback gebunden. Der API-Container wendet Alembic-Migrationen beim Start an. Ein Produktions-Deployment mit Reverse Proxy, TLS, statischem Frontend, zentralem Rate-Limit-Store, Monitoring und getesteten Backups ist noch nicht umgesetzt.

## Vor Produktion

- Linux-Host aktualisieren und Zugriff administrativ einschränken.
- PostgreSQL nicht öffentlich erreichbar machen und dedizierte Anwendungsrollen nutzen.
- Images reproduzierbar bauen und auf feste geprüfte Versionen pinnen.
- Migrationen einmalig im kontrollierten Release-Schritt ausführen, anschließend API starten.
- Frontend als Produktionsbuild bereitstellen, nicht den Vite-Entwicklungsserver exponieren.
- HTTPS-Proxy mit korrekten Headern konfigurieren und Secure-Cookies erzwingen.
- Secrets in einen Host-/Secret-Manager statt in ein Image oder Git legen.
- Healthchecks, Protokollierung ohne Passwörter/Tokens, Monitoring, Backup und Rollback testen.

Eine Produktionsfreigabe wird nicht behauptet, solange diese Schritte nicht umgesetzt und verifiziert sind.
