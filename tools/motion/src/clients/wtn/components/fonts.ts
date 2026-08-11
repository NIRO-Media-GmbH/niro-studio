// ============================================================
// WTN — Local "Robout" brand font (OTFs in /public/fonts/wtn).
// Registered via @remotion/fonts so Remotion waits for load →
// measureText() auto-fit stays accurate. Official NIRO/WTN typeface.
// ============================================================

import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

const ROBOUT_FACES = [
  { weight: "400", file: "Robout-Regular.otf" },
  { weight: "500", file: "Robout-Medium.otf" },
  { weight: "600", file: "Robout-Semibold.otf" },
  { weight: "700", file: "Robout-Bold.otf" },
  { weight: "800", file: "Robout-Extrabold.otf" },
  { weight: "900", file: "Robout-Black.otf" },
] as const;

for (const face of ROBOUT_FACES) {
  loadFont({
    family: "Robout",
    url: staticFile(`fonts/wtn/${face.file}`),
    weight: face.weight,
    format: "opentype",
  }).catch(() => undefined);
}

// Font stack (Robout with safe fallbacks until it loads)
export const FONT = '"Robout", "Arial Narrow", Arial, sans-serif';
