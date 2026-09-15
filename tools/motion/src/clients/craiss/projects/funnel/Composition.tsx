// ============================================================
// Craiss Generation Logistik — "04 Funnel Video" (Landing Page)
// Teil 1 Chef (bis 20,5s) · schwarze Lücke 22,68–23,64s ·
// Teil 2 Recruiterin Eva (ab 23,56s) · zwei Endshots ab 54,2s.
//
// KEIN CTA (Video liegt bereits auf der Landing Page).
// - Hook „WIR SIND DIE KÜMMERER" ab 0,24s OBEN (Shot 1 zu eng für
//   Lower-Third: Kinn ~52%, Kopf-Oberkante ~19% → Block endet bei 16%).
// - Standort-Chip „MÜHLACKER" bei „mit Sitz in Mühlacker" (6,84s).
// - Vollbild-SWIPE-Transition über die schwarze Lücke: rote Kante führt,
//   weißes Panel mit Logo-Lockup hält, Ausfahrt gibt Eva exakt auf ihrem
//   Shot-Beginn (23,64s) frei. Schwarz ist nie sichtbar.
// - Eva: Namens-Karte, „Kein Lebenslauf/Anschreiben", Schritte 1–3,
//   „Sei erreichbar"-Phone-Chip, Outro „Worauf wartest du?".
// - End-Logo NUR auf dem LETZTEN Shot (ab 55,8s): Lockup mit
//   GENERATION LOGISTIK, größer, vertikal mittig.
//
// 9:16 portrait-4k (2160×3840), 25fps, 60,72s (1518 Frames).
// Schnitte: 1,36 / 4,52 / … / 22,68 [schwarz] 23,64 / 30,32 / 33,28 /
// 36,68 / 40,68 / 45,4 / 50,6 / 54,2 / 55,68.
// Gemeinsame Bausteine: ../../lib
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Cta,
  CTA_TEXTS,
  ctaSchema,
  ANTHRACITE,
  FootageCompare,
  footageSchema,
  CraissLogoLockup,
  SOFT,
  FONT_BLACK,
  FONT_BOLD,
  FONT_REGULAR,
  RED,
  WHITE,
} from "../../lib";
import brandJson from "../../brand.json";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);

// --- Schemas ---

