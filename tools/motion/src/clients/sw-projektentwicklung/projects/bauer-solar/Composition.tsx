// ============================================================
// SW Projektentwicklung — Video 03 "Bauer Solar Modul"
// 9:16 Overlay, 56,0 s — Inhalt aus 03_BauerSolar-Modul_V1.srt
// CI wie Video 01/02/04: Orange #FF8022, Anthrazit #2E2D2C, Montserrat.
//
// MARKENNAME: Der Hersteller heisst „Bauer Solar" — in zwei Woertern, mit
// „-er". Die Videodatei heisst faelschlich 03_BauSolar-Modul_V1.mp4; im Bild
// steht ausschliesslich die korrekte Schreibweise.
//
// Wort-SRT mit 149 Cues. Nach dem Feedback zu Video 04 gilt: eine Grafik
// setzt ein, sobald ihr Stichwort BEGINNT — nicht nach dem Wortende plus
// Nachlauf. Alle Startzeiten liegen 0,05–0,15 s hinter dem Wortanfang.
//
// ASR-Korrekturen: „Solar-Zaun-Verwender" → als Solar-Zaun verwenden,
// „vorherrige" → vorherige.
//
// Alle Elemente liegen UNTERHALB der Gesichts-Zone (Pflicht-Check CLAUDE.md).
// Einzige dokumentierte Ausnahme: das Logo der Endkarte, siehe dort.
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
import captionsJson from "../../captions/bauer-solar.json";

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

const brandSchema = timingSchema.extend({
  name: z.string().describe("Markenname"),
  namePos: posSchema.describe("Position: Markenname"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const leistungSchema = timingSchema.extend({
  value: z.string().describe("Leistung (Zahl)"),
  unit: z.string().describe("Einheit"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  blockPos: posSchema.describe("Position: Block"),
});

const glasSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Schnitt-Grafik"),
});

const zellenSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Zellraster"),
});

const zaunSchema = timingSchema.extend({
  row1: z.string().describe("Aussage 1"),
  row1Sub: z.string().describe("Aussage 1 — Zusatz"),
  row2: z.string().describe("Aussage 2 (löst Aussage 1 ab)"),
  row2Sub: z.string().describe("Aussage 2 — Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const steckerSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  goodText: z.string().describe("Was verbaut wird"),
  goodSub: z.string().describe("Zusatz"),
  badText: z.string().describe("Was NICHT verbaut wird"),
  badSub: z.string().describe("Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const staerkeSchema = timingSchema.extend({
  value: z.string().describe("Glasstärke"),
  valueCaption: z.string().describe("Unterzeile zur Stärke"),
  klasseText: z.string().describe("Klasse (löst die Stärke ab)"),
  klasseValue: z.string().describe("Klassenwert"),
  blockPos: posSchema.describe("Position: Block"),
});

const vergleichSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  ownLabel: z.string().describe("Label eigene Module"),
  ownValue: z.string().describe("Wert eigene Module"),
  otherLabel: z.string().describe("Label andere Hersteller"),
  otherValue: z.string().describe("Wert andere Hersteller"),
  barsPos: posSchema.describe("Position: Balken"),
});

const brandschutzSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  value: z.string().describe("Klasse"),
  blockPos: posSchema.describe("Position: Block"),
});

const beweisSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const testsSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  test1: z.string().describe("Test 1"),
  test2: z.string().describe("Test 2"),
  test3: z.string().describe("Test 3"),
  rowPos: posSchema.describe("Position: Test-Reihe"),
});

const endkarteSchema = timingSchema.extend({
  fazitText: z.string().describe("Fazit-Zeile (leer = wird nicht gerendert)"),
  fazitPos: posSchema.describe("Position: Fazit"),
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  logoPos: posSchema.describe("Position: Logo"),
});

