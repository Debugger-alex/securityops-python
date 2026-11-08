// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import OWKSManagement from "./OWKSManagement";
import * as api from "./api";
import type { AuthUser } from "./types";

const qrScanner = vi.hoisted(() => ({
  callback: undefined as
    | ((result: { getText: () => string } | undefined, error: unknown, controls: { stop: () => void }) => void)
    | undefined,
  stop: vi.fn(),
}));

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

vi.mock("@zxing/browser", () => ({
  BrowserMultiFormatReader: class {
    decodeFromVideoDevice(
      _deviceId: string | undefined,
      _video: HTMLVideoElement,
      callback: typeof qrScanner.callback,
    ) {
      qrScanner.callback = callback ?? undefined;
      return Promise.resolve({ stop: qrScanner.stop });
    }
  },
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
    Reflect.deleteProperty(navigator, "mediaDevices");
    Object.defineProperty(window, "isSecureContext", { configurable: true, value: false });
    qrScanner.callback = undefined;
    qrScanner.stop.mockClear();
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
    vi.mocked(api.createOWKSChallenge).mockResolvedValue({
      id: "challenge-1",
      object_id: "object-1",
      expires_at: "2026-11-08T22:00:00Z",
    });
    vi.mocked(api.recordOWKSScan).mockResolvedValue({} as never);
  });

  it("weist ohne sichere Web-NFC-Unterstützung auf QR- und manuelle Eingabe hin", async () => {
    Reflect.deleteProperty(window, "NDEFReader");
    Object.defineProperty(window, "isSecureContext", { configurable: true, value: false });
    render(<OWKSManagement user={user} />);

    expect(await screen.findByText(/Web-NFC ist in diesem Browser\/Gerät oder ohne sicheren Kontext/))
      .toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Kontrollanforderung starten" }));
    const cameraButton = await screen.findByRole("button", { name: "QR-Code mit Kamera scannen" });
    expect(cameraButton.hasAttribute("disabled")).toBe(true);
  });

  it("zeigt den NFC-Leser nur bei sicherem Kontext und vorhandener Web-NFC-API", async () => {
    Object.defineProperty(window, "isSecureContext", { configurable: true, value: true });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn() },
    });
    Reflect.defineProperty(window, "NDEFReader", {
      configurable: true,
      value: class {
        scan = vi.fn();
        write = vi.fn();
        onreading = null;
        onreadingerror = null;
      },
    });
    render(<OWKSManagement user={user} />);

    await screen.findByRole("heading", { name: "Online-Wachbuch" });
    fireEvent.click(screen.getByRole("button", { name: "Kontrollanforderung starten" }));
    await screen.findByRole("button", { name: "NFC-Tag lesen" });
    expect(screen.getByRole("button", { name: "NFC-Tag lesen" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "QR-Code mit Kamera scannen" }).hasAttribute("disabled"))
      .toBe(false);
  });

  it("sendet einen Kamera-QR-Treffer mit der aktiven Server-Challenge zur Verifikation", async () => {
    Object.defineProperty(window, "isSecureContext", { configurable: true, value: true });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn() },
    });
    render(<OWKSManagement user={user} />);

    fireEvent.click(await screen.findByRole("button", { name: "Kontrollanforderung starten" }));
    fireEvent.click(await screen.findByRole("button", { name: "QR-Code mit Kamera scannen" }));
    await waitFor(() => expect(qrScanner.callback).toBeDefined());
    qrScanner.callback?.({ getText: () => "camera-credential" }, undefined, {
      stop: qrScanner.stop,
    });

    await waitFor(() => expect(api.recordOWKSScan).toHaveBeenCalledWith(
      expect.objectContaining({
        challenge_id: "challenge-1",
        credential: "camera-credential",
        client_event_id: expect.any(String),
      }),
    ));
    expect(await screen.findByText(/statischer QR-\/NFC-Tag beweist keine physische Anwesenheit/))
      .toBeTruthy();
    expect(qrScanner.stop).toHaveBeenCalled();
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