const chipSchema = z.object({
  text: z.string().describe("Text"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

const transitionSchema = z.object({
  startSec: z.number().step(0.04).describe("Start (vor der Lücke)"),
  coverSec: z.number().step(0.04).describe("Voll zu (= Lücken-Beginn)"),
  revealSec: z.number().step(0.04).describe("Aufziehen (= Eva-Shot-Beginn)"),
  endSec: z.number().step(0.04).describe("Komplett raus"),
});

const nameCardSchema = z.object({
  name: z.string().describe("Name"),
  role: z.string().describe("Rolle (Chip)"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

const noCvSchema = z.object({
  line1: z.string().describe("Zeile 1"),
  line2: z.string().describe("Zeile 2"),
  startSec: z.number().step(0.04).describe("Start Zeile 1 (Sek)"),
  line2Sec: z.number().step(0.04).describe("Start Zeile 2 (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

const stepSchema = z.object({
  num: z.string().describe("Nummer"),
  label: z.string().describe("Text"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
});

export const craissFunnelSchema = projectPropsSchema.extend({
  chefCard: nameCardSchema.describe("Namens-Karte Chef"),
  location: chipSchema.describe("Standort-Chip"),
  transition: transitionSchema.describe("Swipe-Transition"),
  nameCard: nameCardSchema.describe("Namens-Karte Eva"),
  noCv: noCvSchema.describe("Kein Lebenslauf/Anschreiben"),
  steps: z.array(stepSchema).describe("Bewerbungs-Schritte"),
  phoneChip: chipSchema.describe("Erreichbarkeits-Chip"),
  outro: chipSchema.describe("Outro-Frage"),
  cta: ctaSchema.describe("CTA (letzter Shot)"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissFunnelProps = z.infer<typeof craissFunnelSchema>;

export const craissFunnelDefaults: CraissFunnelProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  // Stand 2026-09-11: Kunden-Schnitt V4 (ohne Animation = V3-Export), 1478 Frames
  durationInSeconds: 59.12,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  // Zeiten 2026-09-11 auf den Kunden-Schnitt V4 umgestellt: per Differenz
  // animierter V4 − Export ohne Animation gemessen und gegen einen Render
  // mit den alten V2-Zeiten ausgerichtet. Chef-Teil (Karte, Standort,
  // Transition) −34 Frames, Eva-Teil inkl. CTA −27 Frames; Positionen
  // unverändert. Wortzeiten in den Kommentaren beziehen sich noch auf V2.
  chefCard: {
    // „…ist Michael Craiss. Ich bin Geschäftsführer…" — V2: „Michael" 2,0s
    name: "MICHAEL CRAISS",
    role: "GESCHÄFTSFÜHRENDER GESELLSCHAFTER",
    startSec: 0.64,
    // raus vor dem Schnitt bei 3,16
    endSec: 3.12,
    offsetY: 0,
  },
  location: {
    // „mit Sitz in Mühlacker"
    text: "MÜHLACKER",
    startSec: 5.24,
    endSec: 6.64,
    offsetY: 0,
  },
  transition: {
    startSec: 21.0,
    coverSec: 21.32,
    revealSec: 22.28,
    endSec: 22.68,
  },
  nameCard: {
    // „mein Name ist Eva"; bis vor „wenn du dich bewerben…"
    name: "EVA",
    role: "DEINE ANSPRECHPARTNERIN",
    startSec: 23.76,
    endSec: 27.32,
    // Kundenwunsch: Evas Hals frei — alle Eva-Elemente +60
    offsetY: 60,
  },
  noCv: {
    line1: "KEIN LEBENSLAUF",
    line2: "KEIN ANSCHREIBEN",
    startSec: 32.48,
    line2Sec: 34.24,
    endSec: 35.52,
    offsetY: 60,
  },
  steps: [
    { num: "1", label: "TRAG DICH EIN", startSec: 35.72, endSec: 37.08 },
    { num: "2", label: "TELEFONAT", startSec: 37.08, endSec: 39.52 },
    { num: "3", label: "PERSÖNLICHES KENNENLERNEN", startSec: 46.88, endSec: 49.32 },
  ],
  phoneChip: {
    // „Schau bitte, dass du erreichbar bist…"
    text: "SEI ERREICHBAR",
    startSec: 39.56,
    endSec: 43.52,
    offsetY: 60,
  },
  outro: {
    // „worauf wartest du?"; raus vor dem Schnitt 53,12
    text: "WORAUF WARTEST DU?",
    startSec: 50.32,
    endSec: 52.92,
    offsetY: 60,
  },
  cta: {
    // Kundenwunsch: Ende mit dem Serien-CTA — nur auf dem LETZTEN Shot (ab 54,6)
    ...CTA_TEXTS,
    startSec: 54.72,
    offsetY: 0,
  },
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: false,
  },
};

export const craissFunnelPreviewDefaults: CraissFunnelProps = {
  ...craissFunnelDefaults,
  transparent: false,
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: true,
  },
};

const FOOTAGE_SRC = "projects/craiss-funnel/ohne-Animation/proxy/04_Funnel_Video_V3_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Gemeinsame Ein-/Aus-Logik der Lower-Third-Elemente
const useInOut = (durFrames: number, outLen = 0.32) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const outOp = interpolate(frame, [durFrames - F(outLen), durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const inP = spring({ frame, fps, config: SOFT });
  const inOp = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return { frame, fps, F, inP, inOp, outOp };
};

// =============================================================
// Standort-Chip — roter Pill mit Pin + Ortsname, Lower-Third
// =============================================================

const LocationChip: React.FC<{ chip: CraissFunnelProps["location"] }> = ({ chip }) => {
  const { inP, inOp, outOp } = useInOut(Math.round((chip.endSec - chip.startSec) * 25));
  const scale = interpolate(inP, [0, 1], [0.95, 1]);
  const op = inOp * outOp;
  if (op <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 990 + chip.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 14,
          backgroundColor: RED,
          borderRadius: 999,
          padding: "18px 36px 18px 28px",
          boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
          opacity: op,
          transform: `scale(${scale})`,
        }}
      >
        <svg width="30" height="40" viewBox="0 0 24 32" style={{ display: "block" }}>
          <path
            d="M12 0C5.4 0 0 5.4 0 12c0 8.4 12 20 12 20s12-11.6 12-20C24 5.4 18.6 0 12 0z"
            fill={WHITE}
          />
          <circle cx="12" cy="12" r="5" fill={RED} />
        </svg>
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: 42,
            letterSpacing: 3,
            color: WHITE,
            textTransform: "uppercase",
          }}
        >
          {chip.text}
        </div>
      </div>
    </div>
  );
};

// =============================================================
// Swipe-Transition — Vollbild-Panel [rot|weiß|rot] fährt von links
// durch. Rote Kante führt, weißes Feld trägt das Logo-Lockup, die
// Ausfahrt gibt das Bild von links nach rechts wieder frei.
// =============================================================

const RED_EDGE = 140;
const PANEL_W = RED_EDGE + BASE_W + RED_EDGE;

const TransitionSwipe: React.FC<{
  t: CraissFunnelProps["transition"];
}> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  const coverF = F(t.coverSec - t.startSec);
  const revealF = F(t.revealSec - t.startSec);
  const endF = F(t.endSec - t.startSec);

  // Cover-Position: weißes Feld (lokal RED_EDGE..RED_EDGE+BASE_W) deckt
  // exakt 0..BASE_W ab → tx = RED_EDGE + BASE_W. Ausfahrt: komplett raus.
  const COVER_TX = RED_EDGE + BASE_W;
  const tx =
    frame < revealF
      ? interpolate(frame, [0, coverF], [0, COVER_TX], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.cubic),
        })
      : interpolate(frame, [revealF, endF], [COVER_TX, COVER_TX + PANEL_W], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.cubic),
        });

  // Logo: poppt nach dem Zudecken, fährt mit dem Panel raus
  const logoStart = coverF + 2;
  const logoP = spring({ frame: frame - logoStart, fps, config: SOFT });
  const logoScale = interpolate(logoP, [0, 1], [0.95, 1]);
  const logoOp = interpolate(frame, [logoStart, logoStart + 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: -PANEL_W,
        width: PANEL_W,
        height: BASE_H,
        display: "flex",
        transform: `translateX(${tx}px)`,
      }}
    >
      <div style={{ width: RED_EDGE, height: "100%", backgroundColor: RED }} />
      <div
        style={{
          width: BASE_W,
          height: "100%",
          backgroundColor: WHITE,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: logoOp,
            transform: `scale(${logoScale})`,
          }}
        >
          <div
            style={{
              fontFamily: FONT_REGULAR,
              fontSize: 40,
              letterSpacing: 6,
              color: ANTHRACITE,
              textTransform: "uppercase",
            }}
          >
            {CTA_TEXTS.lineSmall}
          </div>
          <div style={{ marginTop: 36 }}>
            <CraissLogoLockup width={440} variant="color" />
          </div>
          <div
            style={{
              marginTop: 44,
              backgroundColor: RED,
              borderRadius: 6,
              padding: "22px 52px",
              fontFamily: FONT_BOLD,
              fontSize: 42,
              letterSpacing: 2,
              color: WHITE,
              textTransform: "uppercase",
            }}
          >
            {CTA_TEXTS.buttonText}
          </div>
        </div>
      </div>
      <div style={{ width: RED_EDGE, height: "100%", backgroundColor: RED }} />
    </div>
  );
};

// =============================================================
// Namens-Karte Eva — Name groß + Rollen-Chip (Serie: Headline+Chip)
// =============================================================

const NameCard: React.FC<{ card: CraissFunnelProps["nameCard"] }> = ({ card }) => {
  const { frame, F, inP, inOp, outOp } = useInOut(
    Math.round((card.endSec - card.startSec) * 25),
  );
  const { fps } = useVideoConfig();
  const hlY = interpolate(inP, [0, 1], [-16, 0]);
  const chipDelay = F(0.16);
  const chipIn = spring({ frame: frame - chipDelay, fps, config: SOFT });
  const chipScale = interpolate(chipIn, [0, 1], [0.95, 1]);
  const chipOp =
    interpolate(frame, [chipDelay, chipDelay + 6], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) * outOp;

  return (
    <div
      style={{
        position: "absolute",
        top: 972 + card.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
      }}
    >
      <div
        style={{
          fontFamily: FONT_BLACK,
          fontSize: 72,
          lineHeight: 1,
          color: WHITE,
          textTransform: "uppercase",
          textShadow: "0 4px 26px rgba(0,0,0,0.5)",
          opacity: inOp * outOp,
          transform: `translateY(${hlY}px)`,
        }}
      >
        {card.name}
      </div>
      <div
        style={{
          backgroundColor: RED,
          borderRadius: 6,
          padding: "10px 26px",
          fontFamily: FONT_BOLD,
          fontSize: 30,
          letterSpacing: 2,
          color: WHITE,
          textTransform: "uppercase",
          boxShadow: "0 6px 24px rgba(0,0,0,0.30)",
          opacity: chipOp,
          transform: `scale(${chipScale})`,
        }}
      >
        {card.role}
      </div>
    </div>
  );
};

// =============================================================
// „Kein Lebenslauf / Kein Anschreiben" — zwei Zeilen mit rotem ✕,
// Zeile 2 kommt auf den Wortanfang „Anschreiben"
// =============================================================

const RedCross: React.FC = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" style={{ display: "block" }}>
    <g transform="rotate(45 20 20)">
      <rect x="4" y="15.5" width="32" height="9" rx="4.5" fill={RED} />
      <rect x="15.5" y="4" width="9" height="32" rx="4.5" fill={RED} />
    </g>
  </svg>
);

