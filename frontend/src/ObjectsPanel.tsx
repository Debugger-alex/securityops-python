import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  archiveObject,
  assignUserToObject,
  createObject,
  createObjectContact,
  getCustomers,
  getObject,
  getObjectAssignmentCandidates,
  getObjectAssignments,
  getObjectHistory,
  getObjects,
  getObjectSensitiveData,
  removeObjectAssignment,
  removeObjectContact,
  updateObject,
  updateObjectSensitiveData,
} from "./api";
import type {
  AuthUser,
  Customer,
  ObjectAssignableUser,
  ObjectAssignment,
  ObjectHistory,
  ObjectStatus,
  SecurityObject,
  ObjectSensitiveData,
  OperatingWindow,
  Weekday,
} from "./types";

const pageSize = 25;
type OperatingHours = NonNullable<SecurityObject["operating_hours"]>;
const weekdays: { key: Weekday; label: string }[] = [
  { key: "monday", label: "Montag" },
  { key: "tuesday", label: "Dienstag" },
  { key: "wednesday", label: "Mittwoch" },
  { key: "thursday", label: "Donnerstag" },
  { key: "friday", label: "Freitag" },
  { key: "saturday", label: "Samstag" },
  { key: "sunday", label: "Sonntag" },
];

const actionNames: Record<string, string> = {
  created: "Objekt angelegt",
  updated: "Objektdaten geändert",
  archived: "Objekt archiviert",
  contact_created: "Kontakt hinzugefügt",
  contact_updated: "Kontakt geändert",
  contact_deleted: "Kontakt entfernt",
  user_assigned: "Benutzer zugewiesen",
  user_unassigned: "Benutzerzuweisung entfernt",
  sensitive_data_updated: "Sensible Angaben geändert",
};