export const swBauerSolarSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  brand: brandSchema.describe("Szene 1: Bauer Solar — German Brand"),
  leistung: leistungSchema.describe("Szene 2: 460 Watt"),
  glas: glasSchema.describe("Szene 3: Glas-Glas-Bifazial"),
  zellen: zellenSchema.describe("Szene 4: Zellen sichtbar"),
  zaun: zaunSchema.describe("Szene 5: Solar-Zaun / beide Seiten"),
  stecker: steckerSchema.describe("Szene 6: Stäubli statt MC4"),
  staerke: staerkeSchema.describe("Szene 7: 2 mm → Hagelklasse 3"),
  vergleich: vergleichSchema.describe("Szene 8: 2,0 vs 1,6 mm"),
  brandschutz: brandschutzSchema.describe("Szene 9: Brandschutzklasse A"),
  beweis: beweisSchema.describe("Szene 10: schon getestet"),
  tests: testsSchema.describe("Szene 11: Härte, Feuer, Schlag"),
  endkarte: endkarteSchema.describe("Szene 12: Endkarte"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swBauerSolarSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

const ORANGE = "#FF8022";
const ORANGE_LIGHT = "#FF9A4D";
const DARK = "#2E2D2C";
const WHITE = "#FFFFFF";
const GLASS = "#9FC7DA";

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

// Deutschlandflagge fuer „German Brand". Als CSS-Verlauf statt als Bilddatei:
// bei dieser Groesse (30 px) traegt kein PNG mehr Details, und ein Asset waere
// eine weitere Datei, die mitgepflegt werden muesste.
// Der helle Rahmen ist Pflicht — Schwarz auf dunklem Modul verschwindet sonst,
// und die Flagge saehe nach Rot-Gold statt Schwarz-Rot-Gold aus.
const GermanFlag: React.FC<{ h: number }> = ({ h }) => (
  <div
    style={{
      width: h * (5 / 3),
      height: h,
      borderRadius: 2,
      overflow: "hidden",
      border: "1px solid rgba(255,255,255,0.65)",
      boxSizing: "border-box",
      background: "linear-gradient(180deg, #000000 0 33.34%, #DD0000 33.34% 66.67%, #FFCE00 66.67% 100%)",
      boxShadow: "0 2px 8px rgba(0,0,0,0.7)",
      flexShrink: 0,
    }}
  />
);

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
// SZENE 1 — „Wir verwenden die Module von Bauer Solar. Das ist eine German Brand."
// =============================================================

const BrandScene: React.FC<{
  name: string;
  namePos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ name, namePos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 3,1 s — „Bauer" beginnt 3,04 s.
  const slam = spring({ frame, fps, config: SLAM });
  const rule = spring({ frame: frame - 8, fps, config: SLAM });
  // „German" beginnt 4,48 s → Frame 41.
  const capProg = spring({ frame: frame - 41, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.36 + namePos.y,
          left: width / 2 + namePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(slam, [0, 1], [1.18, 1]) * exitScale})`,
          opacity: settle(slam),
          fontFamily: FONT,
          fontSize: height * 0.030,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 6,
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
          top: stage.top + stage.height * 0.60 + namePos.y,
          left: width / 2 + namePos.x,
          transform: `translate(-50%, -50%) scaleX(${rule}) scale(${exitScale})`,
          width: width * 0.30,
          height: 5,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${ORANGE}, ${ORANGE_LIGHT})`,
          boxShadow: `0 0 20px ${ORANGE}80`,
        }}
      />

      {/* Statt der Standard-Caption: Flagge und Text als eine Zeile, damit
          beide zusammen einlaufen und mittig bleiben. Hoehe wie CAP_Y. */}
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * CAP_Y + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
          display: "flex",
          alignItems: "center",
          gap: width * 0.011,
        }}
      >
        <GermanFlag h={height * 0.0155} />
        <div
          style={{
            fontFamily: FONT,
            fontSize: height * 0.0165,
            fontWeight: 700,
            color: ORANGE_LIGHT,
            letterSpacing: 2,
            whiteSpace: "nowrap",
            textShadow: shadow(0.95),
          }}
        >
          {caption}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 2 — „das 460 Watt Solarmodul von denen"
// =============================================================

