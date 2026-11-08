import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  approveTimeCorrection,
  approveTimeEntry,
  createManualTimeEntry,
  exportTimeEntries,
  getCustomers,
  getEmployees,
  getMissingShifts,
  getObjects,
  getTimeCorrections,
  getTimeEntries,
  getTimeReport,
  pauseTimeEntry,
  rejectTimeCorrection,
  rejectTimeEntry,
  requestTimeCorrection,
  resumeTimeEntry,
  startTimeEntry,
  stopTimeEntry,
  type TimeEntryFilters,
} from "./api";
import type {
  AuthUser,
  Customer,
  Employee,
  MissingShift,
  SecurityObject,
  TimeEntry,
  TimeEntryCorrection,
  TimeEntrySegment,
  TimeEntryStatus,
  TimeEntrySummary,
} from "./types";

type Props = { user: AuthUser };
type SegmentDraft = { kind: "work" | "break"; started_at: string; ended_at: string };
type CorrectionDraft = { entryId: string; reason: string; segments: SegmentDraft[] };

function messageFrom(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function localDate(date: Date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function utcInput(value: string) {
  return value.slice(0, 19);
}

function isoFromUtcInput(value: string) {
  return new Date(`${value}Z`).toISOString();
}

function durationLabel(seconds: number | null | undefined) {
  if (seconds === null || seconds === undefined) return "–";
  const sign = seconds < 0 ? "−" : "";
  const total = Math.floor(Math.abs(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remaining = total % 60;
  return `${sign}${hours} Std. ${String(minutes).padStart(2, "0")} Min. ${String(remaining).padStart(2, "0")} Sek.`;
}

function formatInstant(value: string | null, timeZone: string) {
  if (!value) return "–";
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone,
  }).format(new Date(value));
}

const statusNames: Record<TimeEntryStatus, string> = {
  open: "Laufend",
  submitted: "Eingereicht",
  approved: "Freigegeben",
  rejected: "Abgelehnt",
  correction_requested: "Korrektur offen",
  locked: "Gesperrt",
};

const correctionStatusNames: Record<TimeEntryCorrection["status"], string> = {
  pending: "Offen",
  approved: "Freigegeben",
  rejected: "Abgelehnt",
};

const today = localDate(new Date());
const firstOfMonth = `${today.slice(0, 8)}01`;

export default function TimeTracking({ user }: Props) {
  const canReadAll = user.permissions.includes("time_tracking.read_all");
  const canCorrectOwn = user.permissions.includes("time_tracking.correct_own");
  const canApprove = user.permissions.includes("time_tracking.approve");
  const canReject = user.permissions.includes("time_tracking.reject");
  const canManage = user.permissions.includes("time_tracking.manage");
  const canExport = user.permissions.includes("time_tracking.export");
  const [fromDate, setFromDate] = useState(firstOfMonth);
  const [toDate, setToDate] = useState(today);
  const [employeeFilter, setEmployeeFilter] = useState("");
  const [objectFilter, setObjectFilter] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [groupBy, setGroupBy] = useState<TimeEntryFilters["groupBy"]>("employee");
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [report, setReport] = useState<TimeEntrySummary | null>(null);
  const [corrections, setCorrections] = useState<TimeEntryCorrection[]>([]);
  const [missingShifts, setMissingShifts] = useState<MissingShift[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [objects, setObjects] = useState<SecurityObject[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [correctionDraft, setCorrectionDraft] = useState<CorrectionDraft | null>(null);
  const [manualPauses, setManualPauses] = useState<Array<{ started_at: string; ended_at: string }>>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const filters = useMemo<TimeEntryFilters>(() => ({
    fromDate,
    toDate,
    employeeId: employeeFilter || undefined,
    objectId: objectFilter || undefined,
    customerId: customerFilter || undefined,
    status: statusFilter || undefined,
    groupBy,
  }), [customerFilter, employeeFilter, fromDate, groupBy, objectFilter, statusFilter, toDate]);

  const load = useCallback(async () => {
    try {
      const [entryRows, summary] = await Promise.all([
        getTimeEntries(filters),
        getTimeReport(filters),
      ]);
      setEntries(entryRows);
      setReport(summary);
      if (canReadAll) {
        const [requests, missing] = await Promise.all([
          getTimeCorrections(),
          getMissingShifts(fromDate, toDate),
        ]);
        setCorrections(requests);
        setMissingShifts(missing);
      }
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Arbeitszeiten konnten nicht geladen werden."));
    }
  }, [canReadAll, filters, fromDate, toDate]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const tasks: Promise<void>[] = [];
    if (user.permissions.includes("employees.read")) {
      tasks.push(getEmployees({
        q: "",
        status: "",
        includeArchived: false,
        sortBy: "full_name",
        sortOrder: "asc",
        limit: 500,
        offset: 0,
      }).then((page) => setEmployees(page.items)));
    }
    if (user.permissions.includes("objects.read")) {
      tasks.push(getObjects({
        q: "",
        status: "",
        customerId: "",
        includeArchived: false,
        sortBy: "name",
        sortOrder: "asc",
        limit: 500,
        offset: 0,
      }).then((page) => setObjects(page.items)));
    }
    if (user.permissions.includes("customers.read")) {
      tasks.push(getCustomers({
        q: "",
        status: "",
        contractStatus: "",
        includeArchived: false,
        sortBy: "company_name",
        sortOrder: "asc",
        limit: 500,
        offset: 0,
      }).then((page) => setCustomers(page.items)));
    }
    Promise.all(tasks).catch((reason) =>
      setError(messageFrom(reason, "Filteroptionen konnten nicht geladen werden.")),
    );
  }, [user]);

  const openEntry = entries.find((entry) => entry.status === "open");
  const openSegment = openEntry?.segments.find((segment) => segment.ended_at === null);

  async function perform(action: () => Promise<unknown>, successMessage: string): Promise<boolean> {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(successMessage);
      setCorrectionDraft(null);
      await load();
      return true;
    } catch (reason) {
      setError(messageFrom(reason, "Die Arbeitszeit konnte nicht geändert werden."));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function submitManualEntry(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const employeeId = String(data.get("employee_id"));
    const objectId = String(data.get("object_id"));
    const start = String(data.get("started_at"));
    const end = String(data.get("ended_at"));
    if (!start || !end || new Date(`${end}Z`) <= new Date(`${start}Z`)) {
      setError("Das Ende muss nach dem Beginn liegen.");
      return;
    }
    const segments: Array<{ kind: "work" | "break"; started_at: string; ended_at: string }> = [];
    let cursor = new Date(`${start}Z`);
    for (let index = 0; index < manualPauses.length; index += 1) {
      const pauseStart = String(data.get(`pause_start_${index}`) ?? "");
      const pauseEnd = String(data.get(`pause_end_${index}`) ?? "");
      if (!pauseStart || !pauseEnd) {
        setError("Für jeden Pausenabschnitt müssen Beginn und Ende angegeben werden.");
        return;
      }
      const pauseStartAt = new Date(`${pauseStart}Z`);
      const pauseEndAt = new Date(`${pauseEnd}Z`);
      if (pauseStartAt < cursor || pauseEndAt <= pauseStartAt || pauseEndAt >= new Date(`${end}Z`)) {
        setError("Pausen müssen zeitlich geordnet innerhalb der Arbeitszeit liegen.");
        return;
      }
      segments.push({
        kind: "work",
        started_at: cursor.toISOString(),
        ended_at: pauseStartAt.toISOString(),
      });
      segments.push({
        kind: "break",
        started_at: pauseStartAt.toISOString(),
        ended_at: pauseEndAt.toISOString(),
      });
      cursor = pauseEndAt;
    }
    segments.push({
      kind: "work",
      started_at: cursor.toISOString(),
      ended_at: new Date(`${end}Z`).toISOString(),
    });
    const saved = await perform(
      () => createManualTimeEntry({
        employee_id: employeeId,
        object_id: objectId,
        segments,
      }),
      "Manuelle Zeitbuchung eingereicht.",
    );
    if (saved) {
      form.reset();
      setManualPauses([]);
    }
  }

  async function submitCorrection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!correctionDraft) return;
    const segments = correctionDraft.segments.map((segment) => ({
      kind: segment.kind,
      started_at: isoFromUtcInput(segment.started_at),
      ended_at: isoFromUtcInput(segment.ended_at),
    }));
    await perform(
      () => requestTimeCorrection(correctionDraft.entryId, correctionDraft.reason, segments),
      "Korrekturantrag eingereicht.",
    );
  }

  async function exportCsv() {
    setBusy(true);
    setError("");
    try {
      const blob = await exportTimeEntries(filters);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "arbeitszeiten.csv";
      link.click();
      URL.revokeObjectURL(url);
      setNotice("CSV-Export erstellt.");
    } catch (reason) {
      setError(messageFrom(reason, "CSV-Export fehlgeschlagen."));
    } finally {
      setBusy(false);
    }
  }

  function beginCorrection(entry: TimeEntry) {
    const segments = entry.segments.map((segment: TimeEntrySegment) => ({
      kind: segment.kind,
      started_at: utcInput(segment.started_at),
      ended_at: utcInput(segment.ended_at ?? new Date().toISOString()),
    }));
    setCorrectionDraft({ entryId: entry.id, reason: "", segments });
  }

  async function rejectEntry(entryId: string) {
    const reason = window.prompt("Bitte Ablehnungsgrund eingeben:");
    if (!reason?.trim()) return;
    await perform(() => rejectTimeEntry(entryId, reason.trim()), "Arbeitszeit abgelehnt.");
  }

  async function rejectCorrection(correctionId: string) {
    const reason = window.prompt("Bitte Ablehnungsgrund eingeben:");
    if (!reason?.trim()) return;
    await perform(() => rejectTimeCorrection(correctionId, reason.trim()), "Korrektur abgelehnt.");
  }

  return (
    <section className="time-tracking-module">
      <section className="intro object-intro">
        <p className="eyebrow">EINSATZBETRIEB</p>
        <h1>Zeiterfassung</h1>
        <p>Arbeits- und Pausenzeiten nachvollziehbar erfassen und freigeben.</p>
      </section>
      {error && <p className="alert page-alert" role="alert">{error}</p>}
      {notice && <p className="success page-alert" role="status">{notice}</p>}

      <section className="panel time-clock-panel">
        <div className="panel-heading">
          <div><p className="eyebrow">ZEITERFASSUNG</p><h2>Aktueller Dienst</h2></div>
          {openEntry && <span className="status schedule-status-published">Laufend</span>}
        </div>
        {openEntry ? <>
          <div className="time-clock-details">
            <p><strong>{openEntry.object_name}</strong> · {openEntry.employee_name}</p>
            <p>Beginn: {formatInstant(openEntry.started_at, openEntry.time_zone)}</p>
            <p>Istzeit: {durationLabel(openEntry.actual_work_seconds)} · Pause: {durationLabel(openEntry.actual_break_seconds)}</p>
          </div>
          <div className="time-action-row">
            {openSegment?.kind === "work"
              ? <button className="secondary-button" disabled={busy}
                onClick={() => void perform(() => pauseTimeEntry(openEntry.id), "Pause gestartet.")}>Pause starten</button>
              : <button className="secondary-button" disabled={busy}
                onClick={() => void perform(() => resumeTimeEntry(openEntry.id), "Arbeit fortgesetzt.")}>Pause beenden</button>}
            <button className="danger-button" disabled={busy}
              onClick={() => void perform(() => stopTimeEntry(openEntry.id), "Arbeitszeit eingereicht.")}>Dienst beenden</button>
          </div>
        </> : <div className="time-clock-details">
          <p>Es läuft keine Arbeitszeitbuchung.</p>
          <button disabled={busy} onClick={() => void perform(() => startTimeEntry({}), "Arbeitszeit gestartet.")}>
            Arbeitszeit starten
          </button>
        </div>}
        <p className="muted">Start und Ende werden serverseitig in UTC erfasst. Der aktuelle veröffentlichte Dienst wird automatisch zugeordnet.</p>
      </section>

      {canManage && employees.length > 0 && objects.length > 0 && <section className="panel form-panel time-manual-panel">
        <div className="panel-heading">
          <div><p className="eyebrow">NACHTRAG</p><h2>Manuelle Arbeitszeit</h2></div>
        </div>
        <form className="time-filter-row" onSubmit={(event) => void submitManualEntry(event)}>
          <label>Mitarbeiter
            <select name="employee_id" required defaultValue=""><option value="" disabled>Auswählen</option>
              {employees.map((employee) => <option key={employee.id} value={employee.id}>
                {employee.full_name} ({employee.employee_number})
              </option>)}
            </select>
          </label>
          <label>Objekt
            <select name="object_id" required defaultValue=""><option value="" disabled>Auswählen</option>
              {objects.map((obj) => <option key={obj.id} value={obj.id}>{obj.name} ({obj.code})</option>)}
            </select>
          </label>
          <label>Beginn (UTC)<input name="started_at" type="datetime-local" step="1" required /></label>
          <label>Ende (UTC)<input name="ended_at" type="datetime-local" step="1" required /></label>
          {manualPauses.map((_, index) => <div className="time-pause-input" key={index}>
            <label>Pause {index + 1} – Beginn (UTC)
              <input name={`pause_start_${index}`} type="datetime-local" step="1" required />
            </label>
            <label>Pause {index + 1} – Ende (UTC)
              <input name={`pause_end_${index}`} type="datetime-local" step="1" required />
            </label>
            <button type="button" className="text-button danger-text"
              onClick={() => setManualPauses(manualPauses.filter((_, itemIndex) => itemIndex !== index))}>
              Pause entfernen
            </button>
          </div>)}
          <button type="button" className="secondary-button"
            onClick={() => setManualPauses([...manualPauses, { started_at: "", ended_at: "" }])}>
            Pausenabschnitt hinzufügen
          </button>
          <button type="submit" disabled={busy}>Manuelle Buchung einreichen</button>
        </form>
        <p className="muted">Manuelle Eingaben werden eingereicht und benötigen eine Freigabe. Zeiten werden in UTC angegeben.</p>
      </section>}

      {canReadAll && corrections.length > 0 && <section className="panel">
        <div className="panel-heading">
          <div><p className="eyebrow">PRÜFUNG</p><h2>Offene Korrekturanträge</h2></div>
          <span className="result-count">{corrections.length} Anträge</span>
        </div>
        <div className="time-correction-list">
          {corrections.map((correction) => {
            const entry = entries.find((item) => item.id === correction.entry_id);
            return <article className="time-correction-card" key={correction.id}>
              <p><strong>{entry?.employee_name ?? "Mitarbeiter"}</strong> · {entry?.object_name ?? "Objekt"}</p>
              <p>{correction.reason}</p>
              <small>{correction.segments.length} vorgeschlagene Arbeits-/Pausenabschnitte</small>
              <div className="time-action-row">
                {canApprove && <button className="text-button" disabled={busy}
                  onClick={() => void perform(() => approveTimeCorrection(correction.id), "Korrektur freigegeben.")}>
                  Korrektur freigeben</button>}
                {canReject && <button className="text-button danger-text" disabled={busy}
                  onClick={() => void rejectCorrection(correction.id)}>Ablehnen</button>}
              </div>
            </article>;
          })}
        </div>
      </section>}

      <section className="panel">
        <div className="panel-heading">
          <div><p className="eyebrow">{canReadAll ? "VERWALTUNG" : "MEINE ZEITEN"}</p><h2>Arbeitszeiten</h2></div>
          <span className="result-count">{report?.entry_count ?? entries.length} Einträge</span>
        </div>
        <div className="time-filter-row">
          <label>Von<input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} /></label>
          <label>Bis<input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} /></label>
          {employees.length > 0 && <label>Mitarbeiter
            <select value={employeeFilter} onChange={(event) => setEmployeeFilter(event.target.value)}>
              <option value="">Alle Mitarbeiter</option>
              {employees.map((employee) => <option key={employee.id} value={employee.id}>
                {employee.full_name} ({employee.employee_number})
              </option>)}
            </select>
          </label>}
          {objects.length > 0 && <label>Objekt
            <select value={objectFilter} onChange={(event) => setObjectFilter(event.target.value)}>
              <option value="">Alle Objekte</option>
              {objects.map((obj) => <option key={obj.id} value={obj.id}>{obj.name}</option>)}
            </select>
          </label>}
          {customers.length > 0 && <label>Kunde
            <select value={customerFilter} onChange={(event) => setCustomerFilter(event.target.value)}>
              <option value="">Alle Kunden</option>
              {customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.company_name}</option>)}
            </select>
          </label>}
          <label>Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">Alle</option>
              {Object.entries(statusNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
            </select>
          </label>
          <label>Auswertung gruppieren
            <select value={groupBy ?? ""} onChange={(event) =>
              setGroupBy((event.target.value || undefined) as TimeEntryFilters["groupBy"])}>
              <option value="">Keine Gruppierung</option>
              <option value="employee">Mitarbeiter</option>
              <option value="object">Objekt</option>
              <option value="customer">Kunde</option>
              <option value="day">Tag</option>
              <option value="week">Kalenderwoche</option>
              <option value="month">Monat</option>
            </select>
          </label>
          {canExport && <button className="secondary-button" disabled={busy} onClick={() => void exportCsv()}>
            CSV exportieren
          </button>}
        </div>

        {report && <div className="time-summary-grid">
          <article><span>Ist-Arbeitszeit</span><strong>{durationLabel(report.actual_work_seconds)}</strong></article>
          <article><span>Pausen</span><strong>{durationLabel(report.actual_break_seconds)}</strong></article>
          <article><span>Soll-Arbeitszeit</span><strong>{durationLabel(report.planned_work_seconds)}</strong></article>
          <article><span>Soll-/Ist-Abweichung</span><strong>{durationLabel(report.difference_seconds)}</strong></article>
          <article><span>Mehrzeit gegenüber Dienstplan</span><strong>{durationLabel(report.overtime_seconds)}</strong></article>
          <article><span>Offene Freigaben</span><strong>{report.pending_count}</strong></article>
        </div>}
        {report && report.groups.length > 0 && <div className="table-scroll">
          <table>
            <thead><tr><th>Gruppe</th><th>Buchungen</th><th>Ist-Arbeitszeit</th>
              <th>Pausen</th><th>Sollzeit</th><th>Mehrzeit ggü. Plan</th></tr></thead>
            <tbody>{report.groups.map((group) => <tr key={group.key}>
              <td>{group.label}</td>
              <td>{group.entry_count}</td>
              <td>{durationLabel(group.actual_work_seconds)}</td>
              <td>{durationLabel(group.actual_break_seconds)}</td>
              <td>{durationLabel(group.planned_work_seconds)}</td>
              <td>{durationLabel(group.overtime_seconds)}</td>
            </tr>)}</tbody>
          </table>
        </div>}

        <div className="table-scroll">
          <table>
            <thead><tr>
              <th>Beginn / Ende</th><th>Mitarbeiter</th><th>Objekt / Kunde</th>
              <th>Soll / Ist</th><th>Pause / Abweichung</th><th>Status</th><th>Aktionen</th>
            </tr></thead>
            <tbody>
              {entries.map((entry) => <tr key={entry.id}>
                <td>{formatInstant(entry.started_at, entry.time_zone)}
                  <small>bis {formatInstant(entry.ended_at, entry.time_zone)}</small>
                </td>
                <td>{entry.employee_name}<small>{entry.employee_number}</small></td>
                <td>{entry.object_name}<small>{entry.customer_name}</small></td>
                <td>{durationLabel(entry.planned_work_seconds)}
                  <small>Ist {durationLabel(entry.actual_work_seconds)}</small>
                </td>
                <td>{durationLabel(entry.actual_break_seconds)}
                  <small>Abweichung {durationLabel(entry.difference_seconds)}</small>
                </td>
                <td><span className={`status time-status-${entry.status}`}>{statusNames[entry.status]}</span></td>
                <td><div className="time-action-row">
                  {canApprove && entry.status === "submitted" && <button className="text-button" disabled={busy}
                    onClick={() => void perform(() => approveTimeEntry(entry.id), "Arbeitszeit freigegeben.")}>
                    Freigeben</button>}
                  {canReject && entry.status === "submitted" && <button className="text-button danger-text" disabled={busy}
                    onClick={() => void rejectEntry(entry.id)}>Ablehnen</button>}
                  {(canCorrectOwn || user.permissions.includes("time_tracking.correct_all"))
                    && ["approved", "rejected"].includes(entry.status)
                    && <button className="text-button" disabled={busy}
                      onClick={() => beginCorrection(entry)}>Korrektur beantragen</button>}
                </div></td>
              </tr>)}
              {entries.length === 0 && <tr><td className="empty" colSpan={7}>Keine Arbeitszeitbuchungen im Zeitraum.</td></tr>}
            </tbody>
          </table>
        </div>

        {correctionDraft && <form className="time-correction-form" onSubmit={(event) => void submitCorrection(event)}>
          <div className="panel-heading">
            <div><p className="eyebrow">KORREKTUR</p><h3>Änderung beantragen (Zeitangaben in UTC)</h3></div>
            <button type="button" className="secondary-button" onClick={() => setCorrectionDraft(null)}>Schließen</button>
          </div>
          <label>Begründung<textarea required maxLength={2000} value={correctionDraft.reason}
            onChange={(event) => setCorrectionDraft({ ...correctionDraft, reason: event.target.value })} /></label>
          {correctionDraft.segments.map((segment, index) => <div className="form-row" key={`${index}-${segment.kind}`}>
            <strong>{segment.kind === "work" ? "Arbeitszeit" : "Pause"} {index + 1}</strong>
            <label>Beginn<input type="datetime-local" step="1" required value={segment.started_at}
              onChange={(event) => setCorrectionDraft({
                ...correctionDraft,
                segments: correctionDraft.segments.map((item, itemIndex) =>
                  itemIndex === index ? { ...item, started_at: event.target.value } : item),
              })} /></label>
            <label>Ende<input type="datetime-local" step="1" required value={segment.ended_at}
              onChange={(event) => setCorrectionDraft({
                ...correctionDraft,
                segments: correctionDraft.segments.map((item, itemIndex) =>
                  itemIndex === index ? { ...item, ended_at: event.target.value } : item),
              })} /></label>
          </div>)}
          <button type="submit" disabled={busy}>Korrektur zur Freigabe einreichen</button>
        </form>}
      </section>

      {canReadAll && <section className="panel">
        <div className="panel-heading">
          <div><p className="eyebrow">DIENSTPLANABGLEICH</p><h2>Fehlende Buchungen</h2></div>
          <span className="result-count">{missingShifts.length} Dienste ohne Zeitbuchung</span>
        </div>
        <div className="table-scroll">
          <table><thead><tr><th>Geplanter Dienst</th><th>Mitarbeiter</th><th>Objekt</th></tr></thead>
            <tbody>
              {missingShifts.map((shift) => <tr key={shift.shift_id}>
                <td>{formatInstant(shift.starts_at, shift.time_zone)}<small>bis {formatInstant(shift.ends_at, shift.time_zone)}</small></td>
                <td>{shift.employee_name}<small>{shift.employee_number}</small></td>
                <td>{shift.object_name}<small>{shift.object_code}</small></td>
              </tr>)}
              {missingShifts.length === 0 && <tr><td colSpan={3} className="empty">Keine fehlenden Buchungen für den Zeitraum.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>}

      {canReadAll && corrections.some((correction) => correction.status !== "pending") && <section className="panel">
        <h2>Korrekturverlauf</h2>
        <ul className="history-list">{corrections.filter((correction) => correction.status !== "pending")
          .map((correction) => <li key={correction.id}>
            <strong>{correctionStatusNames[correction.status]}</strong>
            <small>{correction.reason}{correction.rejection_reason ? ` – ${correction.rejection_reason}` : ""}</small>
          </li>)}
        </ul>
      </section>}
    </section>
  );
}