function messageFrom(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function optionalValue(data: FormData, key: string) {
  return String(data.get(key) ?? "").trim() || null;
}

function operatingHoursFrom(form: FormData): OperatingHours {
  const hours = JSON.parse(String(form.get("operating_hours") ?? "{}")) as OperatingHours;
  return Object.fromEntries(
    Object.entries(hours).filter(([, windows]) => windows?.length),
  ) as OperatingHours;
}

export default function ObjectsPanel({ user }: { user: AuthUser }) {
  const [objects, setObjects] = useState<SecurityObject[]>([]);
  const [total, setTotal] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<ObjectStatus | "">("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<SecurityObject | null>(null);
  const [history, setHistory] = useState<ObjectHistory[]>([]);
  const [assignments, setAssignments] = useState<ObjectAssignment[]>([]);
  const [assignmentCandidates, setAssignmentCandidates] = useState<ObjectAssignableUser[]>([]);
  const [sensitive, setSensitive] = useState<ObjectSensitiveData | null>(null);
  const [showSensitive, setShowSensitive] = useState(false);
  const [error, setError] = useState("");
  const [sensitiveError, setSensitiveError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [createFormVersion, setCreateFormVersion] = useState(0);

  const canRead = user.permissions.includes("objects.read");
  const canCreate = user.permissions.includes("objects.create");
  const canManage = user.permissions.includes("objects.manage");
  const canArchive = user.permissions.includes("objects.archive");
  const canAssign = user.permissions.includes("objects.assign");
  const canReadSensitive = user.permissions.includes("objects.sensitive.read");
  const canWriteSensitive = user.permissions.includes("objects.sensitive.write");

  const loadObjects = useCallback(async () => {
    if (!canRead) return;
    setLoading(true);
    try {
      const page = await getObjects({
        q: query,
        customerId: customerFilter,
        status: statusFilter,
        includeArchived,
        limit: pageSize,
        offset,
      });
      setObjects(page.items);
      setTotal(page.total);
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Objekte konnten nicht geladen werden."));
    } finally {
      setLoading(false);
    }
  }, [canRead, customerFilter, includeArchived, offset, query, statusFilter]);

  const refreshSelected = useCallback(async (objectId: string) => {
    const [site, siteHistory] = await Promise.all([
      getObject(objectId),
      getObjectHistory(objectId),
    ]);
    setSelected(site);
    setHistory(siteHistory);
    if (canAssign) {
      const [currentAssignments, candidates] = await Promise.all([
        getObjectAssignments(objectId),
        getObjectAssignmentCandidates(),
      ]);
      setAssignments(currentAssignments);
      setAssignmentCandidates(candidates);
    } else {
      setAssignments([]);
      setAssignmentCandidates([]);
    }
    setSensitive(null);
    setShowSensitive(false);
    setSensitiveError("");
    return site;
  }, [canAssign]);

  useEffect(() => {
    void loadObjects();
  }, [loadObjects]);

  useEffect(() => {
    if (!user.permissions.includes("customers.read")) return;
    getCustomers({
      q: "",
      status: "",
      includeArchived: false,
      sortBy: "company_name",
      sortOrder: "asc",
      limit: 100,
      offset: 0,
    })
      .then((page) => setCustomers(page.items))
      .catch((reason: unknown) => setError(messageFrom(reason, "Kunden konnten nicht geladen werden.")));
  }, [user.permissions]);

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      const created = await createObject({
        customer_id: String(data.get("customer_id")),
        name: String(data.get("name")).trim(),
        street: String(data.get("street")).trim(),
        house_number: String(data.get("house_number")).trim(),
        postal_code: String(data.get("postal_code")).trim(),
        city: String(data.get("city")).trim(),
        country_code: String(data.get("country_code") || "DE").trim().toUpperCase(),
        status: String(data.get("status")) as ObjectStatus,
        description: optionalValue(data, "description"),
        service_instructions: optionalValue(data, "service_instructions"),
        phone: optionalValue(data, "phone"),
        email: optionalValue(data, "email"),
        required_staffing: Number(data.get("required_staffing") || 1),
        qualification_requirements: String(data.get("qualification_requirements") ?? "")
          .split(",").map((value) => value.trim()).filter(Boolean),
        operating_hours: operatingHoursFrom(data),
      });
      form.reset();
      setCreateFormVersion((version) => version + 1);
      setOffset(0);
      await loadObjects();
      await refreshSelected(created.id);
    } catch (reason) {
      setError(messageFrom(reason, "Objekt konnte nicht angelegt werden."));
    } finally {
      setBusy(false);
    }
  }

  async function submitUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await updateObject(selected.id, {
        customer_id: String(data.get("customer_id")),
        name: String(data.get("name")).trim(),
        status: String(data.get("status")) as ObjectStatus,
        street: String(data.get("street")).trim(),
        house_number: String(data.get("house_number")).trim(),
        postal_code: String(data.get("postal_code")).trim(),
        city: String(data.get("city")).trim(),
        country_code: String(data.get("country_code") || "DE").trim().toUpperCase(),
        description: optionalValue(data, "description"),
        service_instructions: optionalValue(data, "service_instructions"),
        phone: optionalValue(data, "phone"),
        email: optionalValue(data, "email"),
        required_staffing: Number(data.get("required_staffing") || 0),
        qualification_requirements: String(data.get("qualification_requirements") ?? "")
          .split(",").map((value) => value.trim()).filter(Boolean),
        operating_hours: operatingHoursFrom(data),
      });
      await Promise.all([loadObjects(), refreshSelected(selected.id)]);
    } catch (reason) {
      setError(messageFrom(reason, "Objekt konnte nicht gespeichert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function openObject(site: SecurityObject) {
    setError("");
    try {
      await refreshSelected(site.id);
    } catch (reason) {
      setError(messageFrom(reason, "Objektdetails konnten nicht geladen werden."));
    }
  }

  async function archiveSelected() {
    if (!selected || !window.confirm(`Soll das Objekt „${selected.name}“ archiviert werden?`)) return;
    setBusy(true);
    try {
      await archiveObject(selected.id);
      await Promise.all([loadObjects(), refreshSelected(selected.id)]);
    } catch (reason) {
      setError(messageFrom(reason, "Objekt konnte nicht archiviert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function addContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      await createObjectContact(selected.id, {
        first_name: String(data.get("first_name")).trim(),
        last_name: String(data.get("last_name")).trim(),
        responsibility: optionalValue(data, "responsibility"),
        email: optionalValue(data, "contact_email"),
        phone: optionalValue(data, "contact_phone"),
        is_primary: data.get("is_primary") === "on",
      });
      form.reset();
      await refreshSelected(selected.id);
    } catch (reason) {
      setError(messageFrom(reason, "Kontakt konnte nicht gespeichert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function deleteContact(contactId: string, fullName: string) {
    if (!selected || !window.confirm(`Soll der Kontakt „${fullName}“ entfernt werden?`)) return;
    try {
      await removeObjectContact(selected.id, contactId);
      await refreshSelected(selected.id);
    } catch (reason) {
      setError(messageFrom(reason, "Kontakt konnte nicht entfernt werden."));
    }
  }

  async function addAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    const userId = String(data.get("assignee"));
    if (!userId) return;
    setBusy(true);
    try {
      await assignUserToObject(selected.id, userId);
      await refreshSelected(selected.id);
    } catch (reason) {
      setError(messageFrom(reason, "Benutzer konnte nicht zugewiesen werden."));
    } finally {
      setBusy(false);
    }
  }

  async function unassignUser(userId: string, fullName: string) {
    if (!selected || !window.confirm(`Soll „${fullName}“ vom Objekt abgezogen werden?`)) return;
    try {
      await removeObjectAssignment(selected.id, userId);
      await refreshSelected(selected.id);
    } catch (reason) {
      setError(messageFrom(reason, "Zuweisung konnte nicht entfernt werden."));
    }
  }

  async function changeManager(userId: string) {
    if (!selected) return;
    try {
      await updateObject(selected.id, { object_manager_user_id: userId || null });
      await refreshSelected(selected.id);
    } catch (reason) {
      setError(messageFrom(reason, "Objektleitung konnte nicht geändert werden."));
    }
  }

  async function revealSensitiveData() {
    if (!selected) return;
    setShowSensitive(true);
    setSensitiveError("");
    try {
      setSensitive(await getObjectSensitiveData(selected.id));
    } catch (reason) {
      setSensitiveError(messageFrom(reason, "Sensible Angaben konnten nicht geladen werden."));
    }
  }

  async function saveSensitiveData(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const updated = await updateObjectSensitiveData(selected.id, {
        alarm_information: optionalValue(data, "alarm_information"),
        emergency_information: optionalValue(data, "emergency_information"),
        key_management: optionalValue(data, "key_management"),
        access_authorizations: optionalValue(data, "access_authorizations"),
      });
      setSensitive(updated);
      await refreshSelected(selected.id);
      setSensitive(updated);
      setShowSensitive(true);
    } catch (reason) {
      setSensitiveError(messageFrom(reason, "Sensible Angaben konnten nicht gespeichert werden."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="objects-module">
      {error && <p className="alert" role="alert">{error}</p>}
      <div className="objects-layout">
        <section className="panel">
          <div className="panel-heading">
            <div><p className="eyebrow">OPERATIVE STAMMDATEN</p><h2>Objekte</h2></div>
            <span className="result-count">{total} Einträge</span>
          </div>
          <label className="search-field">
            <span className="sr-only">Objekte suchen</span><span aria-hidden="true">⌕</span>
            <input value={query} placeholder="Objekt, Nummer, Kunde oder Standort suchen"
              onChange={(event) => {
                setQuery(event.target.value);
                setOffset(0);
              }} />
          </label>
          <div className="filter-row">
            <label>Status<select value={statusFilter} onChange={(event) => {
              setStatusFilter(event.target.value as ObjectStatus | "");
              setOffset(0);
            }}>
              <option value="">Alle Status</option><option value="active">Aktiv</option><option value="inactive">Inaktiv</option>
            </select></label>
            <label>Kunde<select value={customerFilter} onChange={(event) => {
              setCustomerFilter(event.target.value);
              setOffset(0);
            }}>
              <option value="">Alle Kunden</option>
              {customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.company_name}</option>)}
            </select></label>
            {canArchive && <label className="checkbox-label">
              <input type="checkbox" checked={includeArchived} onChange={(event) => {
                setIncludeArchived(event.target.checked);
                setOffset(0);
              }} /> Archivierte einblenden
            </label>}
          </div>
          <div className="table-scroll">
            <table>
              <thead><tr><th>Objekt</th><th>Kunde</th><th>Standort</th><th>Status</th><th /></tr></thead>
              <tbody>
                {objects.map((site) => <tr key={site.id} className={site.archived_at ? "archived-row" : ""}>
                  <td><strong>{site.name}</strong><small>{site.object_number}</small></td>
                  <td>{site.customer_name}</td>
                  <td>{site.postal_code} {site.city}<small>{site.street} {site.house_number}</small></td>
                  <td><span className={`status status-${site.status}`}>
                    {site.archived_at ? "Archiviert" : site.status === "active" ? "Aktiv" : "Inaktiv"}
                  </span></td>
                  <td><button className="text-button" onClick={() => void openObject(site)}>Öffnen</button></td>
                </tr>)}
                {!loading && objects.length === 0 && <tr><td className="empty" colSpan={5}>Keine passenden Objekte vorhanden.</td></tr>}
                {loading && <tr><td className="empty" colSpan={5}>Objekte werden geladen …</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span className="result-count">{total === 0 ? 0 : offset + 1}–{Math.min(offset + pageSize, total)} von {total}</span>
            <div>
              <button className="secondary-button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>Zurück</button>
              <button className="secondary-button" disabled={offset + pageSize >= total} onClick={() => setOffset(offset + pageSize)}>Weiter</button>
            </div>
          </div>
        </section>

        {canCreate && customers.length > 0 && <aside className="panel form-panel">
          <div className="panel-heading"><div><p className="eyebrow">NEU ANLEGEN</p><h2>Objekt hinzufügen</h2></div></div>
          <form onSubmit={submitCreate}>
            <label>Kunde <span aria-hidden="true">*</span><select name="customer_id" required defaultValue="">
              <option value="" disabled>Kunde auswählen</option>
              {customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.company_name}</option>)}
            </select></label>
            <ObjectFields key={createFormVersion} />
            <button type="submit" disabled={busy}>{busy ? "Wird gespeichert …" : "Objekt speichern"}</button>
          </form>
        </aside>}
      </div>

      {selected && <section className="panel detail-panel">
        <div className="panel-heading">
          <div><p className="eyebrow">OBJEKTDETAILS · {selected.object_number}</p><h2>{selected.name}</h2></div>
          <button className="secondary-button" onClick={() => {
            setSelected(null);
            setHistory([]);
            setSensitive(null);
          }}>Schließen</button>
        </div>
        {error && <p className="alert" role="alert">{error}</p>}
        <div className="object-detail-grid">
          {canManage && !selected.archived_at ? <form className="form-panel detail-form" onSubmit={submitUpdate}>
            <label>Kunde<select name="customer_id" defaultValue={selected.customer_id}>
              {customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.company_name}</option>)}
            </select></label>
            <ObjectFields site={selected} />
            <button type="submit" disabled={busy}>Änderungen speichern</button>
          </form> : <div className="detail-summary">
            <p><strong>Kunde:</strong> {selected.customer_name}</p>
            <p><strong>Status:</strong> {selected.archived_at ? "Archiviert" : selected.status === "active" ? "Aktiv" : "Inaktiv"}</p>
            <p><strong>Adresse:</strong><br />{selected.street} {selected.house_number}<br />{selected.postal_code} {selected.city}, {selected.country_code}</p>
            {selected.description && <p><strong>Beschreibung:</strong><br />{selected.description}</p>}
            {selected.service_instructions && <p><strong>Dienstanweisungen:</strong><br />{selected.service_instructions}</p>}
            <p><strong>Soll-Besetzung:</strong> {selected.required_staffing}</p>
            <p><strong>Qualifikationen:</strong> {selected.qualification_requirements.join(", ") || "Keine hinterlegt"}</p>
            <OperatingHoursSummary hours={selected.operating_hours} />
          </div>}
          <div className="object-detail-side">
            {canArchive && !selected.archived_at && <section className="archive-box">
              <h3>Objekt archivieren</h3>
              <p className="muted">Das Objekt bleibt für die Historie erhalten und wird standardmäßig ausgeblendet.</p>
              <button className="danger-button" disabled={busy} onClick={() => void archiveSelected()}>Objekt archivieren</button>
            </section>}

            <section className="contact-section">
              <h3>Objektkontakte</h3>
              {selected.contacts.length === 0 && <p className="muted">Keine Kontakte hinterlegt.</p>}
              {selected.contacts.map((contact) => {
                const fullName = `${contact.first_name} ${contact.last_name}`;
                return <article className="contact-card" key={contact.id}>
                  <div><strong>{fullName}</strong>{contact.is_primary && <span className="primary-tag">Primär</span>}
                    {contact.responsibility && <small>{contact.responsibility}</small>}
                    {contact.email && <small><a href={`mailto:${contact.email}`}>{contact.email}</a></small>}
                    {contact.phone && <small>{contact.phone}</small>}
                  </div>
                  {canManage && !selected.archived_at && <button className="text-button danger-text"
                    onClick={() => void deleteContact(contact.id, fullName)}>Entfernen</button>}
                </article>;
              })}
              {canManage && !selected.archived_at && <form className="contact-form" onSubmit={addContact}>
                <h4>Kontakt hinzufügen</h4>
                <div className="form-row">
                  <label>Vorname<input name="first_name" required maxLength={100} /></label>
                  <label>Nachname<input name="last_name" required maxLength={100} /></label>
                </div>
                <label>Funktion<input name="responsibility" maxLength={120} /></label>
                <label>E-Mail<input name="contact_email" type="email" maxLength={254} /></label>
                <label>Telefon<input name="contact_phone" maxLength={40} /></label>
                <label className="checkbox-label"><input type="checkbox" name="is_primary" /> Primärkontakt</label>
                <button className="secondary-button" type="submit" disabled={busy}>Kontakt hinzufügen</button>
              </form>}
            </section>

            {canAssign && <section className="assignment-section">
              <h3>Zugewiesene Benutzer</h3>
              {assignments.map((assignment) => <article className="contact-card" key={assignment.user_id}>
                <div><strong>{assignment.full_name}</strong><small>{assignment.username}</small></div>
                {!selected.archived_at && <button className="text-button danger-text"
                  onClick={() => void unassignUser(assignment.user_id, assignment.full_name)}>Entfernen</button>}
              </article>)}
              {!selected.archived_at && <form className="contact-form" onSubmit={addAssignment}>
                <label>Benutzer zuweisen<select name="assignee" defaultValue="">
                  <option value="">Benutzer auswählen</option>
                  {assignmentCandidates.filter((candidate) =>
                    !assignments.some((assignment) => assignment.user_id === candidate.id))
                    .map((candidate) => <option value={candidate.id} key={candidate.id}>
                      {candidate.full_name} ({candidate.username})
                    </option>)}
                </select></label>
                <button className="secondary-button" type="submit" disabled={busy}>Zuweisen</button>
              </form>}
              {!selected.archived_at && <label className="manager-select">Objektleitung
                <select value={selected.object_manager_user_id ?? ""} onChange={(event) => void changeManager(event.target.value)}>
                  <option value="">Keine Objektleitung</option>
                  {assignmentCandidates.filter((candidate) =>
                    assignments.some((assignment) => assignment.user_id === candidate.id))
                    .map((candidate) => <option value={candidate.id} key={candidate.id}>{candidate.full_name}</option>)}
                </select>
              </label>}
            </section>}

            {(canReadSensitive || canWriteSensitive) && <section className="sensitive-section">
              <h3>Alarm- und Zutrittsdaten</h3>
              <p className="muted">Diese Angaben werden verschlüsselt gespeichert und sind getrennt berechtigt.</p>
              {canReadSensitive && !showSensitive && <button className="secondary-button" onClick={() => void revealSensitiveData()}>
                Sensible Daten anzeigen
              </button>}
              {sensitiveError && <p className="alert" role="alert">{sensitiveError}</p>}
              {showSensitive && sensitive && <form className="contact-form" onSubmit={saveSensitiveData}>
                <label>Alarmhinweise<textarea name="alarm_information" rows={3} readOnly={!canWriteSensitive}
                  defaultValue={sensitive.alarm_information ?? ""} /></label>
                <label>Notfallinformationen<textarea name="emergency_information" rows={3} readOnly={!canWriteSensitive}
                  defaultValue={sensitive.emergency_information ?? ""} /></label>
                <label>Schlüsselverwaltung<textarea name="key_management" rows={3} readOnly={!canWriteSensitive}
                  defaultValue={sensitive.key_management ?? ""} /></label>
                <label>Zugangsberechtigungen<textarea name="access_authorizations" rows={3} readOnly={!canWriteSensitive}
                  defaultValue={sensitive.access_authorizations ?? ""} /></label>
                {canWriteSensitive && <button type="submit" disabled={busy}>Sensible Angaben verschlüsselt speichern</button>}
                {sensitive.updated_at && <small className="muted">Geändert am {new Date(sensitive.updated_at).toLocaleString("de-DE")}</small>}
              </form>}
            </section>}
          </div>
        </div>
        <section className="history-section">
          <h3>Objektchronik</h3>
          {history.length === 0 ? <p className="muted">Keine Chronikeinträge.</p> : <ol className="history-list">
            {history.map((item) => <li key={item.id}>
              <strong>{actionNames[item.action] ?? item.action}</strong>
              <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString("de-DE")}</time>
              {!!item.changed_fields.length && <small>Geänderte Bereiche: {item.changed_fields.join(", ")}</small>}
            </li>)}
          </ol>}
        </section>
      </section>}
    </section>
  );
}