const LeistungScene: React.FC<{
  value: string;
  unit: string;
  caption: string;
  captionPos: Pos;
  blockPos: Pos;
}> = ({ value, unit, caption, captionPos, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 7,4 s — „460" beginnt 7,36 s.
  const valProg = spring({ frame, fps, config: SLAM });
  // „Watt" beginnt 8,16 s → Frame 23.
  const unitProg = spring({ frame: frame - 23, fps, config: PUNCH });
  // „Solarmodul" beginnt 8,56 s → Frame 35.
  const capProg = spring({ frame: frame - 35, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.40 + blockPos.y,
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "baseline",
          gap: width * 0.018,
        }}
      >
        <div
          style={{
            transform: `scale(${interpolate(valProg, [0, 1], [1.3, 1])})`,
            opacity: settle(valProg),
            fontFamily: FONT,
            fontSize: height * 0.042,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 1,
            lineHeight: 1,
            textShadow: shadow(0.95),
          }}
        >
          {value}
        </div>
        <div
          style={{
            position: "relative",
            top: interpolate(unitProg, [0, 1], [16, 0]),
            opacity: settle(unitProg),
            fontFamily: FONT,
            fontSize: height * 0.024,
            fontWeight: 900,
            color: ORANGE,
            letterSpacing: 3,
            textTransform: "uppercase",
            lineHeight: 1,
            textShadow: shadow(0.95),
          }}
        >
          {unit}
        </div>
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} y={0.70} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 3 — „ein Glas-Glas-Bifazialmodul"
// =============================================================

const GlasScene: React.FC<{
  title: string;
  titlePos: Pos;
  caption: string;
  captionPos: Pos;
  diagramPos: Pos;
}> = ({ title, titlePos, caption, captionPos, diagramPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame, fps, config: PUNCH });
  const cells = spring({ frame: frame - 8, fps, config: SMOOTH });
  // Die beiden Glasscheiben fahren von oben und unten zusammen — das ist die
  // ganze Aussage von „Glas-Glas": Zellen zwischen zwei Scheiben.
  const topGlass = spring({ frame: frame - 14, fps, config: BOUNCE });
  const botGlass = spring({ frame: frame - 18, fps, config: BOUNCE });
  const capProg = spring({ frame: frame - 40, fps, config: SMOOTH });

  const diagW = 300;
  const glassH = 14;
  const cellH = 22;

  const Glass: React.FC<{ prog: number; from: number }> = ({ prog, from }) => (
    <div
      style={{
        width: diagW,
        height: glassH,
        borderRadius: 3,
        background: `linear-gradient(180deg, rgba(255,255,255,0.55), ${GLASS})`,
        border: "1px solid rgba(255,255,255,0.75)",
        boxSizing: "border-box",
        boxShadow: "0 3px 12px rgba(0,0,0,0.5)",
        transform: `translateY(${interpolate(prog, [0, 1], [from, 0])}px)`,
        opacity: settle(prog),
      }}
    />
  );

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <Heading text={title} pos={titlePos} prog={titleProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 5,
          // Dunkle Traegerplatte: der Schnitt liegt teils vor dem hellen Modul
          // und der Glasscheibe fehlt dort jeder Kontrast.
          padding: 8,
          borderRadius: 6,
          backgroundColor: "rgba(0,0,0,0.55)",
          boxShadow: "0 8px 26px rgba(0,0,0,0.5)",
        }}
      >
        <Glass prog={topGlass} from={-30} />

        <div
          style={{
            width: diagW,
            height: cellH,
            borderRadius: 2,
            background: `linear-gradient(180deg, #3A3835, #1F1E1D)`,
            border: "1px solid #57544F",
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-evenly",
            opacity: settle(cells),
          }}
        >
          {Array.from({ length: 8 }, (_, i) => (
            <div
              key={i}
              style={{
                width: 22,
                height: cellH - 9,
                borderRadius: 1,
                backgroundColor: ORANGE,
                opacity: interpolate(cells, [0, 1], [0, 0.85]),
                boxShadow: `0 0 8px ${ORANGE}70`,
              }}
            />
          ))}
        </div>

        <Glass prog={botGlass} from={30} />
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 4 — „man kann direkt die Zellen erkennen"
// =============================================================

