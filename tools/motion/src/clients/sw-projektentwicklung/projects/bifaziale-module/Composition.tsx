// ============================================================
// SW Projektentwicklung — Video 02 "Bifaziale Solarmodule"
// 9:16 Overlay, 35.5s — Inhalt aus 02_Bifaziale_Solarmodule_V1.srt
// CI von sw-projektentwicklung.com: Orange #FF8022, Anthrazit #2E2D2C,
// Montserrat, Radius 10.
// Alle Elemente liegen UNTERHALB der Gesichts-Zone (Pflicht-Check CLAUDE.md).
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Montserrat";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import { SubtitleTrack, subtitlesSchema, SUBTITLE_DEFAULTS } from "../../Subtitles";
import captionsJson from "../../captions/bifaziale-module.json";

loadFont();
const ci = loadBrand("sw-projektentwicklung", brandJson as any);

// =============================================================
// SCHEMA
// =============================================================

const timingSchema = z.object({
  startSec: z.number().step(0.1).describe("Start (Sekunden)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sekunden)"),
});

const posSchema = z.object({
  x: z.number().step(1).describe("X (px)"),
  y: z.number().step(1).describe("Y (px)"),
});

const P0 = { x: 0, y: 0 };

const hookSchema = timingSchema.extend({
  word: z.string().describe("Schlagwort"),
  wordPos: posSchema.describe("Position: Schlagwort"),
  subline: z.string().describe("Unterzeile"),
  sublinePos: posSchema.describe("Position: Unterzeile"),
});

const streitSchema = timingSchema.extend({
  contraText: z.string().describe("Contra-Aussage"),
  contraPos: posSchema.describe("Position: Contra"),
  proText: z.string().describe("Pro-Aussage"),
  proPos: posSchema.describe("Position: Pro"),
});

const titelSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  subline: z.string().describe("Unterzeile"),
  sublinePos: posSchema.describe("Position: Unterzeile"),
});

const beideSeitenSchema = timingSchema.extend({
  leftLabel: z.string().describe("Label links"),
  rightLabel: z.string().describe("Label rechts"),
  caption: z.string().describe("Bildunterschrift"),
  captionPos: posSchema.describe("Position: Bildunterschrift"),
  modulePos: posSchema.describe("Position: Modul"),
});

const zaunSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Bildunterschrift"),
  captionPos: posSchema.describe("Position: Bildunterschrift"),
  fencePos: posSchema.describe("Position: Zaun"),
});

const ertragSchema = timingSchema.extend({
  fromValue: z.number().describe("Startwert"),
  toValue: z.number().describe("Endwert"),
  suffix: z.string().describe("Einheit"),
  numberPos: posSchema.describe("Position: Zahl"),
  label: z.string().describe("Label"),
  labelPos: posSchema.describe("Position: Label"),
  sublabel: z.string().describe("Unterlabel"),
  sublabelPos: posSchema.describe("Position: Unterlabel"),
});

const empfehlungSchema = timingSchema.extend({
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  subline: z.string().describe("Unterzeile"),
  sublinePos: posSchema.describe("Position: Unterzeile"),
  logoPos: posSchema.describe("Position: Logo"),
});

