// ============================================================
// Setzer — Video 6 „Pfefferbeisser" (Prozess-Reel)
// Untertitel + Animationen als transparentes Alpha-Overlay.
// 1080×1920 (9:16), 30 fps (Kundenwunsch 28.08.), t = 0 ist der erste
// Frame des Schnitts. Alle Zeiten liegen in Sekunden — die Framerate
// ist frei umstellbar.
//
// Design-System wie Video 1 (nach Kunden-Feedback 25./26.08.):
//   rot–schwarz (#E30613 auf #0D0802), Iconset-Stil „schwarzer Grund,
//   Icon weiß, Highlights rot", Arial Black Versalien, Script „Have
//   Heart One", Logos nur einfarbig, offizielles Shop-Logo-SVG,
//   offizieller Claim-Vektor.
//
// Sieben Beats, je eine eigene Bewegungsart: Chip-Kaskade · Waage ·
// Vermengen-Rotor · Räucher-Icon · TROCKNEN⇄RAUCHEN-Wechsel ·
// Shop-Logo-Kasten · Marken-Outro.
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
import { BEATS, DURATION_SEC, PAGES, TOGGLE_WORDS } from "./captions";
import type { CaptionPage, CaptionWord } from "./captions";
import brandJson from "../../brand.json";

const ci = loadBrand("setzer", brandJson as any);

const RED = ci.colors.primary;      // #E30613
const INK = ci.colors.secondary;    // #0D0802
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

// --- Zeit-Helfer (wie Video 1) ---

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

// --- Schema ---

export const setzerPfefferbeisserSchema = projectPropsSchema.extend({
  fontSizePx: z.number().min(30).max(120).step(1).describe("Untertitel-Schriftgrad"),
  bandY: z.number().min(0.4).max(0.85).step(0.005).describe("Untertitelband, Mitte (Anteil Höhe)"),
  timeOffsetSec: z.number().min(-3).max(3).step(0.02).describe("Zeit-Offset zum Ausrichten aufs Footage"),
  showSubtitles: z.boolean().describe("Untertitel einblenden"),
  showAnimations: z.boolean().describe("Animationen einblenden"),
  showLogoOutro: z.boolean().describe("Marken-Outro (Logo + Claim)"),
});

export type SetzerPfefferbeisserProps = z.infer<typeof setzerPfefferbeisserSchema>;

