// ============================================================
// SW Projektentwicklung — Video 07 "Recruiting: Elektromeister"
// 9:16 Overlay, 25,63 s — Inhalt aus 07_Recruiting-Elektromeister_V1.srt
// CI wie Video 01–04: Orange #FF8022, Anthrazit #2E2D2C, Montserrat.
//
// BESONDERHEIT: Ab 22,8 s ist das Bild schwarz — dafuer ist die Endkarte da.
// Sie ist deshalb die einzige Szene, die NICHT im 240-px-Band bleibt: ohne
// Sprecher gibt es keine Gesichts-Zone, die freizuhalten waere. Sie nutzt die
// volle Reels-Safe-Zone (134–1104 px). Alle anderen Szenen liegen wie gewohnt
// unterhalb der Gesichts-Zone.
//
// Der Sprecher redet stark Dialekt, das ASR hat entsprechend mitgeschrieben.
// Korrekturen (im Bild steht die richtige Fassung):
//   „Elektromaster"              → Elektromeister
//   „Fotoverteilkeinlage"        → Photovoltaikanlagen
//   „das komplizierte Stär"      → das Komplizierteste
//   „Arschchutz"                 → NA-Schutz  (siehe Hinweis unten)
//   „Tarishaltgeräte"            → Tarifschaltgeräte
//   „pascht"                     → passt
//
// HINWEIS ZU „NA-SCHUTZ": Das ASR schreibt „Arschchutzanschließer". Aus dem
// Kontext (Gewerbeanlagen, direkt gefolgt von „Tarifschaltgeräte anschließen")
// ist NA-Schutz — Netz- und Anlagenschutz — die einzige sinnvolle Lesart; die
// beiden gehoeren beim gewerblichen Netzanschluss zusammen. Vom Kunden noch
// nicht bestaetigt, deshalb als Prop hinterlegt.
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
import captionsJson from "../../captions/recruiting.json";

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

const hookSchema = timingSchema.extend({
  word: z.string().describe("Anrede (schlägt ein)"),
  wordPos: posSchema.describe("Position: Anrede"),
});

const sattSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  row1: z.string().describe("Punkt 1"),
  row1Sub: z.string().describe("Punkt 1 — Zusatz"),
  row2: z.string().describe("Punkt 2 (löst Punkt 1 ab)"),
  row2Sub: z.string().describe("Punkt 2 — Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const richtigSchema = timingSchema.extend({
  line1: z.string().describe("Zeile 1"),
  line2: z.string().describe("Zeile 2 (orange)"),
  linesPos: posSchema.describe("Position: Zeilen"),
});

const gewerbeSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  row1: z.string().describe("Punkt 1"),
  row1Sub: z.string().describe("Punkt 1 — Zusatz"),
  row2: z.string().describe("Punkt 2 (löst Punkt 1 ab)"),
  row2Sub: z.string().describe("Punkt 2 — Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const rolleSchema = timingSchema.extend({
  headline: z.string().describe("Kernsatz"),
  headlinePos: posSchema.describe("Position: Kernsatz"),
  role: z.string().describe("Position/Rolle"),
  rolePos: posSchema.describe("Position: Rolle"),
});

