// ============================================================
// Setzer — Video 4 „Fleischsalat Zutaten" (Prozess-Reel)
// Untertitel + Animationen als transparentes Alpha-Overlay.
// 1080×1920 (9:16), Standard 30 fps (wie Video 6 — Framerate ist pro
// Setzer-Video verschieden, gegen den Schnitt prüfen!). t = 0 ist der
// erste Frame des Schnitts, alle Zeiten in Sekunden.
//
// Design-System wie Video 1/6 (Kunden-Feedback 25./26.08.):
//   rot–schwarz (#E30613 auf #0D0802), Iconset-Stil „schwarzer Grund,
//   Icon weiß, Highlights rot", Arial Black Versalien, Logos nur
//   einfarbig, offizieller Claim-Vektor.
//
// Leitmotiv: die Zutaten-CHECKLISTE — Chips stapeln sich beim
// Aufzählen auf den Wortzeiten (5,4–19,9 s). Die Abhak-Reprise beim
// Live-Reinschütten ist auf Davids Ansage raus (Feedback 01.09.),
// dieses Fenster läuft als Untertitel. Dazu: Waage · HAND ✓ vs.
// MASCHINE ✗ (X auf „kaputt") · 5-MIN-Timer · Waschen/Desinfizieren ·
// 250 g/125 g-Becher-Chips mit Demo-Callback · Marken-Outro.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
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
import {
  BEATS,
  CHECKLIST_ROWS,
  DURATION_SEC,
  PAGES,
} from "./captions";
import type { CaptionPage, CaptionWord, ChecklistRow } from "./captions";
import brandJson from "../../brand.json";

const ci = loadBrand("setzer", brandJson as any);

const RED = ci.colors.primary; // #E30613
const INK = ci.colors.secondary; // #0D0802
const WHITE = "#FFFFFF";

const FONT = '"Arial Black", "Arial Bold", Arial, Helvetica, sans-serif';

const HALO = [
  "0 0 2px rgba(13,8,2,0.95)",
  "-3px -3px 0 rgba(13,8,2,0.72)",
  "3px -3px 0 rgba(13,8,2,0.72)",
  "-3px 3px 0 rgba(13,8,2,0.72)",
  "3px 3px 0 rgba(13,8,2,0.72)",
  "0 6px 22px rgba(13,8,2,0.55)",
].join(", ");

const SHADOW_HARD = "0 10px 0 rgba(13,8,2,0.28), 0 18px 44px rgba(13,8,2,0.34)";

// --- Zeit-Helfer (wie Video 1/6) ---

function useBeat(beat: { start: number; end: number }, offsetSec: number) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps - offsetSec - beat.start;
  const dur = beat.end - beat.start;
  return { t, p: Math.max(0, Math.min(1, t / dur)), dur };
}

function envelope(t: number, dur: number, fps: number, outSec = 0.3) {
  const inS = spring({ frame: Math.round(t * fps), fps, config: { damping: 15, stiffness: 190, mass: 0.8 } });
  const out = interpolate(t, [dur - outSec, dur], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.cubic),
  });
  return { inS, out, visible: t > -0.05 && t < dur + 0.05 };
}

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// --- Schema ---

export const setzerFleischsalatZutatenSchema = projectPropsSchema.extend({
  fontSizePx: z.number().min(30).max(120).step(1).describe("Untertitel-Schriftgrad"),
  bandY: z.number().min(0.4).max(0.85).step(0.005).describe("Untertitelband, Mitte (Anteil Höhe)"),
  timeOffsetSec: z.number().min(-3).max(3).step(0.02).describe("Zeit-Offset zum Ausrichten aufs Footage"),
  showSubtitles: z.boolean().describe("Untertitel einblenden"),
  showAnimations: z.boolean().describe("Animationen einblenden"),
  showLogoOutro: z.boolean().describe("Marken-Outro (Logo + Claim)"),
});