const NoCvCard: React.FC<{ noCv: CraissFunnelProps["noCv"] }> = ({ noCv }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const durFrames = F(noCv.endSec - noCv.startSec);
  const outOp = interpolate(frame, [durFrames - F(0.28), durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const line2Start = F(noCv.line2Sec - noCv.startSec);

  const row = (label: string, start: number, key: string) => {
    const p = spring({ frame: frame - start, fps, config: SOFT });
    const x = interpolate(p, [0, 1], [28, 0]);
    const op =
      interpolate(frame, [start, start + 6], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }) * outOp;
    return (
      <div
        key={key}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 18,
          opacity: op,
          transform: `translateX(${x}px)`,
        }}
      >
        <RedCross />
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: 48,
            letterSpacing: 1,
            color: WHITE,
            textTransform: "uppercase",
            textShadow: "0 3px 18px rgba(0,0,0,0.6)",
          }}
        >
          {label}
        </div>
      </div>
    );
  };

  return (
    <div
      style={{
        position: "absolute",
        top: 950 + noCv.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 14,
      }}
    >
      {row(noCv.line1, 0, "l1")}
      {row(noCv.line2, line2Start, "l2")}
    </div>
  );
};

// =============================================================
// Schritt-Karte — rote Nummern-Kachel + Text (Zahl exakt mittig)
// =============================================================

