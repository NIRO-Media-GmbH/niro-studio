// ============================================================
// LohiBW — Recruiting-Ads, Untertitel-Overlay (9:16, 4K)
// Transparentes Alpha-Overlay über den fertigen Schnitt.
// 2160×3840, 25 fps. Timeline t=0 = erster Frame der Ad.
//
// Stil ist aus den bereits eingebauten Animationen abgeleitet
// (gemessen, siehe _intern/analyze_overlays.py):
//   Gelb  #FFD900 — identisch mit den Keyword-Kästen
//   Font  Open Sans ExtraBold — 92 % Glyphdeckung im Vergleich
//
// Die bestehenden Keyword-Kästen liegen bei y 49,5–54 %. Das
// Untertitelband steht normalerweise genau dort; sobald ein langer
// Kasten kommt, fährt es nach unten. Bei kurzen Kästen entfällt die
// Seite (Entscheidung David, 12.08.2026) — das steckt schon in den
// Daten aus captions.ts, hier wird nur noch dargestellt.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import type { CaptionPage, CaptionWord, ShiftWindow } from "./captions";
import {
  VIDEO_1, VIDEO_1_SHIFTS,
  VIDEO_2, VIDEO_2_SHIFTS,
  VIDEO_3, VIDEO_3_SHIFTS,
  VIDEO_4, VIDEO_4_SHIFTS,
} from "./captions";
import brandJson from "../../brand.json";

const FONT_FACE = `@font-face {
  font-family: "Open Sans LohiBW";
  font-weight: 800;
  src: url("${staticFile("clients/lohi-bw/fonts/OpenSans-ExtraBold.ttf")}") format("truetype");
}`;

if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = FONT_FACE;
  document.head.appendChild(style);
}

const FONT = '"Open Sans LohiBW", "Open Sans", sans-serif';

const ci = loadBrand("lohi-bw", brandJson as any);
const YELLOW = ci.colors.primary;   // #FFD900
const WHITE = "#FFFFFF";

// Bandmitte als Anteil der Bildhöhe.
// normal  = auf Höhe der bestehenden Keyword-Kästen (Mitte 51,75 %)
// unten   = darunter, frei von Kasten (54 %) und vom tiefen Kasten in Video 2 (75,5 %)
const BAND_NORMAL = 0.5175;
// So hoch wie möglich, ohne den Kasten (Unterkante 54 %) zu berühren:
// die Glyphen landen damit bei rund 59–62 % statt 63–66 %.
const BAND_SHIFTED = 0.585;

// Das Band setzt sich vor dem Kasten in Bewegung — dann liest es sich
// als Choreografie und nicht als Ausweichmanöver.
const SHIFT_LEAD_SEC = 0.3;
const SHIFT_RAMP_SEC = 0.42;

// Enger dunkler Saum plus weicher Schatten. Ohne den Saum verliert
// vor allem das Gelb auf hellen Szenen (Büro, Fensterlicht) den Halt;
// ein reiner Weichschatten trägt dort nicht.
const TEXT_SHADOW = [
  "-3px -3px 6px rgba(0,0,0,0.38)",
  "3px -3px 6px rgba(0,0,0,0.38)",
  "-3px 3px 6px rgba(0,0,0,0.38)",
  "3px 3px 6px rgba(0,0,0,0.38)",
  "0 4px 16px rgba(0,0,0,0.50)",
  "0 18px 56px rgba(0,0,0,0.38)",
].join(", ");

const WORD_SPRING = { damping: 28, stiffness: 250, mass: 0.9 };

// --- Schema ---

export const lohiBwUntertitelSchema = projectPropsSchema.extend({
  fontSizePx: z.number().min(60).max(200).step(2).describe("Schriftgrad (4K)"),
  bandShiftY: z.number().min(-400).max(400).step(4)
    .describe("Band vertikal feinjustieren (px)"),
  timeOffsetSec: z.number().min(-2).max(2).step(0.04)
    .describe("Zeit-Offset zum Ausrichten aufs Footage"),
  showAccents: z.boolean().describe("Schlüsselwörter in Gelb"),
});

export type LohiBwUntertitelProps = z.infer<typeof lohiBwUntertitelSchema>;

const BASE_DEFAULTS: Omit<LohiBwUntertitelProps, "durationInSeconds"> = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  transparent: true,
  fontSizePx: 104,
  bandShiftY: 0,
  timeOffsetSec: 0,
  showAccents: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // Gesichter sitzen in diesen Ads im oberen Bilddrittel
    faceZone: { top: 0.06, bottom: 0.45, left: 0.14, right: 0.86 },
    guideOpacity: 0.35,
  },
};

// --- Einzelnes Wort ---