export type SetzerFleischsalatZutatenProps = z.infer<typeof setzerFleischsalatZutatenSchema>;

export const setzerFleischsalatZutatenDefaults: SetzerFleischsalatZutatenProps = {
  format: "portrait",
  fps: 30,
  durationInSeconds: DURATION_SEC,
  transparent: true,
  fontSizePx: 52,
  bandY: 0.7,
  timeOffsetSec: 0,
  showSubtitles: true,
  showAnimations: true,
  showLogoOutro: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.06, bottom: 0.46, left: 0.16, right: 0.84 },
    guideOpacity: 0.35,
  },
};

// ============================================================
// Untertitel (identische Mechanik wie Video 1/6)
// ============================================================

const WordView: React.FC<{ word: CaptionWord; startSec: number; pageStartSec: number; size: number }> = ({
  word,
  startSec,
  pageStartSec,
  size,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - Math.round((startSec - pageStartSec) * fps);

  const enter = spring({ frame: t, fps, config: { damping: 24, stiffness: 260, mass: 0.7 } });
  const opacity = interpolate(t, [0, 3], [0, 1], CLAMP);
  const y = interpolate(enter, [0, 1], [size * 0.3, 0]);
  const scale = interpolate(enter, [0, 1], [0.86, 1]);

  if (word.accent) {
    const boxW = interpolate(enter, [0, 1], [0, 1]);
    return (
      <span
        style={{
          display: "inline-block",
          opacity,
          transform: `translateY(${y}px) scale(${scale})`,
          transformOrigin: "50% 70%",
          background: RED,
          color: WHITE,
          padding: `${size * 0.06}px ${size * 0.16}px ${size * 0.1}px`,
          borderRadius: 3,
          boxShadow: `0 ${size * 0.09}px 0 ${ci.colors.accent}, 0 ${size * 0.16}px ${size * 0.4}px rgba(13,8,2,0.42)`,
          whiteSpace: "nowrap",
          clipPath: `inset(0 ${(1 - boxW) * 100}% 0 0)`,
        }}
      >
        {word.text}
      </span>
    );
  }

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "50% 70%",
        color: WHITE,
        textShadow: HALO,
        whiteSpace: "nowrap",
      }}
    >
      {word.text}
    </span>
  );
};

const PageView: React.FC<{ page: CaptionPage; size: number }> = ({ page, size }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durF = Math.round((page.endSec - page.startSec) * fps);
  const fadeOut = interpolate(frame, [durF - 4, durF - 1], [1, 0], CLAMP);
  const px = size * (page.sizeScale ?? 1);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: px * 0.26,
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: px,
        lineHeight: 1.05,
        letterSpacing: "-0.005em",
        textAlign: "center",
        opacity: fadeOut,
      }}
    >
      {page.lines.map((line, li) => {
        const lineStart = Math.min(...line.map((x) => x.startSec));
        return (
          <div key={li} style={{ display: "flex", columnGap: "0.26em", alignItems: "baseline" }}>
            {line.map((word, wi) => (
              <WordView key={wi} word={word} startSec={lineStart + wi / 24} pageStartSec={page.startSec} size={px} />
            ))}
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// Zutaten-Icons (Line-Art: weiß auf Schwarz, Highlights rot)
// ============================================================

const GurkeIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <g transform="rotate(-28 60 60)">
      <rect x="44" y="22" width="32" height="76" rx="16" fill="none" stroke={WHITE} strokeWidth="7" />
      <circle cx="54" cy="38" r="2.8" fill={WHITE} />
      <circle cx="66" cy="50" r="2.8" fill={WHITE} />
      <circle cx="55" cy="66" r="2.8" fill={WHITE} />
      <circle cx="65" cy="82" r="2.8" fill={WHITE} />
      <line x1="49" y1="55" x2="71" y2="55" stroke={RED} strokeWidth="4.5" strokeLinecap="round" />
      <line x1="49" y1="64" x2="71" y2="64" stroke={RED} strokeWidth="4.5" strokeLinecap="round" />
    </g>
  </svg>
);

const MayoIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <rect x="36" y="42" width="48" height="58" rx="9" fill="none" stroke={WHITE} strokeWidth="7" />
    <rect x="32" y="24" width="56" height="15" rx="6" fill="none" stroke={WHITE} strokeWidth="7" />
    <rect x="45" y="62" width="30" height="17" rx="3" fill={RED} />
  </svg>
);

const LyonerIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <circle cx="60" cy="68" r="29" fill="none" stroke={WHITE} strokeWidth="9" />
    <line x1="53" y1="41" x2="45" y2="27" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
    <line x1="67" y1="41" x2="75" y2="27" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
    <ellipse cx="60" cy="38" rx="6.5" ry="5.5" fill={RED} />
  </svg>
);

const GewuerzIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <path d="M 46 56 L 42 96 Q 42 101 47 101 H 73 Q 78 101 78 96 L 74 56 Z" fill="none" stroke={WHITE} strokeWidth="7" />
    <rect x="42" y="38" width="36" height="15" rx="6" fill="none" stroke={WHITE} strokeWidth="7" />
    <circle cx="90" cy="50" r="4" fill={RED} />
    <circle cx="97" cy="62" r="3.5" fill={RED} />
    <circle cx="89" cy="73" r="3" fill={RED} />
  </svg>
);

