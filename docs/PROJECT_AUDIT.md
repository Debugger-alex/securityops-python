# SecurityOps – Repository-Audit

Stand: 2026-11-08. Grundlage ist der tatsächlich geprüfte Quellcode im Repository, nicht nur README- oder Statusangaben.

## Bestand

| Bereich/Funktion | Status | Tatsächlicher Stand |
|---|---|---|
| Backend-Struktur | TEILWEISE | Ein FastAPI-Monolith mit `api.py`, `identity_api.py`, `auth.py`, zentralen SQLAlchemy-Modellen und Konfiguration. Noch keine fachlichen Modulgrenzen für Objekte, Personal, Planung, OWKS, Dokumente oder Abrechnung. |
| Frontend | TEILWEISE | Eine React-Seite mit Anmeldung, Kundenliste, Suche, Neuanlage, Statusänderung und Kennzahlen. Noch keine modulare Navigation, Detailseiten, Formularbibliothek oder UI-Test-Suite. |
| PostgreSQL/ORM | TEILWEISE | SQLAlchemy-Modelle und vier Migrationen; die vierte ergänzt Kundenanschriften, Ansprechpartner, Archivierung und Historie. Kundenverwaltungs-Tests laufen lokal auf SQLite und gehostet auf PostgreSQL. |
| Alembic | TEILWEISE | Migrationsumgebung und explizite Migrationen vorhanden. Migrationen wurden offline in PostgreSQL-SQL übersetzt; Migration 0004 wurde in gehosteter PostgreSQL-CI erfolgreich angewandt. |
| Anmeldung | TEILWEISE | Benutzername/Passwort, Argon2id, serverseitig widerrufbare opaque Sitzung, generische Fehlermeldung. MFA und Passwortzurücksetzung fehlen. |
| Sitzungen/CSRF | TEILWEISE | HttpOnly-Sitzungscookie, CSRF-Cookie/Header-Abgleich, SameSite=Strict, Idle-/Absolute-Timeout, Logout und Widerruf beim Passwortwechsel. Keine Sitzungsübersicht oder gezielte Einzelwiderruf-UI. |
| Rate-Limit | TEILWEISE | Login ist auf 5 Versuche pro Minute begrenzt. Speicherung ist im Prozessspeicher, nicht instanzübergreifend; Proxy-Client-IP-Konfiguration ist nicht eingerichtet. |
| RBAC | TEILWEISE | Berechtigungen werden im Backend an geschützten Endpunkten geprüft; Standardrollen sind per Migration angelegt. Keine objektbezogenen Zugriffszuweisungen und kein Rolleneditor. Neue Rechtevergabe für Administratorrollen ist auf `users.manage_admin` beschränkt. |
| Benutzerverwaltung | TEILWEISE | Benutzer anlegen/listen/aktivieren/deaktivieren, Rollen zuweisen. Kein Rollen-/Rechteeditor, Einladungs- oder Passwortzurücksetzungsablauf. |
| Audit | TEILWEISE | Anmeldung, fehlgeschlagene Anmeldung, Passwortwechsel, Benutzer- und Kundenänderungen werden geloggt. Keine Änderungen/Löschungen über die Anwendungs-API; kein Schutz vor direkten privilegierten Datenbankänderungen, keine Vollständigkeit über noch nicht implementierte Module. |
| Kunden | TEILWEISE | Anlage, Suche, Filter/Sortierung, UUID-Detailabruf/-änderung, Geschäfts-/Rechnungsanschriften, Ansprechpartner mit Primärkontakt, Archivierung/Reaktivierung und Historie sind implementiert. Vertrags-, Objekt- und Dokumentzuordnung fehlen. Kunden werden archiviert statt physisch gelöscht. |
| Objekte | FEHLT | Kein Objektmodell, keine Endpunkte oder Oberfläche. |
| Personal | FEHLT | Kein Mitarbeitermodell, keine Personalakten oder Qualifikationen. |
| Dienstplanung | FEHLT | Keine Dienste, Zuweisungen, Konflikt- oder Arbeitszeitprüfung. |
| Zeiterfassung | FEHLT | Keine Zeitbuchungen, Korrekturfreigaben oder Abrechnungsschnittstelle. |
| OWKS/Kontrollen | FEHLT | Keine Wachbucheinträge, Kontrollpunkte, QR-/NFC-Validierung oder Offline-Warteschlange. |
| Dokumente/Verträge/Rechnungen | FEHLT | Kein Dateiablage-, Vertrags- oder Rechnungsmodell. |
| Dashboard | TEILWEISE | Kundenanzahl, aktive Kunden und Interessenten werden aus der Datenbank gezählt; operative Kennzahlen fehlen. |
| Docker/Deployment | TEILWEISE | Compose startet PostgreSQL, API und Vite-Entwicklungsserver. Es gibt keinen produktionsfähigen React-Static-Build, Reverse Proxy, TLS- oder Backup-Aufbau. Docker wurde in der Umgebung nicht ausgeführt. |
| Tests | TEILWEISE | 11 Backendtests bestehen lokal auf SQLite; Ruff-Lint/Formatprüfung, Frontend-TypeScript-/Produktionsbuild und Migrationen bis 0004 offline erfolgreich. Gehostete Phase-2-CI prüft PostgreSQL-Migration/API-Tests, Frontend- und Docker-Build. Keine E2E-, Last-, Backup-/Restore- oder Frontend-Komponententests. |

