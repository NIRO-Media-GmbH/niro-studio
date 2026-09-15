// ============================================================
// Setzer — „Unterschied Fleischkäse vs. Leberkäse"
// Untertitel + Animationen als transparentes Alpha-Overlay.
// 1080×1920 (9:16), 24 fps, t = 0 ist der erste Frame des Schnitts.
//
// CI direkt von landmetzgerei.de gelesen (Elementor-Kit post-6.css):
//   #E30613 Primary/Logo-Rot · #B9000B Accent · #0D0802 Secondary
//   #FFFAFA hell · Headlines Arial 900, Versalien, Radius 3 px
//
// Kunden-Feedback V1 (Michael, 25.08., Dropbox-Replay) eingearbeitet:
//   - Farbkonzept ist „rot–schwarz", nicht „rot–weiß" → alle hellen
//     Flächen (Chips, Stempel, Badge, Blase) auf schwarzen Grund gedreht
//   - Zähler: zweistellige %-Werte kollidierten mit dem Ring → kleinere
//     Ziffern, größerer Kreis
//   - 24/7-Kasten nutzt jetzt das Shop-Logo (SVG vom Kunden), nicht Text
//   - Fleischkäs-Grafik im Iconset-Stil: schwarzer Grund, Icon weiß,
//     Highlights rot (siehe Fleischkaes.tsx)
//   - Setzer-Logo nur einfarbig (weiß/rot/schwarz) bzw. rot–schwarz —
//     nie mehr die rot-weiße Kontur-Fassung
//
// Zehn Beats, bewusst jeder in einer anderen Bewegungsart, damit sich
// nichts wiederholt: Chips gegeneinander · Stempel · Grenzwisch ·
// Linienzug · Type-Reveal · Zähler · Badge-Slide · Kasten mit Uhr ·
// gezeichneter Laib · Poll mit Sprechblase.
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
import { BEATS, DURATION_SEC, PAGES } from "./captions";
import type { CaptionPage, CaptionWord } from "./captions";
import brandJson from "../../brand.json";

const ci = loadBrand("setzer", brandJson as any);

const RED = ci.colors.primary;      // #E30613
const RED_DARK = ci.colors.accent;  // #B9000B
const INK = ci.colors.secondary;    // #0D0802
const PAPER = ci.colors.background; // #FFFAFA
const WHITE = "#FFFFFF";

// Die Website lädt keinen Webfont — Headlines sind Arial 900 in Versalien.
// Arial Black liegt auf dem Renderer unter /System/Library/Fonts/Supplemental.
const FONT = '"Arial Black", "Arial Bold", Arial, Helvetica, sans-serif';

// Marker-Script „Have Heart One" (Set Sail Studios) — die korrekte
// Kunden-Font (Michael, 26.08., Dropbox). Voller Zeichensatz inkl.
// Umlauten und Ziffern; die frühere „Have Heart Font.TTF" aus dem
// Kundenmaterial war ein Fake (intern DobiType, 62 Glyphen) und ist
// aus dem Motion-Client entfernt.
const SCRIPT_FACE = `@font-face {
  font-family: "Have Heart One Setzer";
  src: url("${staticFile("clients/setzer/fonts/HaveHeartOne.ttf")}") format("truetype");
}`;
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = SCRIPT_FACE;
  document.head.appendChild(style);
}
const SCRIPT = '"Have Heart One Setzer", "Bradley Hand", cursive';

const HALO = [
  "0 0 2px rgba(13,8,2,0.95)",
  "-3px -3px 0 rgba(13,8,2,0.72)",
  "3px -3px 0 rgba(13,8,2,0.72)",
  "-3px 3px 0 rgba(13,8,2,0.72)",
  "3px 3px 0 rgba(13,8,2,0.72)",
  "0 6px 22px rgba(13,8,2,0.55)",
].join(", ");

const SHADOW_HARD = "0 10px 0 rgba(13,8,2,0.28), 0 18px 44px rgba(13,8,2,0.34)";

// --- Zeit-Helfer ---

/** Sekunden seit Beat-Start (kann negativ sein) + 0..1-Fortschritt */
function useBeat(beat: { start: number; end: number }, offsetSec: number) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps - offsetSec - beat.start;
  const dur = beat.end - beat.start;
  return { t, p: Math.max(0, Math.min(1, t / dur)), dur };
}

/** Rein/Raus-Hüllkurve: springt rein, blendet am Ende weg */
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