const INGREDIENT_ICONS: Record<ChecklistRow["icon"], React.FC<{ size: number }>> = {
  gurke: GurkeIcon,
  mayo: MayoIcon,
  lyoner: LyonerIcon,
  gewuerz: GewuerzIcon,
};

// Roter Haken, zeichnet sich (Dash-Trick)
const CheckMark: React.FC<{ p: number; size: number }> = ({ p, size }) => {
  const len = 62;
  return (
    <svg viewBox="0 0 60 60" width={size} height={size} style={{ display: "block" }}>
      <path
        d="M 12 32 L 25 45 L 49 15"
        fill="none"
        stroke={RED}
        strokeWidth="10"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - p)}
      />
    </svg>
  );
};

// ============================================================
// Zutaten-Checkliste: Chip-Stack (wie die V6-Kaskade — jede Zutat
// ein eigener schwarzer Chip; kein leeres Panel vor den Zeilen)
// ============================================================

const ChecklistStack: React.FC<{
  beat: { start: number; end: number };
  offsetSec: number;
  height: number;
}> = ({ beat, offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(beat, offsetSec);
  const { out, visible } = envelope(t, dur, fps, 0.35);
  if (!visible) return null;

  const tAbs = t + beat.start;

  const iconBox = height * 0.037;
  const labelPx = height * 0.0235;
  const subPx = height * 0.0135;
  const stackGap = height * 0.0095;

  return (
    <div
      style={{
        opacity: out,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: stackGap,
      }}
    >
      {CHECKLIST_ROWS.map((row, i) => {
        const tRow = tAbs - row.appearAt;
        const rowIn = spring({ frame: Math.round(tRow * fps), fps, config: { damping: 16, stiffness: 200, mass: 0.8 } });
        const rowOp = interpolate(tRow, [0, 0.1], [0, 1], CLAMP);
        const dir = i % 2 === 0 ? -1 : 1;
        const rowX = interpolate(rowIn, [0, 1], [dir * height * 0.05, 0]);
        const rowRot = interpolate(rowIn, [0, 1], [dir * 4, 0]);

        const subVisible = row.subAt !== undefined && tAbs >= row.subAt;
        const tSub = row.subAt !== undefined ? tAbs - row.subAt : 1;
        const subOp = interpolate(tSub, [0, 0.18], [0, 1], CLAMP);
        const subY = interpolate(tSub, [0, 0.3], [subPx * 0.5, 0], { ...CLAMP, easing: Easing.out(Easing.cubic) });

        const Icon = INGREDIENT_ICONS[row.icon];

        return (
          <div
            key={row.label}
            style={{
              opacity: rowOp,
              transform: `translateX(${rowX}px) rotate(${rowRot}deg)`,
              background: INK,
              borderRadius: 3,
              borderBottom: `${height * 0.0035}px solid ${RED}`,
              padding: `${height * 0.0062}px ${height * 0.014}px`,
              boxShadow: SHADOW_HARD,
              display: "flex",
              alignItems: "center",
              columnGap: height * 0.011,
            }}
          >
            <div style={{ width: iconBox, height: iconBox, flexShrink: 0 }}>
              <Icon size={iconBox} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", rowGap: height * 0.0015 }}>
              <div
                style={{
                  fontFamily: FONT,
                  fontWeight: 900,
                  fontSize: labelPx,
                  letterSpacing: "-0.005em",
                  color: WHITE,
                  whiteSpace: "nowrap",
                  lineHeight: 1.04,
                }}
              >
                {row.label}
              </div>
              {row.sub && subVisible && (
                <div
                  style={{
                    opacity: subOp,
                    transform: `translateY(${subY}px)`,
                    fontFamily: FONT,
                    fontWeight: 900,
                    fontSize: subPx,
                    letterSpacing: "0.05em",
                    color: RED,
                    whiteSpace: "nowrap",
                    lineHeight: 1.05,
                  }}
                >
                  {row.sub}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// Icon-Chip (wie Video 6): schwarzer Grund, rote Unterkante
// ============================================================

const IconChip: React.FC<{
  beat: { start: number; end: number };
  offsetSec: number;
  heightPx: number;
  children: (t: number) => React.ReactNode;
}> = ({ beat, offsetSec, heightPx, children }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(beat, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.32);
  if (!visible) return null;

  const s = interpolate(inS, [0, 1], [0.55, 1]);

  return (
    <div
      style={{
        transform: `scale(${s})`,
        opacity: out,
        background: INK,
        borderRadius: 3,
        borderBottom: `${heightPx * 0.0045}px solid ${RED}`,
        padding: heightPx * 0.016,
        boxShadow: SHADOW_HARD,
      }}
    >
      {children(t)}
    </div>
  );
};

// Waage (wie Video 6): Zeiger pendelt sich ein
const WaageIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => {
  const needle = interpolate(t, [0.2, 1.4], [-70, 38], {
    ...CLAMP,
    easing: Easing.elastic(1.4),
  });
  return (
    <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
      <path d="M 24 30 Q 60 52 96 30" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
      <line x1="60" y1="44" x2="60" y2="56" stroke={WHITE} strokeWidth="7" />
      <rect x="22" y="56" width="76" height="46" rx="8" fill="none" stroke={WHITE} strokeWidth="7" />
      <circle cx="60" cy="79" r="15" fill="none" stroke={WHITE} strokeWidth="5" />
      <g transform={`rotate(${needle} 60 79)`}>
        <line x1="60" y1="79" x2="60" y2="67" stroke={RED} strokeWidth="5" strokeLinecap="round" />
      </g>
      <circle cx="60" cy="79" r="3.4" fill={RED} />
    </svg>
  );
};

// Hand: Handfläche mit Rühr-Bögen
const HandIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <rect x="36" y="54" width="42" height="38" rx="12" fill="none" stroke={WHITE} strokeWidth="7" />
    <line x1="44" y1="52" x2="44" y2="28" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    <line x1="56" y1="52" x2="56" y2="22" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    <line x1="68" y1="52" x2="68" y2="26" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    <line x1="79" y1="58" x2="94" y2="46" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    <path d="M 26 100 Q 44 112 62 102" fill="none" stroke={RED} strokeWidth="5" strokeLinecap="round" />
    <path d="M 58 108 Q 76 116 92 106" fill="none" stroke={RED} strokeWidth="5" strokeLinecap="round" opacity="0.7" />
  </svg>
);

// Maschine: Zahnrad, das ab strikeAt rot durchgestrichen wird
const MaschineIcon: React.FC<{ tAbs: number; size: number; strikeAt: number }> = ({ tAbs, size, strikeAt }) => {
  const { fps } = useVideoConfig();
  const tS = tAbs - strikeAt;
  const len = 96;
  const p1 = interpolate(tS, [0, 0.2], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const p2 = interpolate(tS, [0.12, 0.32], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const jolt = spring({ frame: Math.round(tS * fps), fps, config: { damping: 10, stiffness: 260, mass: 0.6 } });
  const rot = tS > 0 ? 0 : tAbs * 40; // Zahnrad dreht, bis das X es stoppt
  const shake = tS > 0 ? Math.max(0, 1 - tS * 3) * Math.sin(tS * 60) * 2.2 : 0;

  return (
    <svg
      viewBox="0 0 120 120"
      width={size}
      height={size}
      style={{ display: "block", transform: `translateX(${shake}px) scale(${1 - 0.06 * Math.max(0, jolt) * (tS > 0 ? 1 : 0)})` }}
    >
      <g transform={`rotate(${rot} 60 64)`}>
        <circle cx="60" cy="64" r="26" fill="none" stroke={WHITE} strokeWidth="7" />
        {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => (
          <line
            key={a}
            x1={60 + 26 * Math.cos((a * Math.PI) / 180)}
            y1={64 + 26 * Math.sin((a * Math.PI) / 180)}
            x2={60 + 36 * Math.cos((a * Math.PI) / 180)}
            y2={64 + 36 * Math.sin((a * Math.PI) / 180)}
            stroke={WHITE}
            strokeWidth="8"
            strokeLinecap="round"
          />
        ))}
        <circle cx="60" cy="64" r="9" fill="none" stroke={WHITE} strokeWidth="6" />
      </g>
      <line
        x1="24" y1="28" x2="96" y2="100"
        stroke={RED} strokeWidth="11" strokeLinecap="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - p1)}
      />
      <line
        x1="96" y1="28" x2="24" y2="100"
        stroke={RED} strokeWidth="11" strokeLinecap="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - p2)}
      />
    </svg>
  );
};

// HAND ✓ vs. MASCHINE ✗
const VSBeat: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.vs, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.3);
  if (!visible) return null;

  const tAbs = t + BEATS.vs.start;
  const iconSize = height * 0.082;
  const pad = height * 0.015;

  // roter Ring pulst um die Hand auf „von Hand"
  const tP = tAbs - BEATS.vsHandPulseAt;
  const ringOp = tP >= 0 ? interpolate(tP, [0, 0.12, 0.9], [0, 1, 0.55], CLAMP) : 0;
  const ringS = tP >= 0 ? interpolate(tP, [0, 0.3], [0.86, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) }) : 0.86;

  const chip = (child: React.ReactNode, ring: boolean) => (
    <div
      style={{
        position: "relative",
        background: INK,
        borderRadius: 3,
        borderBottom: `${height * 0.0045}px solid ${RED}`,
        padding: pad,
        boxShadow: SHADOW_HARD,
      }}
    >
      {ring && (
        <div
          style={{
            position: "absolute",
            inset: -height * 0.0045,
            border: `${height * 0.0038}px solid ${RED}`,
            borderRadius: 5,
            opacity: ringOp,
            transform: `scale(${ringS})`,
          }}
        />
      )}
      {child}
    </div>
  );

  return (
    <div
      style={{
        transform: `scale(${interpolate(inS, [0, 1], [0.6, 1])})`,
        opacity: out,
        display: "flex",
        alignItems: "center",
        gap: height * 0.012,
      }}
    >
      {chip(<HandIcon size={iconSize} />, true)}
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: height * 0.019,
          color: WHITE,
          textShadow: HALO,
        }}
      >
        VS
      </div>
      {chip(<MaschineIcon tAbs={tAbs} size={iconSize} strikeAt={BEATS.vsStrikeAt} />, false)}
    </div>
  );
};

// 5-MIN-Timer: Uhr mit rotem Zeiger (konstante Fahrt) + Label
const TimerBeat: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.timer, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.32);
  if (!visible) return null;

  const size = height * 0.082;
  const hand = Math.max(0, t) * 96; // Grad/s, konstant

  return (
    <div
      style={{
        transform: `scale(${interpolate(inS, [0, 1], [0.55, 1])})`,
        opacity: out,
        background: INK,
        borderRadius: 3,
        borderBottom: `${height * 0.0045}px solid ${RED}`,
        padding: `${height * 0.014}px ${height * 0.02}px`,
        boxShadow: SHADOW_HARD,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: height * 0.006,
      }}
    >
      <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
        <circle cx="60" cy="62" r="40" fill="none" stroke={WHITE} strokeWidth="7" />
        <line x1="52" y1="16" x2="68" y2="16" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
        {[0, 90, 180, 270].map((a) => (
          <line
            key={a}
            x1={60 + 33 * Math.cos(((a - 90) * Math.PI) / 180)}
            y1={62 + 33 * Math.sin(((a - 90) * Math.PI) / 180)}
            x2={60 + 39 * Math.cos(((a - 90) * Math.PI) / 180)}
            y2={62 + 39 * Math.sin(((a - 90) * Math.PI) / 180)}
            stroke={WHITE}
            strokeWidth="5"
            strokeLinecap="round"
          />
        ))}
        <g transform={`rotate(${hand} 60 62)`}>
          <line x1="60" y1="62" x2="60" y2="34" stroke={RED} strokeWidth="6" strokeLinecap="round" />
        </g>
        <circle cx="60" cy="62" r="5" fill={RED} />
      </svg>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: height * 0.021, lineHeight: 1, color: WHITE, whiteSpace: "nowrap" }}>
        <span style={{ color: RED }}>5</span> MIN
      </div>
    </div>
  );
};

