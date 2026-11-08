// @vitest-environment node

import QRCode from "qrcode";
import { describe, expect, it } from "vitest";

describe("OWKS-QR-Codierung", () => {
  it("kodiert eine Kontrollpunktkennung in ein echtes QR-SVG", async () => {
    const svg = await QRCode.toString("owks-test-control-point-credential", {
      errorCorrectionLevel: "M",
      type: "svg",
    });

    expect(svg).toContain("<svg");
    expect(svg).toContain("<path");
  });
});