const ZellenScene: React.FC<{
  title: string;
  titlePos: Pos;
  caption: string;
  captionPos: Pos;
  diagramPos: Pos;
}> = ({ title, titlePos, caption, captionPos, diagramPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame, fps, config: PUNCH });
  // „erkennen" beginnt 15,40 s, Szene startet 15,2 s → Frame 6.
  const capProg = spring({ frame: frame - 20, fps, config: SMOOTH });

  const cols = 5;
  const rows = 2;
  const cell = 34;
  const gap = 5;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <Heading text={title} pos={titlePos} prog={titleProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, ${cell}px)`,
          gap,
          // Wie beim Glas-Schnitt: ohne dunkle Platte verschwindet das Raster
          // vor dem hellen Modul im Hintergrund.
          padding: 8,
          borderRadius: 6,
          backgroundColor: "rgba(0,0,0,0.55)",
          boxShadow: "0 8px 26px rgba(0,0,0,0.5)",
        }}
      >
        {Array.from({ length: cols * rows }, (_, i) => {
          // Die Zellen zuenden nacheinander — so liest sich das Raster als
          // Zellstruktur und nicht als Kachelmuster.
          const p = spring({ frame: frame - 4 - i * 2, fps, config: PUNCH });
          return (
            <div
              key={i}
              style={{
                width: cell,
                height: cell,
                borderRadius: 3,
                background: `linear-gradient(140deg, #3A3835, #1C1B1A)`,
                border: `1px solid ${interpolate(p, [0, 1], [0.2, 1]) > 0.5 ? ORANGE : "#57544F"}`,
                boxSizing: "border-box",
                opacity: settle(p),
                transform: `scale(${interpolate(p, [0, 1], [0.4, 1])})`,
                boxShadow: `0 0 ${interpolate(p, [0, 1], [0, 10])}px ${ORANGE}55`,
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: 3,
                  right: 3,
                  height: 1.5,
                  backgroundColor: ORANGE,
                  opacity: 0.55 * p,
                }}
              />
            </div>
          );
        })}
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 5 — „als Solar-Zaun verwenden … von beiden Seiten die Produktion"
// =============================================================

const ZaunScene: React.FC<{
  row1: string;
  row1Sub: string;
  row2: string;
  row2Sub: string;
  rowsPos: Pos;
}> = ({ row1, row1Sub, row2, row2Sub, rowsPos }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();
  const { fps } = useVideoConfig();

  // Szene startet 18,6 s — „Solar-Zaun" beginnt 18,56 s.
  // Zweite Aussage bewusst NICHT auf „von beiden Seiten" (19,96 s → Frame 42):
  // dort stand die erste Karte nur 1,4 s und war nicht zu lesen. Jetzt auf
  // „Produktion" (20,68 s) plus Puffer → Frame 75, also 2,5 s pro Karte.
  const rows = [
    { text: row1, sub: row1Sub, at: 0 },
    { text: row2, sub: row2Sub, at: 75 },
  ];
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        // key erzwingt einen echten Neuaufbau beim Wechsel — sonst liefe die
        // Einflug-Feder beim zweiten Punkt nicht neu an.
        key={activeIndex}
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + rowsPos.y,
          left: width / 2 + rowsPos.x,
          transform: "translate(-50%, -50%)",
        }}
      >
        <MarkCard mark="✓" markColor={ORANGE} text={active.text} sub={active.sub} prog={prog} scale={exitScale} />
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — „Stäubli-Stecker und keine Standard-MC4-Stecker"
// =============================================================

const SteckerScene: React.FC<{
  heading: string;
  headingPos: Pos;
  goodText: string;
  goodSub: string;
  badText: string;
  badSub: string;
  rowsPos: Pos;
}> = ({ heading, headingPos, goodText, goodSub, badText, badSub, rowsPos }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });

  // Szene startet 25,1 s — „Stäubli-Stecker" beginnt 25,04 s.
  // Die Gegenkarte lief zuerst auf Frame 45 („keine Standard-MC4", 26,60 s).
  // Damit stand die Stäubli-Karte nur 1,5 s. Jetzt Frame 66 (27,3 s) — das
  // Wort ist da laengst gefallen, beide Karten stehen ueber 2 s.
  const rows = [
    { mark: "✓", color: ORANGE, text: goodText, sub: goodSub, at: 0 },
    { mark: "✕", color: "#B9B4AE", text: badText, sub: badSub, at: 66 },
  ];
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

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
          mark={active.mark}
          markColor={active.color}
          text={active.text}
          sub={active.sub}
          prog={prog}
          scale={exitScale}
        />
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 7 — „2 mm Stärke … Hagelwiderstandsklasse 3"
// =============================================================