const ctaSchema = timingSchema.extend({
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const endkarteSchema = timingSchema.extend({
  headline: z.string().describe("Überschrift"),
  role: z.string().describe("Stelle"),
  roleSuffix: z.string().describe("Zusatz zur Stelle (z. B. (m/w/d))"),
  pillText: z.string().describe("Text im Button"),
  contact: z.string().describe("Kontakt / Bewerbungsweg (leer = wird weggelassen)"),
  blockPos: posSchema.describe("Position: gesamter Block"),
});

export const swRecruitingSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  hook: hookSchema.describe("Szene 1: Anrede „Elektromeister?“"),
  satt: sattSchema.describe("Szene 2: Was nervt (zwei ✕-Karten)"),
  richtig: richtigSchema.describe("Szene 3: Dann bist du bei uns richtig"),
  gewerbe: gewerbeSchema.describe("Szene 4: Was du hier machst (zwei ✓-Karten)"),
  rolle: rolleSchema.describe("Szene 5: Wir suchen dich als Teamleiter"),
  cta: ctaSchema.describe("Szene 6: Meld dich"),
  endkarte: endkarteSchema.describe("Szene 7: Bewerbungs-Endkarte (Schwarzbild)"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swRecruitingSchema>;
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
// Fuer die Endkarte: faehrt zuegig an und schwingt NICHT ueber. Ein Ueberschwung
// kostet dort nur Standzeit, ohne etwas zu erzaehlen.
const ENTER = { damping: 18, stiffness: 220 };

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
// SZENE 1 — „Elektromeister …"
// =============================================================

const HookScene: React.FC<{ word: string; wordPos: Pos }> = ({ word, wordPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 0,3 s — das Wort beginnt 0,24 s. Erster Frame des Videos,
  // also der Hook: er schlaegt ein und bekommt eine Linie darunter.
  const slam = spring({ frame, fps, config: SLAM });
  const rule = spring({ frame: frame - 7, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.38 + wordPos.y,
          left: width / 2 + wordPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(slam, [0, 1], [1.2, 1]) * exitScale})`,
          opacity: settle(slam),
          fontFamily: FONT,
          fontSize: height * 0.030,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 4,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {word}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.62 + wordPos.y,
          left: width / 2 + wordPos.x,
          transform: `translate(-50%, -50%) scaleX(${rule}) scale(${exitScale})`,
          width: width * 0.34,
          height: 5,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${ORANGE}, ${ORANGE_LIGHT})`,
          boxShadow: `0 0 20px ${ORANGE}80`,
        }}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 2 — „hast es satt, nur PV in Einfamilienhäusern anzuschließen,
//            wo der Überspannungsschutz das Komplizierteste ist"
// =============================================================

const SattScene: React.FC<{
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

  // Szene startet 2,6 s („Photovoltaikanlage" beginnt 2,48 s).
  // „Überspannungsschutz" beginnt 5,64 s → Frame 93.
  const rows = [
    { text: row1, sub: row1Sub, at: 0 },
    { text: row2, sub: row2Sub, at: 93 },
  ];
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
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
          mark="✕"
          markColor="#B9B4AE"
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
// SZENE 3 — „dann [bist] du bei uns genau richtig"
// =============================================================

const RichtigScene: React.FC<{ line1: string; line2: string; linesPos: Pos }> = ({
  line1,
  line2,
  linesPos,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 8,45 s („dann" beginnt 8,36 s).
  // „genau richtig" beginnt 9,08 s → Frame 19 fuer die zweite Zeile.
  const l1 = spring({ frame, fps, config: SLAM });
  const l2 = spring({ frame: frame - 19, fps, config: SLAM });

  const line = (text: string, prog: number, color: string, top: number) => (
    <div
      style={{
        position: "absolute",
        top: stage.top + stage.height * top + linesPos.y,
        left: width / 2 + linesPos.x,
        transform: `translate(-50%, -50%) scale(${interpolate(prog, [0, 1], [1.15, 1]) * exitScale})`,
        opacity: settle(prog),
        fontFamily: FONT,
        fontSize: height * 0.026,
        fontWeight: 900,
        color,
        letterSpacing: 3,
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        textShadow: shadow(0.95),
      }}
    >
      {text}
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      {line(line1, l1, WHITE, 0.32)}
      {line(line2, l2, ORANGE, 0.68)}
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 4 — „hier dürftest du sogar Gewerbe … NA-Schutz … Tarifschaltgeräte"
// =============================================================

const GewerbeScene: React.FC<{
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

  // Szene startet 11,6 s („Gewerbe" beginnt 11,52 s).
  // „Tarifschaltgeräte" beginnt 14,04 s → Frame 73. Der NA-Schutz faellt
  // dazwischen (12,72 s) und steht als Zusatz auf derselben Karte — drei
  // Karten in 4,7 s waeren je unter 1,6 s und nicht lesbar.
  const rows = [
    { text: row1, sub: row1Sub, at: 0 },
    { text: row2, sub: row2Sub, at: 73 },
  ];
  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
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
          mark="✓"
          markColor={ORANGE}
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
// SZENE 5 — „hierfür suchen wir dich als Teamleiter"
// =============================================================

const RolleScene: React.FC<{
  headline: string;
  headlinePos: Pos;
  role: string;
  rolePos: Pos;
}> = ({ headline, headlinePos, role, rolePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 16,55 s („suchen wir dich" beginnt 16,44 s).
  // „Teamleiter" beginnt 17,20 s → Frame 21.
  const head = spring({ frame, fps, config: SLAM });
  const roleProg = spring({ frame: frame - 21, fps, config: PUNCH });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.26 + headlinePos.y,
          left: width / 2 + headlinePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(head, [0, 1], [1.18, 1]) * exitScale})`,
          opacity: settle(head),
          fontFamily: FONT,
          fontSize: height * 0.026,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 4,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {headline}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.72 + rolePos.y,
          left: width / 2 + rolePos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(roleProg, [0, 1], [0.4, 1]) * exitScale})`,
          opacity: settle(roleProg),
          padding: `${stage.height * 0.045}px ${width * 0.038}px`,
          borderRadius: 9999,
          backgroundColor: ORANGE,
          boxShadow: `0 10px 30px rgba(0,0,0,0.5), 0 0 ${30 * glow}px ${ORANGE}70`,
          fontFamily: FONT,
          fontSize: height * 0.021,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
        }}
      >
        {role}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — „melde dich gern bei uns, schauen wir ob du ins Team passt"
// =============================================================

const CtaScene: React.FC<{
  pillText: string;
  pillPos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ pillText, pillPos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  // Szene startet 19,6 s („melde dich" beginnt 19,52 s).
  // „schauen wir, ob du zu uns passt" beginnt 20,80 s → Frame 39.
  const pill = spring({ frame, fps, config: SLAM });
  const capProg = spring({ frame: frame - 39, fps, config: SMOOTH });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.025;

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.38 + pillPos.y,
          left: width / 2 + pillPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.3, 1]) * breathe * exitScale})`,
          opacity: settle(pill),
          padding: `${stage.height * 0.045}px ${width * 0.04}px`,
          borderRadius: 9999,
          backgroundColor: ORANGE,
          boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${34 * glow}px ${ORANGE}70`,
          fontFamily: FONT,
          fontSize: height * 0.0235,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
        }}
      >
        {pillText}
      </div>

      <Caption text={caption} pos={captionPos} prog={capProg} />
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 7 — Bewerbungs-Endkarte auf dem Schwarzbild (ab 22,8 s)
//
// Die einzige Szene ausserhalb des 240-px-Bandes. Begruendung: Ab 22,8 s ist
// das Bild schwarz, es gibt keinen Sprecher und damit keine Gesichts-Zone.
// Genutzt wird die volle Reels-Safe-Zone (134–1104 px) — sonst muesste eine
// Bewerbungs-Endkarte mit Logo, Stelle und CTA in ein Viertel der Hoehe.
// =============================================================

const SAFE_TOP = 0.07;
const SAFE_BOTTOM = 0.575;

const EndkarteScene: React.FC<{
  headline: string;
  role: string;
  roleSuffix: string;
  pillText: string;
  contact: string;
  blockPos: Pos;
}> = ({ headline, role, roleSuffix, pillText, contact, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(4);

  // Die Karte hat nur 85 Frames. Im ersten Entwurf lief der Aufbau bis Frame 46
  // plus Federweg — vollstaendig lesbar war sie damit nur 1,2 s.
  // Jetzt steht alles ab Frame 26, also 2,0 s vollstaendig im Bild.
  // Der Versatz von 2–3 Frames pro Zeile reicht, damit es aufgebaut wirkt.
  const logo = spring({ frame, fps, config: ENTER });
  const head = spring({ frame: frame - 4, fps, config: ENTER });
  const roleProg = spring({ frame: frame - 7, fps, config: ENTER });
  const suffixProg = spring({ frame: frame - 9, fps, config: ENTER });
  const pill = spring({ frame: frame - 11, fps, config: ENTER });
  const contactProg = spring({ frame: frame - 14, fps, config: ENTER });

  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const safeTop = height * SAFE_TOP;
  const safeBottom = height * SAFE_BOTTOM;

  // Alle Werte als Anteil der Safe Zone, damit der Block als Einheit sitzt.
  const at = (f: number) => safeTop + (safeBottom - safeTop) * f + blockPos.y;

  return (
    <AbsoluteFill style={{ opacity: settle(exitProg) }}>
      <div
        style={{
          position: "absolute",
          top: at(0.25),
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(logo, [0, 1], [0.94, 1]) * exitScale})`,
          opacity: settle(logo),
        }}
      >
        <Img
          src={staticFile("clients/sw-projektentwicklung/logo-stack-white.png")}
          style={{
            height: (safeBottom - safeTop) * 0.35,
            display: "block",
            filter: `drop-shadow(0 2px 3px rgba(0,0,0,0.55)) drop-shadow(0 0 14px rgba(0,0,0,0.5))`,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          top: at(0.53),
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(head, [0, 1], [1.06, 1]) * exitScale})`,
          opacity: settle(head),
          fontFamily: FONT,
          fontSize: height * 0.028,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 5,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {headline}
      </div>

      <div
        style={{
          position: "absolute",
          top: at(0.63),
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(roleProg, [0, 1], [8, 0])}px) scale(${exitScale})`,
          opacity: settle(roleProg),
          fontFamily: FONT,
          fontSize: height * 0.026,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
          textShadow: shadow(0.9),
        }}
      >
        {role}
      </div>

      {roleSuffix !== "" && (
        <div
          style={{
            position: "absolute",
            top: at(0.70),
            left: width / 2 + blockPos.x,
            transform: `translate(-50%, -50%) scale(${exitScale})`,
            opacity: settle(suffixProg),
            fontFamily: FONT,
            fontSize: height * 0.0155,
            fontWeight: 700,
            color: WHITE,
            letterSpacing: 3,
            whiteSpace: "nowrap",
            textShadow: shadow(0.9),
          }}
        >
          {roleSuffix}
        </div>
      )}

      <div
        style={{
          position: "absolute",
          top: at(0.84),
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.85, 1]) * exitScale})`,
          opacity: settle(pill),
          padding: `${height * 0.011}px ${width * 0.045}px`,
          borderRadius: 9999,
          backgroundColor: ORANGE,
          boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${34 * glow}px ${ORANGE}70`,
          fontFamily: FONT,
          fontSize: height * 0.0235,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
        }}
      >
        {pillText}
      </div>

      {contact !== "" && (
        <div
          style={{
            position: "absolute",
            top: at(0.95),
            left: width / 2 + blockPos.x,
            transform: `translate(-50%, -50%) scale(${exitScale})`,
            opacity: settle(contactProg),
            fontFamily: FONT,
            fontSize: height * 0.0145,
            fontWeight: 600,
            color: "#C9C4BD",
            letterSpacing: 2,
            whiteSpace: "nowrap",
            textShadow: shadow(0.9),
          }}
        >
          {contact}
        </div>
      )}
    </AbsoluteFill>
  );
};

// =============================================================
// HAUPTKOMPOSITION
// =============================================================

export const SWRecruiting: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Jede Startzeit liegt 0,05–0,15 s hinter dem WORTANFANG des Stichworts.
  hook = {
    startSec: 0.3,
    durationSec: 2.3,
    word: "Elektromeister?",
    wordPos: P0,
  },
  satt = {
    startSec: 2.6,
    durationSec: 5.7,
    heading: "Hast du's satt?",
    headingPos: P0,
    row1: "Nur PV am Einfamilienhaus",
    row1Sub: "immer dasselbe",
    row2: "Überspannungsschutz",
    row2Sub: "das Komplizierteste am Ganzen",
    rowsPos: P0,
  },
  richtig = {
    startSec: 8.45,
    durationSec: 2.9,
    line1: "Dann bist du",
    line2: "bei uns richtig",
    linesPos: P0,
  },
  gewerbe = {
    startSec: 11.6,
    durationSec: 4.7,
    heading: "Bei uns machst du",
    headingPos: P0,
    row1: "Gewerbeanlagen",
    row1Sub: "nicht nur Einfamilienhäuser",
    row2: "NA-Schutz & Tarifschaltgeräte",
    row2Sub: "richtige Elektrotechnik",
    rowsPos: P0,
  },
  rolle = {
    startSec: 16.55,
    durationSec: 2.9,
    headline: "Wir suchen dich",
    headlinePos: P0,
    role: "ALS TEAMLEITER",
    rolePos: P0,
  },
  cta = {
    startSec: 19.6,
    durationSec: 3.15,
    pillText: "MELD DICH GERN",
    pillPos: P0,
    caption: "Schauen wir, ob du ins Team passt",
    captionPos: P0,
  },
  endkarte = {
    startSec: 22.8,
    durationSec: 2.83,
    // Nicht noch einmal „Wir suchen dich" wie in Szene 5 — der O-Ton endet mit
    // „ob du zu uns ins Team passt", die Endkarte nimmt das auf.
    headline: "Komm ins Team",
    role: "ELEKTROMEISTER",
    roleSuffix: "als Teamleiter (m/w/d)",
    pillText: "JETZT BEWERBEN",
    contact: "sw-projektentwicklung.com",
    blockPos: P0,
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

        <Sequence from={s(hook.startSec)} durationInFrames={s(hook.durationSec)}>
          <HookScene word={hook.word} wordPos={hook.wordPos} />
        </Sequence>

        <Sequence from={s(satt.startSec)} durationInFrames={s(satt.durationSec)}>
          <SattScene
            heading={satt.heading}
            headingPos={satt.headingPos}
            row1={satt.row1}
            row1Sub={satt.row1Sub}
            row2={satt.row2}
            row2Sub={satt.row2Sub}
            rowsPos={satt.rowsPos}
          />
        </Sequence>

        <Sequence from={s(richtig.startSec)} durationInFrames={s(richtig.durationSec)}>
          <RichtigScene line1={richtig.line1} line2={richtig.line2} linesPos={richtig.linesPos} />
        </Sequence>

        <Sequence from={s(gewerbe.startSec)} durationInFrames={s(gewerbe.durationSec)}>
          <GewerbeScene
            heading={gewerbe.heading}
            headingPos={gewerbe.headingPos}
            row1={gewerbe.row1}
            row1Sub={gewerbe.row1Sub}
            row2={gewerbe.row2}
            row2Sub={gewerbe.row2Sub}
            rowsPos={gewerbe.rowsPos}
          />
        </Sequence>

        <Sequence from={s(rolle.startSec)} durationInFrames={s(rolle.durationSec)}>
          <RolleScene
            headline={rolle.headline}
            headlinePos={rolle.headlinePos}
            role={rolle.role}
            rolePos={rolle.rolePos}
          />
        </Sequence>

        <Sequence from={s(cta.startSec)} durationInFrames={s(cta.durationSec)}>
          <CtaScene
            pillText={cta.pillText}
            pillPos={cta.pillPos}
            caption={cta.caption}
            captionPos={cta.captionPos}
          />
        </Sequence>

        <Sequence from={s(endkarte.startSec)} durationInFrames={s(endkarte.durationSec)}>
          <EndkarteScene
            headline={endkarte.headline}
            role={endkarte.role}
            roleSuffix={endkarte.roleSuffix}
            pillText={endkarte.pillText}
            contact={endkarte.contact}
            blockPos={endkarte.blockPos}
          />
        </Sequence>

        {/* Untertitel: nur in den Luecken zwischen den Szenen. Die Szenen selbst
            bleiben unveraendert; ihre Start/Dauer-Werte sind hier die Sperrzeiten. */}
        <SubtitleTrack
          pages={captionsJson.pages}
          blocked={[hook, satt, richtig, gewerbe, rolle, cta, endkarte]}
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