const WordView: React.FC<{
  word: CaptionWord;
  pageStartSec: number;
  accentsOn: boolean;
}> = ({ word, pageStartSec, accentsOn }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - Math.round((word.startSec - pageStartSec) * fps);

  const enter = spring({ frame: t, fps, config: WORD_SPRING });
  const opacity = interpolate(t, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [18, 0]);
  const scale = interpolate(enter, [0, 1], [0.93, 1]);
  const blur = interpolate(t, [0, 6], [7, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "50% 80%",
        filter: blur > 0.15 ? `blur(${blur}px)` : undefined,
        color: accentsOn && word.accent ? YELLOW : WHITE,
        whiteSpace: "nowrap",
      }}
    >
      {word.text}
    </span>
  );
};

// --- Eine Untertitelseite ---

const PageView: React.FC<{
  page: CaptionPage;
  fontSizePx: number;
  accentsOn: boolean;
}> = ({ page, fontSizePx, accentsOn }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durF = Math.round((page.endSec - page.startSec) * fps);

  // Ausblenden zum Seitenende, damit der Wechsel nicht hart schneidet
  const fadeOut = interpolate(frame, [durF - 5, durF - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: fontSizePx * 0.16,
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: fontSizePx,
        lineHeight: 1.14,
        letterSpacing: "0.01em",
        textAlign: "center",
        textShadow: TEXT_SHADOW,
        opacity: fadeOut,
      }}
    >
      {page.lines.map((line, li) => (
        <div key={li} style={{ display: "flex", columnGap: "0.28em" }}>
          {line.map((w, wi) => (
            <WordView
              key={wi}
              word={w}
              pageStartSec={page.startSec}
              accentsOn={accentsOn}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

// --- Bandposition als durchgehende Spur ---

function useBandCenter(shifts: ShiftWindow[], offsetSec: number): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps - offsetSec;

  let s = 0;
  for (const w of shifts) {
    const inAt = w.startSec - SHIFT_LEAD_SEC;
    const rampIn = interpolate(t, [inAt, inAt + SHIFT_RAMP_SEC], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    const rampOut = interpolate(t, [w.endSec, w.endSec + SHIFT_RAMP_SEC], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    s = Math.max(s, Math.min(rampIn, rampOut));
  }
  return BAND_NORMAL + (BAND_SHIFTED - BAND_NORMAL) * s;
}

// --- Hauptkomposition (nimmt die Daten als Prop) ---

const LohiBwUntertitelBase: React.FC<
  LohiBwUntertitelProps & { pages: CaptionPage[]; shifts: ShiftWindow[] }
> = ({
  pages,
  shifts,
  fontSizePx,
  bandShiftY,
  timeOffsetSec,
  showAccents,
  review,
}) => {
  const { fps, height } = useVideoConfig();
  const bandCenter = useBandCenter(shifts, timeOffsetSec);
  const centerPx = Math.round(height * bandCenter) + bandShiftY;

  const toF = (sec: number) => Math.round((sec + timeOffsetSec) * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: centerPx,
            transform: "translateY(-50%)",
            display: "flex",
            justifyContent: "center",
          }}
        >
          {pages.map((page, i) => (
            <Sequence
              key={i}
              from={toF(page.startSec)}
              durationInFrames={Math.max(1, toF(page.endSec) - toF(page.startSec))}
              name={`${String(i + 1).padStart(2, "0")} ${page.mode === "shifted" ? "⇣ " : ""}${page.lines[0].map((w) => w.text).join(" ")}`}
              layout="none"
            >
              <div style={{ position: "absolute", left: 0, right: 0, display: "flex", justifyContent: "center" }}>
                <PageView page={page} fontSizePx={fontSizePx} accentsOn={showAccents} />
              </div>
            </Sequence>
          ))}
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

// --- Die vier Ads ---
// Laufzeiten entsprechen den Quelldateien (2160×3840, 25 fps).

export const LohiBwAd1: React.FC<LohiBwUntertitelProps> = (p) => (
  <LohiBwUntertitelBase {...p} pages={VIDEO_1} shifts={VIDEO_1_SHIFTS} />
);
export const LohiBwAd2: React.FC<LohiBwUntertitelProps> = (p) => (
  <LohiBwUntertitelBase {...p} pages={VIDEO_2} shifts={VIDEO_2_SHIFTS} />
);
export const LohiBwAd3: React.FC<LohiBwUntertitelProps> = (p) => (
  <LohiBwUntertitelBase {...p} pages={VIDEO_3} shifts={VIDEO_3_SHIFTS} />
);
export const LohiBwAd4: React.FC<LohiBwUntertitelProps> = (p) => (
  <LohiBwUntertitelBase {...p} pages={VIDEO_4} shifts={VIDEO_4_SHIFTS} />
);

export const lohiBwAd1Defaults: LohiBwUntertitelProps = {
  ...BASE_DEFAULTS, durationInSeconds: 44.56,
};
export const lohiBwAd2Defaults: LohiBwUntertitelProps = {
  ...BASE_DEFAULTS, durationInSeconds: 38.96,
};
export const lohiBwAd3Defaults: LohiBwUntertitelProps = {
  ...BASE_DEFAULTS, durationInSeconds: 35.84,
};
export const lohiBwAd4Defaults: LohiBwUntertitelProps = {
  ...BASE_DEFAULTS, durationInSeconds: 40.16,
};