function ObjectFields({ site }: { site?: SecurityObject }) {
  return <>
    <label>Objektname <span aria-hidden="true">*</span>
      <input name="name" required maxLength={200} defaultValue={site?.name ?? ""} />
    </label>
    <label>Status<select name="status" defaultValue={site?.status ?? "active"}>
      <option value="active">Aktiv</option><option value="inactive">Inaktiv</option>
    </select></label>
    <div className="form-row">
      <label>Straße<input name="street" required maxLength={160} defaultValue={site?.street ?? ""} /></label>
      <label>Hausnummer<input name="house_number" required maxLength={30} defaultValue={site?.house_number ?? ""} /></label>
    </div>
    <div className="form-row">
      <label>PLZ<input name="postal_code" required maxLength={20} defaultValue={site?.postal_code ?? ""} /></label>
      <label>Ort<input name="city" required maxLength={100} defaultValue={site?.city ?? ""} /></label>
    </div>
    <label>Ländercode<input name="country_code" required minLength={2} maxLength={2} defaultValue={site?.country_code ?? "DE"} /></label>
    <div className="form-row">
      <label>Telefon<input name="phone" type="tel" maxLength={40} defaultValue={site?.phone ?? ""} /></label>
      <label>E-Mail<input name="email" type="email" maxLength={254} defaultValue={site?.email ?? ""} /></label>
    </div>
    <label>Objektbeschreibung<textarea name="description" rows={3} maxLength={10000} defaultValue={site?.description ?? ""} /></label>
    <label>Dienstanweisungen<textarea name="service_instructions" rows={3} maxLength={20000}
      defaultValue={site?.service_instructions ?? ""} /></label>
    <label>Erforderliche Personalstärke<input name="required_staffing" type="number" min={0} max={500}
      defaultValue={site?.required_staffing ?? 1} /></label>
    <label>Erforderliche Qualifikationen <small>(durch Komma trennen)</small>
      <input name="qualification_requirements" maxLength={3000}
        defaultValue={site?.qualification_requirements.join(", ") ?? ""} />
    </label>
    <OperatingHoursEditor key={site ? `${site.id}:${site.updated_at}` : undefined}
      initialHours={site?.operating_hours} />
  </>;
}

