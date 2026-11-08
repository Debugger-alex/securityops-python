import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createTimeSurchargeRule,
  exportTimeSurchargeCsv,
  getLockedTimePeriods,
  getTimeSurchargeReport,
  getTimeSurchargeRules,
  getTimeTrackingSettings,
  lockTimePeriod,
  updateTimeTrackingSettings,
} from "./api";
import type {
  AuthUser,
  FederalState,
  TimeSurchargeCalculation,
  TimeSurchargeCategory,
  TimeSurchargeRule,
  TimeTrackingPeriod,
} from "./types";

type Props = {
  user: AuthUser;
  fromDate: string;
  toDate: string;
};

const states: Array<{ code: FederalState; name: string }> = [
  { code: "BW", name: "Baden-Württemberg" },
  { code: "BY", name: "Bayern" },
  { code: "BE", name: "Berlin" },
  { code: "BB", name: "Brandenburg" },
  { code: "HB", name: "Bremen" },
  { code: "HH", name: "Hamburg" },
  { code: "HE", name: "Hessen" },
  { code: "MV", name: "Mecklenburg-Vorpommern" },
  { code: "NI", name: "Niedersachsen" },
  { code: "NW", name: "Nordrhein-Westfalen" },
  { code: "RP", name: "Rheinland-Pfalz" },
  { code: "SL", name: "Saarland" },
  { code: "SN", name: "Sachsen" },
  { code: "ST", name: "Sachsen-Anhalt" },
  { code: "SH", name: "Schleswig-Holstein" },
  { code: "TH", name: "Thüringen" },
];

const categories: Array<{ value: TimeSurchargeCategory; label: string }> = [
  { value: "night", label: "Nachtarbeit" },
  { value: "saturday", label: "Samstagsarbeit" },
  { value: "sunday", label: "Sonntagsarbeit" },
  { value: "public_holiday", label: "Gesetzlicher Feiertag" },
  { value: "business", label: "Individueller betrieblicher Zuschlag" },
];

const weekdays = [
  "Montag",
  "Dienstag",
  "Mittwoch",
  "Donnerstag",
  "Freitag",
  "Samstag",
  "Sonntag",
];

const categoryName = Object.fromEntries(categories.map(({ value, label }) => [value, label]));

