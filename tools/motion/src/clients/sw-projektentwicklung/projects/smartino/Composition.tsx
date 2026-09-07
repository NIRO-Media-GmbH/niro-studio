// ============================================================
// SW Projektentwicklung — Video 05 "Hotel Smartino"
// 9:16 Overlay, 49,25 s — Inhalt aus 05_Hotel-Smartino_V1.srt
// CI wie Video 01–04/07: Orange #FF8022, Anthrazit #2E2D2C, Montserrat.
//
// FEHLENDE ZAHL IM TRANSKRIPT: Zwischen „tatsächlich" (endet 2,16 s) und
// „Autarkiegrad" (beginnt 3,12 s) klafft im SRT eine Luecke von knapp einer
// Sekunde. Gesprochen wird dort „60 Prozent" — vom Kunden nachgereicht. Das
// ist die Kernzahl des Videos und traegt den Hook.
//
// ASR-Korrekturen: „Schwäbischhal" → Schwäbisch Hall,
// „Photovoltaik-Entlage" → Photovoltaikanlage, „Gewerbio-Objekt" → Gewerbeobjekt.
//
// Der Sprecher setzt bei 32,8 s neu an („Also das ist wirklich ein …" —
// Abbruch, dann ab 34,7 s noch einmal). Im Material liegt dort ein Schnitt
// (33,9 s); die Fazit-Szene beginnt deshalb erst danach.
//
// Alle Elemente liegen UNTERHALB der Gesichts-Zone (Pflicht-Check CLAUDE.md).
// Einzige dokumentierte Ausnahme: das Logo der Endkarte, wie in Video 03/04.
// ============================================================
import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  continueRender,
  delayRender,
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
import captionsJson from "../../captions/smartino.json";

// loadFont() alleine blockiert den Render NICHT. Im ersten Export fehlte
// deshalb auf fuenf Frames der Text „Hagelwiderstandsklasse": die Zeile hatte
// bereits ihre Breite (das Badge stand an der richtigen Stelle), aber die
// Glyphen waren noch nicht gerastert — im Video ein Flackern. Der Fehler tritt
// nur sporadisch auf, Einzelbild-Renders derselben Frames waren korrekt.
// delayRender haelt jeden Frame an, bis die Schrift wirklich da ist.
const { waitUntilDone } = loadFont();
const fontHandle = delayRender("Montserrat laden");
waitUntilDone()
  .then(() => continueRender(fontHandle))
  .catch(() => continueRender(fontHandle));

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