const StepCard: React.FC<{ step: z.infer<typeof stepSchema> }> = ({ step }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const durFrames = F(step.endSec - step.startSec);

  const inP = spring({ frame, fps, config: SOFT });
  const inX = interpolate(inP, [0, 1], [120, 0]);
  const inOp = interpolate(frame, [0, 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outX = interpolate(frame, [durFrames - F(0.28), durFrames], [0, -160], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outOp = interpolate(frame, [durFrames - F(0.28), durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const op = inOp * outOp;
  if (op <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 1050,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 20,
          opacity: op,
          transform: `translateX(${inX + outX}px)`,
        }}
      >
        <div
          style={{
            width: 68,
            height: 68,
            borderRadius: 10,
            backgroundColor: RED,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
          }}
        >
          {/* Laski Slab zentriert Ziffern optisch zu tief — Cap-Höhe pro
              Ziffer ausgleichen (die runde „3" hängt zusätzlich tiefer) */}
          <span
            style={{
              fontFamily: FONT_BLACK,
              fontSize: 42,
              lineHeight: 1,
              color: WHITE,
              transform: `translateY(${step.num === "3" ? -10.5 : -6.5}px)`,
            }}
          >
            {step.num}
          </span>
        </div>
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: 44,
            letterSpacing: 1,
            color: WHITE,
            textTransform: "uppercase",
            textShadow: "0 3px 18px rgba(0,0,0,0.6)",
          }}
        >
          {step.label}
        </div>
      </div>
    </div>
  );
};

// =============================================================
// Phone-Chip — „Sei erreichbar", Handy-Icon mit Klingel-Wackeln
// =============================================================

const PhoneChip: React.FC<{ chip: CraissFunnelProps["phoneChip"] }> = ({ chip }) => {
  const { frame, F, inP, inOp, outOp } = useInOut(
    Math.round((chip.endSec - chip.startSec) * 25),
  );
  const scale = interpolate(inP, [0, 1], [0.95, 1]);
  const op = inOp * outOp;
  // Zwei kurze Klingel-Wackler nach dem Einstieg, danach Ruhe
  const wiggleWindow = (start: number) =>
    interpolate(frame, [start, start + 3, start + 12, start + 15], [0, 1, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const wiggleAmp = wiggleWindow(F(0.5));
  const rot = Math.sin(frame * 1.6) * 5 * wiggleAmp;
  if (op <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 990 + chip.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 16,
          backgroundColor: RED,
          borderRadius: 999,
          padding: "18px 36px 18px 26px",
          boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
          opacity: op,
          transform: `scale(${scale})`,
        }}
      >
        <svg
          width="34"
          height="46"
          viewBox="0 0 28 40"
          style={{ display: "block", transform: `rotate(${rot}deg)` }}
        >
          <rect x="1" y="1" width="26" height="38" rx="5" fill="none" stroke={WHITE} strokeWidth="3" />
          <rect x="9" y="32" width="10" height="3" rx="1.5" fill={WHITE} />
        </svg>
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: 42,
            letterSpacing: 3,
            color: WHITE,
            textTransform: "uppercase",
          }}
        >
          {chip.text}
        </div>
      </div>
    </div>
  );
};