// Hände waschen: Hahn + Hand + fallende Tropfen
const WaschIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <path d="M 26 40 H 62 Q 72 40 72 50 V 56" fill="none" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    <line x1="26" y1="30" x2="26" y2="50" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
    {[0, 1, 2].map((i) => {
      const cycle = (t * 0.9 + i * 0.33) % 1;
      const y = 62 + cycle * 26;
      const op = Math.sin(Math.PI * cycle);
      return <circle key={i} cx={72} cy={y} r="4" fill={RED} opacity={op} />;
    })}
    <path d="M 40 100 Q 62 112 88 98" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
    <path d="M 44 92 Q 60 100 78 92" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" opacity="0.65" />
  </svg>
);

// Desinfizieren: Sprühflasche + roter Nebel
const SprayIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <rect x="56" y="56" width="30" height="44" rx="7" fill="none" stroke={WHITE} strokeWidth="7" />
    <path d="M 60 52 V 44 H 84 V 52" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
    <path d="M 60 44 H 44 L 48 56" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="44" y1="44" x2="38" y2="44" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
    {[0, 1, 2].map((i) => {
      const cycle = (t * 1.1 + i * 0.33) % 1;
      const x = 34 - cycle * 16;
      const y = 40 - i * 7 + cycle * (i - 1) * 6;
      const op = Math.sin(Math.PI * cycle) * 0.9;
      return <circle key={i} cx={x} cy={y} r={3 + cycle * 2} fill={RED} opacity={op} />;
    })}
  </svg>
);

