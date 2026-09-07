// ============================================================
// SW Projektentwicklung — Video 01 "Projekt Gottwollshausen"
// 9:16 Overlay, 53.53s — Inhalt aus 01_Projekt-Gottwolfshausen_V1.txt
// (Material- und Transkriptdateien tragen die alte Schreibweise mit „f"; der Ort
//  heisst laut Kunde Gottwollshausen, deshalb steht im Bild die Fassung mit „ll".)
// CI wie Video 02: Orange #FF8022, Anthrazit #2E2D2C, Montserrat, Radius 10.
//
// Das Transkript liefert diesmal nur SEGMENT-Timecodes (kein Wort-SRT wie bei 02).
// Deshalb sitzt jede Grafik bewusst 0,3–0,6 s NACH dem Segmentbeginn: innerhalb
// eines Segments ist die genaue Wortposition unbekannt, und zu frueh eingeblendete
// Grafiken nehmen dem Sprecher die Pointe vorweg.
//
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
import captionsJson from "../../captions/gottwollshausen.json";

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
  line1: z.string().describe("Hook, Zeile 1"),
  line2: z.string().describe("Hook, Zeile 2 (Schlagwort, orange)"),
  linesPos: posSchema.describe("Position: Hook"),
});

const projektSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  subline: z.string().describe("Unterzeile"),
  sublinePos: posSchema.describe("Position: Unterzeile"),
});

const anlageSchema = timingSchema.extend({
  moduleCount: z
    .string()
    .describe("Anzahl Module — LEER LASSEN, wenn unbekannt (Zahl fehlt im Transkript)"),
  wattLabel: z.string().describe("Leistung pro Modul"),
  caption: z.string().describe("Bildunterschrift"),
  captionPos: posSchema.describe("Position: Bildunterschrift"),
  modulePos: posSchema.describe("Position: Modul-Block"),
});

const speicherSchema = timingSchema.extend({
  value: z.string().describe("Kapazität"),
  unit: z.string().describe("Einheit"),
  label: z.string().describe("Label"),
  labelPos: posSchema.describe("Position: Label"),
  batteryPos: posSchema.describe("Position: Speicher"),
});

const ertragSchema = timingSchema.extend({
  toValue: z.number().describe("Endwert (kWh/Jahr)"),
  label: z.string().describe("Label"),
  labelPos: posSchema.describe("Position: Label"),
  sublabel: z.string().describe("Unterlabel"),
  sublabelPos: posSchema.describe("Position: Unterlabel"),
  numberPos: posSchema.describe("Position: Zahl"),
});

const grenzeSchema = timingSchema.extend({
  limitLabel: z.string().describe("Grenzwert"),
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Bildunterschrift"),
  captionPos: posSchema.describe("Position: Bildunterschrift"),
});

const folgenSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  row1: z.string().describe("Folge 1"),
  row1Sub: z.string().describe("Folge 1 — Zusatz"),
  row2: z.string().describe("Folge 2"),
  row2Sub: z.string().describe("Folge 2 — Zusatz"),
  row3: z.string().describe("Folge 3"),
  row3Sub: z.string().describe("Folge 3 — Zusatz"),
  rowsPos: posSchema.describe("Position: Liste"),
});

const ctaFrageSchema = timingSchema.extend({
  line1: z.string().describe("Zeile 1"),
  line2: z.string().describe("Zeile 2"),
  linesPos: posSchema.describe("Position: Text"),
});

const endkarteSchema = timingSchema.extend({
  analyseText: z.string().describe("Angebot"),
  analysePos: posSchema.describe("Position: Angebot"),
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  logoPos: posSchema.describe("Position: Logo"),
});

export const swGottwollshausenSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  hook: hookSchema.describe("Szene 1: Drossel-Hook"),
  projekt: projektSchema.describe("Szene 2: Bauvorhaben"),
  anlage: anlageSchema.describe("Szene 3: Module 460 Wp"),
  speicher: speicherSchema.describe("Szene 4: 18 kWh Speicher"),
  ertrag: ertragSchema.describe("Szene 5: 24.000 kWh/Jahr"),
  grenze: grenzeSchema.describe("Szene 6: Unter 25 kWp"),
  folgen: folgenSchema.describe("Szene 7: Was ab 25 kWp passiert"),
  ctaFrage: ctaFrageSchema.describe("Szene 8: Stromrechnung-Frage"),
  endkarte: endkarteSchema.describe("Szene 9: Endkarte"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swGottwollshausenSchema>;
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

// Deutsche Tausenderpunkte — 24000 wird als „24.000" gelesen, nicht „24,000".
const de = (n: number) => n.toLocaleString("de-DE");

const SolarModule: React.FC<{ w: number; h: number; cols?: number; rows?: number; glow?: number }> = ({
  w,
  h,
  cols = 6,
  rows = 3,
  glow = 0,
}) => (
  <div
    style={{
      width: w,
      height: h,
      borderRadius: 6,
      backgroundColor: DARK,
      border: `${Math.max(2, h * 0.025)}px solid #57544F`,
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
          backgroundColor: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.1)",
        }}
      />
    ))}
  </div>
);