export const swBifazialeModuleSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  hook: hookSchema.describe("Szene 1: Streit-Hook"),
  streit: streitSchema.describe("Szene 2: Der eine / der andere"),
  titel: titelSchema.describe("Szene 3: BIFAZIAL"),
  beideSeiten: beideSeitenSchema.describe("Szene 4: Beide Seiten produzieren"),
  zaun: zaunSchema.describe("Szene 5: Modul als Zaun"),
  ertrag: ertragSchema.describe("Szene 6: 5–20 % Mehrertrag"),
  empfehlung: empfehlungSchema.describe("Szene 7: Empfehlung"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swBifazialeModuleSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

const ORANGE = "#FF8022";
const ORANGE_LIGHT = "#FF9A4D";
const DARK = "#2E2D2C";
const WHITE = "#FFFFFF";
const GREY = "#9E9E9E";
const FONT = "Montserrat, sans-serif";
const RADIUS = 10;

// Reels-Safe-Zone: 0.07–0.575. Gesichts-Zone (Default): 0.08–0.45.
// Die Bühne liegt komplett darunter und bleibt trotzdem im sicheren Bereich.
const STAGE = { top: 0.455, bottom: 0.575 };
const FACE_BOTTOM = 0.45;
const SIDE = 0.05;

const SLAM = { damping: 8, stiffness: 220 };
const PUNCH = { damping: 10, stiffness: 180 };
const SMOOTH = { damping: 14, stiffness: 120 };
const BOUNCE = { damping: 6, stiffness: 260 };

// =============================================================
// HELPERS
// =============================================================

const useStage = () => {
  const { height, width } = useVideoConfig();
  const top = height * STAGE.top;
  const bottom = height * STAGE.bottom;
  return {
    top,
    bottom,
    height: bottom - top,
    center: (top + bottom) / 2,
    left: width * SIDE,
    right: width * (1 - SIDE),
    innerWidth: width * (1 - 2 * SIDE),
  };
};

const useExit = (exitFrames = 8) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const start = Math.max(0, durationInFrames - exitFrames);
  const prog = interpolate(frame, [start, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return { exitProg: prog, exitScale: interpolate(prog, [0, 1], [0.9, 1]) };
};

const shadow = (strength = 0.9) => `0 2px 20px rgba(0,0,0,${strength})`;

// Solarmodul — Vorder- oder Rückseite
const SolarModule: React.FC<{
  w: number;
  h: number;
  back?: boolean;
  cols?: number;
  rows?: number;
  glow?: number;
}> = ({ w, h, back = false, cols = 6, rows = 3, glow = 0 }) => (
  <div
    style={{
      width: w,
      height: h,
      borderRadius: 6,
      backgroundColor: back ? "#3C3B39" : DARK,
      border: `${Math.max(2, h * 0.025)}px solid ${back ? "#7A7875" : "#57544F"}`,
      boxSizing: "border-box",
      display: "grid",
      gridTemplateColumns: `repeat(${cols}, 1fr)`,
      gridTemplateRows: `repeat(${rows}, 1fr)`,
      gap: Math.max(2, h * 0.02),
      padding: Math.max(3, h * 0.03),
      boxShadow: `0 10px 34px rgba(0,0,0,0.5)${glow > 0 ? `, 0 0 ${glow}px ${ORANGE}66` : ""}`,
    }}
  >
    {Array.from({ length: cols * rows }, (_, i) => (
      <div
        key={i}
        style={{
          borderRadius: 2,
          backgroundColor: back ? "rgba(255,255,255,0.16)" : "rgba(255,255,255,0.05)",
          border: `1px solid rgba(255,255,255,${back ? 0.24 : 0.1})`,
        }}
      />
    ))}
  </div>
);

// =============================================================
// SZENE 1 — "Weil da streiten sich ja die Gemüter im Solarmarkt."
// =============================================================

const HookScene: React.FC<{
  word: string;
  wordPos: Pos;
  subline: string;
  sublinePos: Pos;
}> = ({ word, wordPos, subline, sublinePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const slam = spring({ frame, fps, config: { damping: 6, stiffness: 300 } });
  // Startskalierung bewusst klein gehalten: groessere Werte verlassen die Safe Zone
  // und ragen in die Gesichts-Zone (Pre-Delivery-Review).
  const scale = interpolate(slam, [0, 1], [1.32, 1]);
  const slamBlur = interpolate(slam, [0, 0.55, 1], [16, 3, 0], { extrapolateRight: "clamp" });
  const rotate = interpolate(slam, [0, 1], [-6, 0]);
  const shakeX = frame < 12 ? Math.sin(frame * 8) * (12 - frame) * 1.3 : 0;

  const ring = spring({ frame: frame - 2, fps, config: { damping: 20, stiffness: 60 } });
  const ringScale = interpolate(ring, [0, 1], [0, 3.2]);
  const ringOpacity = interpolate(ring, [0, 0.3, 1], [0.8, 0.35, 0]);

  const sub = spring({ frame: frame - 12, fps, config: PUNCH });

  const cx = width / 2;
  const wordY = stage.top + stage.height * 0.34;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {/* Schockwelle wird unterhalb der Gesichts-Zone abgeschnitten */}
      <div
        style={{
          position: "absolute",
          top: height * FACE_BOTTOM,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: wordY + wordPos.y - height * FACE_BOTTOM,
            left: cx + wordPos.x,
            width: height * 0.16,
            height: height * 0.16,
            borderRadius: "50%",
            border: `4px solid ${ORANGE}`,
            transform: `translate(-50%, -50%) scale(${ringScale})`,
            opacity: ringOpacity * exitProg,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          top: wordY + wordPos.y,
          left: cx + wordPos.x,
          transform: `translate(-50%, -50%) scale(${scale * exitScale}) rotate(${rotate}deg) translateX(${shakeX}px)`,
          fontFamily: FONT,
          fontSize: height * 0.052,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: -1,
          whiteSpace: "nowrap",
          textShadow: `0 4px 26px rgba(0,0,0,0.9), 0 0 50px ${ORANGE}66`,
          filter: `blur(${slamBlur}px)`,
          opacity: slam,
        }}
      >
        {word}
        <span style={{ color: ORANGE }}>.</span>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.72 + sublinePos.y,
          left: cx + sublinePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(sub, [0, 1], [26, 0])}px)`,
          opacity: sub * exitProg,
          fontFamily: FONT,
          fontSize: height * 0.019,
          fontWeight: 700,
          color: ORANGE_LIGHT,
          letterSpacing: 4,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(),
        }}
      >
        {subline}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 2 — "Der eine sagt … der andere sagt …"
// =============================================================

const StreitScene: React.FC<{
  contraText: string;
  contraPos: Pos;
  proText: string;
  proPos: Pos;
}> = ({ contraText, contraPos, proText, proPos }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const rows = [
    {
      text: contraText,
      pos: contraPos,
      icon: "✕",
      accent: GREY,
      bg: "rgba(0,0,0,0.7)",
      fromX: -140,
      // Szene startet bei 3,4 s; „es bringt gar nichts" faellt bei 3,48 s.
      delay: 3,
    },
    {
      text: proText,
      pos: proPos,
      icon: "✓",
      accent: ORANGE,
      bg: "rgba(255,128,34,0.92)",
      fromX: 140,
      // „der andere sagt, es bringt was" faellt bei 4,87 s.
      delay: 44,
    },
  ];

  const rowH = stage.height * 0.42;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {rows.map((row, i) => {
        const prog = spring({ frame: frame - row.delay, fps, config: SLAM });
        const shake =
          frame >= row.delay && frame < row.delay + 7
            ? Math.sin((frame - row.delay) * 9) * (7 - (frame - row.delay)) * 1.4
            : 0;
        const badge = spring({ frame: frame - row.delay - 3, fps, config: BOUNCE });

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: stage.top + stage.height * 0.06 + i * (rowH + stage.height * 0.1) + row.pos.y,
              left: stage.left + row.pos.x,
              width: stage.innerWidth,
              height: rowH,
              display: "flex",
              alignItems: "center",
              gap: stage.innerWidth * 0.045,
              padding: `0 ${stage.innerWidth * 0.05}px`,
              boxSizing: "border-box",
              backgroundColor: row.bg,
              borderRadius: RADIUS,
              borderLeft: `5px solid ${row.accent}`,
              boxShadow: `0 8px 30px rgba(0,0,0,0.45)`,
              opacity: prog * exitProg,
              transform: `translateX(${interpolate(prog, [0, 1], [row.fromX, 0]) + shake}px) scale(${exitScale})`,
            }}
          >
            <div
              style={{
                width: rowH * 0.46,
                height: rowH * 0.46,
                borderRadius: "50%",
                flexShrink: 0,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                backgroundColor: i === 0 ? "rgba(158,158,158,0.18)" : "rgba(255,255,255,0.2)",
                border: `2px solid ${i === 0 ? GREY : WHITE}`,
                transform: `scale(${interpolate(badge, [0, 1], [0, 1])}) rotate(${interpolate(badge, [0, 1], [-180, 0])}deg)`,
              }}
            >
              <span
                style={{
                  fontFamily: FONT,
                  fontSize: rowH * 0.24,
                  fontWeight: 900,
                  color: i === 0 ? GREY : WHITE,
                  lineHeight: 1,
                }}
              >
                {row.icon}
              </span>
            </div>
            <span
              style={{
                fontFamily: FONT,
                fontSize: height * 0.026,
                fontWeight: 800,
                color: WHITE,
                textShadow: i === 0 ? shadow(0.95) : "none",
              }}
            >
              {row.text}
            </span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 3 — "… Solarmodule, die bifazial sind."
// =============================================================

const TitelScene: React.FC<{
  title: string;
  titlePos: Pos;
  subline: string;
  sublinePos: Pos;
}> = ({ title, titlePos, subline, sublinePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const chars = title.split("");
  const lineProg = spring({ frame: frame - chars.length * 2 - 2, fps, config: SMOOTH });
  const sub = spring({ frame: frame - chars.length * 2 - 6, fps, config: PUNCH });
  const glow = Math.sin(frame * 0.12) * 0.4 + 0.6;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.3 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          justifyContent: "center",
        }}
      >
        {chars.map((c, i) => {
          const p = spring({ frame: frame - i * 2, fps, config: BOUNCE });
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                fontFamily: FONT,
                fontSize: height * 0.05,
                fontWeight: 900,
                color: ORANGE,
                letterSpacing: 2,
                opacity: p,
                transform: `translateY(${interpolate(p, [0, 1], [50, 0])}px) scale(${interpolate(p, [0, 1], [0.4, 1])})`,
                textShadow: `0 4px 22px rgba(0,0,0,0.85), 0 0 ${34 * glow}px ${ORANGE}70`,
              }}
            >
              {c}
            </span>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.52 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: "translateX(-50%)",
          width: interpolate(lineProg, [0, 1], [0, stage.innerWidth * 0.6]),
          height: 4,
          borderRadius: 2,
          background: `linear-gradient(90deg, transparent, ${ORANGE}, transparent)`,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.68 + sublinePos.y,
          left: width / 2 + sublinePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(sub, [0, 1], [20, 0])}px)`,
          opacity: sub,
          fontFamily: FONT,
          fontSize: height * 0.019,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(),
        }}
      >
        {subline}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 4 — "… von beiden Seiten produzieren."