## Fehler und Risiken

### Behoben in der aktuellen Phase

- **FEHLERHAFT – Rechteausweitung über Benutzerverwaltung:** Die Geschäftsführungsrolle hatte `users.manage`, und die Benutzeranlage nahm beliebige vorhandene Rollen an. Damit hätte sie Administratorrechte vergeben können. Die neue additive Migration trennt `users.manage_admin` ab; Create und Update kontrollieren dieses Recht serverseitig. Ein Regressionstest deckt die Ablehnung ab.
- **SICHERHEIT – unsichere implizite Cookie-Standardeinstellung:** Compose setzte `SESSION_COOKIE_SECURE` standardmäßig auf `false`. Jetzt ist der Compose-Fallback `true`; die lokale `.env.example` setzt für lokales HTTP ausdrücklich `false`.
- **SICHERHEIT – implizites Datenbankpasswort:** Anwendungskonfiguration verlangte kein explizit gesetztes Datenbankpasswort. Sie verlangt jetzt `POSTGRES_PASSWORD`; der Testaufbau setzt einen ausschließlich für Tests bestimmten Wert.

### Offen

- **Sicherheits-/Betriebsrisiko:** Der In-Memory-Rate-Limiter kann zwischen Instanzen nicht teilen und wird nach Prozessneustart zurückgesetzt. Mehrere Worker benötigen gemeinsamen Speicher und eine vertrauenswürdige Proxy-IP-Konfiguration.
- **Sicherheits-/Betriebsrisiko:** Compose startet im Frontend `vite --host`; es ist ein Entwicklungsserver, kein gehärteter Produktions-Webserver. HTTPS/Reverse Proxy fehlt.
- **Sicherheits-/Betriebsrisiko:** Der Audit-Datensatz ist nur über die App-API schreibgeschützt. Datenbankbesitzer oder Administratoren können die Tabelle ändern; Append-only-Berechtigungen/externes unveränderliches Archiv fehlen.
- **Datenbank-/Betriebsrisiko:** Der API-Container führt `alembic upgrade head` bei jedem Start aus. Das ist bei mehreren parallel startenden API-Replikaten zu koordinieren; es gibt kein separates Deployment-Migrationsverfahren.
- **Datenbanklücke:** Kundenstammdaten sind erweitert; die Kundennummer bleibt ein eindeutiger zufälliger UUID-basierter Identifikator statt einer fortlaufenden Nummer. Historie enthält nur geänderte Feldnamen, keine Vorher-/Nachher-Werte.
- **RBAC-Lücke:** Standardrollen und Rechte werden derzeit nur durch Migration initialisiert. Rollenverwaltung in der Oberfläche/API fehlt; Administratorzuweisungen werden durch die laufende Phase separat geschützt.
- **Integrationslücke:** Lokale Tests verwenden SQLite. Gehostete CI deckt Migrationen und API-Tests gegen PostgreSQL ab; systematische Schema-Differenzprüfung und weitere Datenbanktests bleiben offen.
- **Qualitätssicherung:** GitHub Actions prüft Backend, Migrationen gegen temporäres PostgreSQL, Frontend- und Docker-Build. SCA/SAST sind noch nicht eingerichtet.
- **Dokumentationslücke:** Vor dieser Phase waren nur README und ein kurzer Projektstatus vorhanden; Betriebs-, Datenbank-, Sicherheits- und API-Dokumentation fehlten.