const StaerkeScene: React.FC<{
  value: string;
  valueCaption: string;
  klasseText: string;
  klasseValue: string;
  blockPos: Pos;
}> = ({ value, valueCaption, klasseText, klasseValue, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 29,7 s — „2 mm" beginnt 29,68 s.
  // „Hagelwiderstandsklasse" beginnt 32,60 s → Frame 87.
  const SWITCH = 87;
  const valProg = spring({ frame, fps, config: SLAM });
  const capProg = spring({ frame: frame - 34, fps, config: SMOOTH });
  const klasseProg = spring({ frame: frame - SWITCH, fps, config: SLAM });
  // Umschalten statt Ueberblenden: zwei Bloecke an derselben Stelle duerfen
  // sich nie mit Rest-Alpha ueberlagern (gelernt in Video 02).
  const showValue = frame < SWITCH;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {showValue && (
        <>
          <div
            style={{
              position: "absolute",
              top: stage.top + stage.height * 0.38 + blockPos.y,
              left: width / 2 + blockPos.x,
              transform: `translate(-50%, -50%) scale(${interpolate(valProg, [0, 1], [1.25, 1]) * exitScale})`,
              opacity: settle(valProg),
              fontFamily: FONT,
              fontSize: height * 0.036,
              fontWeight: 900,
              color: WHITE,
              letterSpacing: 2,
              whiteSpace: "nowrap",
              textShadow: shadow(0.95),
            }}
          >
            {value}
          </div>
          <Caption text={valueCaption} pos={P0} prog={capProg} color={ORANGE_LIGHT} y={0.67} />
        </>
      )}

      {!showValue && (
        <div
          style={{
            position: "absolute",
            top: stage.top + stage.height * 0.48 + blockPos.y,
            left: width / 2 + blockPos.x,
            transform: `translate(-50%, -50%) scale(${exitScale})`,
            display: "flex",
            alignItems: "center",
            gap: width * 0.022,
          }}
        >
          <div
            style={{
              position: "relative",
              left: interpolate(klasseProg, [0, 1], [-40, 0]),
              opacity: settle(klasseProg),
              fontFamily: FONT,
              fontSize: height * 0.019,
              fontWeight: 900,
              color: WHITE,
              letterSpacing: 2,
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              textShadow: shadow(0.95),
            }}
          >
            {klasseText}
          </div>
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: "50%",
              border: `4px solid ${ORANGE}`,
              backgroundColor: "rgba(0,0,0,0.45)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transform: `scale(${interpolate(klasseProg, [0, 1], [0.3, 1])})`,
              opacity: settle(klasseProg),
              boxShadow: `0 0 26px ${ORANGE}70, 0 6px 18px rgba(0,0,0,0.5)`,
            }}
          >
            <div style={{ fontFamily: FONT, fontSize: height * 0.024, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
              {klasseValue}
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 8 — „andere Hersteller haben nur 1,6 mm"
// =============================================================

const VergleichScene: React.FC<{
  heading: string;
  headingPos: Pos;
  ownLabel: string;
  ownValue: string;
  otherLabel: string;
  otherValue: string;
  barsPos: Pos;
}> = ({ heading, headingPos, ownLabel, ownValue, otherLabel, otherValue, barsPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });
  const bar1 = spring({ frame: frame - 6, fps, config: SMOOTH });
  const bar2 = spring({ frame: frame - 16, fps, config: SMOOTH });

  // labelW 210 statt 150: „Bauer Solar" ist breiter als 150 px, lief unter den
  // Balken und war im Review als „BAUER SOL" abgeschnitten zu sehen.
  const barMax = 240;
  const labelW = 210;

  const Row: React.FC<{
    label: string;
    value: string;
    frac: number;
    color: string;
    prog: number;
  }> = ({ label, value, frac, color, prog }) => (
    <div style={{ display: "flex", alignItems: "center", gap: 16, opacity: prog }}>
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
          boxShadow: `0 4px 14px rgba(0,0,0,0.5)`,
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
    <AbsoluteFill style={{ opacity: exitProg }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.58 + barsPos.y,
          left: width / 2 + barsPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {/* 1,6 / 2,0 — die Balkenlaenge bildet das echte Verhaeltnis ab,
            nicht bloss „laenger und kuerzer". */}
        <Row label={ownLabel} value={ownValue} frac={1} color={ORANGE} prog={bar1} />
        <Row label={otherLabel} value={otherValue} frac={0.8} color="#8A8681" prog={bar2} />
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 9 — „Brandschutzklasse A"
// =============================================================

const BrandschutzScene: React.FC<{
  title: string;
  value: string;
  blockPos: Pos;
}> = ({ title, value, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const badge = spring({ frame, fps, config: BOUNCE });
  const textProg = spring({ frame: frame - 5, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + blockPos.y,
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.026,
        }}
      >
        <div
          style={{
            position: "relative",
            left: interpolate(textProg, [0, 1], [-26, 0]),
            opacity: settle(textProg),
            fontFamily: FONT,
            fontSize: height * 0.0225,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 1,
            whiteSpace: "nowrap",
            textShadow: shadow(0.95),
          }}
        >
          {title}
        </div>

        {/* Die Klasse steht RECHTS vom Begriff — wie man sie liest:
            „Brandschutzklasse A", nicht „A Brandschutzklasse". */}
        <div
          style={{
            width: 62,
            height: 62,
            borderRadius: "50%",
            border: `4px solid ${ORANGE}`,
            backgroundColor: "rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transform: `scale(${interpolate(badge, [0, 1], [0.2, 1])})`,
            opacity: settle(badge),
            boxShadow: `0 0 26px ${ORANGE}70, 0 6px 18px rgba(0,0,0,0.5)`,
          }}
        >
          <div style={{ fontFamily: FONT, fontSize: height * 0.028, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
            {value}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 10 — „dass die Module wirklich so robust sind"
// Ersetzt den frueheren Hinweis auf die alten Videos: der Verweis brachte
// nichts, die Frage nach der Robustheit leitet dagegen direkt in die
// Test-Szene ueber.
// =============================================================

const BeweisScene: React.FC<{
  title: string;
  titlePos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ title, titlePos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame, fps, config: SLAM });
  // Szene startet 43,8 s („so robust" beginnt 43,72 s). Die Unterzeile erst
  // bei „Da zeige ich euch genau" (46,68 s) → Frame 90.
  const capProg = spring({ frame: frame - 90, fps, config: SMOOTH });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.42 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(titleProg, [0, 1], [1.15, 1]) * exitScale})`,
          opacity: settle(titleProg),
          fontFamily: FONT,
          fontSize: height * 0.026,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: 3,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {title}
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 11 — „Härtetest … Feuertest … Schlagtest mit Gewicht"
// =============================================================

const TestsScene: React.FC<{
  heading: string;
  headingPos: Pos;
  test1: string;
  test2: string;
  test3: string;
  rowPos: Pos;
}> = ({ heading, headingPos, test1, test2, test3, rowPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });

  // Szene startet 49,9 s. Anders als bei Klemme/Stecker loesen sich die drei
  // Tests NICHT ab, sondern bleiben stehen — der dritte faellt erst 2,8 s
  // nach dem ersten und haette allein zu wenig Standzeit.
  // „Härtetest" 49,88 → 0 · „Feuertest" 51,08 → 36 · „Schlagtest" 52,72 → 85.
  const tests = [
    { label: test1, at: 0 },
    { label: test2, at: 36 },
    { label: test3, at: 85 },
  ];

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <Heading text={heading} pos={headingPos} prog={headProg} scale={exitScale} />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.56 + rowPos.y,
          left: width / 2 + rowPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.014,
        }}
      >
        {/* Nur gestartete Tests rendern. Sonst haelt die noch unsichtbare
            dritte Pille ihren Platz und die erste steht sichtbar links
            neben der Bildmitte. */}
        {tests.filter((t) => frame >= t.at).map((t, i) => {
          const p = spring({ frame: frame - t.at, fps, config: SLAM });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: `${stage.height * 0.045}px ${width * 0.024}px`,
                borderRadius: 9999,
                backgroundColor: "rgba(0,0,0,0.72)",
                border: `2px solid ${ORANGE}`,
                boxShadow: `0 6px 22px rgba(0,0,0,0.45)`,
                opacity: settle(p),
                transform: `scale(${interpolate(p, [0, 1], [0.5, 1])})`,
              }}
            >
              <div style={{ fontFamily: FONT, fontSize: height * 0.016, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
                ✓
              </div>
              <div
                style={{
                  fontFamily: FONT,
                  fontSize: height * 0.016,
                  fontWeight: 800,
                  color: WHITE,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                }}
              >
                {t.label}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 12 — Endkarte: „Link ist unten drin, schaut es euch gerne an."
// =============================================================

const EndkarteScene: React.FC<{
  fazitText: string;
  fazitPos: Pos;
  pillText: string;
  pillPos: Pos;
  logoPos: Pos;
}> = ({ fazitText, fazitPos, pillText, pillPos, logoPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Wie in Video 04: Logo und Pill stehen GEMEINSAM, nicht nacheinander.
  // Die Endkarte hat ab 54,0 s nur 60 Frames — ein Staffellauf gaebe jeder
  // Phase unter einer Sekunde.
  // „Link" beginnt 53,84 s, die Szene startet 54,0 s → Einsatz bei Frame 3.
  const IN = 3;
  const pill = spring({ frame: frame - IN, fps, config: SLAM });
  const logo = spring({ frame: frame - IN - 4, fps, config: SMOOTH });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.025;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {fazitText !== "" && (
        <div
          style={{
            position: "absolute",
            top: stage.top + stage.height * 0.22 + fazitPos.y,
            left: width / 2 + fazitPos.x,
            transform: `translate(-50%, -50%) scale(${exitScale})`,
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
          {fazitText}
        </div>
      )}

      <div
        style={{
          position: "absolute",
          // Das Logo steht bewusst rund 55 px UEBER der Buehnenoberkante, also
          // im unteren Rand der Default-Gesichts-Zone. Ohne diese Ausnahme
          // klebte es an der Pill. Gegen das echte Material geprueft.
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
          // 0,75 statt 0,814: die Pill atmet (breathe) und federt beim Einflug
          // ueber. Im Vollsequenz-Review lag die Unterkante dadurch auf 1114 px,
          // 10 px unter der Safe Zone. Der Spitzenwert taucht nur in wenigen
          // Frames auf und faellt bei Stichproben nicht auf.
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

export const SWBauerSolar: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Jede Startzeit liegt 0,05–0,15 s hinter dem WORTANFANG des Stichworts.
  brand = {
    startSec: 3.1,
    durationSec: 3.3,
    name: "Bauer Solar",
    namePos: P0,
    caption: "German Brand",
    captionPos: P0,
  },
  leistung = {
    startSec: 7.4,
    durationSec: 3.0,
    value: "460",
    unit: "Watt",
    caption: "pro Modul",
    captionPos: P0,
    blockPos: P0,
  },
  glas = {
    startSec: 10.9,
    durationSec: 3.6,
    title: "Glas-Glas-Bifazial",
    titlePos: P0,
    caption: "Zellen zwischen zwei Scheiben",
    captionPos: P0,
    diagramPos: P0,
  },
  zellen = {
    startSec: 15.2,
    durationSec: 2.9,
    title: "Zellen direkt sichtbar",
    titlePos: P0,
    caption: "durch das Glas erkennbar",
    captionPos: P0,
    diagramPos: P0,
  },
  zaun = {
    startSec: 18.6,
    durationSec: 5.8,
    row1: "Auch als Solar-Zaun",
    row1Sub: "Module stehen senkrecht",
    row2: "Ertrag von beiden Seiten",
    row2Sub: "die Rückseite ist aktiv",
    rowsPos: P0,
  },
  stecker = {
    startSec: 25.1,
    durationSec: 4.6,
    heading: "Stecker",
    headingPos: P0,
    goodText: "Stäubli-Stecker",
    goodSub: "Markenstecker ab Werk",
    badText: "Kein Standard-MC4",
    badSub: "",
    rowsPos: P0,
  },
  staerke = {
    startSec: 29.7,
    durationSec: 5.4,
    value: "2 mm",
    valueCaption: "Glasstärke",
    klasseText: "Hagelwiderstandsklasse",
    klasseValue: "3",
    blockPos: P0,
  },
  vergleich = {
    startSec: 36.3,
    durationSec: 3.4,
    heading: "Im Vergleich",
    headingPos: P0,
    ownLabel: "Bauer Solar",
    ownValue: "2 mm",
    otherLabel: "Andere",
    otherValue: "1,6 mm",
    barsPos: P0,
  },
  brandschutz = {
    startSec: 40.0,
    durationSec: 3.6,
    title: "Brandschutzklasse",
    value: "A",
    blockPos: P0,
  },
  beweis = {
    startSec: 43.8,
    durationSec: 5.9,
    title: "Wirklich so robust?",
    titlePos: P0,
    caption: "Wir haben es getestet",
    captionPos: P0,
  },
  tests = {
    startSec: 49.9,
    durationSec: 4.1,
    heading: "Bestanden",
    headingPos: P0,
    test1: "Härte",
    test2: "Feuer",
    test3: "Schlag",
    rowPos: P0,
  },
  endkarte = {
    startSec: 54.0,
    durationSec: 2.0,
    fazitText: "",
    fazitPos: P0,
    pillText: "LINK UNTEN DRIN",
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

        <Sequence from={s(brand.startSec)} durationInFrames={s(brand.durationSec)}>
          <BrandScene
            name={brand.name}
            namePos={brand.namePos}
            caption={brand.caption}
            captionPos={brand.captionPos}
          />
        </Sequence>

        <Sequence from={s(leistung.startSec)} durationInFrames={s(leistung.durationSec)}>
          <LeistungScene
            value={leistung.value}
            unit={leistung.unit}
            caption={leistung.caption}
            captionPos={leistung.captionPos}
            blockPos={leistung.blockPos}
          />
        </Sequence>

        <Sequence from={s(glas.startSec)} durationInFrames={s(glas.durationSec)}>
          <GlasScene
            title={glas.title}
            titlePos={glas.titlePos}
            caption={glas.caption}
            captionPos={glas.captionPos}
            diagramPos={glas.diagramPos}
          />
        </Sequence>

        <Sequence from={s(zellen.startSec)} durationInFrames={s(zellen.durationSec)}>
          <ZellenScene
            title={zellen.title}
            titlePos={zellen.titlePos}
            caption={zellen.caption}
            captionPos={zellen.captionPos}
            diagramPos={zellen.diagramPos}
          />
        </Sequence>

        <Sequence from={s(zaun.startSec)} durationInFrames={s(zaun.durationSec)}>
          <ZaunScene
            row1={zaun.row1}
            row1Sub={zaun.row1Sub}
            row2={zaun.row2}
            row2Sub={zaun.row2Sub}
            rowsPos={zaun.rowsPos}
          />
        </Sequence>

        <Sequence from={s(stecker.startSec)} durationInFrames={s(stecker.durationSec)}>
          <SteckerScene
            heading={stecker.heading}
            headingPos={stecker.headingPos}
            goodText={stecker.goodText}
            goodSub={stecker.goodSub}
            badText={stecker.badText}
            badSub={stecker.badSub}
            rowsPos={stecker.rowsPos}
          />
        </Sequence>

        <Sequence from={s(staerke.startSec)} durationInFrames={s(staerke.durationSec)}>
          <StaerkeScene
            value={staerke.value}
            valueCaption={staerke.valueCaption}
            klasseText={staerke.klasseText}
            klasseValue={staerke.klasseValue}
            blockPos={staerke.blockPos}
          />
        </Sequence>

        <Sequence from={s(vergleich.startSec)} durationInFrames={s(vergleich.durationSec)}>
          <VergleichScene
            heading={vergleich.heading}
            headingPos={vergleich.headingPos}
            ownLabel={vergleich.ownLabel}
            ownValue={vergleich.ownValue}
            otherLabel={vergleich.otherLabel}
            otherValue={vergleich.otherValue}
            barsPos={vergleich.barsPos}
          />
        </Sequence>

        <Sequence from={s(brandschutz.startSec)} durationInFrames={s(brandschutz.durationSec)}>
          <BrandschutzScene
            title={brandschutz.title}
            value={brandschutz.value}
            blockPos={brandschutz.blockPos}
          />
        </Sequence>

        <Sequence from={s(beweis.startSec)} durationInFrames={s(beweis.durationSec)}>
          <BeweisScene
            title={beweis.title}
            titlePos={beweis.titlePos}
            caption={beweis.caption}
            captionPos={beweis.captionPos}
          />
        </Sequence>

        <Sequence from={s(tests.startSec)} durationInFrames={s(tests.durationSec)}>
          <TestsScene
            heading={tests.heading}
            headingPos={tests.headingPos}
            test1={tests.test1}
            test2={tests.test2}
            test3={tests.test3}
            rowPos={tests.rowPos}
          />
        </Sequence>

        <Sequence from={s(endkarte.startSec)} durationInFrames={s(endkarte.durationSec)}>
          <EndkarteScene
            fazitText={endkarte.fazitText}
            fazitPos={endkarte.fazitPos}
            pillText={endkarte.pillText}
            pillPos={endkarte.pillPos}
            logoPos={endkarte.logoPos}
          />
        </Sequence>

        {/* Untertitel: nur in den Luecken zwischen den Szenen. Die Szenen selbst
            bleiben unveraendert; ihre Start/Dauer-Werte sind hier die Sperrzeiten. */}
        <SubtitleTrack
          pages={captionsJson.pages}
          blocked={[brand, leistung, glas, zellen, zaun, stecker, staerke, vergleich, brandschutz, beweis, tests, endkarte]}
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