// ============================================================
// Becher-Chips 250 g / 125 g (+ Demo-Callback)
// ============================================================

const BecherIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
    <path d="M 34 42 L 41 96 Q 42 101 47 101 H 73 Q 78 101 79 96 L 86 42" fill="none" stroke={WHITE} strokeWidth="7" />
    <ellipse cx="60" cy="38" rx="30" ry="8" fill="none" stroke={RED} strokeWidth="6" />
  </svg>
);

const GramChip: React.FC<{
  label: string;
  enterAt: number;
  beat: { start: number; end: number };
  offsetSec: number;
  height: number;
  pulseAt?: number;
}> = ({ label, enterAt, beat, offsetSec, height, pulseAt }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(beat, offsetSec);
  const { out, visible } = envelope(t, dur, fps, 0.3);
  if (!visible) return null;

  const tAbs = t + beat.start;
  const tIn = tAbs - enterAt;
  if (tIn < -0.05) return null;

  const inS = spring({ frame: Math.round(tIn * fps), fps, config: { damping: 13, stiffness: 220, mass: 0.8 } });
  const tP = pulseAt !== undefined ? tAbs - pulseAt : -1;
  const pulse = tP >= 0 ? 1 + 0.09 * Math.max(0, spring({ frame: Math.round(tP * fps), fps, config: { damping: 9, stiffness: 230, mass: 0.6 } }) - Math.max(0, (tP - 0.3) * 2.6)) : 1;

  return (
    <div
      style={{
        transform: `scale(${interpolate(inS, [0, 1], [0.55, 1]) * pulse})`,
        opacity: out * interpolate(tIn, [0, 0.1], [0, 1], CLAMP),
        background: INK,
        borderRadius: 3,
        borderBottom: `${height * 0.0045}px solid ${RED}`,
        padding: `${height * 0.012}px ${height * 0.018}px`,
        boxShadow: SHADOW_HARD,
        display: "flex",
        alignItems: "center",
        columnGap: height * 0.008,
      }}
    >
      <BecherIcon size={height * 0.062} />
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: height * 0.026, lineHeight: 1, color: WHITE, whiteSpace: "nowrap" }}>
        {label}
      </div>
    </div>
  );
};