function OperatingHoursEditor({ initialHours }: { initialHours?: OperatingHours }) {
  const [hours, setHours] = useState<OperatingHours>(() =>
    Object.fromEntries(weekdays.map(({ key }) => [key, initialHours?.[key] ?? []])) as OperatingHours,
  );

  function updateWindow(day: Weekday, index: number, patch: Partial<OperatingWindow>) {
    setHours((current) => ({
      ...current,
      [day]: (current[day] ?? []).map((window, windowIndex) =>
        windowIndex === index ? { ...window, ...patch } : window),
    }));
  }

  return <fieldset className="address-fields">
    <legend>Betriebszeiten</legend>
    <input type="hidden" name="operating_hours" value={JSON.stringify(hours)} />
    <div className="hours-editor">{weekdays.map((day) => {
      const windows = hours[day.key] ?? [];
      return <div className="hours-day" key={day.key}>
        <strong>{day.label}</strong>
        {windows.map((window, index) => <div className="form-row hours-window" key={`${day.key}-${index}`}>
          <label>Beginn<input type="time" required value={window.start.slice(0, 5)}
            onChange={(event) => updateWindow(day.key, index, { start: event.target.value })} /></label>
          <label>Ende<input type="time" required value={window.end.slice(0, 5)}
            onChange={(event) => updateWindow(day.key, index, { end: event.target.value })} /></label>
          <button type="button" className="text-button danger-text"
            aria-label={`${day.label}: Zeitfenster ${index + 1} entfernen`}
            onClick={() => setHours((current) => ({
              ...current,
              [day.key]: (current[day.key] ?? []).filter((_, windowIndex) => windowIndex !== index),
            }))}>Entfernen</button>
        </div>)}
        <button type="button" className="text-button"
          onClick={() => setHours((current) => ({
            ...current,
            [day.key]: [...(current[day.key] ?? []), { start: "08:00", end: "17:00" }],
          }))}>Zeitfenster hinzufügen</button>
      </div>;
    })}</div>
  </fieldset>;
}

function OperatingHoursSummary({ hours }: { hours: SecurityObject["operating_hours"] }) {
  const entries = weekdays.flatMap((day) => (hours[day.key] ?? []).map((period) =>
    `${day.label}: ${period.start.slice(0, 5)}–${period.end.slice(0, 5)}`));
  return <p><strong>Betriebszeiten:</strong><br />{entries.length ? entries.join(" · ") : "Keine Betriebszeiten hinterlegt."}</p>;
}