// =============================================================

const BeideSeitenScene: React.FC<{
  leftLabel: string;
  rightLabel: string;
  caption: string;
  captionPos: Pos;
  modulePos: Pos;
}> = ({ leftLabel, rightLabel, caption, captionPos, modulePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const enter = spring({ frame, fps, config: PUNCH });
  const leftProg = spring({ frame: frame - 6, fps, config: SLAM });
  const rightProg = spring({ frame: frame - 12, fps, config: SLAM });
  const caps = spring({ frame: frame - 18, fps, config: SMOOTH });
  const pulse = Math.sin(frame * 0.18) * 0.5 + 0.5;

  const modW = width * 0.2;
  const modH = stage.height * 0.4;
  const modCenterY = stage.top + stage.height * 0.42;

  const side = (isLeft: boolean, label: string, prog: number) => (
    <div
      style={{
        position: "absolute",
        top: modCenterY,
        left: isLeft ? width / 2 - modW * 0.62 : width / 2 + modW * 0.62,
        transform: `translate(${isLeft ? "-100%" : "0"}, -50%) translateX(${interpolate(prog, [0, 1], [isLeft ? -60 : 60, 0])}px)`,
        opacity: prog * exitProg,
        display: "flex",
        flexDirection: isLeft ? "row" : "row-reverse",
        alignItems: "center",
        gap: 10,
      }}
    >
      <span
        style={{
          fontFamily: FONT,
          fontSize: height * 0.016,
          fontWeight: 800,
          color: WHITE,
          letterSpacing: 2,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(),
        }}
      >
        {label}
      </span>
      <div
        style={{
          width: width * 0.06,
          height: 4,
          borderRadius: 2,
          background: isLeft
            ? `linear-gradient(90deg, transparent, ${ORANGE})`
            : `linear-gradient(270deg, transparent, ${ORANGE})`,
          boxShadow: `0 0 ${14 * pulse + 6}px ${ORANGE}90`,
        }}
      />
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {side(true, leftLabel, leftProg)}
      {side(false, rightLabel, rightProg)}

      <div
        style={{
          position: "absolute",
          top: modCenterY + modulePos.y,
          left: width / 2 + modulePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(enter, [0, 1], [0.5, 1]) * exitScale})`,
          opacity: enter,
        }}
      >
        <SolarModule w={modW} h={modH} cols={3} rows={3} glow={22 + 18 * pulse} />
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.78 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(caps, [0, 1], [18, 0])}px)`,
          opacity: caps,
          fontFamily: FONT,
          fontSize: height * 0.024,
          fontWeight: 800,
          color: WHITE,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {caption}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 5 — "… mitten in Garten stellen als Zaun."
// =============================================================

const ZaunScene: React.FC<{
  title: string;
  titlePos: Pos;
  caption: string;
  captionPos: Pos;
  fencePos: Pos;
}> = ({ title, titlePos, caption, captionPos, fencePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame: frame - 2, fps, config: PUNCH });
  const capsProg = spring({ frame: frame - 14, fps, config: SMOOTH });

  // Sonne wandert über die Szene: links (Vorderseite) → rechts (Rückseite)
  const sunT = interpolate(frame, [10, durationInFrames - 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const groundY = stage.top + stage.height * 0.8;
  const fenceH = stage.height * 0.3;
  const modW = width * 0.062;
  const gap = width * 0.028;
  const count = 4;
  const fenceW = count * modW + (count - 1) * gap;
  const fenceLeft = width / 2 - fenceW / 2 + fencePos.x;

  const sunX = interpolate(sunT, [0, 1], [width * 0.14, width * 0.86]);
  const sunY = groundY - fenceH - stage.height * 0.14 - Math.sin(sunT * Math.PI) * stage.height * 0.05;
  const sunGlow = Math.sin(frame * 0.14) * 0.3 + 0.7;
  const fromLeft = sunT < 0.5;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(titleProg, [0, 1], [-20, 0])}px) scale(${exitScale})`,
          opacity: titleProg,
          fontFamily: FONT,
          fontSize: height * 0.026,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 1,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {title}
      </div>

      {/* Sonne */}
      <div
        style={{
          position: "absolute",
          top: sunY + fencePos.y,
          left: sunX,
          width: height * 0.022,
          height: height * 0.022,
          borderRadius: "50%",
          backgroundColor: ORANGE,
          transform: "translate(-50%, -50%)",
          boxShadow: `0 0 ${26 * sunGlow}px ${ORANGE}, 0 0 ${60 * sunGlow}px ${ORANGE}70`,
        }}
      />

      {/* Zaun aus stehenden Modulen */}
      {Array.from({ length: count }, (_, i) => {
        const p = spring({ frame: frame - 6 - i * 5, fps, config: SLAM });
        const x = fenceLeft + i * (modW + gap);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: groundY + fencePos.y,
              left: x,
              transformOrigin: "bottom center",
              transform: `translateY(-100%) scaleY(${interpolate(p, [0, 1], [0, 1])}) rotate(${interpolate(p, [0, 1], [-8, 0])}deg)`,
              opacity: p,
            }}
          >
            <SolarModule
              w={modW}
              h={fenceH}
              cols={2}
              rows={4}
              back={!fromLeft}
              glow={16 * sunGlow}
            />
          </div>
        );
      })}

      {/* Sonnenstrahl zur beleuchteten Seite */}
      <div
        style={{
          position: "absolute",
          top: sunY + fencePos.y,
          left: fromLeft ? sunX : width / 2,
          width: fromLeft ? width / 2 - sunX : sunX - width / 2,
          height: 3,
          borderRadius: 2,
          transformOrigin: fromLeft ? "left center" : "right center",
          transform: `rotate(${fromLeft ? 16 : -16}deg)`,
          background: fromLeft
            ? `linear-gradient(90deg, ${ORANGE}, ${ORANGE}20)`
            : `linear-gradient(270deg, ${ORANGE}, ${ORANGE}20)`,
          opacity: 0.85,
          boxShadow: `0 0 12px ${ORANGE}80`,
        }}
      />

      {/* Boden */}
      <div
        style={{
          position: "absolute",
          top: groundY + fencePos.y,
          left: stage.left,
          width: stage.innerWidth,
          height: 3,
          borderRadius: 2,
          background: `linear-gradient(90deg, transparent, ${ORANGE}, transparent)`,
          opacity: 0.8,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.82 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(capsProg, [0, 1], [10, 0])}px)`,
          opacity: capsProg,
          fontFamily: FONT,
          fontSize: height * 0.018,
          fontWeight: 700,
          color: ORANGE_LIGHT,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(),
        }}
      >
        {caption}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — "… zwischen 5 und 20 Prozent mehr Effekt."
// =============================================================

const ErtragScene: React.FC<{
  fromValue: number;
  toValue: number;
  suffix: string;
  numberPos: Pos;
  label: string;
  labelPos: Pos;
  sublabel: string;
  sublabelPos: Pos;
}> = ({ fromValue, toValue, suffix, numberPos, label, labelPos, sublabel, sublabelPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const pop = spring({ frame: frame - 2, fps, config: SLAM });
  const count = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 60 } });
  const value = Math.round(interpolate(count, [0, 1], [fromValue, toValue]));
  const labelProg = spring({ frame: frame - 20, fps, config: PUNCH });
  const subProg = spring({ frame: frame - 28, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.12) * 0.4 + 0.6;

  // Der fruehere Fuellbalken zwischen Zahl und „MEHRERTRAG" ist entfernt
  // (Kundenwunsch 2026-08-18). Er sass so dicht unter der Zahl, dass er wie
  // eine Unterstreichung wirkte statt wie ein Trenner — und er zeigte
  // ohnehin nur dasselbe wie der Zaehler, der bereits von 5 auf 20 laeuft.

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.3 + numberPos.y,
          left: width / 2 + numberPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pop, [0, 1], [2.6, 1]) * exitScale})`,
          opacity: pop,
          fontFamily: FONT,
          fontSize: height * 0.072,
          fontWeight: 900,
          color: ORANGE,
          lineHeight: 1,
          whiteSpace: "nowrap",
          textShadow: `0 0 ${36 * glow}px ${ORANGE}80, 0 4px 20px rgba(0,0,0,0.8)`,
        }}
      >
        {fromValue}–{value}
        <span style={{ fontSize: height * 0.042, color: ORANGE_LIGHT, marginLeft: 6 }}>{suffix}</span>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.62 + labelPos.y,
          left: width / 2 + labelPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(labelProg, [0, 1], [18, 0])}px)`,
          opacity: labelProg,
          fontFamily: FONT,
          fontSize: height * 0.024,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 5,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {label}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.82 + sublabelPos.y,
          left: width / 2 + sublabelPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(subProg, [0, 1], [14, 0])}px)`,
          opacity: subProg,
          fontFamily: FONT,
          fontSize: height * 0.016,
          fontWeight: 600,
          color: "rgba(255,255,255,0.75)",
          letterSpacing: 2,
          whiteSpace: "nowrap",
          textShadow: shadow(),
        }}
      >
        {sublabel}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 7 — "Meine Empfehlung: immer bifazial."
// =============================================================

const EmpfehlungScene: React.FC<{
  pillText: string;
  pillPos: Pos;
  subline: string;
  sublinePos: Pos;
  logoPos: Pos;
}> = ({ pillText, pillPos, subline, sublinePos, logoPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const pill = spring({ frame: frame - 2, fps, config: SLAM });
  const check = spring({ frame: frame - 10, fps, config: BOUNCE });
  const sub = spring({ frame: frame - 16, fps, config: PUNCH });

  // Endlockup: Das gestapelte Logo hat 2,62:1 (vorher 5,69:1 quer) und braucht
  // fuer dieselbe Schriftgroesse rund die doppelte Hoehe. Zwischen Gesichtszone
  // und Safe-Zone-Unterkante liegen nur ~240 px — zu wenig fuer Pill, Unterzeile
  // UND ein lesbares Logo gleichzeitig. Deshalb raeumen Pill und Unterzeile nach
  // 1,5 s die Buehne und das Logo bekommt sie allein.
  const HANDOVER = 44;
  const TEXT_FADE = 8;
  const textOut = interpolate(frame, [HANDOVER, HANDOVER + TEXT_FADE], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Das Logo setzt erst ein, wenn die Pill vollstaendig weg ist. Bei einer
  // Ueberlappung schaut ihr Rand hinter dem Logo hervor und wirkt wie ein Fehler.
  const logo = spring({ frame: frame - HANDOVER - TEXT_FADE, fps, config: SMOOTH });

  // Harte Umschaltung statt nur Opazitaet 0: Pill und Unterzeile werden ab der
  // Uebergabe gar nicht mehr gerendert. Ein Rest-Alpha der grossen orangen
  // Flaeche bleibt sonst hinter dem Logo sichtbar.
  const SWITCH = HANDOVER + TEXT_FADE;
  const showText = frame < SWITCH;
  const showLogo = frame >= SWITCH;

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.025;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {showText && (
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.14 + pillPos.y,
          left: width / 2 + pillPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.3, 1]) * breathe * exitScale})`,
          opacity: pill * textOut,
          display: "flex",
          alignItems: "center",
          gap: width * 0.02,
          padding: `${stage.height * 0.04}px ${width * 0.045}px`,
          borderRadius: 9999,
          backgroundColor: ORANGE,
          boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${40 * glow}px ${ORANGE}55`,
        }}
      >
        <div
          style={{
            width: height * 0.026,
            height: height * 0.026,
            borderRadius: "50%",
            backgroundColor: WHITE,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            flexShrink: 0,
            transform: `scale(${interpolate(check, [0, 1], [0, 1])}) rotate(${interpolate(check, [0, 1], [-180, 0])}deg)`,
          }}
        >
          <span style={{ fontFamily: FONT, fontSize: height * 0.018, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
            ✓
          </span>
        </div>
        <span
          style={{
            fontFamily: FONT,
            fontSize: height * 0.03,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 2,
            whiteSpace: "nowrap",
          }}
        >
          {pillText}
        </span>
      </div>
      )}

      {showText && (
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.34 + sublinePos.y,
          left: width / 2 + sublinePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(sub, [0, 1], [12, 0])}px)`,
          opacity: sub * textOut,
          fontFamily: FONT,
          fontSize: height * 0.019,
          fontWeight: 700,
          color: WHITE,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {subline}
      </div>
      )}

      {showLogo && (
      <div
        style={{
          position: "absolute",
          top: stage.center + logoPos.y,
          left: width / 2 + logoPos.x,
          // Skalierung statt Versatz: eine Bewegung nach unten wuerde das Logo
          // waehrend des Eintritts unter die Safe-Zone-Kante schieben.
          transform: `translate(-50%, -50%) scale(${interpolate(logo, [0, 1], [0.9, 1]) * exitScale})`,
          opacity: logo,
        }}
      >
        {/* Freigestellte Negativ-Version ohne weisse Karte. Der Schlagschatten
            ist nicht Deko: die Endkarte liegt vor hellem Himmel, dort haette
            weisse Schrift ohne ihn zu wenig Kontrast. */}
        <Img
          src={staticFile("clients/sw-projektentwicklung/logo-stack-white.png")}
          style={{
            // 0,90 statt 0,80: zwischen Gesichts-Zone (864 px) und Safe-Zone-
            // Unterkante (1104 px) liegen 240 px. Bei 0,90 ist das Logo 207 px
            // hoch und behaelt oben 21 px, unten 12 px Luft — auch mit dem
            // leichten Ueberschwingen der Einblend-Feder.
            height: stage.height * 0.9,
            display: "block",
            filter: `drop-shadow(0 2px 3px rgba(0,0,0,0.55)) drop-shadow(0 0 14px rgba(0,0,0,0.5))`,
          }}
        />
      </div>
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// DURCHGEHEND
// =============================================================

const EnergyParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { height, width, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Nur im unteren Bereich, damit die Gesichts-Zone frei bleibt.
  const bandTop = height * 0.42;
  const bandHeight = height * 0.2;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: 10 }, (_, i) => {
        const seed = i * 137.508;
        const baseX = ((seed * 7.3) % 100) / 100;
        const baseY = ((seed * 3.7) % 100) / 100;
        const speed = 0.3 + ((seed * 1.9) % 1) * 0.7;
        const size = 2 + ((seed * 2.3) % 1) * 4;

        const x = baseX * width + Math.sin(frame * 0.02 * speed + seed) * 30;
        const y = baseY * bandHeight + Math.cos(frame * 0.015 * speed + seed) * 20 - frame * 0.25 * speed;
        const wrapped = ((y % bandHeight) + bandHeight) % bandHeight;
        const opacity = (Math.sin(frame * 0.05 + seed) * 0.3 + 0.5) * fadeIn * fadeOut * 0.55;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: bandTop + wrapped,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: ORANGE,
              opacity,
              boxShadow: `0 0 ${size * 3}px ${ORANGE}80`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// =============================================================
// HAUPTKOMPOSITION
// =============================================================

export const SWBifazialeModule: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Timings liegen auf den Wortzeitstempeln aus dem SRT, nicht auf gleichmaessigen
  // Bloecken: jede Grafik setzt erst ein, wenn das zugehoerige Wort gefallen ist.
  hook = { startSec: 0, durationSec: 2.4, word: "STREIT", wordPos: P0, subline: "im Solarmarkt", sublinePos: P0 },
  streit = { startSec: 3.4, durationSec: 3.2, contraText: "„Bringt gar nichts.“", contraPos: P0, proText: "„Bringt richtig was.“", proPos: P0 },
  titel = { startSec: 8.0, durationSec: 5.0, title: "BIFAZIAL", titlePos: P0, subline: "Module mit zwei aktiven Seiten", sublinePos: P0 },
  beideSeiten = { startSec: 14.0, durationSec: 2.4, leftLabel: "Sonne", rightLabel: "Reflexion", caption: "Strom von beiden Seiten", captionPos: P0, modulePos: P0 },
  zaun = { startSec: 18.6, durationSec: 5.4, title: "Modul als Gartenzaun", titlePos: P0, caption: "Ertrag von vorne und hinten", captionPos: P0, fencePos: P0 },
  ertrag = { startSec: 25.0, durationSec: 6.3, fromValue: 5, toValue: 20, suffix: "%", numberPos: P0, label: "Mehrertrag", labelPos: P0, sublabel: "je nach Untergrund & Installation", sublabelPos: P0 },
  empfehlung = { startSec: 32.8, durationSec: 3.2, pillText: "IMMER BIFAZIAL", pillPos: P0, subline: "Kann man nichts falsch machen.", sublinePos: P0, logoPos: P0 },
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);
  const stage = useStage();

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent &&
          (footageFile ? (
            <AbsoluteFill>
              <OffthreadVideo
                src={staticFile(`projects/sw-projektentwicklung-solar-wissen/${footageFile}`)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
              <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.15)" }} />
            </AbsoluteFill>
          ) : (
            <AbsoluteFill
              style={{
                background: `radial-gradient(circle at 50% 28%, #4A4845 0%, ${DARK} 55%, #1A1918 100%)`,
              }}
            />
          ))}

        <EnergyParticles />

        <Sequence from={s(hook.startSec)} durationInFrames={s(hook.durationSec)}>
          <HookScene word={hook.word} wordPos={hook.wordPos} subline={hook.subline} sublinePos={hook.sublinePos} />
        </Sequence>

        <Sequence from={s(streit.startSec)} durationInFrames={s(streit.durationSec)}>
          <StreitScene contraText={streit.contraText} contraPos={streit.contraPos} proText={streit.proText} proPos={streit.proPos} />
        </Sequence>

        <Sequence from={s(titel.startSec)} durationInFrames={s(titel.durationSec)}>
          <TitelScene title={titel.title} titlePos={titel.titlePos} subline={titel.subline} sublinePos={titel.sublinePos} />
        </Sequence>

        <Sequence from={s(beideSeiten.startSec)} durationInFrames={s(beideSeiten.durationSec)}>
          <BeideSeitenScene leftLabel={beideSeiten.leftLabel} rightLabel={beideSeiten.rightLabel} caption={beideSeiten.caption} captionPos={beideSeiten.captionPos} modulePos={beideSeiten.modulePos} />
        </Sequence>

        <Sequence from={s(zaun.startSec)} durationInFrames={s(zaun.durationSec)}>
          <ZaunScene title={zaun.title} titlePos={zaun.titlePos} caption={zaun.caption} captionPos={zaun.captionPos} fencePos={zaun.fencePos} />
        </Sequence>

        <Sequence from={s(ertrag.startSec)} durationInFrames={s(ertrag.durationSec)}>
          <ErtragScene fromValue={ertrag.fromValue} toValue={ertrag.toValue} suffix={ertrag.suffix} numberPos={ertrag.numberPos} label={ertrag.label} labelPos={ertrag.labelPos} sublabel={ertrag.sublabel} sublabelPos={ertrag.sublabelPos} />
        </Sequence>

        <Sequence from={s(empfehlung.startSec)} durationInFrames={s(empfehlung.durationSec)}>
          <EmpfehlungScene pillText={empfehlung.pillText} pillPos={empfehlung.pillPos} subline={empfehlung.subline} sublinePos={empfehlung.sublinePos} logoPos={empfehlung.logoPos} />
        </Sequence>

        {/* Untertitel: nur in den Luecken zwischen den Szenen. Die Szenen selbst
            bleiben unveraendert; ihre Start/Dauer-Werte sind hier die Sperrzeiten. */}
        <SubtitleTrack
          pages={captionsJson.pages}
          blocked={[hook, streit, titel, beideSeiten, zaun, ertrag, empfehlung]}
          settings={subtitles}
          stage={stage}
        />

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