function messageFrom(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function secondsLabel(value: number) {
  return `${new Intl.NumberFormat("de-DE", { maximumFractionDigits: 6 }).format(value)} Sek.`;
}

function stateName(value: FederalState | null) {
  return states.find((state) => state.code === value)?.name ?? "Nicht festgelegt";
}

export default function TimeSurchargeAdministration({ user, fromDate, toDate }: Props) {
  const canRead = user.permissions.includes("time_tracking.surcharges.read");
  const canManage = user.permissions.includes("time_tracking.surcharges.manage");
  const canLock = user.permissions.includes("time_tracking.periods.lock");
  const canReadPeriods = user.permissions.includes("time_tracking.periods.read");
  const canExport = user.permissions.includes("time_tracking.export");
  const [federalState, setFederalState] = useState<FederalState | "">("");
  const [rules, setRules] = useState<TimeSurchargeRule[]>([]);
  const [periods, setPeriods] = useState<TimeTrackingPeriod[]>([]);
  const [calculations, setCalculations] = useState<TimeSurchargeCalculation[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const tasks: Promise<void>[] = [];
      if (canRead) {
        tasks.push(
          getTimeTrackingSettings().then((settings) =>
            setFederalState(settings.federal_state ?? ""),
          ),
          getTimeSurchargeRules().then(setRules),
          getTimeSurchargeReport(fromDate, toDate).then(setCalculations),
        );
      }
      if (canReadPeriods || canLock) {
        tasks.push(getLockedTimePeriods().then(setPeriods));
      }
      await Promise.all(tasks);
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Zuschlagsdaten konnten nicht geladen werden."));
    }
  }, [canLock, canRead, canReadPeriods, fromDate, toDate]);

  useEffect(() => {
    void load();
  }, [load]);

  async function submitSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const saved = await updateTimeTrackingSettings(federalState || null);
      setFederalState(saved.federal_state ?? "");
      setNotice("Bundesland gespeichert. Neue Berechnungen verwenden diese Feiertagsregion.");
      await load();
    } catch (reason) {
      setError(messageFrom(reason, "Bundesland konnte nicht gespeichert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function submitRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const category = String(data.get("category")) as TimeSurchargeCategory;
    const calculationType = String(data.get("calculation_type")) as "percentage" | "fixed";
    const selectedWeekdays = Array.from(
      (form.elements.namedItem("weekdays") as HTMLSelectElement).selectedOptions,
      (option) => Number(option.value),
    );
    setBusy(true);
    setError("");
    try {
      await createTimeSurchargeRule({
        code: String(data.get("code")).trim(),
        name: String(data.get("name")).trim(),
        category,
        calculation_type: calculationType,
        value: String(data.get("value")),
        currency: calculationType === "fixed" ? String(data.get("currency")).toUpperCase() : null,
        basis_description: String(data.get("basis_description")).trim(),
        valid_from: String(data.get("valid_from")),
        valid_to: String(data.get("valid_to")) || null,
        priority: Number(data.get("priority")),
        combination_mode: String(data.get("combination_mode")) as "exclusive" | "combine",
        weekdays: category === "business" ? selectedWeekdays : [],
        starts_local: category === "night" || category === "business"
          ? String(data.get("starts_local"))
          : null,
        ends_local: category === "night" || category === "business"
          ? String(data.get("ends_local"))
          : null,
      });
      form.reset();
      setNotice("Zuschlagsregel angelegt. Bestehende Regeln und Berechnungsnachweise bleiben unverändert.");
      await load();
    } catch (reason) {
      setError(messageFrom(reason, "Zuschlagsregel konnte nicht angelegt werden."));
    } finally {
      setBusy(false);
    }
  }

  async function submitPeriodLock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const period = await lockTimePeriod(
        String(data.get("from_date")),
        String(data.get("to_date")),
      );
      setNotice(
        `Periode ${period.from_date} bis ${period.to_date} gesperrt. Die Berechnungsnachweise sind historisiert; die Sperre ist endgültig.`,
      );
      await load();
    } catch (reason) {
      setError(messageFrom(reason, "Abrechnungsperiode konnte nicht gesperrt werden."));
    } finally {
      setBusy(false);
    }
  }

  async function downloadCsv() {
    setBusy(true);
    setError("");
    try {
      const blob = await exportTimeSurchargeCsv(fromDate, toDate);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "zuschlagsnachweise.csv";
      link.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(messageFrom(reason, "Zuschlags-CSV konnte nicht erstellt werden."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel time-surcharge-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">REGELWERK & ABRECHNUNG</p>
          <h2>Zuschläge und Abrechnungszeiträume</h2>
        </div>
        <span className="result-count">{rules.length} Regeln</span>
      </div>
      {error && <p className="alert" role="alert">{error}</p>}
      {notice && <p className="success" role="status">{notice}</p>}

      {canManage && <form className="time-filter-row" onSubmit={(event) => void submitSettings(event)}>
        <label>Bundesland für gesetzliche Feiertage
          <select
            value={federalState}
            onChange={(event) => setFederalState(event.target.value as FederalState | "")}
          >
            <option value="">Nicht festgelegt</option>
            {states.map((state) =>
              <option key={state.code} value={state.code}>{state.name}</option>)}
          </select>
        </label>
        <button type="submit" className="secondary-button" disabled={busy}>Bundesland speichern</button>
      </form>}
      {!canManage && canRead && <p>Feiertagsregion: <strong>{stateName(federalState || null)}</strong></p>}

      {canManage && <form className="time-surcharge-rule-form" onSubmit={(event) => void submitRule(event)}>
        <h3>Neue Zuschlagsregel</h3>
        <div className="time-filter-row">
          <label>Regelcode<input name="code" required minLength={2} maxLength={80} pattern="[a-zA-Z0-9._-]+" /></label>
          <label>Bezeichnung<input name="name" required maxLength={160} /></label>
          <label>Zuschlagsart
            <select name="category" defaultValue="night">
              {categories.map((category) =>
                <option key={category.value} value={category.value}>{category.label}</option>)}
            </select>
          </label>
          <label>Berechnungsart
            <select name="calculation_type" defaultValue="percentage">
              <option value="percentage">Prozentual</option>
              <option value="fixed">Fester Betrag</option>
            </select>
          </label>
          <label>Konfigurierter Wert<input name="value" type="number" min="0.0001" step="0.0001" required /></label>
          <label>Währung (bei festem Betrag)<input name="currency" defaultValue="EUR" minLength={3} maxLength={3} /></label>
          <label>Gültig ab<input name="valid_from" type="date" defaultValue={fromDate} required /></label>
          <label>Gültig bis (optional)<input name="valid_to" type="date" /></label>
          <label>Priorität (höher gewinnt)<input name="priority" type="number" min="0" max="10000" defaultValue="100" required /></label>
          <label>Überlappung
            <select name="combination_mode" defaultValue="exclusive">
              <option value="exclusive">Exklusiv, höchste Priorität</option>
              <option value="combine">Kombination ausdrücklich erlauben</option>
            </select>
          </label>
          <label>Bezugs-/Einheitenbeschreibung
            <input name="basis_description" required maxLength={240}
              placeholder="z. B. Grundvergütung je Arbeitsstunde" />
          </label>
          <label>Beginn des lokalen Zeitfensters
            <input name="starts_local" type="time" defaultValue="22:00" />
          </label>
          <label>Ende des lokalen Zeitfensters
            <input name="ends_local" type="time" defaultValue="06:00" />
          </label>
          <label>Wochentage für betriebliche Zuschläge (0 = Montag)
            <select name="weekdays" multiple size={4}>
              {weekdays.map((day, index) => <option key={day} value={index}>{day}</option>)}
            </select>
          </label>
        </div>
        <button type="submit" disabled={busy}>Regel hinzufügen</button>
        <p className="muted">
          Regeln sind unveränderlich; Änderungen werden als neue Regel mit Gültigkeitszeitraum angelegt.
          Werte werden versioniert, aber ohne bestätigte Lohnbasis, Festzuschlagseinheit und Rundung nicht in Geldbeträge umgerechnet.
        </p>
      </form>}

      {canRead && <div className="table-scroll">
        <table>
          <thead><tr>
            <th>Regel</th><th>Art / Wert</th><th>Gültigkeit</th><th>Priorität / Kombination</th><th>Fenster</th>
          </tr></thead>
          <tbody>
            {rules.map((rule) => <tr key={rule.id}>
              <td>{rule.name}<small>{rule.code} · {categoryName[rule.category]}</small></td>
              <td>{rule.calculation_type === "percentage"
                ? `${rule.value} %`
                : `${rule.value} ${rule.currency}`}
                <small>{rule.basis_description}</small>
              </td>
              <td>{rule.valid_from}{rule.valid_to ? ` bis ${rule.valid_to}` : " und später"}</td>
              <td>{rule.priority} · {rule.combination_mode === "combine" ? "kombinierbar" : "exklusiv"}</td>
              <td>{rule.starts_local && rule.ends_local
                ? `${rule.starts_local}–${rule.ends_local}`
                : rule.weekdays.map((day) => weekdays[day]).join(", ") || "Ganztägig"}
              </td>
            </tr>)}
            {rules.length === 0 && <tr><td className="empty" colSpan={5}>Noch keine Zuschlagsregeln konfiguriert.</td></tr>}
          </tbody>
        </table>
      </div>}

      <div className="panel-heading">
        <div>
          <p className="eyebrow">NACHWEISE</p>
          <h3>Berechnungen für {fromDate} bis {toDate}</h3>
        </div>
        {canExport && canRead && <button className="secondary-button" disabled={busy} onClick={() => void downloadCsv()}>
          Zuschlags-CSV exportieren
        </button>}
      </div>
      {canRead && <div className="time-correction-list">
        {calculations.map((calculation) => <article className="time-correction-card" key={calculation.id}>
          <strong>Buchung {calculation.entry_id} · Version {calculation.version}</strong>
          <small>{calculation.time_zone} · Feiertagsregion {stateName(calculation.federal_state)} ·
            {` ${secondsLabel(Number(calculation.gross_work_seconds))} Gesamtarbeit`}
          </small>
          {calculation.allocation_snapshot.map((allocation, index) =>
            <p key={`${allocation.rule_id ?? "none"}-${index}`}>
              {allocation.rule_name}: {secondsLabel(Number(allocation.eligible_work_seconds))}
              {allocation.configured_value !== null
                ? ` · Regelwert ${allocation.configured_value}${allocation.currency ? ` ${allocation.currency}` : " %"}`
                : ""}
              <small>{allocation.calculation_note}</small>
            </p>)}
        </article>)}
        {calculations.length === 0 && <p className="empty">Keine aktuellen Berechnungsnachweise im Zeitraum.</p>}
      </div>}

      {canLock && <form className="time-filter-row" onSubmit={(event) => void submitPeriodLock(event)}>
        <h3>Abrechnungsperiode endgültig sperren</h3>
        <label>Von<input name="from_date" type="date" defaultValue={fromDate} required /></label>
        <label>Bis<input name="to_date" type="date" defaultValue={toDate} required /></label>
        <button type="submit" className="danger-button" disabled={busy}>Periode prüfen und sperren</button>
        <p className="muted">
          Nur vollständig abgelaufene Perioden ohne offene Buchungen oder fehlende veröffentlichte Schichten
          können gesperrt werden. Die Sperre ist endgültig.
        </p>
      </form>}
      {canReadPeriods && <div className="table-scroll">
        <table>
          <thead><tr><th>Gesperrter Zeitraum</th><th>Zeitzone</th><th>Feiertagsregion</th><th>Gesperrt am (UTC)</th></tr></thead>
          <tbody>
            {periods.map((period) => <tr key={period.id}>
              <td>{period.from_date} bis {period.to_date}</td>
              <td>{period.time_zone}</td>
              <td>{stateName(period.federal_state)}</td>
              <td>{new Date(period.locked_at).toISOString()}</td>
            </tr>)}
            {periods.length === 0 && <tr><td className="empty" colSpan={4}>Keine Abrechnungsperioden gesperrt.</td></tr>}
          </tbody>
        </table>
      </div>}
    </section>
  );
}