export const setzerFleischkaeseSchema = projectPropsSchema.extend({
  fontSizePx: z.number().min(30).max(120).step(1).describe("Untertitel-Schriftgrad"),
  bandY: z.number().min(0.4).max(0.85).step(0.005).describe("Untertitelband, Mitte (Anteil Höhe)"),
  timeOffsetSec: z.number().min(-3).max(3).step(0.02).describe("Zeit-Offset zum Ausrichten aufs Footage"),
  showSubtitles: z.boolean().describe("Untertitel einblenden"),
  showAnimations: z.boolean().describe("Animationen einblenden"),
  showLogoOutro: z.boolean().describe("Setzer-Logo im Hero-Moment"),
  showHohenlohe: z.boolean().describe("Hohenlohe-Badge (Freigabe Volker offen)"),
});

export type SetzerFleischkaeseProps = z.infer<typeof setzerFleischkaeseSchema>;

export const setzerFleischkaeseDefaults: SetzerFleischkaeseProps = {
  format: "portrait",
  fps: 24,
  durationInSeconds: DURATION_SEC,
  transparent: true,
  fontSizePx: 52,
  bandY: 0.665,
  timeOffsetSec: 0,
  showSubtitles: true,
  showAnimations: true,
  showLogoOutro: true,
  showHohenlohe: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // Nico steht mittig, Kopf im oberen Drittel
    faceZone: { top: 0.06, bottom: 0.46, left: 0.16, right: 0.84 },
    guideOpacity: 0.35,
  },
};

