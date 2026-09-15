// ============================================================
// Craiss Generation Logistik — gemeinsame Bausteine der 4-Ads-Serie
// Hook (Varianten: oben / Lower-Third) + CTA + Footage-Vergleich.
// Verwendet von erster-tag (01), arbeitsalltag (02), …
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  getRemotionEnvironment,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";

// --- Laski Slab (Original-Webfonts von craiss.com) ---
const CRAISS_FACES = [
  { family: "LaskiSlabLight", file: "LaskiSlab-LightWeb.woff2" },
  { family: "LaskiSlabRegular", file: "LaskiSlab-RegularWeb.woff2" },
  { family: "LaskiSlabBold", file: "LaskiSlab-BoldWeb.woff2" },
  { family: "LaskiSlabBlack", file: "LaskiSlab-BlackWeb.woff2" },
] as const;

if (typeof document !== "undefined") {
  for (const face of CRAISS_FACES) {
    const style = document.createElement("style");
    style.textContent = `@font-face { font-family: "${face.family}"; font-weight: 400; font-display: block; src: url("${staticFile(
      `clients/craiss/fonts/${face.file}`,
    )}") format("woff2"); }`;
    document.head.appendChild(style);
  }
}

export const FONT_BLACK = '"LaskiSlabBlack", "Rockwell", serif';
export const FONT_BOLD = '"LaskiSlabBold", "Rockwell", serif';
export const FONT_REGULAR = '"LaskiSlabRegular", "Rockwell", serif';

// --- CI (von craiss.com: Logo-Fill, Button-Rot, Anthrazit) ---
export const RED = "#CD202C";
export const WHITE = "#FFFFFF";

// --- Basis-Layout 1080×1920, uniform auf echte Leinwand skaliert ---
export const BASE_W = 1080;
export const BASE_H = 1920;

// Springs nur für Transforms (nie für Opacity → Flicker-Regel),
// clamped: kein Nachwackeln.
export const ENTER = { damping: 22, stiffness: 160, mass: 0.9, overshootClamping: true };
// Kundenfeedback (2026-09-07, Video 04): Animationen „hüpfen" zu viel →
// deutlich weichere Feder + kleinere Wege für ruhige Einstiege.
export const SOFT = { damping: 34, stiffness: 75, mass: 1, overshootClamping: true };

// =============================================================
// Schemas
// =============================================================

