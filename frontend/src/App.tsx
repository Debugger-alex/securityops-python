import { FormEvent, useCallback, useEffect, useState } from "react";
import { createCustomer, getCustomers, getDashboard, updateCustomerStatus } from "./api";
import type { Customer, CustomerStatus, Dashboard } from "./types";

const statusNames: Record<CustomerStatus, string> = {
  active: "Aktiv",
  inactive: "Inaktiv",
  lead: "Interessent",
};

export default function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [matchingCustomers, setMatchingCustomers] = useState(0);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [page, stats] = await Promise.all([getCustomers(search), getDashboard()]);
      setCustomers(page.items);
      setMatchingCustomers(page.total);
      setDashboard(stats);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Daten konnten nicht geladen werden.");
    }
  }, [search]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function submitCustomer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      await createCustomer({
        company_name: String(data.get("company_name")).trim(),
        email: String(data.get("email")).trim() || undefined,
        phone: String(data.get("phone")).trim() || undefined,
      });
      form.reset();
      await loadData();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kunde konnte nicht gespeichert werden.");
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(customer: Customer, status: CustomerStatus) {
    try {
      await updateCustomerStatus(customer.id, status);
      await loadData();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Status konnte nicht geändert werden.");
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SecurityOps Startseite">
          <span className="brand-mark">S</span>
          <span>SECURITY<span className="brand-light">OPS</span></span>
        </a>
        <span className="topbar-label">Verwaltungsplattform</span>
      </header>

      <section className="intro">
        <p className="eyebrow">KUNDENVERWALTUNG</p>
        <h1>Guten Tag.</h1>
        <p>Ihre Kundenstammdaten an einem zentralen Ort.</p>
      </section>

      <section className="stats" aria-label="Kundenübersicht">
        <article className="stat-card">
          <span>Kunden gesamt</span><strong>{dashboard?.customers_total ?? "–"}</strong>
        </article>
        <article className="stat-card">
          <span>Aktive Kunden</span><strong>{dashboard?.customers_active ?? "–"}</strong>
        </article>
        <article className="stat-card">
          <span>Interessenten</span><strong>{dashboard?.customers_leads ?? "–"}</strong>
        </article>
      </section>

      <section className="content-grid">
        <section className="panel">
          <div className="panel-heading">
            <div><p className="eyebrow">STAMMDATEN</p><h2>Kunden</h2></div>
            <span className="result-count">{matchingCustomers} Einträge</span>
          </div>
          <label className="search-field">
            <span className="sr-only">Kunden suchen</span>
            <span aria-hidden="true">⌕</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name, Kundennummer oder E-Mail suchen"
            />
          </label>
          {error && <p className="alert" role="alert">{error}</p>}
          <div className="table-scroll">
            <table>
              <thead><tr><th>Kunde</th><th>Kontakt</th><th>Status</th></tr></thead>
              <tbody>
                {customers.map((customer) => (
                  <tr key={customer.id}>
                    <td>
                      <strong>{customer.company_name}</strong>
                      <small>{customer.customer_number}</small>
                    </td>
                    <td>
                      {customer.email && <a href={`mailto:${customer.email}`}>{customer.email}</a>}
                      {customer.phone && <small>{customer.phone}</small>}
                      {!customer.email && !customer.phone && <span className="muted">Keine Kontaktdaten</span>}
                    </td>
                    <td>
                      <label className="sr-only" htmlFor={`status-${customer.id}`}>Status für {customer.company_name}</label>
                      <select
                        id={`status-${customer.id}`}
                        value={customer.status}
                        onChange={(event) => void changeStatus(customer, event.target.value as CustomerStatus)}
                      >
                        {Object.entries(statusNames).map(([value, name]) =>
                          <option key={value} value={value}>{name}</option>,
                        )}
                      </select>
                    </td>
                  </tr>
                ))}
                {customers.length === 0 && (
                  <tr><td className="empty" colSpan={3}>Noch keine Kunden vorhanden.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="panel form-panel">
          <div className="panel-heading">
            <div><p className="eyebrow">NEU ANLEGEN</p><h2>Kunde hinzufügen</h2></div>
          </div>
          <form onSubmit={submitCustomer}>
            <label>Unternehmen <span aria-hidden="true">*</span>
              <input name="company_name" required maxLength={200} placeholder="Muster GmbH" />
            </label>
            <label>E-Mail
              <input name="email" type="email" maxLength={254} placeholder="kontakt@unternehmen.de" />
            </label>
            <label>Telefon
              <input name="phone" type="tel" maxLength={40} placeholder="+49 30 123456" />
            </label>
            <button type="submit" disabled={busy}>{busy ? "Wird gespeichert …" : "Kunden speichern"}</button>
          </form>
        </aside>
      </section>
      <footer>SecurityOps <span>·</span> Erste Ausbaustufe</footer>
    </main>
  );
}