const statSchema = timingSchema.extend({
  value: z.string().describe("Zahl"),
  unit: z.string().describe("Einheit / Zusatz (leer = weglassen)"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  blockPos: posSchema.describe("Position: Block"),
});

const objektSchema = timingSchema.extend({
  name: z.string().describe("Objektname"),
  namePos: posSchema.describe("Position: Objektname"),
  ort: z.string().describe("Ort"),
  caption: z.string().describe("Unterzeile (kommt später)"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const anlageSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  value1: z.string().describe("Wert 1"),
  label1: z.string().describe("Label 1"),
  value2: z.string().describe("Wert 2"),
  label2: z.string().describe("Label 2"),
  rowPos: posSchema.describe("Position: Werte"),
});

const netzSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  oldLabel: z.string().describe("Label vorher"),
  oldValue: z.string().describe("Wert vorher"),
  newLabel: z.string().describe("Label jetzt"),
  newValue: z.string().describe("Wert jetzt"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  barsPos: posSchema.describe("Position: Balken"),
});

const fazitSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  chip1: z.string().describe("Kennzahl 1"),
  chip2: z.string().describe("Kennzahl 2"),
  chip3: z.string().describe("Kennzahl 3"),
  rowPos: posSchema.describe("Position: Kennzahlen"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const ctaSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  row1: z.string().describe("Punkt 1"),
  row1Sub: z.string().describe("Punkt 1 — Zusatz"),
  row2: z.string().describe("Punkt 2 (löst Punkt 1 ab)"),
  row2Sub: z.string().describe("Punkt 2 — Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const endkarteSchema = timingSchema.extend({
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  logoPos: posSchema.describe("Position: Logo"),
});

export const swSmartinoSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  autarkie: statSchema.describe("Szene 1: 60 % Autarkie (Hook)"),
  prognose: statSchema.describe("Szene 2: 65–70 % aufs Jahr"),
  objekt: objektSchema.describe("Szene 3: Hotel Smartino, Schwäbisch Hall"),
  anlage: anlageSchema.describe("Szene 4: 144 Module / 63 kWp"),
  verbrauch: statSchema.describe("Szene 5: 70.000 kWh Verbrauch"),
  netz: netzSchema.describe("Szene 6: Netzbezug 70.000 → 25.000"),
  fazit: fazitSchema.describe("Szene 7: perfekt ausgelegt"),
  cta: ctaSchema.describe("Szene 8: Analyse fürs Gewerbedach"),
  endkarte: endkarteSchema.describe("Szene 9: Endkarte"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swSmartinoSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

const ORANGE = "#FF8022";
const ORANGE_LIGHT = "#FF9A4D";
const DARK = "#2E2D2C";
const WHITE = "#FFFFFF";

const FONT = "Montserrat, sans-serif";
const RADIUS = 10;

// Reels-Safe-Zone: 0.07–0.575. Gesichts-Zone (Default): 0.08–0.45.
const STAGE = { top: 0.455, bottom: 0.575 };
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

// Federn konvergieren gegen 1, erreichen es aber nie exakt (0,9999…).
// Ein Element mit Deckkraft < 1 bekommt in Chrome eine eigene Render-Surface —
// die bleibt dadurch fuer immer bestehen. In Video 03 fiel auf jedem achten
// Frame der Text „Hagelwiderstandsklasse" weg: dort sass die Deckkraft als
// einzige Stelle im Video auf dem GRUPPEN-Element statt auf den Kindern, und
// die Surface hat den Textknoten zeitweise nicht mitgezeichnet.
// settle() schnappt auf glatte 1 und loest die Surface auf.
const settle = (v: number) => (v > 0.999 ? 1 : v);

// Chrome laesst beim Einzelframe-Rendern gelegentlich die Glyphen eines
// Textknotens weg, wenn dieser eine eigene animierte `transform` traegt und in
// einem bereits transformierten Eltern-Knoten steckt. Im Export sah man das als
// Flackern (Video 03, „Hagelwiderstandsklasse", fuenf Frames). Reproduzierbar
// nur in voller Aufloesung und nicht bei jedem Lauf.
// Regel: Textknoten werden ueber `position: relative` + `left`/`top` versetzt,
// nicht ueber transform. Reine Grafik-Elemente duerfen transform behalten.


// Ueberschrift und Unterzeile sitzen in JEDER Szene an derselben Stelle.
// 0,87 statt 0,90 fuer die Unterzeile: bei 0,90 endete die Zeile im Review
// exakt auf 1104 px — der Unterkante der Safe Zone. Kein Puffer.
const HEAD_Y = 0.12;
const CAP_Y = 0.87;

const Heading: React.FC<{ text: string; pos: Pos; prog: number; scale: number }> = ({
  text,
  pos,
  prog,
  scale,
}) => {
  const { height, width } = useVideoConfig();
  const stage = useStage();
  return (
    <div
      style={{
        position: "absolute",
        top: stage.top + stage.height * HEAD_Y + pos.y,
        left: width / 2 + pos.x,
        transform: `translate(-50%, -50%) translateY(${interpolate(prog, [0, 1], [-14, 0])}px) scale(${scale})`,
        opacity: settle(prog),
        fontFamily: FONT,
        fontSize: height * 0.019,
        fontWeight: 900,
        color: ORANGE,
        letterSpacing: 4,
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        textShadow: shadow(0.95),
      }}
    >
      {text}
    </div>
  );
};

const Caption: React.FC<{
  text: string;
  pos: Pos;
  prog: number;
  color?: string;
  // Standard ist die Unterkante der Buehne. Szenen, deren Unterzeile direkt
  // zu einer grossen Zahl gehoert, ruecken sie naeher heran — sonst stehen
  // Zahl und Erklaerung als zwei getrennte Elemente im Bild.
  y?: number;
}> = ({ text, pos, prog, color = WHITE, y = CAP_Y }) => {
  const { height, width } = useVideoConfig();
  const stage = useStage();
  if (text === "") return null;
  return (
    <div
      style={{
        position: "absolute",
        top: stage.top + stage.height * y + pos.y,
        left: width / 2 + pos.x,
        transform: `translate(-50%, -50%) translateY(${interpolate(prog, [0, 1], [12, 0])}px)`,
        opacity: settle(prog),
        fontFamily: FONT,
        fontSize: height * 0.0165,
        fontWeight: 700,
        color,
        letterSpacing: 2,
        whiteSpace: "nowrap",
        textShadow: shadow(0.95),
      }}
    >
      {text}
    </div>
  );
};

// Karte mit Haken oder Kreuz — im 230-px-Band traegt immer nur EINE.
const MarkCard: React.FC<{
  mark: string;
  markColor: string;
  text: string;
  sub: string;
  prog: number;
  scale: number;
}> = ({ mark, markColor, text, sub, prog, scale }) => {
  const { height, width } = useVideoConfig();
  const stage = useStage();
  return (
    <div
      style={{
        position: "relative",
        left: interpolate(prog, [0, 1], [-90, 0]),
        transform: scale === 1 ? undefined : `scale(${scale})`,
        opacity: settle(prog),
        display: "flex",
        alignItems: "center",
        gap: width * 0.022,
        padding: `${stage.height * 0.05}px ${width * 0.04}px`,
        borderRadius: RADIUS,
        backgroundColor: "rgba(0,0,0,0.72)",
        borderLeft: `5px solid ${markColor}`,
        boxShadow: "0 8px 30px rgba(0,0,0,0.45)",
        maxWidth: stage.innerWidth,
        boxSizing: "border-box",
      }}
    >
      <div style={{ fontFamily: FONT, fontSize: height * 0.022, fontWeight: 900, color: markColor, lineHeight: 1 }}>
        {mark}
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
          {text}
        </div>
        {sub !== "" && (
          <div
            style={{
              fontFamily: FONT,
              fontSize: height * 0.0135,
              fontWeight: 600,
              color: ORANGE_LIGHT,
              letterSpacing: 1,
              whiteSpace: "nowrap",
            }}
          >
            {sub}
          </div>
        )}
      </div>
    </div>
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
// GEMEINSAMER ZAHLEN-BLOCK
// Drei Szenen zeigen dieselbe Form: eine grosse Zahl mit Einheit und einer
// Unterzeile direkt darunter. Die Einsatz-Frames unterscheiden sich und
// stehen deshalb in den drei Wrappern, nicht hier.
// =============================================================

const StatBlock: React.FC<{
  value: string;
  unit: string;
  caption: string;
  captionPos: Pos;
  blockPos: Pos;
  valProg: number;
  unitProg: number;
  capProg: number;
  big?: boolean;
}> = ({ value, unit, caption, captionPos, blockPos, valProg, unitProg, capProg, big = false }) => {
  const { height, width } = useVideoConfig();
  const stage = useStage();
  const { exitScale } = useExit();

  return (
    <>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.40 + blockPos.y,
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "baseline",
          gap: width * 0.016,
        }}
      >
        <div
          style={{
            transform: `scale(${interpolate(valProg, [0, 1], [big ? 1.35 : 1.25, 1])})`,
            opacity: settle(valProg),
            fontFamily: FONT,
            fontSize: height * (big ? 0.046 : 0.040),
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 1,
            lineHeight: 1,
            whiteSpace: "nowrap",
            textShadow: shadow(0.95),
          }}
        >
          {value}
        </div>
        {unit !== "" && (
          <div
            style={{
              position: "relative",
              top: interpolate(unitProg, [0, 1], [14, 0]),
              opacity: settle(unitProg),
              fontFamily: FONT,
              fontSize: height * 0.023,
              fontWeight: 900,
              color: ORANGE,
              letterSpacing: 3,
              textTransform: "uppercase",
              lineHeight: 1,
              whiteSpace: "nowrap",
              textShadow: shadow(0.95),
            }}
          >
            {unit}
          </div>
        )}
      </div>

      {/* Unterzeile dicht an der Zahl — Lehre aus Video 03: an der
          Buehnenunterkante liest sie sich als eigenes Element. */}
      <Caption text={caption} pos={captionPos} prog={capProg} y={0.72} />
    </>
  );
};

// =============================================================
// SZENE 1 — „innerhalb der 6 Monate … 60 Prozent Autarkiegrad erreichen"
// Die Zahl fehlt im SRT (Luecke 2,16–3,12 s), vom Kunden nachgereicht.
// =============================================================

const AutarkieScene: React.FC<{
  value: string;
  unit: string;
  caption: string;
  captionPos: Pos;
  blockPos: Pos;
}> = ({ value, unit, caption, captionPos, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { exitProg } = useExit();

  // Szene startet 2,3 s — dort faellt „60 Prozent".
  // „Autarkiegrad" beginnt 3,12 s → Frame 25 fuer Einheit und Unterzeile.
  const valProg = spring({ frame, fps, config: SLAM });
  const unitProg = spring({ frame: frame - 25, fps, config: PUNCH });
  const capProg = spring({ frame: frame - 33, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <StatBlock
        value={value}
        unit={unit}
        caption={caption}
        captionPos={captionPos}
        blockPos={blockPos}
        valProg={valProg}
        unitProg={unitProg}
        capProg={capProg}
        big
      />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 2 — „am Ende des Tages zwischen 65 und 70, aufs Jahr"
// =============================================================

const PrognoseScene: React.FC<{
  value: string;
  unit: string;
  caption: string;
  captionPos: Pos;
  blockPos: Pos;
}> = ({ value, unit, caption, captionPos, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { exitProg } = useExit();

  // Szene startet 6,3 s („65" beginnt 6,24 s).
  // „70" beginnt 7,08 s → Frame 24. „aufs Jahr" beginnt 8,12 s → Frame 55.
  const valProg = spring({ frame, fps, config: SLAM });
  const unitProg = spring({ frame: frame - 24, fps, config: PUNCH });
  const capProg = spring({ frame: frame - 55, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <StatBlock
        value={value}
        unit={unit}
        caption={caption}
        captionPos={captionPos}
        blockPos={blockPos}
        valProg={valProg}
        unitProg={unitProg}
        capProg={capProg}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 3 — „Hotel Smartino in Schwäbisch Hall … vor 6 Monaten in Betrieb"
// =============================================================

const ObjektScene: React.FC<{
  name: string;
  namePos: Pos;
  ort: string;
  caption: string;
  captionPos: Pos;
}> = ({ name, namePos, ort, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 10,5 s („Hotel" beginnt 10,48 s).
  // „Schwäbisch Hall" beginnt 11,36 s → Frame 27.
  // „Photovoltaikanlage in Betrieb" beginnt 13,96 s → Frame 106.
  const nameProg = spring({ frame, fps, config: SLAM });
  const ortProg = spring({ frame: frame - 27, fps, config: SMOOTH });
  const capProg = spring({ frame: frame - 106, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.30 + namePos.y,
          left: width / 2 + namePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(nameProg, [0, 1], [1.15, 1]) * exitScale})`,
          opacity: settle(nameProg),
          fontFamily: FONT,
          fontSize: height * 0.028,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {name}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.56 + namePos.y,
          left: width / 2 + namePos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          opacity: settle(ortProg),
          fontFamily: FONT,
          fontSize: height * 0.019,
          fontWeight: 800,
          color: ORANGE,
          letterSpacing: 5,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {ort}
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 4 — „exakt 144 Module und 63 Kilowatt Peak"
// =============================================================

const AnlageScene: React.FC<{
  heading: string;
  headingPos: Pos;
  value1: string;
  label1: string;
  value2: string;
  label2: string;
  rowPos: Pos;
}> = ({ heading, headingPos, value1, label1, value2, label2, rowPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });
  // Szene startet 16,15 s („exakt" beginnt 16,08 s).
  // „144" beginnt 16,68 s → Frame 16. „63" beginnt 18,12 s → Frame 59.
  const p1 = spring({ frame: frame - 16, fps, config: SLAM });
  const p2 = spring({ frame: frame - 59, fps, config: SLAM });

  // Beide Werte bleiben stehen — sie gehoeren zusammen und werden im O-Ton
  // in einem Atemzug genannt.
  const stat = (value: string, label: string, prog: number) => (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 2,
        opacity: settle(prog),
        transform: `scale(${interpolate(prog, [0, 1], [0.6, 1])})`,
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontSize: height * 0.032,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 1,
          lineHeight: 1,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontSize: height * 0.0145,
          fontWeight: 800,
          color: ORANGE,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.9),
        }}
      >
        {label}
      </div>
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.56 + rowPos.y,
          left: width / 2 + rowPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.07,
        }}
      >
        {stat(value1, label1, p1)}
        {stat(value2, label2, p2)}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 5 — „Stromverbrauch von 70.000 kWh pro Jahr"
// =============================================================

const VerbrauchScene: React.FC<{
  value: string;
  unit: string;
  caption: string;
  captionPos: Pos;
  blockPos: Pos;
}> = ({ value, unit, caption, captionPos, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { exitProg } = useExit();

  // Szene startet 21,4 s („Stromverbrauch" beginnt 21,28 s).
  // „70.000" beginnt 22,12 s → Frame 22. „kWh" 23,00 s → Frame 48.
  // „pro Jahr" 23,36 s → Frame 59.
  const valProg = spring({ frame: frame - 22, fps, config: SLAM });
  const unitProg = spring({ frame: frame - 48, fps, config: PUNCH });
  const capProg = spring({ frame: frame - 59, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <StatBlock
        value={value}
        unit={unit}
        caption={caption}
        captionPos={captionPos}
        blockPos={blockPos}
        valProg={valProg}
        unitProg={unitProg}
        capProg={capProg}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — „dieses Jahr bei gerade mal noch 25.000 maximal … Netzbezug"
// Der Vergleich ist die Pointe des ganzen Videos: 70.000 waren es vorher.
// =============================================================

const NetzScene: React.FC<{
  heading: string;
  headingPos: Pos;
  oldLabel: string;
  oldValue: string;
  newLabel: string;
  newValue: string;
  caption: string;
  captionPos: Pos;
  barsPos: Pos;
}> = ({ heading, headingPos, oldLabel, oldValue, newLabel, newValue, caption, captionPos, barsPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });
  // Szene startet 27,2 s („25.000" beginnt 27,12 s).
  const bar1 = spring({ frame: frame - 4, fps, config: SMOOTH });
  const bar2 = spring({ frame: frame - 14, fps, config: SMOOTH });
  // „Netzbezug" beginnt 29,92 s → Frame 82.
  const capProg = spring({ frame: frame - 82, fps, config: SMOOTH });

  // labelW 130 statt 90: „VORHER" ist bei dieser Schriftgroesse rund 110 px
  // breit, lief unter den Balken und war im Review als „VORHE" abgeschnitten
  // zu sehen — derselbe Fehler wie bei „Bauer Solar" in Video 03.
  const barMax = 210;
  const labelW = 130;

  const Row: React.FC<{
    label: string;
    value: string;
    frac: number;
    color: string;
    prog: number;
  }> = ({ label, value, frac, color, prog }) => (
    <div style={{ display: "flex", alignItems: "center", gap: 14, opacity: settle(prog) }}>
      <div
        style={{
          width: labelW,
          textAlign: "right",
          fontFamily: FONT,
          fontSize: height * 0.0135,
          fontWeight: 800,
          color: WHITE,
          letterSpacing: 1,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.9),
        }}
      >
        {label}
      </div>
      <div
        style={{
          width: barMax * frac * prog,
          height: 22,
          borderRadius: 4,
          background: `linear-gradient(90deg, ${color}, ${color}CC)`,
          boxShadow: "0 4px 14px rgba(0,0,0,0.5)",
        }}
      />
      <div
        style={{
          fontFamily: FONT,
          fontSize: height * 0.0165,
          fontWeight: 900,
          color,
          letterSpacing: 1,
          whiteSpace: "nowrap",
          textShadow: shadow(0.9),
        }}
      >
        {value}
      </div>
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + barsPos.y,
          left: width / 2 + barsPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {/* Balkenlaenge im echten Verhaeltnis: 25.000 zu 70.000 ist 0,36. */}
        {/* Helles Grau statt #8A8681: der Wert stand vor hellem Dach zu
            kontrastarm. Gedaempft bleibt er trotzdem gegenueber Orange. */}
        <Row label={oldLabel} value={oldValue} frac={1} color="#C9C4BD" prog={bar1} />
        <Row label={newLabel} value={newValue} frac={0.36} color={ORANGE} prog={bar2} />
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 7 — „ein richtig gelungenes Projekt und perfekt ausgelegt"
//
// Erster Entwurf war eine weisse Zeile plus Pill — der Kunde fand sie
// langweilig, zu Recht: an dieser Stelle steht nur eine Behauptung im Bild.
// Jetzt traegt die Szene den Beweis: die drei Kennzahlen des Videos laufen
// als Chips nacheinander ein (Muster aus Video 03, Härte/Feuer/Schlag — das
// hat der Kunde ausdruecklich gelobt). Erfunden wird nichts, alle drei Zahlen
// sind vorher im O-Ton gefallen. „Perfekt ausgelegt" wird zur Unterzeile und
// sitzt damit auf dem Wort statt davor.
// =============================================================

const FazitScene: React.FC<{
  heading: string;
  headingPos: Pos;
  chip1: string;
  chip2: string;
  chip3: string;
  rowPos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ heading, headingPos, chip1, chip2, chip3, rowPos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 35,3 s („richtig gelungenes Projekt" beginnt 35,24 s).
  // Chips dicht gestaffelt, damit alle drei stehen, bevor die Unterzeile kommt.
  // „perfekt ausgelegt" beginnt 37,08 s → Frame 54 fuer die Unterzeile.
  const headProg = spring({ frame, fps, config: PUNCH });
  const capProg = spring({ frame: frame - 54, fps, config: SMOOTH });

  const chips = [
    { text: chip1, at: 8 },
    { text: chip2, at: 18 },
    { text: chip3, at: 28 },
  ];

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.52 + rowPos.y,
          left: width / 2 + rowPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          // 0,011 statt 0,014, Innenabstand 0,018 statt 0,022 und Schrift
          // 0,015 statt 0,016: mit den urspruenglichen Werten reichte die
          // Reihe bis 1025 px — die Safe Zone endet bei 1026, also kein Puffer.
          gap: width * 0.011,
        }}
      >
        {/* Nur gestartete Chips rendern, sonst halten die unsichtbaren ihren
            Platz und die Reihe steht nicht mittig (Lehre aus Video 03). */}
        {chips
          .filter((c) => frame >= c.at)
          .map((c, i) => {
            const p = spring({ frame: frame - c.at, fps, config: SLAM });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: `${stage.height * 0.045}px ${width * 0.018}px`,
                  borderRadius: 9999,
                  backgroundColor: "rgba(0,0,0,0.72)",
                  border: `2px solid ${ORANGE}`,
                  boxShadow: "0 6px 22px rgba(0,0,0,0.45)",
                  opacity: settle(p),
                  transform: `scale(${interpolate(p, [0, 1], [0.5, 1])})`,
                }}
              >
                <div
                  style={{
                    fontFamily: FONT,
                    fontSize: height * 0.015,
                    fontWeight: 900,
                    color: ORANGE,
                    lineHeight: 1,
                  }}
                >
                  ✓
                </div>
                <div
                  style={{
                    fontFamily: FONT,
                    fontSize: height * 0.015,
                    fontWeight: 800,
                    color: WHITE,
                    letterSpacing: 1,
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                  }}
                >
                  {c.text}
                </div>
              </div>
            );
          })}
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} color={ORANGE_LIGHT} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 8 — „wenn auch du ein Gewerbeobjekt hast … Analyse … Autarkie"
// =============================================================

const CtaScene: React.FC<{
  heading: string;
  headingPos: Pos;
  row1: string;
  row1Sub: string;
  row2: string;
  row2Sub: string;
  rowsPos: Pos;
}> = ({ heading, headingPos, row1, row1Sub, row2, row2Sub, rowsPos }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });

  // Szene startet 39,4 s („Gewerbeobjekt" beginnt 39,36 s).
  // „Analyse" beginnt 41,08 s → Frame 51.
  // „Autarkie" beginnt 43,44 s → Frame 122. Die Szene laeuft bis 45,9 s,
  // damit die zweite Karte 2,4 s steht — im ersten Entwurf endete sie nach
  // 1,0 s und war nicht zu lesen.
  const rows = [
    { text: row1, sub: row1Sub, at: 51 },
    { text: row2, sub: row2Sub, at: 122 },
  ];
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });
  // Vor Frame 51 steht nur die Ueberschrift — die Karte kaeme sonst vor
  // dem Wort „Analyse".
  const showCard = frame >= rows[0].at;

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      {showCard && (
        <div
          key={activeIndex}
          style={{
            position: "absolute",
            top: stage.top + stage.height * 0.56 + rowsPos.y,
            left: width / 2 + rowsPos.x,
            transform: "translate(-50%, -50%)",
          }}
        >
          <MarkCard
            mark="✓"
            markColor={ORANGE}
            text={active.text}
            sub={active.sub}
            prog={prog}
            scale={exitScale}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 9 — Endkarte: „melde dich doch bei uns"
// Aufbau wie Video 03/04: Logo und Pill stehen GEMEINSAM, nicht nacheinander.
// =============================================================

const EndkarteScene: React.FC<{
  pillText: string;
  pillPos: Pos;
  logoPos: Pos;
}> = ({ pillText, pillPos, logoPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 46,0 s. Der letzte SRT-Eintrag hat keine Wortzeiten mehr
  // (Fliesstext ab 44,0 s); „dann melde dich doch bei uns" faellt nach dem
  // Sprechtempo bei rund 46,0 s.
  const IN = 4;
  const pill = spring({ frame: frame - IN, fps, config: SLAM });
  const logo = spring({ frame: frame - IN - 4, fps, config: SMOOTH });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.025;

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          // Wie in Video 03/04: das Logo steht rund 55 px ueber der
          // Buehnenoberkante, sonst klebt es an der Pill. Gegen das echte
          // Material geprueft — der Sprecher endet deutlich darueber.
          top: stage.top - stage.height * 0.06 + logoPos.y,
          left: width / 2 + logoPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(logo, [0, 1], [0.9, 1]) * exitScale})`,
          opacity: settle(logo),
        }}
      >
        <Img
          src={staticFile("clients/sw-projektentwicklung/logo-stack-white.png")}
          style={{
            height: stage.height * 0.75,
            display: "block",
            filter: `drop-shadow(0 2px 3px rgba(0,0,0,0.55)) drop-shadow(0 0 14px rgba(0,0,0,0.5))`,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          // 0,75: die Pill atmet und federt beim Einflug ueber — bei 0,814 lag
          // die Unterkante im Vollsequenz-Review unter der Safe Zone.
          top: stage.top + stage.height * 0.75 + pillPos.y,
          left: width / 2 + pillPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.3, 1]) * breathe * exitScale})`,
          opacity: settle(pill),
          display: "flex",
          alignItems: "center",
          padding: `${stage.height * 0.04}px ${width * 0.038}px`,
          borderRadius: 9999,
          backgroundColor: ORANGE,
          boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${34 * glow}px ${ORANGE}70`,
        }}
      >
        <div
          style={{
            fontFamily: FONT,
            fontSize: height * 0.0225,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 2,
            whiteSpace: "nowrap",
          }}
        >
          {pillText}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// HAUPTKOMPOSITION
// =============================================================

export const SWSmartino: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Jede Startzeit liegt 0,05–0,15 s hinter dem WORTANFANG des Stichworts.
  autarkie = {
    startSec: 2.3,
    durationSec: 2.9,
    value: "60 %",
    unit: "Autarkie",
    caption: "in den ersten 6 Monaten",
    captionPos: P0,
    blockPos: P0,
  },
  prognose = {
    startSec: 6.3,
    durationSec: 3.0,
    value: "65–70 %",
    unit: "",
    caption: "Prognose aufs ganze Jahr",
    captionPos: P0,
    blockPos: P0,
  },
  objekt = {
    startSec: 10.5,
    durationSec: 5.4,
    name: "Hotel Smartino",
    namePos: P0,
    ort: "Schwäbisch Hall",
    caption: "PV-Anlage seit 6 Monaten in Betrieb",
    captionPos: P0,
  },
  anlage = {
    startSec: 16.15,
    durationSec: 3.7,
    heading: "Die Anlage",
    headingPos: P0,
    value1: "144",
    label1: "Module",
    value2: "63",
    label2: "kWp",
    rowPos: P0,
  },
  verbrauch = {
    startSec: 21.4,
    durationSec: 3.4,
    value: "70.000",
    unit: "kWh",
    caption: "Stromverbrauch pro Jahr",
    captionPos: P0,
    blockPos: P0,
  },
  netz = {
    startSec: 27.2,
    durationSec: 4.3,
    heading: "Nur noch",
    headingPos: P0,
    oldLabel: "Vorher",
    oldValue: "70.000 kWh",
    newLabel: "Jetzt",
    newValue: "25.000 kWh",
    caption: "Netzbezug in diesem Jahr",
    captionPos: P0,
    barsPos: P0,
  },
  fazit = {
    startSec: 35.3,
    durationSec: 3.1,
    heading: "Richtig gelungenes Projekt",
    headingPos: P0,
    chip1: "63 kWp",
    chip2: "144 Module",
    chip3: "60 % Autarkie",
    rowPos: P0,
    caption: "perfekt ausgelegt",
    captionPos: P0,
  },
  cta = {
    startSec: 39.4,
    durationSec: 6.5,
    heading: "Du hast ein Gewerbeobjekt?",
    headingPos: P0,
    row1: "Analyse deines Dachs",
    row1Sub: "wir schauen es uns an",
    row2: "Wie viel Autarkie geht?",
    row2Sub: "konkret für dein Objekt",
    rowsPos: P0,
  },
  endkarte = {
    startSec: 46.0,
    durationSec: 3.25,
    pillText: "MELD DICH GERN",
    pillPos: P0,
    logoPos: P0,
  },
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

        <Sequence from={s(autarkie.startSec)} durationInFrames={s(autarkie.durationSec)}>
          <AutarkieScene
            value={autarkie.value}
            unit={autarkie.unit}
            caption={autarkie.caption}
            captionPos={autarkie.captionPos}
            blockPos={autarkie.blockPos}
          />
        </Sequence>

        <Sequence from={s(prognose.startSec)} durationInFrames={s(prognose.durationSec)}>
          <PrognoseScene
            value={prognose.value}
            unit={prognose.unit}
            caption={prognose.caption}
            captionPos={prognose.captionPos}
            blockPos={prognose.blockPos}
          />
        </Sequence>

        <Sequence from={s(objekt.startSec)} durationInFrames={s(objekt.durationSec)}>
          <ObjektScene
            name={objekt.name}
            namePos={objekt.namePos}
            ort={objekt.ort}
            caption={objekt.caption}
            captionPos={objekt.captionPos}
          />
        </Sequence>

        <Sequence from={s(anlage.startSec)} durationInFrames={s(anlage.durationSec)}>
          <AnlageScene
            heading={anlage.heading}
            headingPos={anlage.headingPos}
            value1={anlage.value1}
            label1={anlage.label1}
            value2={anlage.value2}
            label2={anlage.label2}
            rowPos={anlage.rowPos}
          />
        </Sequence>

        <Sequence from={s(verbrauch.startSec)} durationInFrames={s(verbrauch.durationSec)}>
          <VerbrauchScene
            value={verbrauch.value}
            unit={verbrauch.unit}
            caption={verbrauch.caption}
            captionPos={verbrauch.captionPos}
            blockPos={verbrauch.blockPos}
          />
        </Sequence>

        <Sequence from={s(netz.startSec)} durationInFrames={s(netz.durationSec)}>
          <NetzScene
            heading={netz.heading}
            headingPos={netz.headingPos}
            oldLabel={netz.oldLabel}
            oldValue={netz.oldValue}
            newLabel={netz.newLabel}
            newValue={netz.newValue}
            caption={netz.caption}
            captionPos={netz.captionPos}
            barsPos={netz.barsPos}
          />
        </Sequence>

        <Sequence from={s(fazit.startSec)} durationInFrames={s(fazit.durationSec)}>
          <FazitScene
            heading={fazit.heading}
            headingPos={fazit.headingPos}
            chip1={fazit.chip1}
            chip2={fazit.chip2}
            chip3={fazit.chip3}
            rowPos={fazit.rowPos}
            caption={fazit.caption}
            captionPos={fazit.captionPos}
          />
        </Sequence>

        <Sequence from={s(cta.startSec)} durationInFrames={s(cta.durationSec)}>
          <CtaScene
            heading={cta.heading}
            headingPos={cta.headingPos}
            row1={cta.row1}
            row1Sub={cta.row1Sub}
            row2={cta.row2}
            row2Sub={cta.row2Sub}
            rowsPos={cta.rowsPos}
          />
        </Sequence>

        <Sequence from={s(endkarte.startSec)} durationInFrames={s(endkarte.durationSec)}>
          <EndkarteScene
            pillText={endkarte.pillText}
            pillPos={endkarte.pillPos}
            logoPos={endkarte.logoPos}
          />
        </Sequence>

        {/* Untertitel: nur in den Luecken zwischen den Szenen. Die Szenen selbst
            bleiben unveraendert; ihre Start/Dauer-Werte sind hier die Sperrzeiten. */}
        <SubtitleTrack
          pages={captionsJson.pages}
          blocked={[autarkie, prognose, objekt, anlage, verbrauch, netz, fazit, cta, endkarte]}
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
