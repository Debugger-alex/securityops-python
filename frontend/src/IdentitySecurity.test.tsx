// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import IdentitySecurity from "./IdentitySecurity";
import * as api from "./api";
import type { AuthUser } from "./types";

const user: AuthUser = {
  id: "user-1",
  username: "test",
  email: "test@example.de",
  full_name: "Testkonto",
  is_active: true,
  roles: [],
  permissions: [],
};

vi.mock("./api", () => ({
  changePassword: vi.fn(),
  disableMFA: vi.fn(),
  enableMFA: vi.fn(),
  getMFAStatus: vi.fn(),
  getUserSessions: vi.fn(),
  getUserSessionsForAdmin: vi.fn(),
  getUsers: vi.fn(),
  revokeUserSession: vi.fn(),
  resetUserPassword: vi.fn(),
  startMFASetup: vi.fn(),
}));

describe("Kontosicherheit", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getUserSessions).mockResolvedValue([
      {
        id: "session-other",
        created_at: "2026-11-01T10:00:00Z",
        last_seen_at: "2026-11-02T10:00:00Z",
        expires_at: "2026-11-02T11:00:00Z",
        absolute_expires_at: "2026-11-03T10:00:00Z",
        ip_address: "192.0.2.1",
        user_agent: "Testbrowser",
        is_current: false,
      },
    ]);
    vi.mocked(api.getMFAStatus).mockResolvedValue({ enabled: false });
    vi.mocked(api.revokeUserSession).mockResolvedValue(undefined);
  });

  it("listet Sitzungen und widerruft ausgewählte Sitzungen serverseitig", async () => {
    const onSignedOut = vi.fn();
    render(<IdentitySecurity user={user} onSignedOut={onSignedOut} onPasswordChanged={vi.fn()} />);

    expect(await screen.findByText("Testbrowser")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Widerrufen" }));

    await waitFor(() => {
      expect(api.revokeUserSession).toHaveBeenCalledWith("session-other");
    });
    expect(onSignedOut).not.toHaveBeenCalled();
    expect(screen.queryByText("Testbrowser")).toBeNull();
  });

  it("zeigt Wiederherstellungscodes nur nach bestätigter MFA-Einrichtung", async () => {
    vi.mocked(api.startMFASetup).mockResolvedValue({
      secret: "BASE32TESTSECRET",
      otpauth_uri: "otpauth://totp/SecurityOps:test?secret=BASE32TESTSECRET",
    });
    vi.mocked(api.enableMFA).mockResolvedValue({
      recovery_codes: ["ABCD1234ABCD1234ABCD1234ABCD1234"],
    });
    render(<IdentitySecurity user={user} onSignedOut={vi.fn()} onPasswordChanged={vi.fn()} />);

    await screen.findByRole("heading", { name: "Mehr-Faktor-Authentifizierung" });
    const currentPassword = screen.getAllByLabelText("Aktuelles Passwort")[0];
    fireEvent.change(currentPassword, { target: { value: "aktuelles-passwort" } });
    fireEvent.submit(currentPassword.closest("form")!);

    expect(await screen.findByText("BASE32TESTSECRET")).toBeTruthy();
    const code = screen.getByLabelText("Sechsstelligen App-Code bestätigen");
    fireEvent.change(code, { target: { value: "123456" } });
    fireEvent.submit(code.closest("form")!);

    expect(await screen.findByText("ABCD1234ABCD1234ABCD1234ABCD1234")).toBeTruthy();
    expect(api.startMFASetup).toHaveBeenCalledWith("aktuelles-passwort");
    expect(api.enableMFA).toHaveBeenCalledWith("123456");
    expect(screen.getByText("MFA ist aktiviert. Wiederherstellungscodes jetzt sicher speichern.")).toBeTruthy();
  });

  it("sendet keine Passwortänderung, wenn die Bestätigung abweicht", async () => {
    render(<IdentitySecurity user={user} onSignedOut={vi.fn()} onPasswordChanged={vi.fn()} />);
    const section = (await screen.findByRole("heading", { name: "Passwort ändern" })).closest("section")!;
    const form = section.querySelector("form")!;
    fireEvent.change(form.querySelector('input[name="current_password"]')!, {
      target: { value: "aktuelles-passwort" },
    });
    fireEvent.change(form.querySelector('input[name="new_password"]')!, {
      target: { value: "ein-neues-passwort-2026" },
    });
    fireEvent.change(form.querySelector('input[name="confirm_password"]')!, {
      target: { value: "anderes-neues-passwort-2026" },
    });
    fireEvent.submit(form);

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Die neuen Passwörter stimmen nicht überein.",
    );
    expect(api.changePassword).not.toHaveBeenCalled();
  });

  it("sendet Admin-Resets ohne das Übergangspasswort zurückzugeben", async () => {
    const admin: AuthUser = {
      ...user,
      permissions: ["users.manage", "users.password_reset"],
    };
    vi.mocked(api.getUsers).mockResolvedValue([
      admin,
      { ...user, id: "target-user", username: "ziel" },
    ]);
    vi.mocked(api.resetUserPassword).mockResolvedValue(undefined);
    render(<IdentitySecurity user={admin} onSignedOut={vi.fn()} onPasswordChanged={vi.fn()} />);

    await screen.findByRole("option", { name: "Testkonto (ziel)" });
    const section = screen.getByRole("heading", {
      name: "Passwort administrativ zurücksetzen",
    }).closest("section")!;
    const form = section.querySelector("form")!;
    fireEvent.change(form.querySelector('select[name="user_id"]')!, {
      target: { value: "target-user" },
    });
    fireEvent.change(form.querySelector('input[name="temporary_password"]')!, {
      target: { value: "uebergangs-passwort-2026" },
    });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(api.resetUserPassword).toHaveBeenCalledWith(
        "target-user",
        "uebergangs-passwort-2026",
      );
    });
    expect(await screen.findByText(/separaten sicheren Kanal/)).toBeTruthy();
  });

  it("zeigt und widerruft fremde Sitzungen nur in der berechtigten Oberfläche", async () => {
    const admin: AuthUser = {
      ...user,
      permissions: ["users.read", "sessions.manage"],
    };
    vi.mocked(api.getUsers).mockResolvedValue([
      admin,
      { ...user, id: "target-user", username: "ziel" },
    ]);
    vi.mocked(api.getUserSessionsForAdmin).mockResolvedValue([
      {
        id: "foreign-session",
        created_at: "2026-11-01T10:00:00Z",
        last_seen_at: "2026-11-02T10:00:00Z",
        expires_at: "2026-11-02T11:00:00Z",
        absolute_expires_at: "2026-11-03T10:00:00Z",
        ip_address: "192.0.2.2",
        user_agent: "Fremder Browser",
        is_current: false,
      },
    ]);
    render(<IdentitySecurity user={admin} onSignedOut={vi.fn()} onPasswordChanged={vi.fn()} />);

    await screen.findByRole("option", { name: "Testkonto (ziel)" });
    const selector = screen.getByLabelText("Benutzerkonto");
    fireEvent.change(selector, { target: { value: "target-user" } });
    expect(await screen.findByText("Fremder Browser")).toBeTruthy();
    const managedSection = screen.getByRole("heading", {
      name: "Sitzungen anderer Konten",
    }).closest("section")!;
    fireEvent.click(managedSection.querySelector("button.danger-text")!);

    await waitFor(() => {
      expect(api.revokeUserSession).toHaveBeenCalledWith("foreign-session");
    });
    expect(screen.queryByText("Fremder Browser")).toBeNull();
  });
});