// =============================================================
// SZENE 1 — "… kann deine Anlage drosseln."
// =============================================================

// Statt eines einzelnen Schlagworts steht hier jetzt der gesprochene Satz
// (Kundenwunsch 2026-08-18: Text muss wortgleich zum O-Ton sein). Ein ganzer
// Satz laesst sich nicht mehr als ein Wort einschlagen — er braucht zwei Zeilen
// und muss deutlich kleiner gesetzt sein, sonst passt er nicht zwischen
// Gesichts-Zone und Safe-Zone-Unterkante. Die Wucht der alten Szene bleibt
// erhalten, indem beide Zeilen versetzt einschlagen und der Schockwellenring
// weiter unter der zweiten Zeile aufgeht.
const HookScene: React.FC<{
  line1: string;
  line2: string;
  linesPos: Pos;
}> = ({ line1, line2, linesPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const slam1 = spring({ frame, fps, config: { damping: 7, stiffness: 280 } });
  const slam2 = spring({ frame: frame - 6, fps, config: { damping: 6, stiffness: 300 } });

  // Startskalierung bewusst klein: groessere Werte ragen beim Einschlag in die
  // Gesichts-Zone (Pre-Delivery-Review).
  const scale1 = interpolate(slam1, [0, 1], [1.2, 1]);
  const scale2 = interpolate(slam2, [0, 1], [1.26, 1]);
  const blur1 = interpolate(slam1, [0, 0.55, 1], [14, 3, 0], { extrapolateRight: "clamp" });
  const blur2 = interpolate(slam2, [0, 0.55, 1], [16, 3, 0], { extrapolateRight: "clamp" });
  // Wackler haengt am zweiten Einschlag (Frame 6), nicht am Szenenstart.
  const shakeX = frame >= 6 && frame < 18 ? Math.sin((frame - 6) * 8) * (18 - frame) * 1.2 : 0;

  const ring = spring({ frame: frame - 8, fps, config: { damping: 20, stiffness: 60 } });
  const ringScale = interpolate(ring, [0, 1], [0, 3.2]);
  const ringOpacity = interpolate(ring, [0, 0.3, 1], [0.8, 0.35, 0]);

  const cx = width / 2;
  // Zwei Zeilen brauchen mehr Bauhoehe als das alte Einzelwort. 0,30 / 0,66
  // legt sie mittig auf die Buehne, ohne oben die Gesichts-Zone (864 px) oder
  // unten die Safe Zone (1104 px) zu beruehren.
  const y1 = stage.top + stage.height * 0.3;
  const y2 = stage.top + stage.height * 0.66;
  const FS = height * 0.0335;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {/* Schockwelle wird an der Gesichts-Zone abgeschnitten */}
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
            top: y2 + linesPos.y - height * FACE_BOTTOM,
            left: cx + linesPos.x,
            width: height * 0.14,
            height: height * 0.14,
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
          top: y1 + linesPos.y,
          left: cx + linesPos.x,
          transform: `translate(-50%, -50%) scale(${scale1 * exitScale})`,
          fontFamily: FONT,
          fontSize: FS,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: -0.5,
          whiteSpace: "nowrap",
          textShadow: `0 4px 26px rgba(0,0,0,0.9), 0 0 50px ${ORANGE}55`,
          filter: `blur(${blur1}px)`,
          opacity: slam1,
        }}
      >
        {line1}
      </div>

      <div
        style={{
          position: "absolute",
          top: y2 + linesPos.y,
          left: cx + linesPos.x,
          transform: `translate(-50%, -50%) scale(${scale2 * exitScale}) translateX(${shakeX}px)`,
          fontFamily: FONT,
          fontSize: FS,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: -0.5,
          whiteSpace: "nowrap",
          textShadow: `0 4px 26px rgba(0,0,0,0.9), 0 0 50px ${ORANGE}55`,
          filter: `blur(${blur2}px)`,
          opacity: slam2,
        }}
      >
        {line2}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 2 — "Wir sind hier gerade bei einem Bauvorhaben …"
// =============================================================

