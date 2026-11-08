// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OWKSControlPointQr, OWKSScanTools } from "./OWKSScanTools";

const scannerMocks = vi.hoisted(() => ({
  callback: undefined as
    | ((result: { getText: () => string } | undefined, error: unknown, controls: { stop: () => void }) => void)
    | undefined,
  stop: vi.fn(),
  reject: undefined as unknown,
}));

vi.mock("@zxing/browser", () => ({
  BrowserMultiFormatReader: class {
    decodeFromVideoDevice(
      _deviceId: string | undefined,
      _video: HTMLVideoElement,
      callback: typeof scannerMocks.callback,
    ) {
      scannerMocks.callback = callback ?? undefined;
      if (scannerMocks.reject) return Promise.reject(scannerMocks.reject);
      return Promise.resolve({ stop: scannerMocks.stop });
    }
  },
}));

vi.mock("qrcode", () => ({
  default: { toDataURL: vi.fn().mockResolvedValue("data:image/png;base64,qr") },
}));

function enableSecureContext() {
  Object.defineProperty(window, "isSecureContext", { configurable: true, value: true });
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia: vi.fn() },
  });
}

describe("OWKS-Scan-Werkzeuge", () => {
  afterEach(() => {
    cleanup();
    Reflect.deleteProperty(window, "NDEFReader");
    Reflect.deleteProperty(navigator, "mediaDevices");
    Object.defineProperty(window, "isSecureContext", { configurable: true, value: false });
    scannerMocks.callback = undefined;
    scannerMocks.reject = undefined;
    scannerMocks.stop.mockClear();
  });

  it("erstellt einen herunterladbaren QR-Code für die Kennung", async () => {
    render(<OWKSControlPointQr credential="geheimer-kontrollpunktschluessel" />);

    expect(await screen.findByRole("img", { name: /QR-Code für den einmalig angezeigten/ }))
      .toBeTruthy();
    expect(screen.getByRole("link", { name: "QR-Code herunterladen" }).getAttribute("href"))
      .toBe("data:image/png;base64,qr");
  });

  it("liest einen QR-Code über die Kamera und stoppt den Reader nach einem Treffer", async () => {
    enableSecureContext();
    const detected = vi.fn();
    render(<OWKSScanTools onDetected={detected} disabled={false} />);
    fireEvent.click(screen.getByRole("button", { name: "QR-Code mit Kamera scannen" }));

    await screen.findByLabelText("Kamerabild für QR-Scan");
    await waitFor(() => expect(scannerMocks.callback).toBeDefined());
    scannerMocks.callback?.({ getText: () => "qr-credential" }, undefined, {
      stop: scannerMocks.stop,
    });

    expect(detected).toHaveBeenCalledWith("qr-credential");
    expect(scannerMocks.stop).toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByLabelText("Kamerabild für QR-Scan")).toBeNull());
  });

  it("zeigt bei verweigerter Kameraberechtigung einen manuellen Fallback", async () => {
    enableSecureContext();
    scannerMocks.reject = new DOMException("denied", "NotAllowedError");
    render(<OWKSScanTools onDetected={vi.fn()} disabled={false} />);
    fireEvent.click(screen.getByRole("button", { name: "QR-Code mit Kamera scannen" }));

    expect(await screen.findByText(/Kamerazugriff wurde verweigert/)).toBeTruthy();
  });

  it("liest NFC-Text nur nach explizitem Start und beendet den Reader nach einem Treffer", async () => {
    enableSecureContext();
    type MockReaderLike = {
      onreading: ((event: { message: { records: { recordType: string; data: DataView }[] } }) => void) | null;
      onreadingerror: (() => void) | null;
      scan: ReturnType<typeof vi.fn>;
    };
    let activeReader: MockReaderLike | undefined;
    class MockNDEFReader {
      onreading: MockReaderLike["onreading"] = null;
      onreadingerror: (() => void) | null = null;
      scan = vi.fn(async (_options: { signal: AbortSignal }) => {});

      constructor() {
        activeReader = this;
      }
    }
    Reflect.defineProperty(window, "NDEFReader", {
      configurable: true,
      value: MockNDEFReader,
    });
    const detected = vi.fn();
    render(<OWKSScanTools onDetected={detected} disabled={false} />);
    fireEvent.click(screen.getByRole("button", { name: "NFC-Tag lesen" }));

    await screen.findByText(/NFC-Lesen aktiv/);
    await waitFor(() => expect(activeReader?.scan).toHaveBeenCalled());
    const bytes = new Uint8Array([
      0x02,
      0x65,
      0x6e,
      ...new TextEncoder().encode("nfc-credential"),
    ]);
    activeReader?.onreading?.({
      message: { records: [{ recordType: "text", data: new DataView(bytes.buffer) }] },
    });

    expect(detected).toHaveBeenCalledWith("nfc-credential");
    await waitFor(() => expect(activeReader?.scan.mock.calls[0][0].signal.aborted).toBe(true));
  });

  it("beschreibt einen NFC-Tag erst nach Klick und meldet Berechtigungsfehler", async () => {
    enableSecureContext();
    const write = vi.fn(async () => {});
    class MockNDEFReader {
      scan = vi.fn();
      write = write.mockRejectedValue(new DOMException("denied", "NotAllowedError"));
      onreading = null;
      onreadingerror = null;
    }
    Reflect.defineProperty(window, "NDEFReader", {
      configurable: true,
      value: MockNDEFReader,
    });
    render(<OWKSControlPointQr credential="nfc-key" />);
    fireEvent.click(await screen.findByRole("button", { name: "NFC-Tag beschreiben" }));

    expect(await screen.findByText(/NFC-Schreibzugriff wurde verweigert/)).toBeTruthy();
    expect(write).toHaveBeenCalledWith(
      { records: [{ recordType: "text", data: "nfc-key" }] },
      { signal: expect.any(AbortSignal) },
    );
  });

  it("bricht einen laufenden NFC-Schreibvorgang auf ausdrückliche Aktion ab", async () => {
    enableSecureContext();
    let writeSignal: AbortSignal | undefined;
    class MockNDEFReader {
      scan = vi.fn();
      write = vi.fn(async (_message: unknown, options: { signal: AbortSignal }) => {
        writeSignal = options.signal;
        await new Promise<void>((_resolve, reject) => {
          options.signal.addEventListener("abort", () => {
            reject(new DOMException("aborted", "AbortError"));
          });
        });
      });
      onreading = null;
      onreadingerror = null;
    }
    Reflect.defineProperty(window, "NDEFReader", {
      configurable: true,
      value: MockNDEFReader,
    });
    render(<OWKSControlPointQr credential="nfc-key" />);
    fireEvent.click(await screen.findByRole("button", { name: "NFC-Tag beschreiben" }));
    fireEvent.click(await screen.findByRole("button", { name: "NFC-Schreiben abbrechen" }));

    expect(writeSignal?.aborted).toBe(true);
    expect(await screen.findByText("NFC-Schreiben wurde abgebrochen.")).toBeTruthy();
  });
});
