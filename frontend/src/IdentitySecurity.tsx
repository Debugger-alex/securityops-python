import { FormEvent, useEffect, useState } from "react";
import {
  changePassword,
  disableMFA,
  enableMFA,
  getMFAStatus,
  getUserSessions,
  getUserSessionsForAdmin,
  getUsers,
  revokeUserSession,
  resetUserPassword,
  startMFASetup,
} from "./api";
import type { AuthUser, MFASetup, UserSession } from "./types";

interface Props {
  user: AuthUser;
  onSignedOut: () => void;
  onPasswordChanged: () => void;
}

function messageFrom(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function IdentitySecurity({ user, onSignedOut, onPasswordChanged }: Props) {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [managedSessions, setManagedSessions] = useState<UserSession[]>([]);
  const [selectedSessionOwner, setSelectedSessionOwner] = useState("");
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [setup, setSetup] = useState<MFASetup | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const [sessionRows, status] = await Promise.all([getUserSessions(), getMFAStatus()]);
      setSessions(sessionRows);
      setMfaEnabled(status.enabled);
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Sicherheitseinstellungen konnten nicht geladen werden."));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const canResetPasswords = user.permissions.includes("users.manage")
    && user.permissions.includes("users.password_reset");
  const canManageSessions = user.permissions.includes("sessions.manage")
    && user.permissions.includes("users.read");

  useEffect(() => {
    if (!canResetPasswords && !canManageSessions) return;
    getUsers()
      .then(setUsers)
      .catch((reason: unknown) =>
        setError(messageFrom(reason, "Benutzerliste konnte nicht geladen werden.")),
      );
  }, [canManageSessions, canResetPasswords]);

  async function revokeSession(id: string, isCurrent: boolean) {
    try {
      await revokeUserSession(id);
      if (isCurrent) {
        onSignedOut();
        return;
      }
      setSessions((current) => current.filter((session) => session.id !== id));
      setNotice("Die Sitzung wurde widerrufen.");
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Sitzung konnte nicht widerrufen werden."));
    }
  }

  async function loadManagedSessions(ownerId: string) {
    setSelectedSessionOwner(ownerId);
    if (!ownerId) {
      setManagedSessions([]);
      return;
    }
    try {
      setManagedSessions(await getUserSessionsForAdmin(ownerId));
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Fremde Sitzungen konnten nicht geladen werden."));
    }
  }

  async function revokeManagedSession(id: string) {
    try {
      await revokeUserSession(id);
      setManagedSessions((current) => current.filter((session) => session.id !== id));
      setNotice("Die Sitzung wurde widerrufen.");
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Sitzung konnte nicht widerrufen werden."));
    }
  }

  async function beginSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      setSetup(await startMFASetup(String(data.get("current_password"))));
      setNotice("MFA-Schlüssel in einer Authenticator-App hinterlegen und anschließend bestätigen.");
      setError("");
      form.reset();
    } catch (reason) {
      setError(messageFrom(reason, "MFA-Einrichtung konnte nicht gestartet werden."));
    } finally {
      setBusy(false);
    }
  }

  async function confirmSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      const result = await enableMFA(String(data.get("code")));
      setRecoveryCodes(result.recovery_codes);
      setMfaEnabled(true);
      setSetup(null);
      setNotice("MFA ist aktiviert. Wiederherstellungscodes jetzt sicher speichern.");
      setError("");
      form.reset();
    } catch (reason) {
      setError(messageFrom(reason, "MFA-Code konnte nicht bestätigt werden."));
    } finally {
      setBusy(false);
    }
  }

  async function turnOffMFA(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      await disableMFA(
        String(data.get("current_password")),
        String(data.get("code")),
      );
      setMfaEnabled(false);
      setRecoveryCodes([]);
      setNotice("MFA wurde deaktiviert.");
      setError("");
      form.reset();
    } catch (reason) {
      setError(messageFrom(reason, "MFA konnte nicht deaktiviert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function updatePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const currentPassword = String(data.get("current_password"));
    const newPassword = String(data.get("new_password"));
    if (newPassword !== String(data.get("confirm_password"))) {
      setError("Die neuen Passwörter stimmen nicht überein.");
      return;
    }
    setBusy(true);
    try {
      await changePassword(currentPassword, newPassword);
      setNotice("Passwort geändert. Bitte erneut anmelden.");
      setError("");
      onPasswordChanged();
    } catch (reason) {
      setError(messageFrom(reason, "Passwort konnte nicht geändert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function resetPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      await resetUserPassword(
        String(data.get("user_id")),
        String(data.get("temporary_password")),
      );
      setNotice("Übergangspasswort gesetzt. Bitte ausschließlich über einen separaten sicheren Kanal weitergeben.");
      setError("");
      form.reset();
    } catch (reason) {
      setError(messageFrom(reason, "Passwort konnte nicht zurückgesetzt werden."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="identity-security">
      <header className="panel-heading">
        <div><p className="eyebrow">KONTO</p><h2>Sicherheit</h2></div>
      </header>
      {error && <p className="alert" role="alert">{error}</p>}
      {notice && <p className="success-message" role="status">{notice}</p>}

      <section className="panel security-panel" aria-labelledby="sessions-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">ZUGRIFFE</p><h3 id="sessions-heading">Aktive Sitzungen</h3></div>
          <button type="button" className="text-button" onClick={() => void refresh()}>
            Aktualisieren
          </button>
        </div>
        {sessions.length === 0
          ? <p className="muted">Keine aktiven Sitzungen gefunden.</p>
          : <ul className="security-session-list">
            {sessions.map((session) => (
              <li key={session.id}>
                <div>
                  <strong>{session.is_current ? "Diese Sitzung" : "Weitere Sitzung"}</strong>
                  <span>{session.user_agent || "Geräteinformationen nicht verfügbar"}</span>
                  <span>IP-Adresse: {session.ip_address || "nicht verfügbar"}</span>
                  <span>Zuletzt aktiv: {formatDate(session.last_seen_at)}</span>
                  <span>Läuft ab: {formatDate(session.expires_at)}</span>
                </div>
                <button
                  type="button"
                  className="text-button danger-text"
                  onClick={() => void revokeSession(session.id, session.is_current)}
                >
                  Widerrufen
                </button>
              </li>
            ))}
          </ul>}
      </section>

      {canManageSessions && <section className="panel security-panel" aria-labelledby="managed-sessions-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">ADMINISTRATION</p><h3 id="managed-sessions-heading">Sitzungen anderer Konten</h3></div>
        </div>
        <label className="security-owner-select">Benutzerkonto
          <select
            value={selectedSessionOwner}
            onChange={(event) => void loadManagedSessions(event.currentTarget.value)}
          >
            <option value="">Benutzer auswählen</option>
            {users.filter((candidate) => candidate.id !== user.id).map((candidate) => (
              <option key={candidate.id} value={candidate.id}>
                {candidate.full_name} ({candidate.username})
              </option>
            ))}
          </select>
        </label>
        {selectedSessionOwner && managedSessions.length === 0
          ? <p className="muted">Keine aktiven Sitzungen gefunden.</p>
          : <ul className="security-session-list">
            {managedSessions.map((session) => (
              <li key={session.id}>
                <div>
                  <strong>{session.user_agent || "Geräteinformationen nicht verfügbar"}</strong>
                  <span>IP-Adresse: {session.ip_address || "nicht verfügbar"}</span>
                  <span>Zuletzt aktiv: {formatDate(session.last_seen_at)}</span>
                  <span>Läuft ab: {formatDate(session.expires_at)}</span>
                </div>
                <button
                  type="button"
                  className="text-button danger-text"
                  onClick={() => void revokeManagedSession(session.id)}
                >
                  Widerrufen
                </button>
              </li>
            ))}
          </ul>}
      </section>}

      <section className="panel security-panel" aria-labelledby="mfa-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">ZWEITER FAKTOR</p><h3 id="mfa-heading">Mehr-Faktor-Authentifizierung</h3></div>
          <strong>{mfaEnabled ? "Aktiv" : "Nicht aktiviert"}</strong>
        </div>
        {mfaEnabled
          ? <form className="security-form" onSubmit={(event) => void turnOffMFA(event)}>
            <p className="muted">Bei der Anmeldung ist zusätzlich ein TOTP- oder Wiederherstellungscode erforderlich.</p>
            <label>Aktuelles Passwort
              <input name="current_password" type="password" autoComplete="current-password" required />
            </label>
            <label>Authenticator-Code
              <input name="code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required />
            </label>
            <button type="submit" disabled={busy}>MFA deaktivieren</button>
          </form>
          : setup
            ? <div className="security-form">
              <p>Authenticator-App mit diesem Schlüssel einrichten:</p>
              <code className="mfa-secret">{setup.secret}</code>
              <a href={setup.otpauth_uri}>Authenticator-App öffnen</a>
              <form onSubmit={(event) => void confirmSetup(event)}>
                <label>Sechsstelligen App-Code bestätigen
                  <input name="code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required />
                </label>
                <button type="submit" disabled={busy}>MFA aktivieren</button>
              </form>
            </div>
            : <form className="security-form" onSubmit={(event) => void beginSetup(event)}>
              <p className="muted">MFA schützt Anmeldungen zusätzlich zum Passwort mit einem zeitbasierten Code.</p>
              <label>Aktuelles Passwort
                <input name="current_password" type="password" autoComplete="current-password" required />
              </label>
              <button type="submit" disabled={busy}>MFA einrichten</button>
            </form>}
        {recoveryCodes.length > 0 && <div className="recovery-codes" role="region" aria-label="Wiederherstellungscodes">
          <strong>Einmalige Wiederherstellungscodes</strong>
          <p>Jeder Code kann nur einmal verwendet werden. Sie werden später nicht erneut angezeigt.</p>
          <ul>{recoveryCodes.map((code) => <li key={code}><code>{code}</code></li>)}</ul>
          <button type="button" className="text-button" onClick={() => setRecoveryCodes([])}>
            Codes sicher gespeichert
          </button>
        </div>}
      </section>

      <section className="panel security-panel" aria-labelledby="password-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">ZUGANGSDATEN</p><h3 id="password-heading">Passwort ändern</h3></div>
        </div>
        <form className="security-form" onSubmit={(event) => void updatePassword(event)}>
          <label>Aktuelles Passwort
            <input name="current_password" type="password" autoComplete="current-password" required />
          </label>
          <label>Neues Passwort (mindestens 12 Zeichen)
            <input name="new_password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required />
          </label>
          <label>Neues Passwort wiederholen
            <input name="confirm_password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required />
          </label>
          <button type="submit" disabled={busy}>Passwort ändern</button>
        </form>
      </section>

      {canResetPasswords && <section className="panel security-panel" aria-labelledby="admin-reset-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">BENUTZERVERWALTUNG</p><h3 id="admin-reset-heading">Passwort administrativ zurücksetzen</h3></div>
        </div>
        <p className="muted">Das neue Übergangspasswort wird nicht in der Antwort angezeigt. Die nächste Anmeldung erzwingt eine Passwortänderung.</p>
        <form className="security-form" onSubmit={(event) => void resetPassword(event)}>
          <label>Benutzerkonto
            <select name="user_id" required defaultValue="">
              <option value="" disabled>Benutzer auswählen</option>
              {users.filter((candidate) => candidate.id !== user.id).map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.full_name} ({candidate.username})
                </option>
              ))}
            </select>
          </label>
          <label>Neues Übergangspasswort
            <input name="temporary_password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required />
          </label>
          <button type="submit" disabled={busy}>Passwort zurücksetzen</button>
        </form>
      </section>}
    </section>
  );
}