## Datenbankbeobachtungen

- UUID-Primärschlüssel, Fremdschlüssel, Status-Constraints und Zeitstempel sind in Grundtabellen vorhanden.
- Benutzerrollen und Rollenberechtigungen sind Many-to-many verknüpft; Löschregeln sind überwiegend `CASCADE`. Kunden werden derzeit nicht physisch über eine API gelöscht.
- `UserSession.token_hash` ist eindeutig; absolute und gleitende Fristen sind gespeichert.
- `AuditLog.details` ist JSON; es gibt keine Datenbankregel, die Updates/Deletes für die Laufzeitrolle verhindert.
- Modell- und Migrationsdefinitionen müssen weiter gegen echte PostgreSQL-Instanzen geprüft werden.

## Architekturbeobachtungen

- Ein modularer Monolith ist für den aktuellen Umfang angemessen.
- Fachmodule sind noch nicht aus dem API-/Modellkern extrahiert; beim Wachstum sollten Domänen und Zugriffsgrenzen getrennt werden.
- Die Oberfläche ruft die API zentral über `api.ts` auf, hat aber noch kein Router-/Feature-Modul-Layout.
- Produktive Frontend-Auslieferung, Reverse Proxy, zentrale Secrets-/Rate-Limit-Verwaltung und Monitoring fehlen.

## Empfohlene Entwicklungsreihenfolge

1. Phase 1 abschließen: PostgreSQL-Integrationslauf und reproduzierbare Deployment-Prüfung ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).
2. Kundenverwaltung fachlich prüfen und Vertrags-/Dokumentzuordnung planen ([#6](https://github.com/Xonni-star/securityops-python/issues/6)).
3. Objektmodell mit Kundenbeziehung und objektbezogener Zugriffskontrolle ([#2](https://github.com/Xonni-star/securityops-python/issues/2)).
4. Personal, Qualifikationen und restriktive Personalaktenberechtigungen ([#5](https://github.com/Xonni-star/securityops-python/issues/5)).
5. Dienstplanung mit Konflikt-/Qualifikationsprüfungen ([#10](https://github.com/Xonni-star/securityops-python/issues/10)), danach Zeiterfassung/Freigaben ([#4](https://github.com/Xonni-star/securityops-python/issues/4)).
6. OWKS und manipulationsnachweisbare Kontrollereignisse ([#3](https://github.com/Xonni-star/securityops-python/issues/3)).
7. Dokumente, Verträge und Fristüberwachung ([#8](https://github.com/Xonni-star/securityops-python/issues/8)).
8. Rechnungswesen mit versionierten, nach Freigabe nicht überschreibbaren Rechnungen ([#7](https://github.com/Xonni-star/securityops-python/issues/7)).
9. Dashboard, E2E-/PostgreSQL-/Backup-Tests, Härtung und produktionsfähiges Deployment ([#9](https://github.com/Xonni-star/securityops-python/issues/9)).

## Prüfbelege

- Phase-2-Arbeitsstand: 11 Backend-Tests bestanden; Ruff-Lint/Formatprüfung und Frontend-TypeScript-/Produktionsbuild bestanden; Alembic-Migrationen einschließlich 0004 offline und in gehosteter PostgreSQL-CI geprüft.
- PostgreSQL und Docker waren in der Entwicklungsumgebung nicht verfügbar; gehostete CI hat PostgreSQL-Migration/API-Tests sowie Frontend- und Docker-Build erfolgreich abgeschlossen.
- Der GitHub-Actions-Lauf mit kurzlebigem PostgreSQL, Frontend-Build und Docker-Images war nach Behebung der Test-Fixture erfolgreich.
