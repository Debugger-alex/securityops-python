import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";

type NDEFRecordData = {
  recordType: string;
  data: DataView | null;
  encoding?: string | null;
  lang?: string | null;
};

type NDEFReaderLike = {
  onreading: ((event: { message: { records: NDEFRecordData[] } }) => void) | null;
  onreadingerror: (() => void) | null;
  scan: (options: { signal: AbortSignal }) => Promise<void>;
  write: (
    message: { records: { recordType: "text"; data: string }[] },
    options: { signal: AbortSignal },
  ) => Promise<void>;
};

type NDEFReaderConstructor = new () => NDEFReaderLike;

function isSecureContextAvailable() {
  return typeof window !== "undefined" && window.isSecureContext;
}

export function supportsWebNfc() {
  return isSecureContextAvailable() && ndefReaderConstructor() !== undefined;
}

export function supportsCameraQr() {
  return isSecureContextAvailable() && Boolean(navigator.mediaDevices?.getUserMedia);
}

function ndefReaderConstructor(): NDEFReaderConstructor | undefined {
  const constructor = Reflect.get(window, "NDEFReader") as unknown;
  return typeof constructor === "function"
    ? (constructor as NDEFReaderConstructor)
    : undefined;
}

function decodeTextRecord(record: NDEFRecordData) {
  if (!record.data || record.data.byteLength < 1) return "";
  const bytes = new Uint8Array(
    record.data.buffer,
    record.data.byteOffset,
    record.data.byteLength,
  );
  const languageLength = bytes[0] & 0x3f;
  const contentOffset = 1 + languageLength;
  if (contentOffset > bytes.length) return "";
  const encoding = record.encoding === "utf-16" ? "utf-16" : "utf-8";
  return new TextDecoder(encoding).decode(bytes.subarray(contentOffset)).trim();
}

export function OWKSControlPointQr({ credential }: { credential: string }) {
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");
  const [nfcMessage, setNfcMessage] = useState("");
  const [isWritingNfc, setIsWritingNfc] = useState(false);
  const nfcWriteController = useRef<AbortController | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    let active = true;
    setImageUrl("");
    setError("");
    QRCode.toDataURL(credential, {
      errorCorrectionLevel: "M",
      margin: 2,
      width: 256,
    }).then((url) => {
      if (active) setImageUrl(url);
    }).catch(() => {
      if (active) setError("Der QR-Code konnte nicht erstellt werden. Bitte Kennung sicher kopieren.");
    });
    return () => {
      active = false;
    };
  }, [credential]);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      nfcWriteController.current?.abort();
    };
  }, []);

  async function writeNfcTag() {
    if (!isSecureContextAvailable()) {
      setNfcMessage("NFC-Schreiben benötigt HTTPS oder eine lokale sichere Verbindung.");
      return;
    }
    const Reader = ndefReaderConstructor();
    if (!Reader) {
      setNfcMessage("Web-NFC ist in diesem Browser nicht verfügbar. Verwenden Sie den QR-Code.");
      return;
    }
    const controller = new AbortController();
    nfcWriteController.current = controller;
    setIsWritingNfc(true);
    try {
      await new Reader().write(
        { records: [{ recordType: "text", data: credential }] },
        { signal: controller.signal },
      );
      setNfcMessage("Kontrollpunktschlüssel auf den NFC-Tag geschrieben. Scannen Sie ihn zur Kontrolle testweise ein.");
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") {
        if (mounted.current) setNfcMessage("NFC-Schreiben wurde abgebrochen.");
        return;
      }
      const denied = reason instanceof DOMException
        && (reason.name === "NotAllowedError" || reason.name === "PermissionDeniedError");
      if (mounted.current) {
        setNfcMessage(denied
          ? "NFC-Schreibzugriff wurde verweigert. Erlauben Sie den Zugriff oder verwenden Sie den QR-Code."
          : "NFC-Tag konnte nicht beschrieben werden. Prüfen Sie Gerät und Tag oder verwenden Sie den QR-Code.");
      }
    } finally {
      if (nfcWriteController.current === controller) nfcWriteController.current = null;
      if (mounted.current) setIsWritingNfc(false);
    }
  }

  return (
    <div className="owks-qr-code">
      {imageUrl
        ? <img src={imageUrl} alt="QR-Code für den einmalig angezeigten Kontrollpunktschlüssel" />
        : <p role={error ? "alert" : undefined}>{error || "QR-Code wird erstellt …"}</p>}
      {imageUrl && <a href={imageUrl} download="owks-kontrollpunkt.png">QR-Code herunterladen</a>}
      {supportsWebNfc() && <button
        type="button"
        className="secondary-button"
        disabled={isWritingNfc}
        onClick={() => void writeNfcTag()}
      >{isWritingNfc ? "NFC-Tag beschreiben …" : "NFC-Tag beschreiben"}</button>}
      {isWritingNfc && <button
        type="button"
        className="text-button"
        onClick={() => nfcWriteController.current?.abort()}
      >NFC-Schreiben abbrechen</button>}
      {nfcMessage && <p role="status">{nfcMessage}</p>}
    </div>
  );
}

