// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";
import type { Customer } from "./types";

vi.mock("./api", () => ({
  archiveCustomer: vi.fn(),
  createCustomer: vi.fn(),
  createCustomerContact: vi.fn(),
  deleteCustomerContact: vi.fn(),
  getCustomer: vi.fn(),
  getCustomerHistory: vi.fn(),
  getCustomerObjects: vi.fn(),
  getCustomers: vi.fn(),
  getDashboard: vi.fn(),
  getSession: vi.fn(),
  getScheduleSettings: vi.fn(),
  getScheduleShifts: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  reactivateCustomer: vi.fn(),
  updateCustomer: vi.fn(),
  updateCustomerContact: vi.fn(),
}));

const customer: Customer = {
  id: "customer-1",
  customer_number: "K-CUSTOMER1",
  company_name: "Beispiel GmbH",
  status: "active",
  contract_status: "none",
  email: null,
  phone: null,
  legal_form: null,
  website: null,
  vat_number: null,
  tax_number: null,
  internal_notes: null,
  archived_at: null,
  business_address: null,
  billing_address: null,
  contacts: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("Kundenformulare", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getSession).mockResolvedValue({
      user: {
        id: "user-1",
        username: "test",
        email: "test@example.de",
        full_name: "Testkonto",
        is_active: true,
        roles: [],
        permissions: ["customers.read", "customers.create"],
      },
    });
    vi.mocked(api.getCustomers).mockResolvedValue({
      items: [],
      total: 0,
      limit: 25,
      offset: 0,
    });
    vi.mocked(api.createCustomer).mockResolvedValue(customer);
    vi.mocked(api.getCustomer).mockResolvedValue(customer);
    vi.mocked(api.getCustomerHistory).mockResolvedValue([]);
  });

  it("sendet Website und Vertragsstatus beim Anlegen", async () => {
    render(<App />);

    await screen.findByRole("heading", { name: "Kunde hinzufügen" });
    fireEvent.change(screen.getByPlaceholderText("Muster GmbH"), {
      target: { value: "Beispiel GmbH" },
    });
    fireEvent.change(screen.getByLabelText("Website"), {
      target: { value: "https://beispiel.de" },
    });
    const form = screen.getByPlaceholderText("Muster GmbH").closest("form")!;
    fireEvent.change(form.querySelector('select[name="contract_status"]')!, {
      target: { value: "draft" },
    });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(api.createCustomer).toHaveBeenCalledWith(
        expect.objectContaining({
          website: "https://beispiel.de",
          contract_status: "draft",
        }),
      );
    });
  });

  it("zeigt Validierungsfehler der API im Formular an", async () => {
    vi.mocked(api.createCustomer).mockRejectedValueOnce(
      new Error("Website muss eine HTTP- oder HTTPS-Adresse sein."),
    );
    render(<App />);

    await screen.findByRole("heading", { name: "Kunde hinzufügen" });
    fireEvent.change(screen.getByPlaceholderText("Muster GmbH"), {
      target: { value: "Beispiel GmbH" },
    });
    fireEvent.submit(screen.getByText("Kunden speichern").closest("form")!);

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Website muss eine HTTP- oder HTTPS-Adresse sein.",
    );
  });

  it("zeigt berechtigten Nutzern den Dienstplan mit Zeit und Schichtstatus", async () => {
    vi.mocked(api.getSession).mockResolvedValue({
      user: {
        id: "schedule-reader",
        username: "planleser",
        email: "planleser@example.de",
        full_name: "Planleser",
        is_active: true,
        roles: ["employee"],
        permissions: ["scheduling.read"],
      },
    });
    vi.mocked(api.getScheduleSettings).mockResolvedValue({
      time_zone: "Europe/Berlin",
      minimum_rest_hours: 11,
      updated_at: "2026-01-01T00:00:00Z",
    });
    vi.mocked(api.getScheduleShifts).mockResolvedValue([{
      id: "shift-1",
      employee_id: "employee-1",
      employee_number: "P-1001",
      employee_name: "Testperson",
      object_id: "object-1",
      object_code: "OBJ-001",
      object_name: "Testobjekt",
      starts_at: "2026-12-01T08:00:00Z",
      ends_at: "2026-12-01T16:00:00Z",
      time_zone: "Europe/Berlin",
      break_minutes: 30,
      required_qualification: "Erste Hilfe",
      status: "published",
      created_by_id: "manager-1",
      created_at: "2026-11-01T00:00:00Z",
      updated_at: "2026-11-01T00:00:00Z",
    }]);

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Dienstplanung" })).toBeTruthy();
    expect(await screen.findByText("Testperson")).toBeTruthy();
    expect(screen.getByText("Veröffentlicht")).toBeTruthy();
    expect(screen.getByRole("option", { name: "Monat" })).toBeTruthy();
    expect(api.getScheduleShifts).toHaveBeenCalled();
  });
});
