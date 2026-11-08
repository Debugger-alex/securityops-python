// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import OWKSManagement from "./OWKSManagement";
import * as api from "./api";
import type { AuthUser } from "./types";

vi.mock("./api", () => ({
  createOWKSChallenge: vi.fn(),
  createOWKSControlPoint: vi.fn(),
  createOWKSEvent: vi.fn(),
  createOWKSRoute: vi.fn(),
  getOWKSControlPoints: vi.fn(),
  getOWKSAttachments: vi.fn(),
  getOWKSEvents: vi.fn(),
  getOWKSObjects: vi.fn(),
  getOWKSRoutes: vi.fn(),
  monitorOWKSRoute: vi.fn(),
  owksAttachmentUrl: vi.fn(),
  recordOWKSScan: vi.fn(),
  syncOWKSEvents: vi.fn(),
  updateOWKSEventStatus: vi.fn(),
  uploadOWKSAttachment: vi.fn(),
}));

const user: AuthUser = {
  id: "employee-1",
  username: "wache",
  email: "wache@example.de",
  full_name: "Testwache",
  is_active: true,
  roles: ["employee"],
  permissions: ["owks.read", "owks.write"],
};

describe("OWKS-NFC-Fallback", () => {
  afterEach(() => {
    cleanup();
    Reflect.deleteProperty(window, "NDEFReader");
  });

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    vi.mocked(api.getOWKSObjects).mockResolvedValue([
      { id: "object-1", code: "OBJ-1", name: "Testobjekt" },
    ]);
    vi.mocked(api.getOWKSEvents).mockResolvedValue([]);
    vi.mocked(api.getOWKSControlPoints).mockResolvedValue([]);
    vi.mocked(api.getOWKSRoutes).mockResolvedValue([]);
  });

  it("weist ohne Web-NFC auf QR- und manuelle Eingabe hin", async () => {
    Reflect.deleteProperty(window, "NDEFReader");
    render(<OWKSManagement user={user} />);

    expect(await screen.findByText(/Dieser Browser unterstützt kein Web-NFC/)).toBeTruthy();
    expect(screen.getByText(/QR-Code mit einer Scanner-App auslesen und die Kennung einfügen/))
      .toBeTruthy();
  });

  it("verspricht trotz Web-NFC-Unterstützung kein automatisches NFC-Lesen", async () => {
    Reflect.defineProperty(window, "NDEFReader", { configurable: true, value: undefined });
    render(<OWKSManagement user={user} />);

    expect(await screen.findByText(/Web-NFC wird in dieser Version nicht automatisch ausgelesen/))
      .toBeTruthy();
    expect(screen.getByText(/QR-Code mit einer Scanner-App auslesen und die Kennung einfügen/))
      .toBeTruthy();
  });

  it("speichert Ereignisse offline in der Warteschlange", async () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    render(<OWKSManagement user={user} />);

    await screen.findByRole("heading", { name: "Online-Wachbuch" });
    fireEvent.change(screen.getByLabelText("Titel"), { target: { value: "Offline-Eintrag" } });
    fireEvent.submit(screen.getByLabelText("Titel").closest("form")!);

    expect(await screen.findByText("Ereignis lokal gespeichert und wartet auf Synchronisierung."))
      .toBeTruthy();
    const queued = JSON.parse(localStorage.getItem("securityops-owks-offline-queue") ?? "[]");
    expect(queued).toHaveLength(1);
    expect(queued[0].title).toBe("Offline-Eintrag");
  });

  it("behält Synchronisierungskonflikte sichtbar und lokal", async () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    localStorage.setItem("securityops-owks-offline-queue", JSON.stringify([{
      object_id: "object-1",
      event_type: "control",
      title: "Offline-Kontrolle",
      description: "",
      severity: "warning",
      occurred_at: "2026-11-08T19:00:00Z",
      client_event_id: "offline-event-1",
    }]));
    vi.mocked(api.syncOWKSEvents).mockResolvedValue([
      {
        client_event_id: "offline-event-1",
        status: "conflict",
        event: null,
        detail: "Offline-Kontrolle muss geprüft werden.",
      },
    ]);
    render(<OWKSManagement user={user} />);

    await screen.findByRole("heading", { name: "Online-Wachbuch" });
    const syncButton = screen.getByRole("button", { name: "Warteschlange synchronisieren" });
    expect((syncButton as HTMLButtonElement).disabled).toBe(true);
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    window.dispatchEvent(new Event("online"));
    await waitFor(() => expect((syncButton as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Warteschlange synchronisieren" }));

    await waitFor(() => expect(api.syncOWKSEvents).toHaveBeenCalled());
    expect(await screen.findByText("Konflikt – manuelle Prüfung erforderlich")).toBeTruthy();
    expect(api.syncOWKSEvents).toHaveBeenCalledWith(
      expect.arrayContaining([expect.objectContaining({ title: "Offline-Kontrolle" })]),
    );
    await waitFor(() => {
      expect(
        JSON.parse(localStorage.getItem("securityops-owks-offline-queue") ?? "[]"),
      ).toHaveLength(1);
    });
  });
});