// ============================================================
// Untertitel
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
    // Akzentwort sitzt auf einem roten Kasten — Logo-Rot, Radius 3 wie im Web
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
          boxShadow: `0 ${size * 0.09}px 0 ${RED_DARK}, 0 ${size * 0.16}px ${size * 0.4}px rgba(13,8,2,0.42)`,
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

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: size * 0.26,
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: size,
        lineHeight: 1.05,
        letterSpacing: "-0.005em",
        textAlign: "center",
        opacity: fadeOut,
      }}
    >
      {page.lines.map((line, li) => {
        // Eine Zeile kommt als Ganzes. Wortweise Einblenden würde die
        // Zeile beim Wachsen aus der Mitte schieben und halb aufgebaute,
        // linksbündige Zwischenzustände zeigen.
        const lineStart = Math.min(...line.map((x) => x.startSec));
        return (
          <div key={li} style={{ display: "flex", columnGap: "0.26em", alignItems: "baseline" }}>
            {line.map((word, wi) => (
              <WordView
                key={wi}
                word={word}
                startSec={lineStart + wi / 24}
                pageStartSec={page.startSec}
                size={size}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// Beat 1 — LEBERKÄS vs. FLEISCHKÄS
// ============================================================

const Chip: React.FC<{
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

  // rot–schwarz: gefüllt = Rot, ungefüllt = Schwarz mit roter Kante
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

const VsBadge: React.FC<{ offsetSec: number; size: number }> = ({ offsetSec, size }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.vsBadge, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.28);
  if (!visible) return null;

  const s = interpolate(inS, [0, 1], [0.2, 1]);
  const rot = interpolate(inS, [0, 1], [-140, -8]);

  return (
    <div
      style={{
        position: "absolute",
        transform: `scale(${s}) rotate(${rot}deg)`,
        opacity: out,
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: size,
        color: WHITE,
        background: INK,
        width: size * 2,
        height: size * 2,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `${size * 0.14}px solid ${RED}`,
        boxShadow: SHADOW_HARD,
      }}
    >
      VS
    </div>
  );
};

// ============================================================
// Beat 2 — Metzger-Stempel
// ============================================================

const Stempel: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.stempel, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  // harter Aufschlag: von groß und schräg auf Endgröße, mit Rückprall
  const hit = spring({ frame: Math.round(t * fps), fps, config: { damping: 11, stiffness: 320, mass: 1.1 } });
  const s = interpolate(hit, [0, 1], [1.9, 1]);
  const rot = interpolate(hit, [0, 1], [-22, -7]);
  const op = interpolate(t, [0, 0.06, dur - 0.26, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Staubring beim Aufschlag
  const ring = interpolate(t, [0.1, 0.5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const size = height * 0.062;

  return (
    <div style={{ position: "relative", opacity: op, transform: `scale(${s}) rotate(${rot}deg)` }}>
      {ring > 0 && ring < 1 && (
        <div
          style={{
            position: "absolute",
            inset: `${-height * 0.022}px`,
            border: `${height * 0.005}px solid ${RED}`,
            borderRadius: 6,
            opacity: (1 - ring) * 0.7,
            transform: `scale(${1 + ring * 0.45})`,
          }}
        />
      )}
      {/* Doppelrahmen aus zwei echten Kästen — `outline` erzeugt im
          Alpha-Render eine Haarlinie an der Innenkante.
          rot–schwarz: schwarzer Grund, weiße Type, rote Rahmen. */}
      <div
        style={{
          border: `${size * 0.055}px solid ${RED}`,
          borderRadius: 3,
          padding: `${size * 0.075}px`,
          background: INK,
          boxShadow: "0 16px 44px rgba(0,0,0,0.55)",
        }}
      >
        <div
          style={{
            border: `${size * 0.11}px solid ${RED}`,
            borderRadius: 2,
            padding: `${size * 0.2}px ${size * 0.42}px ${size * 0.26}px`,
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: size,
            letterSpacing: "0.02em",
            color: WHITE,
            textAlign: "center",
            lineHeight: 0.98,
          }}
        >
          KEINE
          <br />
          LEBER
        </div>
      </div>
    </div>
  );
};

// ============================================================
// Beat 3 — Grenze verlassen (rein grafisch, kein Text)
// ============================================================

// Bayerische Rautenflagge — bewusste Ausnahme vom rot–schwarz-Konzept:
// das Weiß-Blau IST hier die Aussage („sobald man Bayern verlässt").
// Dünne schwarze Kontur, damit sie auf hellem Footage hält.
const BAYERN_BLAU = "#0098D4";

const BayernFlag: React.FC<{ t: number; heightPx: number }> = ({ t, heightPx }) => {
  const { fps } = useVideoConfig();
  // entrollt sich vom Mast, exakt wenn „Bayern" fällt (0,12 s nach Beat-Start)
  const pop = Math.max(
    0,
    spring({ frame: Math.round((t - 0.12) * fps), fps, config: { damping: 13, stiffness: 210, mass: 0.9 } })
  );
  const wave = Math.sin(t * 5.2) * 3.2;

  // Rautenraster (wird um -12° gedreht und auf die Fahne geclippt)
  const CW = 30;
  const CH = 19;
  const diamonds: React.ReactNode[] = [];
  for (let ry = 0; ry < 9; ry++) {
    for (let cx = 0; cx < 10; cx++) {
      if ((ry + cx) % 2 === 1) continue;
      const x = -20 + cx * CW;
      const y = -14 + ry * CH;
      diamonds.push(
        <polygon
          key={`${ry}-${cx}`}
          points={`${x},${y - CH} ${x + CW / 2},${y} ${x},${y + CH} ${x - CW / 2},${y}`}
          fill={BAYERN_BLAU}
        />
      );
    }
  }

  return (
    <svg
      viewBox="0 0 200 215"
      width={(heightPx * 200) / 215}
      height={heightPx}
      style={{ overflow: "visible", display: "block" }}
    >
      <defs>
        <clipPath id="szBayern">
          <rect x="0" y="0" width="160" height="98" rx="4" />
        </clipPath>
      </defs>
      {/* Mast mit roter Spitze */}
      <line x1="14" y1="18" x2="14" y2="207" stroke="#FFFFFF" strokeWidth="9" strokeLinecap="round" />
      <circle cx="14" cy="12" r="7" fill="#E30613" />
      {/* Fahne: entrollt sich vom Mast, leichtes Wehen um die Mastkante */}
      <g transform={`translate(18 16) scale(${pop} 1) skewY(${wave})`}>
        <g clipPath="url(#szBayern)">
          <rect x="0" y="0" width="160" height="98" fill="#FFFFFF" />
          <g transform="rotate(-12 80 49)">{diamonds}</g>
        </g>
        <rect x="0" y="0" width="160" height="98" rx="4" fill="none" stroke="#0D0802" strokeWidth="6" />
      </g>
    </svg>
  );
};

const Grenze: React.FC<{ offsetSec: number }> = ({ offsetSec }) => {
  const { width, height } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.grenze, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const wipe = interpolate(t, [0, 0.75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const arrow = interpolate(t, [0.5, 1.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const op = interpolate(t, [0, 0.15, dur - 0.35, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Innerhalb der Safe Zone bleiben — sonst hängt der erste Strich
  // angeschnitten am Bildrand.
  const lineW = width * 0.76;
  const dash = height * 0.016;

  return (
    <div style={{ position: "relative", width: lineW, height: height * 0.06, opacity: op }}>
      {/* Bayern-Flagge am linken Ende — der Pfeil zieht von ihr weg */}
      <div
        style={{
          position: "absolute",
          left: lineW * 0.015,
          top: "50%",
          transform: "translateY(-100%)",
        }}
      >
        <BayernFlag t={t} heightPx={height * 0.095} />
      </div>
      {/* gestrichelte Grenze */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: 0,
          width: lineW * wipe,
          height: dash * 0.42,
          background: `repeating-linear-gradient(90deg, ${PAPER} 0 ${dash}px, transparent ${dash}px ${dash * 1.9}px)`,
          transform: "translateY(-50%)",
          filter: "drop-shadow(0 4px 12px rgba(13,8,2,0.6))",
        }}
      />
      {/* roter Pfeil zieht über die Grenze */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: interpolate(arrow, [0, 1], [lineW * 0.24, lineW * 0.9]),
          transform: `translate(-50%, -50%) scale(${interpolate(arrow, [0, 0.12, 1], [0, 1, 1])})`,
          width: 0,
          height: 0,
          borderTop: `${dash * 1.5}px solid transparent`,
          borderBottom: `${dash * 1.5}px solid transparent`,
          borderLeft: `${dash * 2.3}px solid ${RED}`,
          filter: "drop-shadow(0 6px 16px rgba(13,8,2,0.55))",
        }}
      />
    </div>
  );
};

// ============================================================
// Beat 4 — rote Linie zieht sich unter das Band
// ============================================================

const RegelLinie: React.FC<{ offsetSec: number; width: number; height: number }> = ({
  offsetSec,
  width,
  height,
}) => {
  const { t, dur } = useBeat(BEATS.regelLinie, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const grow = interpolate(t, [0, 1.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const op = interpolate(t, [0, 0.2, dur - 0.3, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: width * 0.7 * grow,
        height: height * 0.006,
        background: RED,
        borderRadius: 3,
        opacity: op,
        boxShadow: `0 0 ${height * 0.012}px rgba(227,6,19,0.6), 0 6px 18px rgba(13,8,2,0.5)`,
      }}
    />
  );
};

// ============================================================
// Beat 5 — FLEISCHKÄSE landet
// ============================================================

const Aufloesung: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.auflösung, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const land = spring({ frame: Math.round(t * fps), fps, config: { damping: 13, stiffness: 240, mass: 0.9 } });
  const s = interpolate(land, [0, 1], [1.55, 1]);
  const y = interpolate(land, [0, 1], [-height * 0.05, 0]);
  const bar = interpolate(t, [0.16, 0.52], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const op = interpolate(t, [0, 0.08, dur - 0.3, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Etikett-Look („Backofen Fleischkäse"): schwarzer Grund, weißes
  // Marker-Script, rote Kante.
  const size = height * 0.075;

  return (
    <div
      style={{
        position: "relative",
        opacity: op,
        transform: `translateY(${y}px) scale(${s})`,
        padding: `${size * 0.34}px ${size * 0.5}px ${size * 0.3}px`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: INK,
          borderRadius: 3,
          borderBottom: `${size * 0.06}px solid ${RED}`,
          transform: `scaleX(${bar})`,
          transformOrigin: "0% 50%",
          boxShadow: SHADOW_HARD,
        }}
      />
      <span
        style={{
          position: "relative",
          fontFamily: SCRIPT,
          fontSize: size,
          color: WHITE,
          whiteSpace: "nowrap",
          transform: "rotate(-3deg)",
          display: "inline-block",
        }}
      >
        Fleischkäse
      </span>
    </div>
  );
};

// ============================================================
// Beat 6 — Zähler 100 → 0
// ============================================================

const Zaehler: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.zaehler, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const pop = spring({ frame: Math.round(t * fps), fps, config: { damping: 16, stiffness: 200, mass: 0.8 } });
  const count = interpolate(t, [0.25, 1.25], [100, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const value = Math.round(count);
  // wenn die Null steht, gibt es einen kleinen Nachschlag
  const hit = interpolate(t, [1.25, 1.4], [1.14, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const op = interpolate(t, [0, 0.14, dur - 0.28, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Kreis größer, Ziffern kleiner: bei zweistelligen Werten (99–10 %)
  // kollidierte die Prozentzahl mit dem Ring (Kunden-Feedback 25.08.).
  // rot–schwarz: schwarzer Kreis, roter Ring, Zahl weiß, LEBER rot.
  const ringSize = height * 0.215;
  const num = height * 0.058;

  return (
    <div
      style={{
        opacity: op,
        transform: `scale(${interpolate(pop, [0, 1], [0.6, 1]) * hit})`,
        width: ringSize,
        height: ringSize,
        borderRadius: "50%",
        background: INK,
        border: `${height * 0.008}px solid ${RED}`,
        boxShadow: SHADOW_HARD,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT,
        fontWeight: 900,
        color: WHITE,
        lineHeight: 0.92,
      }}
    >
      <div style={{ fontSize: num, letterSpacing: "-0.02em", fontVariantNumeric: "tabular-nums" }}>
        {value}%
      </div>
      <div style={{ fontSize: num * 0.4, letterSpacing: "0.14em", marginTop: height * 0.006, color: RED }}>
        LEBER
      </div>
    </div>
  );
};

// ============================================================
// Beat 7 — Herkunfts-Badge
// ============================================================

const HohenloheBadge: React.FC<{ offsetSec: number; height: number; width: number }> = ({
  offsetSec,
  height,
  width,
}) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.hohenlohe, offsetSec);
  const { inS, out, visible } = envelope(t, dur, fps, 0.3);
  if (!visible) return null;

  const x = interpolate(inS, [0, 1], [-width * 0.7, 0]);
  const size = height * 0.026;

  // rot–schwarz. Ob „Hohenlohe" stehen darf, klärt Volker —
  // bis dahin per Prop `showHohenlohe` abschaltbar.
  return (
    <div
      style={{
        transform: `translateX(${x}px)`,
        opacity: out,
        display: "flex",
        alignItems: "center",
        gap: size * 0.5,
        background: INK,
        borderLeft: `${size * 0.5}px solid ${RED}`,
        padding: `${size * 0.42}px ${size * 0.8}px ${size * 0.46}px ${size * 0.6}px`,
        borderRadius: 3,
        boxShadow: SHADOW_HARD,
        fontFamily: FONT,
        fontWeight: 900,
      }}
    >
      <svg width={size * 1.15} height={size * 1.4} viewBox="0 0 24 30">
        <path
          d="M12 0C5.4 0 0 5.4 0 12c0 8.4 12 18 12 18s12-9.6 12-18C24 5.4 18.6 0 12 0z"
          fill={RED}
        />
        <circle cx="12" cy="11.6" r="4.4" fill={INK} />
      </svg>
      {/* Nur „HOHENLOHE" — „Region" steht schon im Untertitel,
          und Dopplung Animation/Untertitel ist gesperrt. */}
      <span style={{ fontSize: size, color: WHITE, letterSpacing: "0.02em" }}>HOHENLOHE</span>
    </div>
  );
};

// ============================================================
// Beat 8 — 24/7 Shops
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

  // Kundenwunsch 25.08.: das offizielle 24/7-Shop-Logo verwenden, nicht
  // Text + Uhr-Icon. Das SVG ist weiß/rot und braucht schwarzen Grund.
  const logoW = width * 0.42;
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
      <Img
        src={staticFile("clients/setzer/shop-logo.svg")}
        style={{ width: logoW, display: "block" }}
      />
    </div>
  );
};

// ============================================================
// Beat 9 — Hero: Setzer-Logo + Claim auf schwarzem Panel
// (Die gezeichnete Fleischkäs-Grafik ist auf Davids Wunsch vom
// 25.08. komplett raus — nur noch das Marken-Panel.)
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

  const ease = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

  const rise = spring({ frame: Math.round(t * fps), fps, config: { damping: 18, stiffness: 150, mass: 1 } });
  const groupY = interpolate(rise, [0, 1], [height * 0.04, 0]);
  const op = interpolate(t, [0, 0.12, dur - 0.4, dur], [0, 1, 1, 0], ease);

  // Panel klappt auf, Logo landet mit Nachdruck, Claim schreibt sich dazu
  const panelP = interpolate(t, [0, 0.38], [0, 1], { ...ease, easing: Easing.out(Easing.cubic) });
  const logoS = spring({ frame: Math.round((t - 0.25) * fps), fps, config: { damping: 12, stiffness: 220, mass: 0.9 } });
  const claimOp = interpolate(t, [0.85, 1.25], [0, 1], ease);
  const claimY = interpolate(t, [0.85, 1.25], [height * 0.012, 0], { ...ease, easing: Easing.out(Easing.cubic) });

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
      {/* Iconset-Stil: satter schwarzer Grund wie auf dem Etikett */}
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

      {/* Kunden-Original „Logo ohne hg.png" (einfarbig rot) — die
          rot-weiße Kontur-Version ist laut Kunde gesperrt.
          Rot auf Schwarz = Favicon-Look. */}
      <div
        style={{
          position: "relative",
          transform: `scale(${interpolate(Math.max(0, logoS), [0, 1], [0.6, 1])})`,
          opacity: interpolate(t, [0.25, 0.4], [0, 1], ease),
        }}
      >
        <Img
          src={staticFile("clients/setzer/setzer-logo-rot.png")}
          style={{ width: width * 0.46, display: "block" }}
        />
      </div>

      {/* Offizieller Claim als Kunden-Vektor (Setzer_CLAIM_WEISS.ai) —
          nicht mehr selbst gesetzt, die Font war laut Michael falsch. */}
      <div
        style={{
          position: "relative",
          transform: `translateY(${claimY}px)`,
          opacity: claimOp,
          marginTop: height * 0.008,
        }}
      >
        <Img
          src={staticFile("clients/setzer/claim-weiss.png")}
          style={{ width: width * 0.38, display: "block" }}
        />
      </div>
    </div>
  );
};

// ============================================================
// Beat 10 — Poll + Kommentar-Blase
// ============================================================

const PollChips: React.FC<{ offsetSec: number; height: number; width: number }> = ({
  offsetSec,
  height,
  width,
}) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.pollChips, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const size = height * 0.035;
  const op = interpolate(t, [0, 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const chip = (label: string, delay: number, filled: boolean) => {
    const s = spring({
      frame: Math.round((t - delay) * fps),
      fps,
      config: { damping: 14, stiffness: 230, mass: 0.8 },
    });
    // leichtes Wippen, sobald der Chip steht
    const wob = Math.sin(Math.max(0, t - delay - 0.4) * 5.2) * 1.4 * Math.max(0, 1 - (t - delay - 0.4) / 1.6);
    // rot–schwarz: eine Antwort rot, eine schwarz mit roter Kante
    return (
      <div
        style={{
          transform: `scale(${interpolate(s, [0, 1], [0.3, 1])}) rotate(${wob}deg)`,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size,
          color: WHITE,
          background: filled ? RED : INK,
          border: filled ? "none" : `${size * 0.055}px solid ${RED}`,
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

  // Gestapelt, nicht nebeneinander: zwei lange Wörter plus „ODER" sind
  // im 9:16 breiter als das Bild und wurden sonst beidseitig abgeschnitten.
  return (
    <div
      style={{
        opacity: op,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: height * 0.008,
      }}
    >
      {chip("FLEISCHKÄSE", 0, true)}
      <span
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size * 0.62,
          color: WHITE,
          textShadow: HALO,
          letterSpacing: "0.16em",
        }}
      >
        ODER
      </span>
      {chip("LEBERKÄSE", 0.42, false)}
    </div>
  );
};

const CommentBubble: React.FC<{ offsetSec: number; height: number }> = ({ offsetSec, height }) => {
  const { fps } = useVideoConfig();
  const { t, dur } = useBeat(BEATS.pollBubble, offsetSec);
  if (t < -0.05 || t > dur + 0.05) return null;

  const s = spring({ frame: Math.round(t * fps), fps, config: { damping: 15, stiffness: 220, mass: 0.8 } });
  const y = interpolate(s, [0, 1], [height * 0.045, 0]);
  const op = interpolate(t, [0, 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Klein genug, dass die Zeile samt Icon in die Safe Zone passt —
  // bei 0,027 lief sie über die volle Bildbreite.
  const size = height * 0.02;
  // Cursor blinkt im Eingabefeld
  const caret = Math.floor(t * 2.4) % 2 === 0 ? 1 : 0.15;

  return (
    <div style={{ opacity: op, transform: `translateY(${y}px)`, position: "relative" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: size * 0.6,
          background: INK,
          padding: `${size * 0.6}px ${size * 0.9}px ${size * 0.66}px`,
          borderRadius: 3,
          border: `${size * 0.07}px solid ${RED}`,
          boxShadow: SHADOW_HARD,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size,
          color: WHITE,
          letterSpacing: "0.01em",
          whiteSpace: "nowrap",
        }}
      >
        <svg width={size * 1.25} height={size * 1.25} viewBox="0 0 32 32">
          <path
            d="M4 4h24a2 2 0 012 2v15a2 2 0 01-2 2H14l-8 6v-6H4a2 2 0 01-2-2V6a2 2 0 012-2z"
            fill={RED}
          />
        </svg>
        SCHREIB'S IN DIE KOMMENTARE
        <span style={{ opacity: caret, color: RED }}>|</span>
      </div>
    </div>
  );
};

// ============================================================
// Hauptkomposition
// ============================================================

export const SetzerFleischkaeseVsLeberkaese: React.FC<SetzerFleischkaeseProps> = ({
  fontSizePx,
  bandY,
  timeOffsetSec,
  showSubtitles,
  showAnimations,
  showLogoOutro,
  showHohenlohe,
  review,
}) => {
  const { fps, width, height } = useVideoConfig();
  const toF = (sec: number) => Math.round((sec + timeOffsetSec) * fps);

  // Elementzeile über dem Untertitelband — bleibt unter der Gesichtszone
  const rowY = Math.round(height * 0.505);
  const bandPx = Math.round(height * bandY);

  const row: React.CSSProperties = {
    position: "absolute",
    left: 0,
    right: 0,
    top: rowY,
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
            {/* 1 — LEBERKÄSE vs. FLEISCHKÄSE (Schreibweise wie auf der Website) */}
            <div style={{ ...row, top: Math.round(height * 0.545) }}>
              <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: height * 0.012 }}>
                <Chip label="LEBERKÄSE" filled from="left" beat={BEATS.vsLeberkaes} offsetSec={timeOffsetSec} size={height * 0.038} />
                <Chip label="FLEISCHKÄSE" filled={false} from="right" beat={BEATS.vsFleischkaes} offsetSec={timeOffsetSec} size={height * 0.038} />
                <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
                  <VsBadge offsetSec={timeOffsetSec} size={height * 0.024} />
                </div>
              </div>
            </div>

            {/* 2 — Stempel */}
            <div style={{ ...row, top: Math.round(height * 0.575) }}>
              <Stempel offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 3 — Grenze */}
            <div style={{ ...row, top: Math.round(height * 0.555) }}>
              <Grenze offsetSec={timeOffsetSec} />
            </div>

            {/* 4 — Linie unter dem Band */}
            <div style={{ ...row, top: bandPx + Math.round(height * 0.1) }}>
              <RegelLinie offsetSec={timeOffsetSec} width={width} height={height} />
            </div>

            {/* 5 — FLEISCHKÄSE */}
            <div style={{ ...row, top: Math.round(height * 0.6) }}>
              <Aufloesung offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 6 — Zähler */}
            <div style={{ ...row, top: Math.round(height * 0.615) }}>
              <Zaehler offsetSec={timeOffsetSec} height={height} />
            </div>

            {/* 7 — Herkunft (abschaltbar, bis Volker „Hohenlohe" freigibt) */}
            {showHohenlohe && (
              <div style={{ ...row, top: Math.round(height * 0.53) }}>
                <HohenloheBadge offsetSec={timeOffsetSec} height={height} width={width} />
              </div>
            )}

            {/* 8 — 24/7 Shops (offizielles Shop-Logo) */}
            <div style={{ ...row, top: Math.round(height * 0.55) }}>
              <ShopsBox offsetSec={timeOffsetSec} height={height} width={width} />
            </div>

            {/* 9 — Hero: nur noch Logo-Panel, sitzt mittig im unteren Feld */}
            <div style={{ ...row, top: Math.round(height * 0.62) }}>
              <Hero offsetSec={timeOffsetSec} height={height} width={width} showLogo={showLogoOutro} />
            </div>

            {/* 10 — Poll */}
            <div style={{ ...row, top: Math.round(height * 0.56) }}>
              <PollChips offsetSec={timeOffsetSec} height={height} width={width} />
            </div>
            <div style={{ ...row, top: Math.round(height * 0.735) }}>
              <CommentBubble offsetSec={timeOffsetSec} height={height} />
            </div>
          </>
        )}

        {/* Untertitelband */}
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