// ============================================================
// Marken-Outro (wie Video 1/6)
// ============================================================

const Hero: React.FC<{ offsetSec: number; height: number; width: number; showLogo: boolean }> = ({
  offsetSec,
  height,
  width,
  showLogo,
}) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.hero, offsetSec);
  if (!showLogo || t < -0.05 || t > dur + 0.05) return null;

  const rise = spring({ frame: Math.round(t * fps), fps, config: { damping: 18, stiffness: 150, mass: 1 } });
  const groupY = interpolate(rise, [0, 1], [height * 0.04, 0]);
  const op = interpolate(t, [0, 0.12, dur - 0.35, dur], [0, 1, 1, 0], CLAMP);
  const panelP = interpolate(t, [0, 0.38], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const logoS = spring({ frame: Math.round((t - 0.22) * fps), fps, config: { damping: 12, stiffness: 220, mass: 0.9 } });
  const claimOp = interpolate(t, [0.7, 1.05], [0, 1], CLAMP);
  const claimY = interpolate(t, [0.7, 1.05], [height * 0.012, 0], { ...CLAMP, easing: Easing.out(Easing.cubic) });

  return (
    <div
      style={{
        opacity: op,
        transform: `translateY(${groupY}px)`,
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: `${height * 0.024}px ${width * 0.06}px ${height * 0.022}px`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: INK,
          borderRadius: 3,
          borderTop: `${height * 0.005}px solid ${RED}`,
          transform: `scaleY(${panelP})`,
          transformOrigin: "50% 0%",
          boxShadow: "0 24px 60px rgba(0,0,0,0.55)",
        }}
      />
      <div
        style={{
          position: "relative",
          transform: `scale(${interpolate(Math.max(0, logoS), [0, 1], [0.6, 1])})`,
          opacity: interpolate(t, [0.22, 0.38], [0, 1], CLAMP),
        }}
      >
        <Img src={staticFile("clients/setzer/setzer-logo-rot.png")} style={{ width: width * 0.46, display: "block" }} />
      </div>
      <div
        style={{
          position: "relative",
          transform: `translateY(${claimY}px)`,
          opacity: claimOp,
          marginTop: height * 0.008,
        }}
      >
        <Img src={staticFile("clients/setzer/claim-weiss.png")} style={{ width: width * 0.38, display: "block" }} />
      </div>
    </div>
  );
};