// =============================================================
// Outro — „Worauf wartest du?" Headline + roter Balken (Klammer
// zum Hook)
// =============================================================

const OutroCard: React.FC<{ chip: CraissFunnelProps["outro"] }> = ({ chip }) => {
  const { frame, F, inP, inOp, outOp } = useInOut(
    Math.round((chip.endSec - chip.startSec) * 25),
  );
  const { fps } = useVideoConfig();
  const hlY = interpolate(inP, [0, 1], [-16, 0]);
  const barDelay = F(0.16);
  const barIn = spring({ frame: frame - barDelay, fps, config: SOFT });
  const barScale = interpolate(barIn, [0, 1], [0, 1]);
  const barOp =
    interpolate(frame, [barDelay, barDelay + 6], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) * outOp;

  return (
    <div
      style={{
        position: "absolute",
        top: 990 + chip.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
      }}
    >
      <div
        style={{
          fontFamily: FONT_BLACK,
          fontSize: 60,
          color: WHITE,
          textTransform: "uppercase",
          textAlign: "center",
          textShadow: "0 4px 26px rgba(0,0,0,0.5)",
          opacity: inOp * outOp,
          transform: `translateY(${hlY}px)`,
          padding: "0 40px",
        }}
      >
        {chip.text}
      </div>
      <div
        style={{
          width: 280,
          height: 10,
          borderRadius: 5,
          backgroundColor: RED,
          boxShadow: "0 4px 18px rgba(0,0,0,0.35)",
          opacity: barOp,
          transform: `scaleX(${barScale})`,
        }}
      />
    </div>
  );
};

// =============================================================
// Composition
// =============================================================

export const CraissFunnel: React.FC<CraissFunnelProps> = ({
  review,
  chefCard,
  location,
  transition,
  nameCard,
  noCv,
  steps,
  phoneChip,
  outro,
  cta,
  footage,
}) => {
  const { fps, width, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const S = width / BASE_W;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <FootageCompare src={FOOTAGE_SRC} footage={footage} ctaStartSec={999} />

        {/* Layout-Bühne 1080×1920 → uniform skaliert */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: BASE_W,
            height: BASE_H,
            transform: `scale(${S})`,
            transformOrigin: "top left",
          }}
        >
          <Sequence from={s(chefCard.startSec)} durationInFrames={s(chefCard.endSec) - s(chefCard.startSec)} name="Name Chef">
            <NameCard card={chefCard} />
          </Sequence>

          <Sequence from={s(location.startSec)} durationInFrames={s(location.endSec) - s(location.startSec)} name="Standort">
            <LocationChip chip={location} />
          </Sequence>

          <Sequence from={s(transition.startSec)} durationInFrames={s(transition.endSec) - s(transition.startSec)} name="Swipe-Transition">
            <TransitionSwipe t={transition} />
          </Sequence>

          <Sequence from={s(nameCard.startSec)} durationInFrames={s(nameCard.endSec) - s(nameCard.startSec)} name="Name Eva">
            <NameCard card={nameCard} />
          </Sequence>

          <Sequence from={s(noCv.startSec)} durationInFrames={s(noCv.endSec) - s(noCv.startSec)} name="Kein Lebenslauf">
            <NoCvCard noCv={noCv} />
          </Sequence>

          {steps.map((step, i) => (
            <Sequence key={i} from={s(step.startSec)} durationInFrames={s(step.endSec) - s(step.startSec)} name={`Schritt ${step.num}`}>
              <StepCard step={step} />
            </Sequence>
          ))}

          <Sequence from={s(phoneChip.startSec)} durationInFrames={s(phoneChip.endSec) - s(phoneChip.startSec)} name="Erreichbar">
            <PhoneChip chip={phoneChip} />
          </Sequence>

          <Sequence from={s(outro.startSec)} durationInFrames={s(outro.endSec) - s(outro.startSec)} name="Outro">
            <OutroCard chip={outro} />
          </Sequence>

          <Sequence from={s(cta.startSec)} durationInFrames={durationInFrames - s(cta.startSec)} name="End-CTA">
            <Cta cta={cta} />
          </Sequence>
        </div>

        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            showFaceZone={review.showFaceZone ?? true}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