export const hookSchema = z.object({
  headline: z.string().describe("Hook Headline"),
  chip: z.string().describe("Hook Chip (rot)"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

export const ctaSchema = z.object({
  lineSmall: z.string().describe("Zeile klein (Regular)"),
  lineBig: z.string().describe("Zeile groß (Black)"),
  buttonText: z.string().describe("Button-Text"),
  website: z.string().describe("Website-Zeile"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

export const footageSchema = z.object({
  showInStudio: z.boolean().describe("Footage im Studio zeigen"),
  simulateBlur: z.boolean().describe("Schnitt-Blur ab CTA simulieren"),
  renderInExport: z.boolean().describe("Footage mitrendern (nur Preview-Comp!)"),
});

export type HookProps = z.infer<typeof hookSchema>;
export type CtaProps = z.infer<typeof ctaSchema>;
export type FootageProps = z.infer<typeof footageSchema>;

// CTA-Inhalte der Serie (per Props überschreibbar)
export const CTA_TEXTS = {
  lineSmall: "WERDE TEIL DER",
  lineBig: "GENERATION\nLOGISTIK",
  buttonText: "JETZT BEWERBEN",
  website: "craiss.com/karriere",
} as const;

// =============================================================
// Footage-Vergleich (Studio / Preview-Comp; nie im Alpha-Export)
// Quelle immer der H.264-Proxy — 10-bit-HEVC aus Resolve liefert
// im Render-Frame-Extraktor falsche Frames beim Seeken.
// =============================================================

export const FootageCompare: React.FC<{
  src: string;
  footage: FootageProps;
  ctaStartSec: number;
}> = ({ src, footage, ctaStartSec }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { isRendering } = getRemotionEnvironment();

  if (isRendering ? !footage.renderInExport : !footage.showInStudio) {
    return null;
  }

  // Simuliert Davids Blur auf dem Endshot, damit die CTA-Lesbarkeit
  // realistisch beurteilt werden kann.
  const blurPx = footage.simulateBlur
    ? interpolate(
        frame,
        [Math.round((ctaStartSec - 0.12) * fps), Math.round((ctaStartSec + 0.48) * fps)],
        [0, 16],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
      )
    : 0;

  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: blurPx > 0.1 ? `blur(${blurPx}px)` : undefined,
        }}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// Hook — Headline + roter Chip.
// layout "top": über dem Himmel (Video 01, keine Gesichter vorne).
// layout "lower": Lower-Third unter der Gesichts-Zone (Video 02,
// Talking-Head-Opener) — kompakter, endet vor der unteren Safe-Kante.
// =============================================================

const HOOK_LAYOUTS = {
  top: { top: 300, headlineSize: 92, chipSize: 44, gap: 26 },
  lower: { top: 940, headlineSize: 76, chipSize: 38, gap: 20 },
} as const;

export const Hook: React.FC<{
  hook: HookProps;
  layout?: keyof typeof HOOK_LAYOUTS;
  // Ruhige Variante (Kundenfeedback „hüpft zu stark"): SOFT-Feder, kurze Wege.
  calm?: boolean;
}> = ({ hook, layout = "top", calm = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const L = HOOK_LAYOUTS[layout];

  const durFrames = F(hook.endSec - hook.startSec);
  const outStart = durFrames - F(0.32);

  // Gemeinsames Ausblenden (linear, exakt 0/1 — kein Feder-Opacity)
  const outOp = interpolate(frame, [outStart, durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Headline: Fade + sanft von oben, clamped Spring auf Transform
  const hlIn = spring({ frame, fps, config: calm ? SOFT : ENTER });
  const hlY = interpolate(hlIn, [0, 1], [calm ? -12 : -34, 0]);
  const hlOp =
    interpolate(frame, [0, 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) * outOp;

  // Chip: leicht versetzt hinterher
  const chipDelay = F(0.16);
  const chipIn = spring({ frame: frame - chipDelay, fps, config: calm ? SOFT : ENTER });
  const chipScale = interpolate(chipIn, [0, 1], [calm ? 0.95 : 0.85, 1]);
  const chipOp =
    interpolate(frame, [chipDelay, chipDelay + 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) * outOp;

  return (
    <div
      style={{
        position: "absolute",
        top: L.top + hook.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: L.gap,
      }}
    >
      <div
        style={{
          fontFamily: FONT_BLACK,
          fontSize: L.headlineSize,
          lineHeight: 1.04,
          color: WHITE,
          textTransform: "uppercase",
          textAlign: "center",
          textShadow: "0 4px 26px rgba(0,0,0,0.45)",
          opacity: hlOp,
          transform: `translateY(${hlY}px)`,
          padding: "0 40px",
        }}
      >
        {hook.headline}
      </div>
      <div
        style={{
          backgroundColor: RED,
          borderRadius: 6,
          padding: layout === "lower" ? "13px 32px" : "16px 38px",
          fontFamily: FONT_BOLD,
          fontSize: L.chipSize,
          letterSpacing: 3,
          color: WHITE,
          textTransform: "uppercase",
          boxShadow: "0 6px 24px rgba(0,0,0,0.30)",
          opacity: chipOp,
          transform: `scale(${chipScale})`,
        }}
      >
        {hook.chip}
      </div>
    </div>
  );
};

// =============================================================
// Logo-Bausteine — Wordmark als Inline-SVG (Pfad aus logo.svg von
// craiss.com), damit die Farbe frei wählbar ist (rot/weiß/anthrazit),
// plus Lockup mit „GENERATION LOGISTIK"-Unterzeile.
// =============================================================

export const ANTHRACITE = "#3D3D3D";

const WORDMARK_RATIO = 75.4 / 558.3;

export const CraissWordmark: React.FC<{ width: number; fill?: string }> = ({
  width,
  fill = RED,
}) => (
  <svg
    width={width}
    height={width * WORDMARK_RATIO}
    viewBox="0 0 558.3 75.4"
    style={{ display: "block" }}
  >
    <g fill={fill}>
      <path d="M94.6,46.9c-0.1,10.8-0.4,14.5-2,17.8c-2.9,6.4-8.9,9.4-20.5,10.1c-4.6,0.4-13.5,0.6-28.3,0.6 c-21.4,0-28.3-1-34.3-4.9C2.1,65.9,0,58.1,0,36C0,16.4,2.2,9.4,10,4.9C16.7,1,23.8,0,44.7,0c27.7,0,33.8,0.6,40.1,3.7 c6,3,8.8,9.6,8.8,20.5v2.5H72c-0.4-8.1-2.1-8.8-21.7-8.8c-18.5,0-21.8,0.4-24.6,2.9c-2.7,2.5-3.2,5.5-3.2,17.5 c0,17.8,1.7,19.2,23.4,19.2c16.8,0,19.3-0.1,22.4-1.5c3.2-1.3,4.5-3.7,4.5-9H94.6z" />
      <path d="M107,0.6h64.1c13.1,0,18.9,1.1,23.2,4.7c4.3,3.5,6.4,9.8,6.4,19.8c0,13.8-3.3,19.3-12.8,21.4 c9.2,1.6,12,5.5,11.8,16.7v11.7h-23v-9.2c-0.1-8-2.3-9.7-12.5-9.5h-34.7v18.7H107V0.6z M164.9,38c10.9,0,13-1.3,13-8.7 c0-4.8-0.4-6.8-1.9-8.4c-1.7-1.8-3.6-2.1-10.4-2.1h-36.1V38H164.9z" />
      <path d="M248.9,0.6h30.3l40.7,74.3h-24.7l-7.4-13.3h-47.9l-7.1,13.3h-25.6L248.9,0.6z M279.9,46.1l-16-29.6L248,46.1 H279.9z" />
      <rect x="326.4" y="0.6" width="22.6" height="74.3" />
      <path d="M384.2,51.1c0.2,5.1,0.8,6.4,3.5,7.4c1.7,0.7,8,1.1,15.2,1.1c26.2,0,29.3-0.8,29.3-6.9c0-3-1.5-5.2-3.8-6 c-2.5-0.8-2.5-0.8-14.2-0.9h-20.5c-13.7,0-19.4-0.8-24.2-3.2c-5.3-2.8-7.8-8.7-7.8-18.8c0-13.4,3.8-19.1,14.5-21.6 c6-1.6,14.7-2.1,31-2.1c26.1,0,32.1,0.7,37.4,4.1c5.1,3.5,6.8,8,6.8,19.2h-22.1c0-6.5-2.2-7.4-16.8-7.4c-7.2,0-16.9,0.2-20.5,0.4 c-6,0.4-8,2-8,6.2c0,3.1,1.6,5.1,4.8,5.9c1.3,0.3,1.8,0.4,9.1,0.6H419c2,0,12,0.3,15.8,0.6c14.2,0.7,19.7,6.9,19.7,21.8 c0,13.7-4,19.7-14.9,22.1c-5.6,1.2-16.6,1.9-32.8,1.9c-25.7,0-31.4-0.6-38-3.9c-4.6-2.2-6.9-7.9-6.9-16.7c0-0.7,0-2.1,0.1-3.7 H384.2z" />
      <path d="M488,51.1c0.2,5.1,0.8,6.4,3.5,7.4c1.7,0.7,8,1.1,15.2,1.1c26.2,0,29.3-0.8,29.3-6.9c0-3-1.5-5.2-3.8-6 c-2.5-0.8-2.5-0.8-14.2-0.9h-20.5c-13.7,0-19.4-0.8-24.2-3.2c-5.3-2.8-7.8-8.7-7.8-18.8c0-13.4,3.8-19.1,14.5-21.6 c6-1.6,14.7-2.1,31-2.1C537,0,543,0.7,548.4,4.1c5.1,3.5,6.8,8,6.8,19.2h-22.1c0-6.5-2.2-7.4-16.8-7.4c-7.2,0-16.9,0.2-20.5,0.4 c-6,0.4-8,2-8,6.2c0,3.1,1.6,5.1,4.8,5.9c1.3,0.3,1.8,0.4,9.1,0.6h21.1c2,0,12,0.3,15.8,0.6c14.2,0.7,19.7,6.9,19.7,21.8 c0,13.7-4,19.7-14.9,22.1c-5.6,1.2-16.6,1.9-32.8,1.9c-25.7,0-31.4-0.6-38-3.9c-4.6-2.2-6.9-7.9-6.9-16.7c0-0.7,0-2.1,0.1-3.7H488z" />
    </g>
  </svg>
);

// Craiss-Blau — Primärfarbe laut CD-Handbuch (S. 21): RGB 0/47/95
export const CRAISS_BLUE = "#002F5F";

// Offizielles Logo laut CD-Handbuch S. 13 „Logoversionen":
// Wortmarke + rechts daneben zweizeilig GENERATION (Regular) über
// LOGISTIK (Bold). Farbversion: Rot + Craiss-Blau (nur auf hellem
// Grund, S. 11); negativ: alles Weiß; schwarz: alles Schwarz.
// Proportionen aus dem Handbuch abgemessen (Wortmarke = W):
// Spaltenabstand ~4% W, GENERATION ~6,3% W, LOGISTIK ~7,2% W.
export const CraissLogoLockup: React.FC<{
  width: number; // Breite der WORTMARKE (Gesamt ~1,6×)
  variant?: "color" | "white" | "black";
}> = ({ width, variant = "color" }) => {
  const wordmarkFill = variant === "color" ? RED : variant === "white" ? WHITE : "#000000";
  const textColor = variant === "color" ? CRAISS_BLUE : wordmarkFill;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: Math.round(width * 0.042) }}>
      <CraissWordmark width={width} fill={wordmarkFill} />
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div
          style={{
            fontFamily: FONT_REGULAR,
            fontSize: width * 0.063,
            lineHeight: 1.08,
            letterSpacing: width * 0.0045,
            color: textColor,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          Generation
        </div>
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: width * 0.072,
            lineHeight: 1.02,
            letterSpacing: width * 0.0012,
            color: textColor,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          Logistik
        </div>
      </div>
    </div>
  );
};

// =============================================================
// Flaggen — für die Kollegen-Aufzählung (Video 03).
// Inline-SVG (offizielle Flaggenfarben, bewusst nicht CI):
// Chip = Flagge + Label, poppt am Wortanfang auf, gemeinsame
// Ausblendung über outOp (linear, exakt 0/1).
// =============================================================

const FLAG_RECTS: Record<string, React.ReactElement> = {
  HU: (
    <>
      <rect width="5" height="1" y="0" fill="#CD2A3E" />
      <rect width="5" height="1" y="1" fill="#FFFFFF" />
      <rect width="5" height="1" y="2" fill="#436F4D" />
    </>
  ),
  CZ: (
    <>
      <rect width="5" height="1.5" y="0" fill="#FFFFFF" />
      <rect width="5" height="1.5" y="1.5" fill="#D7141A" />
      <path d="M0,0 L2.5,1.5 L0,3 Z" fill="#11457E" />
    </>
  ),
  RO: (
    <>
      <rect width="1.667" height="3" x="0" fill="#002B7F" />
      <rect width="1.667" height="3" x="1.667" fill="#FCD116" />
      <rect width="1.666" height="3" x="3.334" fill="#CE1126" />
    </>
  ),
  LT: (
    <>
      <rect width="5" height="1" y="0" fill="#FDB913" />
      <rect width="5" height="1" y="1" fill="#006A44" />
      <rect width="5" height="1" y="2" fill="#C1272D" />
    </>
  ),
  PL: (
    <>
      <rect width="5" height="1.5" y="0" fill="#FFFFFF" />
      <rect width="5" height="1.5" y="1.5" fill="#DC143C" />
    </>
  ),
};

export const flagItemSchema = z.object({
  country: z.enum(["HU", "CZ", "RO", "LT", "PL"]).describe("Land"),
  label: z.string().describe("Label unter der Flagge"),
  startSec: z.number().step(0.04).describe("Einsatz (Sek, absolut)"),
});

export const flagsSchema = z.object({
  items: z.array(flagItemSchema).describe("Flaggen"),
  startSec: z.number().step(0.04).describe("Sequenz-Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

export type FlagsProps = z.infer<typeof flagsSchema>;

// Kompakt genug, dass die Reihe im Close-up (Kinn bei ~936px) unter dem
// Gesicht bleibt und das Label die Safe-Zone-Unterkante (1104px) exakt hält.
const FLAG_W = 160;
const FLAG_H = 96;

// Staffellauf statt Sammelreihe: Jede Flagge fliegt am Wortanfang von
// rechts in die Bildmitte und beim nächsten Wort nach links wieder raus —
// nichts bleibt stehen (sonst wirkt es wie eine abgeschlossene Auswahl).
// Exit von Flagge i = startSec von Flagge i+1; die letzte geht bei endSec.
export const FlagsRow: React.FC<{ flags: FlagsProps; calm?: boolean }> = ({ flags, calm = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  // Ruhige Variante: SOFT-Feder und 120 statt 340 px Weg (wie Video 04)
  const travel = calm ? 120 : 340;

  return (
    <div
      style={{
        position: "absolute",
        top: 972 + flags.offsetY,
        left: 0,
        right: 0,
        height: FLAG_H + 10 + 26,
      }}
    >
      {flags.items.map((item, i) => {
        const enter = F(item.startSec - flags.startSec);
        const exitSec = flags.items[i + 1]?.startSec ?? flags.endSec - 0.28;
        const exit = F(exitSec - flags.startSec);

        // Einflug: Spring auf X (clamped), Fade linear auf exakt 1
        const inP = spring({ frame: frame - enter, fps, config: calm ? SOFT : ENTER });
        const inX = interpolate(inP, [0, 1], [travel, 0]);
        const inOp = interpolate(frame, [enter, enter + 5], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        // Ausflug: linear nach links + Fade auf exakt 0
        const outX = interpolate(frame, [exit, exit + F(0.28)], [0, -travel], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const outOp = interpolate(frame, [exit, exit + F(0.24)], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const op = inOp * outOp;
        if (op <= 0) return null; // raus = raus (unmounten statt 0%-Deckkraft)

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
              opacity: op,
              transform: `translateX(${inX + outX}px)`,
            }}
          >
            <svg
              width={FLAG_W}
              height={FLAG_H}
              viewBox="0 0 5 3"
              preserveAspectRatio="none"
              style={{
                borderRadius: 10,
                boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
                display: "block",
              }}
            >
              {FLAG_RECTS[item.country]}
            </svg>
            <div
              style={{
                fontFamily: FONT_BOLD,
                fontSize: 26,
                letterSpacing: 2,
                color: WHITE,
                textTransform: "uppercase",
                textShadow: "0 3px 16px rgba(0,0,0,0.6)",
              }}
            >
              {item.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// =============================================================
// Endcard — CTA auf opakem Grund (Website-Look: weiß, rot,
// Anthrazit), wenn das Footage keinen freien Endshot hergibt.
// Verlängert das Video; Stack und Timing wie beim Overlay-CTA.
// =============================================================

export const Endcard: React.FC<{ cta: CtaProps }> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  const bgOp = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const tClaim = F(0.2);
  const tLogo = F(0.4);
  const tButton = F(0.64);
  const tWeb = F(0.88);

  const fadeIn = (start: number) =>
    interpolate(frame, [start, start + 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const rise = (start: number) => {
    const p = spring({ frame: frame - start, fps, config: SOFT });
    return interpolate(p, [0, 1], [24, 0]);
  };

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* Opaker Grund — bewusst nicht transparent */}
      <div style={{ position: "absolute", inset: 0, backgroundColor: WHITE, opacity: bgOp }} />
      {/* Roter Akzentbalken oben (Website-Motiv) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 24,
          backgroundColor: RED,
          opacity: bgOp,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: 560 + cta.offsetY,
          left: 0,
          right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {/* Kundenwunsch: „WERDE TEIL DER" + offizielles Logo */}
        <div
          style={{
            fontFamily: FONT_REGULAR,
            fontSize: 44,
            letterSpacing: 6,
            color: ANTHRACITE,
            textTransform: "uppercase",
            opacity: fadeIn(tClaim),
            transform: `translateY(${rise(tClaim)}px)`,
          }}
        >
          {cta.lineSmall}
        </div>
        <div
          style={{
            marginTop: 44,
            opacity: fadeIn(tLogo),
            transform: `translateY(${rise(tLogo)}px)`,
          }}
        >
          <CraissLogoLockup width={520} variant="color" />
        </div>

        <div
          style={{
            marginTop: 56,
            backgroundColor: RED,
            borderRadius: 6,
            padding: "26px 58px",
            fontFamily: FONT_BOLD,
            fontSize: 46,
            letterSpacing: 2,
            color: WHITE,
            textTransform: "uppercase",
            boxShadow: `0 10px 36px ${RED}44`,
            opacity: fadeIn(tButton),
            transform: `translateY(${rise(tButton)}px)`,
          }}
        >
          {cta.buttonText}
        </div>

        <div
          style={{
            marginTop: 28,
            fontFamily: FONT_BOLD,
            fontSize: 38,
            letterSpacing: 2,
            color: ANTHRACITE,
            opacity: fadeIn(tWeb),
            transform: `translateY(${rise(tWeb)}px)`,
          }}
        >
          {cta.website}
        </div>
      </div>
    </div>
  );
};

// =============================================================
// CTA — Kundenwunsch (2026-09-07): „WERDE TEIL DER" + offizielles
// Logo (CRAISS GENERATION LOGISTIK) statt Text-Claim. Farbversion
// des Logos auf weißer Karte (CD-Handbuch S. 11: farbig nur auf
// hellem Grund). lineBig aus dem Schema wird nicht mehr gerendert.
// =============================================================

export const Cta: React.FC<{ cta: CtaProps }> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  // Gestaffelte Einsätze; alles steht nach ~1,1s (CTA früh!)
  const tClaim = 0;
  const tLogo = F(0.2);
  const tButton = F(0.44);
  const tWeb = F(0.68);

  const fadeIn = (start: number) =>
    interpolate(frame, [start, start + 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const rise = (start: number) => {
    const p = spring({ frame: frame - start, fps, config: SOFT });
    return interpolate(p, [0, 1], [24, 0]);
  };

  return (
    <div
      style={{
        position: "absolute",
        top: 520 + cta.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Claim */}
      <div
        style={{
          fontFamily: FONT_REGULAR,
          fontSize: 44,
          letterSpacing: 6,
          color: WHITE,
          textTransform: "uppercase",
          textShadow: "0 3px 20px rgba(0,0,0,0.45)",
          opacity: fadeIn(tClaim),
          transform: `translateY(${rise(tClaim)}px)`,
        }}
      >
        {cta.lineSmall}
      </div>

      {/* Offizielles Logo auf weißer Karte */}
      <div
        style={{
          marginTop: 30,
          backgroundColor: WHITE,
          borderRadius: 12,
          padding: "36px 48px",
          boxShadow: "0 10px 40px rgba(0,0,0,0.28)",
          opacity: fadeIn(tLogo),
          transform: `translateY(${rise(tLogo)}px)`,
        }}
      >
        <CraissLogoLockup width={480} variant="color" />
      </div>

      {/* Button */}
      <div
        style={{
          marginTop: 46,
          backgroundColor: RED,
          borderRadius: 6,
          padding: "26px 58px",
          fontFamily: FONT_BOLD,
          fontSize: 46,
          letterSpacing: 2,
          color: WHITE,
          textTransform: "uppercase",
          boxShadow: "0 10px 36px rgba(0,0,0,0.35)",
          opacity: fadeIn(tButton),
          transform: `translateY(${rise(tButton)}px)`,
        }}
      >
        {cta.buttonText}
      </div>

      {/* Website */}
      <div
        style={{
          marginTop: 26,
          fontFamily: FONT_BOLD,
          fontSize: 38,
          letterSpacing: 2,
          color: WHITE,
          textShadow: "0 3px 22px rgba(0,0,0,0.65)",
          opacity: fadeIn(tWeb),
          transform: `translateY(${rise(tWeb)}px)`,
        }}
      >
        {cta.website}
      </div>
    </div>
  );
};
