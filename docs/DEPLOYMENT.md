# Deployment-Status

## Was im Repository existiert

`docker-compose.yml` beschreibt die lokale Entwicklungsumgebung mit PostgreSQL 17, FastAPI und Frontend-Vite. API und Frontend-Ports sind an `127.0.0.1` gebunden; der Datenbankport wird nicht nach außen veröffentlicht. Das Frontend-Image startet Vite im Development-Modus. Der API-Container wartet auf den DB-Healthcheck und führt Alembic-Migrationen beim Containerstart aus.

Die Anwendungsdatenbankverbindung und Cookie/CORS-Einstellungen kommen aus Umgebungsvariablen. `POSTGRES_PASSWORD` ist erforderlich. `SESSION_COOKIE_SECURE` fällt in Compose auf `true`; ein lokales HTTP-Setup kann es bewusst auf `false` setzen. Health-Endpunkte prüfen Prozess (`/health/live`) und Datenbankzugriff (`/health/ready`). GitHub Actions baut Backend-/Frontend-Images, deployt diese aber nicht.

## Nicht als produktives Deployment umgesetzt

Es gibt keinen bereitgestellten TLS-Reverse-Proxy, Produktions-Webserver für statische Frontenddateien, zentralen Secret Store, verteilten Rate-Limit-Store, separates Release-Migrationsverfahren, Datenbankrollen-/Netzwerkdesign, Monitoring, Alerting, automatisierte Backups oder Restore-Nachweis. Healthchecks und CI ersetzen diese Kontrollen nicht. Bei mehreren API-Replikaten kann die Migration beim Start konkurrieren; der Schritt ist vor Produktion als kontrollierter Einzelprozess auszuführen.

## Mindestanforderungen für einen späteren Betriebsaufbau

- Unterstützte, gepflegte Infrastruktur und Images mit geprüften Versionen; Images auf feste Artefakte/Versionen pinnen.
- PostgreSQL nur im internen Netzwerk betreiben. Getrennte minimale Laufzeit-, Migrations- und Backuprollen verwenden; Zugangsdaten über einen Secret Manager injizieren.
- Alembic genau einmal in einem kontrollierten Deploy-Schritt ausführen und Schema-/Anwendungskompatibilität verifizieren. Daten-destruktive Downgrades nicht als Rollbackstrategie einsetzen.
- Frontend als geprüfte statische Produktionsdateien ausliefern; Vite-Devserver nicht exponieren.
- TLS am vertrauenswürdigen Reverse Proxy, korrekte Proxy-Header, Secure-Cookie, HSTS und weitere nach Sicherheitsprüfung bestimmte Browser-Header einrichten.
- CORS-Origin, Uploadgrenzen/-Quarantäne, Rate-Limits und Authentifizierungs-/Autorisierungsfehler konkret testen.
- Logs ohne Passwörter, Session-/CSRF-Tokens, unnötige personenbezogene Werte oder Dateiinhalt; zentrale Aufbewahrung, Monitoring und Alarmierung festlegen.
- Backup/Restore, Incident-Abläufe, Wiederanlauf-/Rollbackverfahren und Datenschutz-/Aufbewahrungspflichten vor Inbetriebnahme testen.

Diese Liste ist eine offene Betriebsanforderung, kein Nachweis bereits ausgeführter Kontrollen. Das Projekt ist nicht produktionsfreigegeben.