export const setzerPfefferbeisserDefaults: SetzerPfefferbeisserProps = {
  format: "portrait",
  fps: 30,
  durationInSeconds: DURATION_SEC,
  transparent: true,
  fontSizePx: 52,
  bandY: 0.665,
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
// Untertitel (identische Mechanik wie Video 1)
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
  const opacity = interpolate(t, [0, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
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
  const fadeOut = interpolate(frame, [durF - 4, durF - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
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
// Beat 1 — Intro-Kaskade SCHULTER / SCHLEGEL / PFEFFERBEISSER
// ============================================================

const CascadeChip: React.FC<{
  label: string;
  filled: boolean;
  from: "left" | "right";
  beat: { start: number; end: number };
  offsetSec: number;
  size: number;
}> = ({ label, filled, from, beat, offsetSec, size }) => {
  const { fps, width } = useVideoConfig();
  const { t, dur } = useBeat(beat, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.28);
  if (!visible) return null;

  const dir = from === "left" ? -1 : 1;
  const x = interpolate(inS, [0, 1], [dir * width * 0.75, 0]);
  const rot = interpolate(inS, [0, 1], [dir * 9, 0]);

  return (
    <div
      style={{
        transform: `translateX(${x}px) rotate(${rot}deg)`,
        opacity: out,
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: size,
        letterSpacing: "-0.01em",
        color: WHITE,
        background: filled ? RED : INK,
        border: filled ? "none" : `${size * 0.055}px solid ${RED}`,
        padding: `${size * 0.2}px ${size * 0.42}px ${size * 0.26}px`,
        borderRadius: 3,
        boxShadow: SHADOW_HARD,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </div>
  );
};

// ============================================================
// Icon-Chip: schwarzer Grund, weißes Icon, rotes Highlight
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

// Waage: Zeiger pendelt sich auf einen Wert ein
const WaageIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => {
  const needle = interpolate(t, [0.2, 1.4], [-70, 38], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.elastic(1.4),
  });
  return (
    <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
      {/* Schale */}
      <path d="M 24 30 Q 60 52 96 30" fill="none" stroke={WHITE} strokeWidth="7" strokeLinecap="round" />
      <line x1="60" y1="44" x2="60" y2="56" stroke={WHITE} strokeWidth="7" />
      {/* Korpus */}
      <rect x="22" y="56" width="76" height="46" rx="8" fill="none" stroke={WHITE} strokeWidth="7" />
      {/* Skala */}
      <circle cx="60" cy="79" r="15" fill="none" stroke={WHITE} strokeWidth="5" />
      <g transform={`rotate(${needle} 60 79)`}>
        <line x1="60" y1="79" x2="60" y2="67" stroke={RED} strokeWidth="5" strokeLinecap="round" />
      </g>
      <circle cx="60" cy="79" r="3.4" fill={RED} />
    </svg>
  );
};

// Vermengen: zwei Pfeilbögen rotieren
const MixerIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => {
  const rot = t * 160;
  return (
    <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: "block" }}>
      <g transform={`rotate(${rot} 60 60)`}>
        <path d="M 60 18 A 42 42 0 0 1 102 60" fill="none" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
        <path d="M 60 102 A 42 42 0 0 1 18 60" fill="none" stroke={WHITE} strokeWidth="8" strokeLinecap="round" />
        <polygon points="102,48 114,64 92,64" fill={RED} />
        <polygon points="18,72 6,56 28,56" fill={RED} />
      </g>
      <circle cx="60" cy="60" r="7" fill={RED} />
    </svg>
  );
};

// Räuchern: Buchenscheite + Flamme + aufsteigender Rauch
const RauchIcon: React.FC<{ t: number; size: number }> = ({ t, size }) => {
  const flicker = 1 + Math.sin(t * 9) * 0.06;
  return (
    <svg viewBox="0 0 130 150" width={(size * 130) / 150} height={size} style={{ display: "block" }}>
      {/* Rauch: drei Schwaden, die im Loop aufsteigen */}
      {[0, 1, 2].map((i) => {
        const cycle = (t * 0.55 + i * 0.33) % 1;
        const y = 66 - cycle * 46;
        const op = Math.sin(Math.PI * cycle) * 0.85;
        return (
          <path
            key={i}
            d={`M ${46 + i * 20} ${y} c -9 -11 9 -18 0 -30`}
            fill="none"
            stroke={WHITE}
            strokeWidth="7"
            strokeLinecap="round"
            opacity={op}
          />
        );
      })}
      {/* Flamme (rotes Highlight) */}
      <g transform={`translate(65 96) scale(${flicker}) translate(-65 -96)`}>
        <path
          d="M 65 74 C 74 84 79 92 74 102 C 71 108 59 108 56 102 C 51 92 56 84 65 74 Z"
          fill={RED}
        />
      </g>
      {/* zwei gekreuzte Scheite */}
      <g stroke={WHITE} strokeWidth="8" strokeLinecap="round">
        <line x1="30" y1="112" x2="100" y2="132" />
        <line x1="100" y1="112" x2="30" y2="132" />
      </g>
    </svg>
  );
};

// ============================================================
// Beat 5 — TROCKNEN ⇄ RAUCHEN (aktiv wechselt auf Wortzeit)
// ============================================================

const ToggleBeat: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.toggle, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.3);
  if (!visible) return null;

  const tAbs = t + BEATS.toggle.start;
  let active: "TROCKNEN" | "RAUCHEN" | null = null;
  let lastSwitch = -10;
  for (const wrd of TOGGLE_WORDS) {
    if (tAbs >= wrd.atSec) {
      active = wrd.word;
      lastSwitch = wrd.atSec;
    }
  }
  // kleiner Puls bei jedem Wechsel
  const pulse = 1 + Math.max(0, 0.12 - (tAbs - lastSwitch) * 0.7);

  const size = height * 0.028;
  const chip = (label: "TROCKNEN" | "RAUCHEN") => {
    const on = active === label;
    return (
      <div
        style={{
          transform: `scale(${on ? pulse : 1})`,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size,
          color: WHITE,
          background: on ? RED : INK,
          border: on ? "none" : `${size * 0.055}px solid ${RED}`,
          opacity: on ? 1 : 0.75,
          padding: `${size * 0.22}px ${size * 0.46}px ${size * 0.28}px`,
          borderRadius: 3,
          boxShadow: SHADOW_HARD,
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </div>
    );
  };

  return (
    <div
      style={{
        transform: `scale(${interpolate(inS, [0, 1], [0.6, 1])})`,
        opacity: out,
        display: "flex",
        alignItems: "center",
        gap: height * 0.011,
      }}
    >
      {chip("TROCKNEN")}
      <svg width={size * 1.1} height={size * 1.1} viewBox="0 0 40 40">
        <path d="M 8 14 H 28 M 22 6 L 30 14 L 22 22" fill="none" stroke={WHITE} strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M 32 26 H 12 M 18 18 L 10 26 L 18 34" fill="none" stroke={WHITE} strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {chip("RAUCHEN")}
    </div>
  );
};

// ============================================================
// Beat 6 — Shop-Logo-Kasten · Beat 7 — Marken-Outro (wie Video 1)
// ============================================================

const ShopsBox: React.FC<{ offsetSec: number; height: number; width: number }> = ({
  offsetSec,
  height,
  width,
}) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.shops, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.3);
  if (!visible) return null;

  const s = interpolate(inS, [0, 1], [0.72, 1]);
  const pad = height * 0.014;

  return (
    <div
      style={{
        transform: `scale(${s})`,
        opacity: out,
        background: INK,
        borderRadius: 3,
        borderBottom: `${height * 0.004}px solid ${RED}`,
        padding: `${pad}px ${pad * 1.5}px`,
        boxShadow: SHADOW_HARD,
      }}
    >
      <Img src={staticFile("clients/setzer/shop-logo.svg")} style={{ width: width * 0.42, display: "block" }} />
    </div>
  );
};

const Hero: React.FC<{ offsetSec: number; height: number; width: number; showLogo: boolean }> = ({
  offsetSec,
  height,
  width,
  showLogo,
}) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.hero, offsetSec);
  if (!showLogo || t < -0.05 || t > dur + 0.05) return null;

  const ease = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const rise = spring({ frame: Math.round(t * fps), fps, config: { damping: 18, stiffness: 150, mass: 1 } });
  const groupY = interpolate(rise, [0, 1], [height * 0.04, 0]);
  const op = interpolate(t, [0, 0.12, dur - 0.35, dur], [0, 1, 1, 0], ease);
  const panelP = interpolate(t, [0, 0.38], [0, 1], { ...ease, easing: Easing.out(Easing.cubic) });
  const logoS = spring({ frame: Math.round((t - 0.22) * fps), fps, config: { damping: 12, stiffness: 220, mass: 0.9 } });
  const claimOp = interpolate(t, [0.7, 1.05], [0, 1], ease);
  const claimY = interpolate(t, [0.7, 1.05], [height * 0.012, 0], { ...ease, easing: Easing.out(Easing.cubic) });

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
          opacity: interpolate(t, [0.22, 0.38], [0, 1], ease),
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

export const SetzerPfefferbeisser: React.FC<SetzerPfefferbeisserProps> = ({
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
            {/* 1 — Intro-Kaskade */}
            <div style={{ ...row, top: Math.round(height * 0.565) }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: height * 0.011 }}>
                <CascadeChip label="SCHULTER" filled={false} from="left" beat={BEATS.chipSchulter} offsetSec={timeOffsetSec} size={height * 0.032} />
                <CascadeChip label="SCHLEGEL" filled={false} from="right" beat={BEATS.chipSchlegel} offsetSec={timeOffsetSec} size={height * 0.032} />
                <CascadeChip label="PFEFFERBEISSER" filled from="left" beat={BEATS.chipTitel} offsetSec={timeOffsetSec} size={height * 0.04} />
              </div>
            </div>

            {/* 2 — Waage */}
            <div style={{ ...row, top: Math.round(height * 0.55) }}>
              <IconChip beat={BEATS.waage} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <WaageIcon t={t} size={height * 0.085} />}
              </IconChip>
            </div>

            {/* 3 — Vermengen */}
            <div style={{ ...row, top: Math.round(height * 0.55) }}>
              <IconChip beat={BEATS.mixer} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <MixerIcon t={t} size={height * 0.082} />}
              </IconChip>
            </div>

            {/* 4 — Räuchern */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <IconChip beat={BEATS.rauch} offsetSec={timeOffsetSec} heightPx={height}>
                {(t) => <RauchIcon t={t} size={height * 0.1} />}
              </IconChip>
            </div>

            {/* 5 — TROCKNEN ⇄ RAUCHEN */}
            <div style={{ ...row, top: Math.round(height * 0.56) }}>
              <ToggleBeat offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 6 — 24/7 Shop-Logo */}
            <div style={{ ...row, top: Math.round(height * 0.55) }}>
              <ShopsBox offsetSec={timeOffsetSec} height={height} width={width} />
            </div>

            {/* 7 — Marken-Outro */}
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
