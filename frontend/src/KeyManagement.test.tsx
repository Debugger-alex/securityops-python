// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import KeyManagement from "./KeyManagement";
import * as api from "./api";

vi.mock("./api", () => ({
  archiveKey: vi.fn(),
  createKey: vi.fn(),
  createKeyMovement: vi.fn(),
  getEligibleKeyEmployees: vi.fn(),
  getKeyMovements: vi.fn(),
  getKeyObjects: vi.fn(),
  getKeys: vi.fn(),
  updateKey: vi.fn(),
}));

const key = {
  id: "key-1",
  key_number: "K-001",
  description: "Haupteingang",
  object_id: "object-1",
  object_code: "OBJ-001",
  object_name: "Verwaltungsgebäude",
  status: "available" as const,
  current_employee_id: null,
  current_employee_name: null,
  archived_at: null,
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T10:00:00Z",
};

describe("Schlüsselverwaltung", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getKeys).mockResolvedValue({
      items: [key],
      total: 1,
      limit: 25,
      offset: 0,
    });
    vi.mocked(api.getKeyObjects).mockResolvedValue([]);
    vi.mocked(api.getKeyMovements).mockResolvedValue({
      items: [{
        id: "movement-1",
        key_id: key.id,
        key_number: key.key_number,
        object_id: key.object_id,
        employee_id: null,
        employee_name: null,
        actor_id: "actor-1",
        actor_name: "Test Administration",
        movement_type: "inventory",
        key_status_after: "available",
        acknowledged_at: null,
        acknowledgement_note: null,
        note: "Bestand geprüft",
        created_at: "2026-11-02T10:00:00Z",
      }],
      total: 1,
      limit: 100,
      offset: 0,
    });
  });

  it("zeigt Status, Inventurhistorie und objektbezogene Schlüsselangaben", async () => {
    render(<KeyManagement canManage={false} canMove={false} />);
    expect(await screen.findByText("K-001")).toBeTruthy();
    expect(screen.getByText("Haupteingang")).toBeTruthy();
    expect(screen.getByText("OBJ-001 · Verwaltungsgebäude")).toBeTruthy();
    expect(screen.getByText("Verfügbar", { selector: "span" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Historie" }));
    expect(await screen.findByText("Inventur bestätigt")).toBeTruthy();
    expect(screen.getByText(/Test Administration/)).toBeTruthy();
  });

  it("zeigt leere und Fehlerzustände", async () => {
    vi.mocked(api.getKeys).mockResolvedValueOnce({
      items: [],
      total: 0,
      limit: 25,
      offset: 0,
    });
    const empty = render(<KeyManagement canManage={false} canMove={false} />);
    expect(await screen.findByText("Keine Schlüssel für diese Auswahl vorhanden.")).toBeTruthy();
    empty.unmount();

    vi.mocked(api.getKeys).mockRejectedValueOnce(new Error("Register nicht erreichbar"));
    render(<KeyManagement canManage={false} canMove={false} />);
    expect((await screen.findByRole("alert")).textContent).toContain("Register nicht erreichbar");
  });
});