export function OWKSScanTools({
  onDetected,
  disabled,
}: {
  onDetected: (credential: string) => void;
  disabled: boolean;
}) {
  const [mode, setMode] = useState<"camera" | "nfc" | null>(null);
  const [message, setMessage] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const onDetectedRef = useRef(onDetected);

  useEffect(() => {
    onDetectedRef.current = onDetected;
  }, [onDetected]);

  useEffect(() => {
    if (mode !== "camera") return;
    if (!isSecureContextAvailable()) {
      setMessage("Kamerascans benötigen HTTPS oder eine lokale sichere Verbindung. Sie können den QR-Code extern scannen oder die Kennung manuell eingeben.");
      setMode(null);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !videoRef.current) {
      setMessage("Kamerascans werden von diesem Browser nicht unterstützt. Sie können den QR-Code extern scannen oder die Kennung manuell eingeben.");
      setMode(null);
      return;
    }

    let active = true;
    let controls: { stop: () => void } | undefined;
    const video = videoRef.current;
    void import("@zxing/browser").then(({ BrowserMultiFormatReader }) => {
      if (!active) return undefined;
      const reader = new BrowserMultiFormatReader();
      return reader.decodeFromVideoDevice(undefined, video, (result, _error, scannerControls) => {
        if (!active || !result) return;
        active = false;
        scannerControls.stop();
        setMode(null);
        setMessage("");
        onDetectedRef.current(result.getText());
      });
    }).then((scannerControls) => {
      if (!scannerControls) return;
      if (active) controls = scannerControls;
      else scannerControls.stop();
    }).catch((reason: unknown) => {
      if (!active) return;
      active = false;
      setMode(null);
      const denied = reason instanceof DOMException
        && (reason.name === "NotAllowedError" || reason.name === "PermissionDeniedError");
      setMessage(denied
        ? "Der Kamerazugriff wurde verweigert. Erlauben Sie den Kamerazugriff oder geben Sie die Kennung manuell ein."
        : "Der QR-Kamerascanner konnte nicht gestartet werden. Sie können die Kennung manuell eingeben.");
    });
    return () => {
      active = false;
      controls?.stop();
    };
  }, [mode]);

  useEffect(() => {
    if (mode !== "nfc") return;
    if (!isSecureContextAvailable()) {
      setMessage("NFC-Lesen benötigt HTTPS oder eine lokale sichere Verbindung. Verwenden Sie QR-Scan oder manuelle Eingabe.");
      setMode(null);
      return;
    }
    const Reader = ndefReaderConstructor();
    if (!Reader) {
      setMessage("Web-NFC ist in diesem Browser nicht verfügbar. Verwenden Sie QR-Scan oder manuelle Eingabe.");
      setMode(null);
      return;
    }

    let active = true;
    const abortController = new AbortController();
    const reader = new Reader();
    reader.onreading = (event) => {
      if (!active) return;
      const textRecord = event.message.records.find((record) => record.recordType === "text");
      if (!textRecord) {
        setMessage("Der NFC-Tag enthält keine unterstützte Textkennung. Prüfen Sie den Tag oder geben Sie die Kennung manuell ein.");
        return;
      }
      const credential = decodeTextRecord(textRecord);
      if (!credential) {
        setMessage("Der NFC-Tag enthält keine Kennung. Verwenden Sie QR-Scan oder manuelle Eingabe.");
        return;
      }
      active = false;
      setMode(null);
      setMessage("");
      onDetectedRef.current(credential);
    };
    reader.onreadingerror = () => {
      if (active) setMessage("Der NFC-Tag konnte nicht gelesen werden. Halten Sie das Gerät erneut an den Tag oder geben Sie die Kennung manuell ein.");
    };
    void reader.scan({ signal: abortController.signal }).catch((reason: unknown) => {
      if (!active) return;
      active = false;
      setMode(null);
      const denied = reason instanceof DOMException
        && (reason.name === "NotAllowedError" || reason.name === "PermissionDeniedError");
      setMessage(denied
        ? "Der NFC-Zugriff wurde verweigert. Prüfen Sie die Browserberechtigung oder verwenden Sie QR-Scan/manuelle Eingabe."
        : "NFC-Lesen konnte nicht gestartet werden. Verwenden Sie QR-Scan oder manuelle Eingabe.");
    });
    return () => {
      active = false;
      abortController.abort();
      reader.onreading = null;
      reader.onreadingerror = null;
    };
  }, [mode]);

  return (
    <div className="owks-scan-tools">
      <div className="time-action-row">
        <button
          type="button"
          className="secondary-button"
          disabled={disabled || mode !== null || !supportsCameraQr()}
          onClick={() => {
            setMessage("");
            setMode("camera");
          }}
        >QR-Code mit Kamera scannen</button>
        {supportsWebNfc() && <button
          type="button"
          className="secondary-button"
          disabled={disabled || mode !== null}
          onClick={() => {
            setMessage("");
            setMode("nfc");
          }}
        >NFC-Tag lesen</button>}
        {mode !== null && <button
          type="button"
          className="text-button"
          onClick={() => {
            setMode(null);
            setMessage("Scan abgebrochen. Sie können erneut scannen oder die Kennung manuell eingeben.");
          }}
        >Scan abbrechen</button>}
      </div>
      {mode === "camera" && <video
        ref={videoRef}
        className="owks-camera-preview"
        aria-label="Kamerabild für QR-Scan"
        autoPlay
        muted
        playsInline
      />}
      {mode === "nfc" && <p role="status">NFC-Lesen aktiv. Halten Sie das Gerät an den Kontrollpunkt.</p>}
      {message && <p className="muted" role="status">{message}</p>}
    </div>
  );
}