const ProjektScene: React.FC<{
  title: string;
  titlePos: Pos;
  subline: string;
  sublinePos: Pos;
}> = ({ title, titlePos, subline, sublinePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const bar = spring({ frame, fps, config: SLAM });
  const titleProg = spring({ frame: frame - 6, fps, config: PUNCH });
  const subProg = spring({ frame: frame - 16, fps, config: SMOOTH });

  const barW = stage.innerWidth * 0.16;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {/* Kurze Orange-Kante als Anker — ersetzt eine Rahmenbox, die im
          230-px-Band zu massiv wirken wuerde. */}
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.16,
          left: width / 2,
          transform: `translateX(-50%) scaleX(${bar})`,
          width: barW,
          height: 5,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${ORANGE_LIGHT}, ${ORANGE})`,
          boxShadow: `0 0 18px ${ORANGE}90`,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.34 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(titleProg, [0, 1], [-18, 0])}px) scale(${exitScale})`,
          opacity: titleProg,
          fontFamily: FONT,
          fontSize: height * 0.034,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 1,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: `0 4px 24px rgba(0,0,0,0.9)`,
        }}
      >
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.64 + sublinePos.y,
          left: width / 2 + sublinePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(subProg, [0, 1], [16, 0])}px)`,
          opacity: subProg,
          fontFamily: FONT,
          fontSize: height * 0.0185,
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
// SZENE 3 — "… verbauen wir unsere Solarmodule mit 460 Watt."
// =============================================================

const AnlageScene: React.FC<{
  moduleCount: string;
  wattLabel: string;
  caption: string;
  captionPos: Pos;
  modulePos: Pos;
}> = ({ moduleCount, wattLabel, caption, captionPos, modulePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const enter = spring({ frame, fps, config: PUNCH });
  const wattProg = spring({ frame: frame - 8, fps, config: SLAM });
  const capProg = spring({ frame: frame - 18, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.14) * 0.4 + 0.6;

  const modH = stage.height * 0.34;
  const modW = modH * 1.7;
  const rowY = stage.top + stage.height * 0.32;

  // Die Stueckzahl fehlt im Transkript (Sprecher sagt „insgesamt …", die Zahl
  // ist nicht mitgeschrieben). Statt zu raten wird der Block nur gerendert,
  // wenn jemand den Wert in den Props setzt.
  const hasCount = moduleCount.trim().length > 0;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: rowY + modulePos.y,
          left: width / 2 + modulePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(enter, [0, 1], [0.6, 1]) * exitScale})`,
          opacity: enter,
          display: "flex",
          alignItems: "center",
          gap: width * 0.035,
        }}
      >
        <SolarModule w={modW} h={modH} cols={6} rows={3} glow={26 * glow} />

        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {hasCount && (
            <div
              style={{
                fontFamily: FONT,
                fontSize: height * 0.019,
                fontWeight: 800,
                color: "rgba(255,255,255,0.8)",
                letterSpacing: 3,
                whiteSpace: "nowrap",
                textShadow: shadow(),
              }}
            >
              {moduleCount} ×
            </div>
          )}
          <div
            style={{
              transform: `scale(${interpolate(wattProg, [0, 1], [1.6, 1])})`,
              transformOrigin: "left center",
              opacity: wattProg,
              fontFamily: FONT,
              fontSize: height * 0.042,
              fontWeight: 900,
              color: ORANGE,
              lineHeight: 1,
              whiteSpace: "nowrap",
              textShadow: `0 0 ${30 * glow}px ${ORANGE}80, 0 4px 18px rgba(0,0,0,0.85)`,
            }}
          >
            {wattLabel}
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.74 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(capProg, [0, 1], [14, 0])}px)`,
          opacity: capProg,
          fontFamily: FONT,
          fontSize: height * 0.0175,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 3,
          textTransform: "uppercase",
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
// SZENE 4 — "… noch einen Stromspeicher von 18 Kilowattstunden."
// =============================================================

const SpeicherScene: React.FC<{
  value: string;
  unit: string;
  label: string;
  labelPos: Pos;
  batteryPos: Pos;
}> = ({ value, unit, label, labelPos, batteryPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const enter = spring({ frame, fps, config: PUNCH });
  const fillProg = spring({ frame: frame - 6, fps, config: { damping: 18, stiffness: 55 } });
  const valueProg = spring({ frame: frame - 10, fps, config: SLAM });
  const labelProg = spring({ frame: frame - 20, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.13) * 0.4 + 0.6;

  const battH = stage.height * 0.36;
  const battW = battH * 0.62;
  const rowY = stage.top + stage.height * 0.32;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: rowY + batteryPos.y,
          left: width / 2 + batteryPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(enter, [0, 1], [0.6, 1]) * exitScale})`,
          opacity: enter,
          display: "flex",
          alignItems: "center",
          gap: width * 0.035,
        }}
      >
        {/* Akku: Kontakt + Korpus. Der Fuellstand laeuft mit der Feder hoch. */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div
            style={{
              width: battW * 0.38,
              height: Math.max(3, battH * 0.06),
              borderRadius: 2,
              backgroundColor: "#7A7875",
            }}
          />
          <div
            style={{
              width: battW,
              height: battH,
              borderRadius: RADIUS * 0.8,
              backgroundColor: "rgba(0,0,0,0.55)",
              border: `3px solid #7A7875`,
              boxSizing: "border-box",
              padding: 4,
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-end",
              boxShadow: `0 10px 30px rgba(0,0,0,0.55)`,
            }}
          >
            <div
              style={{
                width: "100%",
                height: `${fillProg * 88}%`,
                borderRadius: RADIUS * 0.5,
                background: `linear-gradient(180deg, ${ORANGE_LIGHT}, ${ORANGE})`,
                boxShadow: `0 0 ${18 * glow}px ${ORANGE}90`,
              }}
            />
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div
            style={{
              transform: `scale(${interpolate(valueProg, [0, 1], [1.7, 1])})`,
              transformOrigin: "left center",
              opacity: valueProg,
              fontFamily: FONT,
              fontSize: height * 0.046,
              fontWeight: 900,
              color: ORANGE,
              lineHeight: 1,
              whiteSpace: "nowrap",
              textShadow: `0 0 ${32 * glow}px ${ORANGE}80, 0 4px 18px rgba(0,0,0,0.85)`,
            }}
          >
            {value}
            <span style={{ fontSize: height * 0.024, color: ORANGE_LIGHT, marginLeft: 5 }}>{unit}</span>
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.74 + labelPos.y,
          left: width / 2 + labelPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(labelProg, [0, 1], [14, 0])}px)`,
          opacity: labelProg,
          fontFamily: FONT,
          fontSize: height * 0.0175,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {label}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 5 — "… auf 24.000 Kilowattstunden pro Jahr."
// =============================================================

const ErtragScene: React.FC<{
  toValue: number;
  numberPos: Pos;
  label: string;
  labelPos: Pos;
  sublabel: string;
  sublabelPos: Pos;
}> = ({ toValue, numberPos, label, labelPos, sublabel, sublabelPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const pop = spring({ frame: frame - 2, fps, config: SLAM });
  const count = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 60 } });
  // Auf 100er gerundet, damit die Zaehlung nicht als unruhiges Ziffernflimmern
  // laeuft und am Ende exakt auf dem genannten Wert steht.
  const value = Math.round(interpolate(count, [0, 1], [0, toValue]) / 100) * 100;
  const labelProg = spring({ frame: frame - 20, fps, config: PUNCH });
  const subProg = spring({ frame: frame - 28, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.12) * 0.4 + 0.6;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.32 + numberPos.y,
          left: width / 2 + numberPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pop, [0, 1], [2.4, 1]) * exitScale})`,
          opacity: pop,
          fontFamily: FONT,
          fontSize: height * 0.062,
          fontWeight: 900,
          color: ORANGE,
          lineHeight: 1,
          whiteSpace: "nowrap",
          textShadow: `0 0 ${36 * glow}px ${ORANGE}80, 0 4px 20px rgba(0,0,0,0.8)`,
        }}
      >
        {de(value)}
        <span style={{ fontSize: height * 0.03, color: ORANGE_LIGHT, marginLeft: 8 }}>kWh</span>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.6 + labelPos.y,
          left: width / 2 + labelPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(labelProg, [0, 1], [18, 0])}px)`,
          opacity: labelProg,
          fontFamily: FONT,
          fontSize: height * 0.023,
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

      {/* Dritte Zeile nur, wenn gefuellt. Standard ist leer: „24.000 kWh
          pro Jahr" sagt bereits alles, eine Erklaerzeile darunter kostet nur
          Lesezeit (Kundenrueckmeldung 2026-08-17). */}
      {sublabel.trim().length > 0 && (
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
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — "… bleibt man unter 25 Kilowatt Peak."
// =============================================================

const GrenzeScene: React.FC<{
  limitLabel: string;
  title: string;
  titlePos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ limitLabel, title, titlePos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  // Kurze Ausblende (5 statt 8 Frames) und zusammengeschobener Ablauf: Die
  // Szene steht nur 36 Frames. Mit dem urspruenglichen, langsam fuellenden
  // Balken (damping 20 / stiffness 55, Start Frame 6) war sie noch mitten in
  // der Animation, als die Ausblende schon lief — lesbar war fast nichts.
  // Jetzt steht alles ab Frame 12 und haelt bis Frame 31.
  const { exitProg, exitScale } = useExit(5);

  const trackProg = spring({ frame, fps, config: SLAM });
  const fillProg = spring({ frame: frame - 3, fps, config: { damping: 18, stiffness: 130 } });
  const markProg = spring({ frame: frame - 8, fps, config: BOUNCE });
  const capProg = spring({ frame: frame - 12, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;

  const barW = stage.innerWidth * 0.66;
  const barY = stage.top + stage.height * 0.52;
  // Anlage liegt knapp unter der Grenze — der Balken endet bewusst kurz davor.
  const FILL = 0.82;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.1 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, 0) scale(${exitScale})`,
          opacity: trackProg,
          fontFamily: FONT,
          fontSize: height * 0.024,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 4,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {title}
      </div>

      {/* Balken mit Grenzmarke: zeigt „knapp drunter" ohne Zahlenkolonne */}
      <div
        style={{
          position: "absolute",
          top: barY,
          left: width / 2,
          transform: `translateX(-50%) scaleX(${trackProg})`,
          width: barW,
          height: 10,
          borderRadius: 5,
          backgroundColor: "rgba(255,255,255,0.18)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${fillProg * FILL * 100}%`,
            height: "100%",
            borderRadius: 5,
            background: `linear-gradient(90deg, ${ORANGE_LIGHT}, ${ORANGE})`,
            boxShadow: `0 0 ${16 * glow}px ${ORANGE}90`,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          top: barY - 8,
          left: width / 2 + barW * 0.5,
          transform: `translateX(-50%) scaleY(${markProg})`,
          transformOrigin: "center",
          width: 4,
          height: 26,
          borderRadius: 2,
          backgroundColor: WHITE,
          boxShadow: "0 0 10px rgba(0,0,0,0.8)",
        }}
      />

      <div
        style={{
          position: "absolute",
          top: barY - 40,
          left: width / 2 + barW * 0.5,
          transform: `translateX(-50%) scale(${markProg})`,
          opacity: markProg,
          fontFamily: FONT,
          fontSize: height * 0.017,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {limitLabel}
      </div>

      {/* Standardmaessig leer. Die Szene steht nur 36 Frames, danach ist die
          Aussage erzaehlt — in 1,2 s ist eine dritte Zeile nicht lesbar
          (Kundenrueckmeldung 2026-08-17). */}
      {caption.trim().length > 0 && (
        <div
          style={{
            position: "absolute",
            top: stage.top + stage.height * 0.76 + captionPos.y,
            left: width / 2 + captionPos.x,
            transform: `translate(-50%, 0) translateY(${interpolate(capProg, [0, 1], [14, 0])}px)`,
            opacity: capProg,
            fontFamily: FONT,
            fontSize: height * 0.0175,
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
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 7 — Was ab 25 kWp passiert (drei Folgen, nacheinander)
// =============================================================

const FolgenScene: React.FC<{
  heading: string;
  headingPos: Pos;
  row1: string;
  row1Sub: string;
  row2: string;
  row2Sub: string;
  row3: string;
  row3Sub: string;
  rowsPos: Pos;
}> = ({ heading, headingPos, row1, row1Sub, row2, row2Sub, row3, row3Sub, rowsPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });

  // Die drei Folgen kommen zu ihren Sprechzeiten, nicht gleichmaessig verteilt.
  // Szene startet bei 25,6 s; Sprechzeitpunkte laut Transkript:
  // Rundsteuergeraet 25,7 s | Drosselung 31,9 s | Montagekosten 39,8 s.
  // Als Szenen-Frames bei 30 fps: (Zeit − 25,6) × 30.
  //
  // WICHTIG — warum nur EINE Karte gleichzeitig sichtbar ist: Eine Karte ist mit
  // Text, Unterzeile und Innenabstand rund 74 px hoch. Zwischen Gesichts-Zone
  // (864 px) und Safe-Zone-Unterkante (1104 px) liegen 240 px, davon gehen noch
  // ~40 px fuer die Ueberschrift ab. Drei gestapelte Karten (222 px + Abstaende)
  // passen dort nicht — sie ueberlappten sich und die dritte lief unten heraus.
  // Da die Sprechzeiten ohnehin 5–8 s auseinanderliegen, loest ein Wechsel das
  // Platzproblem, ohne dass Information verlorengeht.
  const rows = [
    { text: row1, sub: row1Sub, at: 4 },
    { text: row2, sub: row2Sub, at: 189 },
    { text: row3, sub: row3Sub, at: 426 },
  ];

  // Aktive Karte = die letzte, deren Zeitpunkt erreicht ist. Die vorherige wird
  // nicht ausgeblendet, sondern ersetzt — nur ein Element traegt Deckung.
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), -1);
  const active = activeIndex >= 0 ? rows[activeIndex] : null;
  const prog = spring({
    frame: frame - (active ? rows[activeIndex].at : 0),
    fps,
    config: SLAM,
  });

  const rowY = stage.top + stage.height * 0.52;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.06 + headingPos.y,
          left: width / 2 + headingPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(headProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: headProg,
          fontFamily: FONT,
          fontSize: height * 0.019,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: 5,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {heading}
      </div>

      {active && (
        <div
          // key erzwingt einen echten Neuaufbau beim Wechsel — sonst liefe die
          // Einflug-Feder beim zweiten und dritten Punkt nicht neu an.
          key={activeIndex}
          style={{
            position: "absolute",
            top: rowY + rowsPos.y,
            left: width / 2 + rowsPos.x,
            transform: `translate(-50%, -50%) translateX(${interpolate(prog, [0, 1], [-90, 0])}px) scale(${exitScale})`,
            opacity: prog,
            display: "flex",
            alignItems: "center",
            gap: width * 0.022,
            padding: `${stage.height * 0.05}px ${width * 0.04}px`,
            borderRadius: RADIUS,
            backgroundColor: "rgba(0,0,0,0.72)",
            borderLeft: `5px solid ${ORANGE}`,
            boxShadow: "0 8px 30px rgba(0,0,0,0.45)",
            maxWidth: stage.innerWidth,
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              fontFamily: FONT,
              fontSize: height * 0.022,
              fontWeight: 900,
              color: ORANGE,
              lineHeight: 1,
            }}
          >
            ✕
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <div
              style={{
                fontFamily: FONT,
                fontSize: height * 0.0195,
                fontWeight: 800,
                color: WHITE,
                letterSpacing: 0.5,
                whiteSpace: "nowrap",
              }}
            >
              {active.text}
            </div>
            <div
              style={{
                fontFamily: FONT,
                fontSize: height * 0.014,
                fontWeight: 600,
                color: "rgba(255,255,255,0.7)",
                letterSpacing: 1,
                whiteSpace: "nowrap",
              }}
            >
              {active.sub}
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 8 — "Wenn deine Stromrechnung dir die Haare vom Kopf frisst …"
// =============================================================

const CtaFrageScene: React.FC<{
  line1: string;
  line2: string;
  linesPos: Pos;
}> = ({ line1, line2, linesPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const l1 = spring({ frame, fps, config: PUNCH });
  const l2 = spring({ frame: frame - 12, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.26 + linesPos.y,
          left: width / 2 + linesPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(l1, [0, 1], [18, 0])}px) scale(${exitScale})`,
          opacity: l1,
          fontFamily: FONT,
          fontSize: height * 0.0205,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {line1}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.54 + linesPos.y,
          left: width / 2 + linesPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(l2, [0, 1], [22, 0])}px) scale(${interpolate(l2, [0, 1], [1.25, 1]) * exitScale})`,
          opacity: l2,
          fontFamily: FONT,
          fontSize: height * 0.034,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: 1,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: `0 0 40px ${ORANGE}70, 0 4px 22px rgba(0,0,0,0.9)`,
        }}
      >
        {line2}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 9 — Endkarte: Analyse → 70 % Autarkie → Logo
// =============================================================

const EndkarteScene: React.FC<{
  analyseText: string;
  analysePos: Pos;
  pillText: string;
  pillPos: Pos;
  logoPos: Pos;
}> = ({ analyseText, analysePos, pillText, pillPos, logoPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // „komplette Analyse" faellt bei 47,2 s → Frame 12 bei 30 fps.
  //
  // Die Pill startet auf Frame 88 (49,7 s) statt auf dem exakten Sprechzeitpunkt
  // von „mindestens 70 % Autarkiegrad" (rund 50,3 s). Bewusste Ausnahme von der
  // Regel „nie vor dem Wort": Sie ist die Kernaussage des Videos und war mit der
  // urspruenglichen Aufteilung zu kurz zum Lesen (Kundenrueckmeldung
  // 2026-08-17). Der Vorlauf betraegt gut eine halbe Sekunde, das Wort faellt
  // also waehrend die Pill noch steht.
  const analyse = spring({ frame: frame - 12, fps, config: PUNCH });
  const pill = spring({ frame: frame - 88, fps, config: SLAM });

  // Uebergabe an das Logo. Gelernt aus Video 02: Opazitaet 0 reicht NICHT —
  // die grosse orange Flaeche schimmert sonst hinter dem teiltransparenten
  // Logo-PNG durch. Beide Phasen schliessen sich deshalb hart aus.
  // Die Szene hat mit der gelieferten Cliplaenge 201 Frames. Aufteilung:
  // Pill 88–166 (2,6 s Lesezeit), Logo ab 166 bis zur Ausblende (1,2 s).
  // Frueher lag der Umschaltpunkt bei 138 — dann stand die Pill nur 1,6 s und
  // war nicht lesbar, waehrend das Logo laenger als noetig hielt. Das Logo ist
  // eine Bildmarke, die in 1,2 s erfasst wird; die Pill ist Text und braucht
  // mehr (Kundenrueckmeldung 2026-08-17).
  const HANDOVER = 158;
  const TEXT_FADE = 8;
  const SWITCH = HANDOVER + TEXT_FADE;
  const textOut = interpolate(frame, [HANDOVER, SWITCH], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const showText = frame < SWITCH;
  const showLogo = frame >= SWITCH;
  const logo = spring({ frame: frame - SWITCH, fps, config: SMOOTH });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.025;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {showText && (
        <div
          style={{
            position: "absolute",
            // 0,78 statt 0,16: In den Sekunden, in denen diese Zeile allein
            // steht, zeigt die Footage die Beratungsszene am Tisch — dort
            // sitzen drei Gesichter deutlich tiefer als beim Dachsprecher und
            // reichen bis rund 911 px herunter. Auf 0,16 (910 px) lag die
            // Zeile genau auf Mund und Kinn. Auf 0,78 sitzt sie bei 1053 px,
            // also unter allen Gesichtern und immer noch in der Safe Zone
            // (Unterkante 1104 px).
            top: stage.top + stage.height * 0.78 + analysePos.y,
            left: width / 2 + analysePos.x,
            transform: `translate(-50%, 0) translateY(${interpolate(analyse, [0, 1], [16, 0])}px) scale(${exitScale})`,
            opacity: analyse * textOut,
            fontFamily: FONT,
            fontSize: height * 0.0195,
            fontWeight: 800,
            color: WHITE,
            letterSpacing: 3,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            textShadow: shadow(0.95),
          }}
        >
          {analyseText}
        </div>
      )}

      {showText && (
        <div
          style={{
            position: "absolute",
            // Rueckt nach oben, weil die Analyse-Zeile jetzt unten sitzt. Die
            // Pill erscheint erst nach dem Schnitt zurueck auf den Dach-
            // sprecher, dort ist auf dieser Hoehe kein Gesicht.
            top: stage.top + stage.height * 0.32 + pillPos.y,
            left: width / 2 + pillPos.x,
            transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.3, 1]) * breathe * exitScale})`,
            opacity: pill * textOut,
            display: "flex",
            alignItems: "center",
            gap: width * 0.02,
            padding: `${stage.height * 0.04}px ${width * 0.045}px`,
            borderRadius: 9999,
            backgroundColor: ORANGE,
            boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${34 * glow}px ${ORANGE}70`,
          }}
        >
          <div style={{ fontFamily: FONT, fontSize: height * 0.021, fontWeight: 900, color: WHITE, lineHeight: 1 }}>
            ✓
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontSize: height * 0.021,
              fontWeight: 900,
              color: WHITE,
              letterSpacing: 2,
              whiteSpace: "nowrap",
            }}
          >
            {pillText}
          </div>
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
              // 0,90: zwischen Gesichts-Zone (864 px) und Safe-Zone-Unterkante
              // (1104 px) liegen 240 px. Bei 0,90 ist das Logo 207 px hoch und
              // behaelt oben 21 px, unten 12 px Luft — auch mit Federueberschwung.
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
// HINTERGRUND-PARTIKEL
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

export const SWGottwollshausen: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Timings folgen den Segment-Timecodes aus dem Transkript (t = 0 bei
  // 00:59:59:24), jeweils leicht nach hinten versetzt — siehe Kopfkommentar.
  hook = { startSec: 1.3, durationSec: 4.0, line1: "Der Netzbetreiber kann", line2: "deine Anlage drosseln!", linesPos: P0 },
  projekt = { startSec: 6.2, durationSec: 4.0, title: "Bauvorhaben", titlePos: P0, subline: "Gottwollshausen", sublinePos: P0 },
  anlage = { startSec: 10.9, durationSec: 2.9, moduleCount: "", wattLabel: "460 Watt", caption: "pro Solarmodul", captionPos: P0, modulePos: P0 },
  speicher = { startSec: 14.2, durationSec: 2.8, value: "18", unit: "kWh", label: "Stromspeicher", labelPos: P0, batteryPos: P0 },
  ertrag = { startSec: 18.9, durationSec: 3.3, toValue: 24000, numberPos: P0, label: "pro Jahr", labelPos: P0, sublabel: "", sublabelPos: P0 },
  grenze = { startSec: 22.2, durationSec: 2.0, limitLabel: "25 kWp", title: "Bewusst darunter geplant", titlePos: P0, caption: "", captionPos: P0 },
  folgen = {
    startSec: 25.6,
    durationSec: 15.9,
    heading: "Ab 25 kWp gilt",
    headingPos: P0,
    row1: "Rundsteuer-Empfänger nötig",
    row1Sub: "pauschal ab ca. 600 €",
    row2: "Netzbetreiber darf drosseln",
    row2Sub: "auch deinen Eigenverbrauch",
    row3: "Höhere Montagekosten",
    row3Sub: "zusätzlicher Aufwand am Bau",
    rowsPos: P0,
  },
  ctaFrage = { startSec: 41.8, durationSec: 4.4, line1: "Frisst dir die Stromrechnung", line2: "die Haare vom Kopf?", linesPos: P0 },
  endkarte = { startSec: 46.8, durationSec: 6.7, analyseText: "Komplette Analyse", analysePos: P0, pillText: "MIND. 70 % AUTARKIE", pillPos: P0, logoPos: P0 },
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
          <HookScene line1={hook.line1} line2={hook.line2} linesPos={hook.linesPos} />
        </Sequence>

        <Sequence from={s(projekt.startSec)} durationInFrames={s(projekt.durationSec)}>
          <ProjektScene title={projekt.title} titlePos={projekt.titlePos} subline={projekt.subline} sublinePos={projekt.sublinePos} />
        </Sequence>

        <Sequence from={s(anlage.startSec)} durationInFrames={s(anlage.durationSec)}>
          <AnlageScene moduleCount={anlage.moduleCount} wattLabel={anlage.wattLabel} caption={anlage.caption} captionPos={anlage.captionPos} modulePos={anlage.modulePos} />
        </Sequence>

        <Sequence from={s(speicher.startSec)} durationInFrames={s(speicher.durationSec)}>
          <SpeicherScene value={speicher.value} unit={speicher.unit} label={speicher.label} labelPos={speicher.labelPos} batteryPos={speicher.batteryPos} />
        </Sequence>

        <Sequence from={s(ertrag.startSec)} durationInFrames={s(ertrag.durationSec)}>
          <ErtragScene toValue={ertrag.toValue} numberPos={ertrag.numberPos} label={ertrag.label} labelPos={ertrag.labelPos} sublabel={ertrag.sublabel} sublabelPos={ertrag.sublabelPos} />
        </Sequence>

        <Sequence from={s(grenze.startSec)} durationInFrames={s(grenze.durationSec)}>
          <GrenzeScene limitLabel={grenze.limitLabel} title={grenze.title} titlePos={grenze.titlePos} caption={grenze.caption} captionPos={grenze.captionPos} />
        </Sequence>

        <Sequence from={s(folgen.startSec)} durationInFrames={s(folgen.durationSec)}>
          <FolgenScene
            heading={folgen.heading}
            headingPos={folgen.headingPos}
            row1={folgen.row1}
            row1Sub={folgen.row1Sub}
            row2={folgen.row2}
            row2Sub={folgen.row2Sub}
            row3={folgen.row3}
            row3Sub={folgen.row3Sub}
            rowsPos={folgen.rowsPos}
          />
        </Sequence>

        <Sequence from={s(ctaFrage.startSec)} durationInFrames={s(ctaFrage.durationSec)}>
          <CtaFrageScene line1={ctaFrage.line1} line2={ctaFrage.line2} linesPos={ctaFrage.linesPos} />
        </Sequence>

        <Sequence from={s(endkarte.startSec)} durationInFrames={s(endkarte.durationSec)}>
          <EndkarteScene
            analyseText={endkarte.analyseText}
            analysePos={endkarte.analysePos}
            pillText={endkarte.pillText}
            pillPos={endkarte.pillPos}
            logoPos={endkarte.logoPos}
          />
        </Sequence>

        {/* Untertitel: nur in den Luecken zwischen den Szenen. Die Szenen selbst
            bleiben unveraendert; ihre Start/Dauer-Werte sind hier die Sperrzeiten. */}
        <SubtitleTrack
          pages={captionsJson.pages}
          blocked={[hook, projekt, anlage, speicher, ertrag, grenze, folgen, ctaFrage, endkarte]}
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