// ============================================================
// Hauptkomposition
// ============================================================

export const SetzerFleischsalatZutaten: React.FC<SetzerFleischsalatZutatenProps> = ({
  fontSizePx,
  bandY,
  timeOffsetSec,
  showSubtitles,
  showAnimations,
  showLogoOutro,
  review,
}) => {
  const { fps, width, height } = useVideoConfig();
  const toF = (sec: number) => Math.round((sec + timeOffsetSec) * fps);
  const bandPx = Math.round(height * bandY);

  const row: React.CSSProperties = {
    position: "absolute",
    left: 0,
    right: 0,
    transform: "translateY(-50%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {showAnimations && (
          <>
            {/* 1 — Zutaten-Checkliste (Aufbau; Abhak-Reprise raus, 01.09.) */}
            <div style={{ ...row, top: Math.round(height * 0.65) }}>
              <ChecklistStack beat={BEATS.checklistBuild} offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 3 — Waage (alles abgewogen) */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <IconChip beat={BEATS.waage} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <WaageIcon t={t} size={height * 0.085} />}
              </IconChip>
            </div>

            {/* 4 — HAND vs. MASCHINE */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <VSBeat offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 5 — 5-MIN-Timer */}
            <div style={{ ...row, top: Math.round(height * 0.55) }}>
              <TimerBeat offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 6 — Hände waschen / desinfizieren */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <IconChip beat={BEATS.wasch} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <WaschIcon t={t} size={height * 0.088} />}
              </IconChip>
            </div>
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <IconChip beat={BEATS.spray} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <SprayIcon t={t} size={height * 0.088} />}
              </IconChip>
            </div>

            {/* 7 — 250 g / 125 g */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <div style={{ display: "flex", alignItems: "center", gap: height * 0.012 }}>
                <GramChip label="250 g" enterAt={BEATS.gram250At} beat={BEATS.grams} offsetSec={timeOffsetSec} height={height} />
                <GramChip label="125 g" enterAt={BEATS.gram125At} beat={BEATS.grams} offsetSec={timeOffsetSec} height={height} />
              </div>
            </div>

            {/* 8 — Demo-Callback 250 g (Puls auf „250 Gramm raus") */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <GramChip
                label="250 g"
                enterAt={BEATS.demo.start + 0.05}
                beat={BEATS.demo}
                offsetSec={timeOffsetSec}
                height={height}
                pulseAt={BEATS.demoPulseAt}
              />
            </div>

            {/* 9 — Marken-Outro */}
            <div style={{ ...row, top: Math.round(height * 0.62) }}>
              <Hero offsetSec={timeOffsetSec} height={height} width={width} showLogo={showLogoOutro} />
            </div>
          </>
        )}

        {showSubtitles && (
          <div
            style={{
              position: "absolute",
              left: width * 0.06,
              right: width * 0.06,
              top: bandPx,
              transform: "translateY(-50%)",
              display: "flex",
              justifyContent: "center",
            }}
          >
            {PAGES.map((page, i) => (
              <Sequence
                key={i}
                from={toF(page.startSec)}
                durationInFrames={Math.max(1, toF(page.endSec) - toF(page.startSec))}
                name={`UT ${String(i + 1).padStart(2, "0")} · ${page.lines[0].map((x) => x.text).join(" ")}`}
                layout="none"
              >
                <div style={{ position: "absolute", left: 0, right: 0, display: "flex", justifyContent: "center" }}>
                  <PageView page={page} size={fontSizePx} />
                </div>
              </Sequence>
            ))}
          </div>
        )}

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
