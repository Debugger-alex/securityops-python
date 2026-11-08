import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DocumentContractManagement from "./DocumentContractManagement";
import type { AuthUser, ManagedDocument } from "./types";

const api = vi.hoisted(() => ({
  getDocuments: vi.fn(),
  getDocumentApprovals: vi.fn(),
  getCustomers: vi.fn(),
  getObjects: vi.fn(),
  getEmployees: vi.fn(),
}));

vi.mock("./api", () => api);

const testUser: AuthUser = {
  id: "user-1",
  username: "test",
  email: "test@example.com",
  full_name: "Testkonto",
  is_active: true,
  roles: ["administration"],
  permissions: ["documents.read", "documents.create", "documents.update", "documents.download"],
};

const testDocument: ManagedDocument = {
  id: "document-1",
  document_number: "D-2026-001",
  title: "Testdokument",
  description: null,
  category: "Versicherung",
  status: "active",
  customer_id: null,
  object_id: null,
  employee_id: null,
  expires_on: "2027-01-15",
  archived_at: null,
  created_at: "2026-11-08T10:00:00Z",
  updated_at: "2026-11-08T10:00:00Z",
  latest_version: {
    id: "version-1",
    document_id: "document-1",
    version: 1,
    file_name: "test.pdf",
    media_type: "application/pdf",
    size_bytes: 100,
    sha256: "a".repeat(64),
    uploaded_by_id: "user-1",
    created_at: "2026-11-08T10:00:00Z",
  },
};

describe("Dokumenten- und Vertragsverwaltung", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    api.getDocuments.mockResolvedValue({
      items: [testDocument],
      total: 1,
      limit: 100,
      offset: 0,
    });
    api.getDocumentApprovals.mockResolvedValue([]);
  });

  it("zeigt echte Dokumentmetadaten und den Upload für berechtigte Benutzer", async () => {
    render(<DocumentContractManagement user={testUser} />);

    expect(await screen.findByText("Testdokument")).toBeTruthy();
    expect(screen.getByText("D-2026-001")).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Versicherung" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Dokument sicher hochladen" })).toBeTruthy();
    expect(screen.getByLabelText("Dokumentnummer")).toBeTruthy();
    expect(api.getDocuments).toHaveBeenCalled();
  });

  it("zeigt den Fehlerzustand beim Laden statt eine Erfolgsliste vorzutäuschen", async () => {
    api.getDocuments.mockRejectedValue(new Error("Dokumentdienst nicht erreichbar"));
    render(<DocumentContractManagement user={testUser} />);

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain("Dokumentdienst nicht erreichbar");
    });
    expect(screen.queryByText("D-2026-001")).toBeNull();
  });
});
