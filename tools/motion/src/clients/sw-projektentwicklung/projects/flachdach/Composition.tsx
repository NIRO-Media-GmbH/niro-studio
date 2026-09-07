// ============================================================
// SW Projektentwicklung — Video 04 "Flachdach-Erklärung"
// 9:16 Overlay, 79,47 s — Inhalt aus 04_Flachdach-Erklaerung_V1.srt
// CI wie Video 01/02: Orange #FF8022, Anthrazit #2E2D2C, Montserrat, Radius 10.
//
// Anders als bei Video 01 liegt hier ein WORT-SRT vor (231 Cues). Jede Grafik
// haengt deshalb am exakten Wortende ihres Stichworts + 0,1–0,6 s Nachlauf.
// Regel aus dem Kundenfeedback: nie vor dem gesprochenen Wort einblenden.
//
// Der Sprecher redet Dialekt und das ASR hat mitgeschrieben, was es gehoert
// hat. Im Bild steht die korrekte Fassung:
//   „Ost-West-Pfauenlage"  → Ost-West-Aufständerung
//   „reingeklegt"          → reingelegt
//   „Angrifffläche"        → Angriffsfläche
//   „net" / „wegwählen"    → nicht / wegfallen
//
// Footage: 04_Flachdach-Erklaerung_V1.mp4, 2160x3840, 25 fps, 79,509 s.
// Komposition steht auf 79,47 s (2385 Frames), damit der letzte Frame noch
// Bild hat. Die Endkarte musste dafuer von 4,5 s auf 3,15 s.
//
// Alle Elemente liegen UNTERHALB der Gesichts-Zone (Pflicht-Check CLAUDE.md).
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
import captionsJson from "../../captions/flachdach.json";

// loadFont() alleine blockiert den Render NICHT — in Video 03 fehlten dadurch
// auf einzelnen Frames die Glyphen einer Zeile, im Video ein Flackern.
// delayRender haelt jeden Frame an, bis die Schrift wirklich geladen ist.
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

const dichtSchema = timingSchema.extend({
  headline: z.string().describe("Kernaussage (orange)"),
  headlinePos: posSchema.describe("Position: Kernaussage"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
});

const ostWestSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  leftLabel: z.string().describe("Label links"),
  rightLabel: z.string().describe("Label rechts"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  dachPos: posSchema.describe("Position: Zelt-Grafik"),
});

const winkelSchema = timingSchema.extend({
  value: z.string().describe("Winkel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Winkel-Grafik"),
});

const schieneSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile (kommt mit den Steinen)"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Schienen-Grafik"),
});

const durchstossenSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  subline: z.string().describe("Unterzeile"),
  blockPos: posSchema.describe("Position: Block"),
});

const auflegenSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Grafik"),
});

const klemmenSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  row1: z.string().describe("Klemme 1"),
  row1Sub: z.string().describe("Klemme 1 — Zusatz"),
  row2: z.string().describe("Klemme 2"),
  row2Sub: z.string().describe("Klemme 2 — Zusatz"),
  rowsPos: posSchema.describe("Position: Karte"),
});

const fertigSchema = timingSchema.extend({
  line1: z.string().describe("Zwischenschritt"),
  line1Pos: posSchema.describe("Position: Zwischenschritt"),
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
});

const suedSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption: z.string().describe("Unterzeile"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Grafik"),
});

const unterschiedSchema = timingSchema.extend({
  heading: z.string().describe("Überschrift"),
  headingPos: posSchema.describe("Position: Überschrift"),
  caption: z.string().describe("Unterzeile (kommt mit „Angriffsfläche“)"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Grafik"),
});

const windfangSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  caption1: z.string().describe("Unterzeile 1"),
  caption2: z.string().describe("Unterzeile 2 (löst Unterzeile 1 ab)"),
  captionPos: posSchema.describe("Position: Unterzeile"),
  diagramPos: posSchema.describe("Position: Grafik"),
});

const endkarteSchema = timingSchema.extend({
  fazitText: z.string().describe("Fazit-Zeile"),
  fazitPos: posSchema.describe("Position: Fazit"),
  pillText: z.string().describe("Text im Button"),
  pillPos: posSchema.describe("Position: Button"),
  logoPos: posSchema.describe("Position: Logo"),
});

export const swFlachdachSchema = projectPropsSchema.extend({
  footageFile: z
    .string()
    .describe("Datei im Material/Video-Ordner (leer = Platzhalter-Hintergrund)"),
  dicht: dichtSchema.describe("Szene 1: Kein Dichtigkeitsproblem"),
  ostWest: ostWestSchema.describe("Szene 2: Ost-West-Aufständerung"),
  winkel: winkelSchema.describe("Szene 3: 10 Grad aufgewinkelt"),
  schiene: schieneSchema.describe("Szene 4: Schiene + Ballast"),
  durchstossen: durchstossenSchema.describe("Szene 5: Keine Dachdurchdringung"),
  auflegen: auflegenSchema.describe("Szene 6: Module auflegen"),
  klemmen: klemmenSchema.describe("Szene 7: Mittel- und Endklemme"),
  fertig: fertigSchema.describe("Szene 8: Verkabeln → fertige Anlage"),
  sued: suedSchema.describe("Szene 9: Süd-Aufständerung"),
  unterschied: unterschiedSchema.describe("Szene 10: Angriffsfläche für Wind"),
  windfang: windfangSchema.describe("Szene 11: Windfangblech"),
  endkarte: endkarteSchema.describe("Szene 12: Endkarte"),
  subtitles: subtitlesSchema.describe("Untertitel — laufen nur, wenn keine Szene aktiv ist"),
});

export type Props = z.infer<typeof swFlachdachSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

const ORANGE = "#FF8022";
const ORANGE_LIGHT = "#FF9A4D";
const DARK = "#2E2D2C";
const WHITE = "#FFFFFF";
const STONE = "#8A8681";
const ROOF = "#6E6A65";
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

// Federn konvergieren gegen 1, erreichen es aber nie exakt (0,9999…).
// Ein Element mit Deckkraft < 1 bekommt in Chrome eine eigene Render-Surface,
// die dadurch dauerhaft bestehen bleibt und auf einzelnen Frames Kindknoten
// weglaesst — in Video 03 fiel so eine ganze Textzeile auf jedem achten Frame
// aus. Der fertige Export dieser Komposition ist nachweislich nicht betroffen
// (Frame-fuer-Frame geprueft), settle() verhindert es fuer kuenftige Renders.
const settle = (v: number) => (v > 0.999 ? 1 : v);

// Chrome laesst beim Einzelframe-Rendern gelegentlich die Glyphen eines
// Textknotens weg, wenn dieser eine eigene animierte `transform` traegt und in
// einem bereits transformierten Eltern-Knoten steckt. Im Export sah man das als
// Flackern (Video 03, „Hagelwiderstandsklasse", fuenf Frames). Reproduzierbar
// nur in voller Aufloesung und nicht bei jedem Lauf.
// Regel: Textknoten werden ueber `position: relative` + `left`/`top` versetzt,
// nicht ueber transform. Reine Grafik-Elemente duerfen transform behalten.


// Ein Solarmodul in Seitenansicht — im 230-px-Band ist kein Platz fuer die
// Aufsicht mit Zellraster aus Video 01/02. Die schmale Kante liest sich
// ausserdem richtig, weil hier die Neigung die Aussage ist.
const PanelSide: React.FC<{ w: number; h: number; glow?: number }> = ({ w, h, glow = 0 }) => (
  <div
    style={{
      width: w,
      height: h,
      borderRadius: 3,
      background: `linear-gradient(180deg, #4A4845 0%, ${DARK} 45%, #1A1918 100%)`,
      border: `1px solid #57544F`,
      boxSizing: "border-box",
      boxShadow: `0 6px 20px rgba(0,0,0,0.55)${glow > 0 ? `, 0 0 ${glow}px ${ORANGE}66` : ""}`,
      position: "relative",
      overflow: "hidden",
    }}
  >
    {/* Lichtkante — sonst verschwindet die dunkle Kante vor dunkler Footage */}
    <div
      style={{
        position: "absolute",
        top: 1,
        left: 2,
        right: 2,
        height: Math.max(1, h * 0.16),
        borderRadius: 2,
        background: "rgba(255,255,255,0.22)",
      }}
    />
  </div>
);

// Flachdach-Kante als Bezugslinie. Ohne sie schweben Schiene, Steine und
// Module im Nichts und die Aussage „nichts wird durchstossen" verpufft.
const RoofLine: React.FC<{ w: number }> = ({ w }) => (
  <div
    style={{
      width: w,
      height: 8,
      borderRadius: 4,
      // Deutlich heller als im ersten Entwurf: dort war die Kante vor dunklem
      // Hintergrund praktisch unsichtbar — und ohne sichtbares Dach verpufft
      // die Aussage „liegt nur drauf, nichts geht hindurch".
      background: `linear-gradient(180deg, #C9C4BD 0%, ${ROOF} 55%, #4C4945 100%)`,
      boxShadow: "0 4px 14px rgba(0,0,0,0.6)",
    }}
  />
);

// Aufgeständertes Modul in Seitenansicht: Dachkante, niedrige Vorderstütze,
// hohe Hinterstütze, Modul quer darüber. Drei Szenen brauchen exakt dieses
// Bild (Unterkonstruktion, Angriffsfläche, Windfangblech) — und in allen
// dreien ist der OFFENE SPALT unter der hohen Rückseite die eigentliche
// Aussage. Deshalb Stützen statt Dreiecken: nur so bleibt der Spalt sichtbar.
const ROOF_H = 8;
const PANEL_H = 20;

// Szene 10 und 11 zeigen dieselbe Süd-Aufständerung — einmal ohne, einmal mit
// Windfangblech. Gemeinsame Masse, damit der Schnitt dazwischen sitzt.
// 18° statt der 10° aus der Ost-West-Variante: bei Süd ist der Spalt hinten
// deutlich hoeher, und genau dieser Spalt ist die Angriffsflaeche.
const RIG_SPAN = 210;
const RIG_TILT = 18;
const RIG_FRONT = 12;

const rigGeometry = (span: number, tiltDeg: number, postFront: number) => {
  const rad = (tiltDeg * Math.PI) / 180;
  // Modullänge so, dass die waagerechte Projektion genau dem Stützenabstand
  // entspricht — dann liegen beide Enden exakt auf den Stützenköpfen.
  const panelW = Math.round(span / Math.cos(rad));
  const rise = Math.round(panelW * Math.sin(rad));
  const postBack = postFront + rise;
  return { panelW, postBack, height: ROOF_H + postBack + PANEL_H };
};

const TiltRig: React.FC<{
  w: number;
  span: number;
  tiltDeg: number;
  postFront: number;
  roofProg: number;
  frontProg: number;
  backProg: number;
  panelProg: number;
  panelDrop?: number;
  glow?: number;
}> = ({ w, span, tiltDeg, postFront, roofProg, frontProg, backProg, panelProg, panelDrop = 0, glow = 0 }) => {
  const { panelW, postBack, height } = rigGeometry(span, tiltDeg, postFront);

  return (
    <div style={{ position: "relative", width: w, height }}>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          transform: `scaleX(${roofProg})`,
          opacity: roofProg,
        }}
      >
        <RoofLine w={w} />
      </div>

      {/* Hohe Stütze LINKS, niedrige rechts: die Module schauen nach rechts —
          und rechts liegt in Szene 9 der Süd-Pfeil. Damit zeigen alle Szenen
          dieselbe Orientierung, „hinten" ist überall dieselbe Seite. */}
      {[
        { offset: -span / 2, h: postBack, p: backProg },
        { offset: span / 2, h: postFront, p: frontProg },
      ].map((post, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            bottom: ROOF_H,
            left: `calc(50% + ${post.offset}px)`,
            transform: `translateX(-50%) scaleY(${post.p})`,
            transformOrigin: "bottom center",
            opacity: post.p,
            width: 10,
            height: post.h,
            borderRadius: 4,
            backgroundColor: "rgba(255,255,255,0.5)",
            boxShadow: "0 3px 10px rgba(0,0,0,0.5)",
          }}
        />
      ))}

      <div
        style={{
          position: "absolute",
          bottom: ROOF_H + (postFront + postBack) / 2 - PANEL_H / 2,
          left: "50%",
          transform: `translateX(-50%) translateY(${panelDrop}px) rotate(${tiltDeg}deg)`,
          opacity: settle(panelProg),
        }}
      >
        <PanelSide w={panelW} h={PANEL_H} glow={glow} />
      </div>
    </div>
  );
};

// Pfeil fuer den Wind: Balken + Spitze aus CSS-Borders (kein SVG noetig).
const WindArrow: React.FC<{ len: number; thickness: number; opacity: number }> = ({
  len,
  thickness,
  opacity,
}) => (
  <div style={{ display: "flex", alignItems: "center", opacity }}>
    <div
      style={{
        width: len,
        height: thickness,
        borderRadius: thickness,
        backgroundColor: "rgba(255,255,255,0.85)",
      }}
    />
    <div
      style={{
        width: 0,
        height: 0,
        borderTop: `${thickness * 2.4}px solid transparent`,
        borderBottom: `${thickness * 2.4}px solid transparent`,
        borderLeft: `${thickness * 3.4}px solid rgba(255,255,255,0.85)`,
      }}
    />
  </div>
);

// =============================================================
// SZENE 1 — „Man hat kein Dichtigkeitsproblem."
// =============================================================

const DichtScene: React.FC<{
  headline: string;
  headlinePos: Pos;
  caption: string;
  captionPos: Pos;
}> = ({ headline, headlinePos, caption, captionPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const slam = spring({ frame, fps, config: { damping: 7, stiffness: 280 } });
  const rule = spring({ frame: frame - 8, fps, config: SLAM });
  // 2,16 s spricht er „Das ist immer die erste Frage" — Szene startet 1,9 s,
  // also Frame 8 … die Zeile kommt bewusst erst auf 14, damit der Satz laeuft.
  const capProg = spring({ frame: frame - 40, fps, config: SMOOTH });

  // Startskalierung 1,15 statt 1,2: die Zeile ist mit 24 Zeichen die breiteste
  // im ganzen Video, bei 1,2 stiess der Ueberschwung an die Safe-Zone-Seiten.
  const scale = interpolate(slam, [0, 1], [1.15, 1]);
  const blur = interpolate(slam, [0, 0.55, 1], [14, 3, 0], { extrapolateRight: "clamp" });
  const shake = frame < 12 ? Math.sin(frame * 8) * (12 - frame) * 1.1 : 0;

  const ring = spring({ frame: frame - 6, fps, config: { damping: 20, stiffness: 60 } });
  const ringScale = interpolate(ring, [0, 1], [0, 3.0]);
  const ringOpacity = interpolate(ring, [0, 0.3, 1], [0.75, 0.3, 0]);

  const y = stage.top + stage.height * 0.34;

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
            top: y + headlinePos.y - height * FACE_BOTTOM,
            left: width / 2 + headlinePos.x,
            width: height * 0.13,
            height: height * 0.13,
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
          top: y + headlinePos.y,
          left: width / 2 + headlinePos.x + shake,
          transform: `translate(-50%, -50%) scale(${scale * exitScale})`,
          fontFamily: FONT,
          fontSize: height * 0.0265,
          fontWeight: 900,
          color: ORANGE,
          letterSpacing: 0.5,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: `0 4px 26px rgba(0,0,0,0.9), 0 0 50px ${ORANGE}55`,
          filter: `blur(${blur}px)`,
          opacity: settle(slam),
        }}
      >
        {headline}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.56,
          left: width / 2,
          transform: `translateX(-50%) scaleX(${rule})`,
          width: stage.innerWidth * 0.34,
          height: 4,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${ORANGE_LIGHT}, ${ORANGE})`,
          boxShadow: `0 0 16px ${ORANGE}90`,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.78 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(capProg, [0, 1], [14, 0])}px)`,
          opacity: settle(capProg),
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
// SZENE 2 — „… eine Ost-West-Aufständerung … wie so ein kleines Zelt."
// =============================================================

const OstWestScene: React.FC<{
  title: string;
  titlePos: Pos;
  leftLabel: string;
  rightLabel: string;
  caption: string;
  captionPos: Pos;
  dachPos: Pos;
}> = ({ title, titlePos, leftLabel, rightLabel, caption, captionPos, dachPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame: frame - 2, fps, config: PUNCH });
  // Die beiden Zeltseiten klappen versetzt auf — erst Ost, dann West. Das ist
  // genau das Bild, das der Sprecher mit „in zwei Seiten" meint.
  const leftProg = spring({ frame: frame - 10, fps, config: BOUNCE });
  const rightProg = spring({ frame: frame - 16, fps, config: BOUNCE });
  // „wie so ein kleines Zelt" faellt bei 15,4 s, Szene startet 11,9 s.
  const capProg = spring({ frame: frame - 120, fps, config: SMOOTH });

  const panelW = 168;
  const panelH = 26;
  const labelFS = height * 0.0155;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(titleProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(titleProg),
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
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.48 + dachPos.y,
          left: width / 2 + dachPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.022,
        }}
      >
        <div
          style={{
            fontFamily: FONT,
            fontSize: labelFS,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 3,
            opacity: leftProg,
            textShadow: shadow(),
          }}
        >
          {leftLabel}
        </div>

        {/* Zelt: zwei gegenlaeufig geneigte Module, die sich am First treffen.
            −2 px Abstand laesst die Kanten sauber aneinanderstossen. */}
        <div style={{ display: "flex", alignItems: "center", marginBottom: panelW * 0.09 }}>
          <div
            style={{
              transform: `rotate(${interpolate(leftProg, [0, 1], [0, -10])}deg)`,
              transformOrigin: "right center",
              opacity: leftProg,
            }}
          >
            <PanelSide w={panelW} h={panelH} glow={18} />
          </div>
          <div
            style={{
              marginLeft: -2,
              transform: `rotate(${interpolate(rightProg, [0, 1], [0, 10])}deg)`,
              transformOrigin: "left center",
              opacity: rightProg,
            }}
          >
            <PanelSide w={panelW} h={panelH} glow={18} />
          </div>
        </div>

        <div
          style={{
            fontFamily: FONT,
            fontSize: labelFS,
            fontWeight: 900,
            color: WHITE,
            letterSpacing: 3,
            opacity: rightProg,
            textShadow: shadow(),
          }}
        >
          {rightLabel}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.88 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
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
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 3 — „Die Module werden immer 10 Grad aufgewinkelt."
// =============================================================

const WinkelScene: React.FC<{
  value: string;
  caption: string;
  captionPos: Pos;
  diagramPos: Pos;
}> = ({ value, caption, captionPos, diagramPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const base = spring({ frame, fps, config: SLAM });
  // Das Modul kippt aus der Waagerechten hoch — die Bewegung IST die Aussage.
  const tilt = spring({ frame: frame - 6, fps, config: { damping: 16, stiffness: 110 } });
  const valueProg = spring({ frame: frame - 12, fps, config: SLAM });
  const capProg = spring({ frame: frame - 48, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.14) * 0.4 + 0.6;

  const lineW = 210;
  const angle = interpolate(tilt, [0, 1], [0, -10]);

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.40 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.035,
        }}
      >
        <div style={{ position: "relative", width: lineW, height: 56, opacity: base }}>
          {/* Waagerechte Dachkante als Bezug */}
          <div
            style={{
              position: "absolute",
              bottom: 8,
              left: 0,
              width: lineW,
              height: 5,
              borderRadius: 3,
              backgroundColor: "rgba(255,255,255,0.35)",
              transform: `scaleX(${base})`,
              transformOrigin: "left center",
            }}
          />
          {/* Das aufgewinkelte Modul */}
          <div
            style={{
              position: "absolute",
              bottom: 13,
              left: 0,
              transform: `rotate(${angle}deg)`,
              transformOrigin: "left bottom",
            }}
          >
            <PanelSide w={lineW * 0.92} h={20} glow={22 * glow} />
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          <div
            style={{
              transform: `scale(${interpolate(valueProg, [0, 1], [1.5, 1])})`,
              transformOrigin: "left center",
              opacity: valueProg,
              fontFamily: FONT,
              fontSize: height * 0.044,
              fontWeight: 900,
              color: ORANGE,
              lineHeight: 1,
              whiteSpace: "nowrap",
              textShadow: `0 0 ${30 * glow}px ${ORANGE}80, 0 4px 18px rgba(0,0,0,0.85)`,
            }}
          >
            {value}
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.85 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
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
// SZENE 4 — „… nur eine Schiene gespannt und da werden Steine reingelegt."
// =============================================================

const SchieneScene: React.FC<{
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
  const roofProg = spring({ frame: frame - 2, fps, config: SLAM });
  const railProg = spring({ frame: frame - 6, fps, config: SLAM });
  // „Steine" faellt bei 26,16 s, Szene startet 25,6 s → Frame 17.
  const capProg = spring({ frame: frame - 20, fps, config: SMOOTH });

  const diagW = 430;
  const stoneW = 62;
  const stoneH = 24;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(titleProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(titleProg),
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
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          width: diagW,
          height: 74,
        }}
      >
        {/* Dachkante */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            transform: `scaleX(${roofProg})`,
            transformOrigin: "center",
            opacity: roofProg,
          }}
        >
          <RoofLine w={diagW} />
        </div>

        {/* Schiene — liegt AUF dem Dach, nichts geht hindurch */}
        <div
          style={{
            position: "absolute",
            bottom: 7,
            left: "50%",
            transform: `translateX(-50%) scaleX(${railProg})`,
            width: diagW * 0.78,
            height: 12,
            borderRadius: 6,
            background: `linear-gradient(180deg, ${ORANGE_LIGHT}, ${ORANGE})`,
            boxShadow: `0 0 20px ${ORANGE}80`,
            opacity: settle(railProg),
          }}
        />

        {/* Ballast: drei Steine fallen versetzt in die Schiene */}
        {[-1, 0, 1].map((slot, i) => {
          const drop = spring({ frame: frame - (17 + i * 5), fps, config: BOUNCE });
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                bottom: 19,
                left: `calc(50% + ${slot * 130}px)`,
                transform: `translateX(-50%) translateY(${interpolate(drop, [0, 1], [-46, 0])}px)`,
                opacity: drop,
                width: stoneW,
                height: stoneH,
                borderRadius: 5,
                background: `linear-gradient(180deg, #A5A19B 0%, ${STONE} 60%, #6B6762 100%)`,
                boxShadow: "0 5px 14px rgba(0,0,0,0.55)",
              }}
            />
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          // 0,87 statt 0,90: bei 0,90 endete die Zeile im Review exakt auf
          // 1104 px — der Unterkante der Safe Zone. Kein Puffer.
          top: stage.top + stage.height * 0.87 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
          fontFamily: FONT,
          fontSize: height * 0.0165,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 2,
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
// SZENE 5 — „… und nichts durchstoßen oder ähnliches."
// =============================================================

const DurchstossenScene: React.FC<{
  title: string;
  subline: string;
  blockPos: Pos;
}> = ({ title, subline, blockPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit(5);

  // Kurze Szene (2,4 s) — die Federn sind entsprechend gestaucht, damit die
  // Ausblende nicht mitten in die Einblende faellt.
  const badge = spring({ frame, fps, config: BOUNCE });
  const textProg = spring({ frame: frame - 4, fps, config: SLAM });

  const badgeSize = 58;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.58 + blockPos.y,
          left: width / 2 + blockPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.028,
        }}
      >
        <div
          style={{
            width: badgeSize,
            height: badgeSize,
            borderRadius: "50%",
            border: `4px solid ${ORANGE}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${interpolate(badge, [0, 1], [0.2, 1])}) rotate(${interpolate(badge, [0, 1], [-70, 0])}deg)`,
            opacity: settle(badge),
            boxShadow: `0 0 26px ${ORANGE}70, 0 6px 18px rgba(0,0,0,0.5)`,
            backgroundColor: "rgba(0,0,0,0.45)",
            flexShrink: 0,
          }}
        >
          <div style={{ fontFamily: FONT, fontSize: height * 0.02, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
            ✕
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 4,
            position: "relative",
            left: interpolate(textProg, [0, 1], [-26, 0]),
            opacity: settle(textProg),
          }}
        >
          <div
            style={{
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
          <div
            style={{
              fontFamily: FONT,
              fontSize: height * 0.0155,
              fontWeight: 700,
              color: ORANGE_LIGHT,
              letterSpacing: 2,
              whiteSpace: "nowrap",
              textShadow: shadow(0.9),
            }}
          >
            {subline}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 6 — „… auf diese Unterkonstruktion die Module gelegt."
// =============================================================

const AuflegenScene: React.FC<{
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
  const baseProg = spring({ frame: frame - 3, fps, config: SLAM });
  // Das Modul legt sich von oben auf die Unterkonstruktion.
  const layProg = spring({ frame: frame - 14, fps, config: { damping: 15, stiffness: 100 } });
  // „befestigt" faellt bei 37,48 s, Szene startet 32,9 s → Frame 137. Die
  // Szene endet bei 37,9 s, deshalb kommt die Zeile schon auf 120 (36,9 s),
  // sonst stuende sie nur einen Wimpernschlag.
  const capProg = spring({ frame: frame - 66, fps, config: SMOOTH });

  const diagW = 400;
  const span = 260;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(titleProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(titleProg),
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
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
        }}
      >
        <TiltRig
          w={diagW}
          span={span}
          tiltDeg={10}
          postFront={12}
          roofProg={baseProg}
          frontProg={spring({ frame: frame - 6, fps, config: BOUNCE })}
          backProg={spring({ frame: frame - 10, fps, config: BOUNCE })}
          panelProg={layProg}
          panelDrop={interpolate(layProg, [0, 1], [-56, 0])}
          glow={20}
        />
      </div>

      <div
        style={{
          position: "absolute",
          // 0,87 statt 0,90: bei 0,90 endete die Zeile im Review exakt auf
          // 1104 px — der Unterkante der Safe Zone. Kein Puffer.
          top: stage.top + stage.height * 0.87 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
          fontFamily: FONT,
          fontSize: height * 0.0165,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 2,
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
// SZENE 7 — Mittelklemme → Endklemme
// =============================================================

const KlemmenScene: React.FC<{
  heading: string;
  headingPos: Pos;
  row1: string;
  row1Sub: string;
  row2: string;
  row2Sub: string;
  rowsPos: Pos;
}> = ({ heading, headingPos, row1, row1Sub, row2, row2Sub, rowsPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });

  // Wie in Video 01: nur EINE Karte traegt Deckung. Zwischen Gesichts-Zone
  // (864 px) und Safe-Zone-Unterkante (1104 px) liegen 240 px — zwei gestapelte
  // Karten plus Ueberschrift passen dort nicht. Die Sprechzeiten liegen ohnehin
  // 4,5 s auseinander, ein Wechsel verliert also keine Information.
  // Szene startet 39,9 s. „Endklemme" endet 44,16 s → Frame (44,3 − 39,9)·30.
  const rows = [
    { text: row1, sub: row1Sub, at: 0 },
    { text: row2, sub: row2Sub, at: 135 },
  ];

  const activeIndex = rows.reduce((acc, row, i) => (frame >= row.at ? i : acc), 0);
  const active = rows[activeIndex];
  const prog = spring({ frame: frame - active.at, fps, config: SLAM });

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.06 + headingPos.y,
          left: width / 2 + headingPos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(headProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(headProg),
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

      <div
        // key erzwingt einen echten Neuaufbau beim Wechsel — sonst liefe die
        // Einflug-Feder beim zweiten Punkt nicht neu an.
        key={activeIndex}
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.54 + rowsPos.y,
          left: width / 2 + rowsPos.x,
          transform: `translate(-50%, -50%) translateX(${interpolate(prog, [0, 1], [-90, 0])}px) scale(${exitScale})`,
          opacity: settle(prog),
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
        <div style={{ fontFamily: FONT, fontSize: height * 0.022, fontWeight: 900, color: ORANGE, lineHeight: 1 }}>
          ✓
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
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 8 — „… verkabelt, dann habe ich meine fertige Anlage."
// =============================================================

const FertigScene: React.FC<{
  line1: string;
  line1Pos: Pos;
  pillText: string;
  pillPos: Pos;
}> = ({ line1, line1Pos, pillText, pillPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const lineProg = spring({ frame, fps, config: PUNCH });
  // „fertige Anlage" faellt bei 48,32 s, Szene startet 47,6 s → Frame 22.
  const pillProg = spring({ frame: frame - 48, fps, config: SLAM });
  const glow = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const breathe = 1 + Math.sin(frame * 0.18) * 0.02;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.20 + line1Pos.y,
          left: width / 2 + line1Pos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(lineProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: lineProg,
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
        {line1}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.66 + pillPos.y,
          left: width / 2 + pillPos.x,
          transform: `translate(-50%, -50%) scale(${interpolate(pillProg, [0, 1], [0.3, 1]) * breathe * exitScale})`,
          opacity: pillProg,
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
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 9 — „… nur als Südaufständerung … eine Reihe, in Süd ausgerichtet."
// =============================================================

const SuedScene: React.FC<{
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
  // „eine Reihe" faellt bei 57,04 s, Szene startet 54,2 s → Frame 85.
  const capProg = spring({ frame: frame - 108, fps, config: SMOOTH });
  const glow = Math.sin(frame * 0.14) * 0.4 + 0.6;

  const panelW = 118;
  const panelH = 20;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(titleProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(titleProg),
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
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          display: "flex",
          alignItems: "center",
          gap: width * 0.026,
        }}
      >
        {/* Drei Module, alle in dieselbe Richtung geneigt = eine Reihe */}
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {[0, 1, 2].map((i) => {
            const p = spring({ frame: frame - (4 + i * 5), fps, config: BOUNCE });
            return (
              <div
                key={i}
                style={{
                  // +16°: hohe Kante links, Modulfläche zeigt nach rechts —
                  // dorthin, wo der SÜD-Pfeil steht.
                  transform: `rotate(${interpolate(p, [0, 1], [0, 16])}deg)`,
                  transformOrigin: "center",
                  opacity: settle(p),
                }}
              >
                <PanelSide w={panelW} h={panelH} glow={16 * glow} />
              </div>
            );
          })}
        </div>

        {/* Richtungspfeil nach Sueden — zeigt in die Richtung, in die die
            Module geneigt sind. Ein nach unten zeigendes Dreieck (erster
            Entwurf) las sich wie eine Markierung statt wie eine Ausrichtung. */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 5,
            opacity: spring({ frame: frame - 18, fps, config: SMOOTH }),
          }}
        >
          <div style={{ display: "flex", alignItems: "center" }}>
            <div
              style={{
                width: 26,
                height: 5,
                borderRadius: 3,
                backgroundColor: ORANGE,
              }}
            />
            <div
              style={{
                width: 0,
                height: 0,
                borderTop: "10px solid transparent",
                borderBottom: "10px solid transparent",
                borderLeft: `14px solid ${ORANGE}`,
                filter: `drop-shadow(0 0 ${12 * glow}px ${ORANGE}90)`,
              }}
            />
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontSize: height * 0.0155,
              fontWeight: 900,
              color: ORANGE,
              letterSpacing: 3,
              textShadow: shadow(),
            }}
          >
            SÜD
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          // 0,87 statt 0,90: bei 0,90 endete die Zeile im Review exakt auf
          // 1104 px — der Unterkante der Safe Zone. Kein Puffer.
          top: stage.top + stage.height * 0.87 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
          fontFamily: FONT,
          fontSize: height * 0.0165,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 2,
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
// SZENE 10 — „… der einzige Unterschied … da habe ich eine Angriffsfläche."
// =============================================================

const UnterschiedScene: React.FC<{
  heading: string;
  headingPos: Pos;
  caption: string;
  captionPos: Pos;
  diagramPos: Pos;
}> = ({ heading, headingPos, caption, captionPos, diagramPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const headProg = spring({ frame, fps, config: PUNCH });
  const panelProg = spring({ frame: frame - 6, fps, config: BOUNCE });
  // „Angrifffläche" endet 64,60 s, Szene startet 61,4 s → Frame 96.
  const capProg = spring({ frame: frame - 114, fps, config: SMOOTH });

  const diagW = 320;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + headingPos.y,
          left: width / 2 + headingPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(headProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(headProg),
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
        {heading}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          width: diagW,
        }}
      >
        <TiltRig
          w={diagW}
          span={RIG_SPAN}
          tiltDeg={RIG_TILT}
          postFront={RIG_FRONT}
          roofProg={panelProg}
          frontProg={panelProg}
          backProg={panelProg}
          panelProg={panelProg}
        />

        {/* Wind faehrt von links in den offenen Spalt unter dem Modul.
            Die Pfeile laufen durch — genau das ist die Angriffsflaeche. */}
        {[0, 1, 2].map((i) => {
          const w = (frame - (14 + i * 6)) % 34;
          const t = w < 0 ? 0 : w / 34;
          const fade = interpolate(t, [0, 0.15, 0.75, 1], [0, 1, 1, 0]);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                bottom: 12 + i * 16,
                left: interpolate(t, [0, 1], [-34, diagW * 0.62]),
              }}
            >
              <WindArrow len={30} thickness={3} opacity={fade * 0.9 * panelProg} />
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          // 0,87 statt 0,90: bei 0,90 endete die Zeile im Review exakt auf
          // 1104 px — der Unterkante der Safe Zone. Kein Puffer.
          top: stage.top + stage.height * 0.87 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(capProg, [0, 1], [12, 0])}px)`,
          opacity: settle(capProg),
          fontFamily: FONT,
          fontSize: height * 0.0175,
          fontWeight: 800,
          color: ORANGE_LIGHT,
          letterSpacing: 2,
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
// SZENE 11 — „… ein Windfangblech, dass der Wind hinten nicht durch kann."
// =============================================================

const WindfangScene: React.FC<{
  title: string;
  titlePos: Pos;
  caption1: string;
  caption2: string;
  captionPos: Pos;
  diagramPos: Pos;
}> = ({ title, titlePos, caption1, caption2, captionPos, diagramPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const stage = useStage();
  const { exitProg, exitScale } = useExit();

  const titleProg = spring({ frame, fps, config: PUNCH });
  const panelProg = spring({ frame: frame - 4, fps, config: BOUNCE });
  // Das Blech schliesst die Rueckseite — es faehrt hoch, das ist die Aussage.
  const blechProg = spring({ frame: frame - 12, fps, config: { damping: 14, stiffness: 130 } });

  // Zwei Unterzeilen loesen einander ab (nie beide gleichzeitig — im 230-px-Band
  // ist nur eine Zeile Platz). Szene startet 67,6 s.
  // „durch kann" endet 69,84 s → Frame 27 fuer Zeile 1.
  // „brauchen wir hier nicht" endet 71,48 s → Frame 81 fuer Zeile 2.
  const CAP1 = 27;
  const CAP2 = 81;
  const cap1Prog = spring({ frame: frame - CAP1, fps, config: SMOOTH });
  const cap2Prog = spring({ frame: frame - CAP2, fps, config: SMOOTH });
  const showCap2 = frame >= CAP2;

  const diagW = 320;
  // Gleiche Geometrie wie in Szene 10 — der Zuschauer sieht dasselbe Gestell,
  // nur mit geschlossener Rueckseite. Deshalb der gemeinsame Rig.
  const { postBack } = rigGeometry(RIG_SPAN, RIG_TILT, RIG_FRONT);
  const blechX = diagW / 2 - RIG_SPAN / 2 - 14;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.12 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(titleProg, [0, 1], [-14, 0])}px) scale(${exitScale})`,
          opacity: settle(titleProg),
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
        {title}
      </div>

      <div
        style={{
          position: "absolute",
          top: stage.top + stage.height * 0.50 + diagramPos.y,
          left: width / 2 + diagramPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          width: diagW,
        }}
      >
        <TiltRig
          w={diagW}
          span={RIG_SPAN}
          tiltDeg={RIG_TILT}
          postFront={RIG_FRONT}
          roofProg={panelProg}
          frontProg={panelProg}
          backProg={panelProg}
          panelProg={panelProg}
        />

        {/* Das Windfangblech schliesst die hohe Rueckseite (links) —
            es waechst genau bis auf Hoehe der hinteren Stuetze. */}
        <div
          style={{
            position: "absolute",
            bottom: ROOF_H,
            left: blechX,
            width: 8,
            height: interpolate(blechProg, [0, 1], [0, postBack]),
            borderRadius: 3,
            background: `linear-gradient(180deg, ${ORANGE_LIGHT}, ${ORANGE})`,
            boxShadow: `0 0 18px ${ORANGE}90`,
            opacity: settle(blechProg),
          }}
        />

        {/* Wind laeuft wie in Szene 10 von links an — kommt aber nur bis
            zum Blech und prallt dort ab, statt unter das Modul zu fahren. */}
        {[0, 1].map((i) => {
          const w = (frame - (18 + i * 8)) % 30;
          const t = w < 0 ? 0 : w / 30;
          const fade = interpolate(t, [0, 0.15, 0.7, 1], [0, 1, 0.9, 0]);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                bottom: ROOF_H + 14 + i * 18,
                left: interpolate(t, [0, 1], [-30, blechX - 28]),
              }}
            >
              <WindArrow len={26} thickness={3} opacity={fade * 0.8 * blechProg} />
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          // 0,87 statt 0,90: bei 0,90 endete die Zeile im Review exakt auf
          // 1104 px — der Unterkante der Safe Zone. Kein Puffer.
          top: stage.top + stage.height * 0.87 + captionPos.y,
          left: width / 2 + captionPos.x,
          transform: `translate(-50%, -50%) translateY(${interpolate(showCap2 ? cap2Prog : cap1Prog, [0, 1], [12, 0])}px)`,
          opacity: showCap2 ? cap2Prog : cap1Prog,
          fontFamily: FONT,
          fontSize: height * 0.0165,
          fontWeight: 700,
          color: WHITE,
          letterSpacing: 2,
          whiteSpace: "nowrap",
          textShadow: shadow(0.95),
        }}
      >
        {showCap2 ? caption2 : caption1}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SZENE 12 — Endkarte: „Relativ simpel." → Fragen? → Logo
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

  // Kein Staffellauf mehr. In Video 01/02 loeste das Logo den Text ab; dort
  // war die Endkarte 6,7 s lang. Hier bleiben ab 76,3 s nur 95 Frames — jede
  // Phase bekaeme unter einer Sekunde und waere nicht lesbar.
  // Deshalb: Pill und Logo stehen GEMEINSAM, 2,4 s lang, uebereinander.
  // Szene startet 76,3 s, „Fragen" faellt 77,28 s → Frame 21 fuer beide.
  const IN = 21;
  const pill = spring({ frame: frame - IN, fps, config: SLAM });
  const logo = spring({ frame: frame - IN - 6, fps, config: SMOOTH });

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

      {
        <div
          style={{
            position: "absolute",
            // 0,75 statt 0,814: die Pill atmet (breathe) und federt beim
            // Einflug ueber. Im Vollsequenz-Review von Video 03 lag die
            // Unterkante dadurch auf 1114 px, 10 px unter der Safe Zone —
            // der Spitzenwert taucht nur in wenigen Frames auf und faellt
            // bei Stichproben nicht auf. Hier derselbe Aufbau, also derselbe Wert.
            top: stage.top + stage.height * 0.75 + pillPos.y,
            left: width / 2 + pillPos.x,
            transform: `translate(-50%, -50%) scale(${interpolate(pill, [0, 1], [0.3, 1]) * breathe * exitScale})`,
            opacity: settle(pill),
            display: "flex",
            alignItems: "center",
            // Seitenpolster 0,038 statt 0,045: „FRAGEN? GERNE MELDEN" ist die
            // breiteste Pill im Video, im Feder-Ueberschwung ragte sie mit dem
            // groesseren Polster 2 px ueber die Safe Zone hinaus.
            padding: `${stage.height * 0.04}px ${width * 0.038}px`,
            borderRadius: 9999,
            backgroundColor: ORANGE,
            boxShadow: `0 10px 34px rgba(0,0,0,0.5), 0 0 ${34 * glow}px ${ORANGE}70`,
          }}
        >
          {/* Das separate Fragezeichen ist raus — es stand vor „FRAGEN?" und
              doppelte damit das Satzzeichen im Text. */}
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
      }

      {
        <div
          style={{
            position: "absolute",
            top: stage.top - stage.height * 0.06 + logoPos.y,
            left: width / 2 + logoPos.x,
            transform: `translate(-50%, -50%) scale(${interpolate(logo, [0, 1], [0.9, 1]) * exitScale})`,
            opacity: settle(logo),
          }}
        >
          <Img
            src={staticFile("clients/sw-projektentwicklung/logo-stack-white.png")}
            style={{
              // Das Logo steht bewusst rund 55 px UEBER der Buehnenoberkante,
              // also im unteren Rand der Default-Gesichts-Zone. Geprueft: der
              // Sprecher endet in diesem Clip bei ca. 680 px, das Logo beginnt
              // bei 830 px — es deckt kein Gesicht ab. Ohne diese Ausnahme
              // klebte es an der Pill.
              // 0,64 statt 0,90 wie in Video 01/02: dort stand das Logo allein
              // auf der Buehne. Hier teilt es sich die 230 px mit der Pill —
              // Logo oben, Pill darunter, dazwischen ~14 px Luft.
              // Gemessen: Block 894 bis 1100 px. Gesichts-Zone endet bei 864,
              // Safe Zone bei 1104.
              height: stage.height * 0.75,
              display: "block",
              filter: `drop-shadow(0 2px 3px rgba(0,0,0,0.55)) drop-shadow(0 0 14px rgba(0,0,0,0.5))`,
            }}
          />
        </div>
      }
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

export const SWFlachdach: React.FC<Props> = ({
  transparent = false,
  review,
  footageFile = "",
  subtitles = SUBTITLE_DEFAULTS,
  // Alle Startzeiten liegen NACH dem jeweiligen Stichwort im Wort-SRT.
  dicht = {
    startSec: 0.9,
    durationSec: 6.2,
    headline: "Kein Dichtigkeitsproblem",
    headlinePos: P0,
    caption: "Die erste Frage überhaupt",
    captionPos: P0,
  },
  ostWest = {
    startSec: 10.9,
    durationSec: 5.6,
    title: "Ost-West-Aufständerung",
    titlePos: P0,
    leftLabel: "OST",
    rightLabel: "WEST",
    caption: "wie ein kleines Zelt",
    captionPos: P0,
    dachPos: P0,
  },
  winkel = {
    startSec: 18.8,
    durationSec: 3.6,
    value: "10°",
    caption: "Module aufgewinkelt",
    captionPos: P0,
    diagramPos: P0,
  },
  schiene = {
    startSec: 25.6,
    durationSec: 3.6,
    title: "Nur eine Schiene",
    titlePos: P0,
    caption: "Steine als Ballast — mehr nicht",
    captionPos: P0,
    diagramPos: P0,
  },
  durchstossen = {
    startSec: 29.2,
    durationSec: 2.4,
    title: "Keine Dachdurchdringung",
    subline: "nichts wird durchstoßen",
    blockPos: P0,
  },
  auflegen = {
    startSec: 32.4,
    durationSec: 5.0,
    title: "Unterkonstruktion",
    titlePos: P0,
    caption: "Module werden aufgelegt",
    captionPos: P0,
    diagramPos: P0,
  },
  klemmen = {
    startSec: 39.3,
    durationSec: 6.4,
    heading: "Befestigung",
    headingPos: P0,
    row1: "Mittelklemme",
    row1Sub: "zwischen zwei Modulen",
    row2: "Endklemme",
    row2Sub: "am Ende jeder Reihe",
    rowsPos: P0,
  },
  fertig = {
    startSec: 46.9,
    durationSec: 4.6,
    line1: "Module verkabeln",
    line1Pos: P0,
    pillText: "ANLAGE FERTIG",
    pillPos: P0,
  },
  sued = {
    startSec: 53.6,
    durationSec: 5.6,
    title: "Süd-Aufständerung",
    titlePos: P0,
    caption: "eine Reihe, nach Süden ausgerichtet",
    captionPos: P0,
    diagramPos: P0,
  },
  unterschied = {
    startSec: 60.9,
    durationSec: 4.4,
    heading: "Der einzige Unterschied",
    headingPos: P0,
    caption: "Angriffsfläche für Wind",
    captionPos: P0,
    diagramPos: P0,
  },
  windfang = {
    startSec: 67.6,
    durationSec: 4.2,
    title: "Windfangblech",
    titlePos: P0,
    caption1: "Wind kommt hinten nicht durch",
    caption2: "bei Ost-West nicht nötig",
    captionPos: P0,
    diagramPos: P0,
  },
  endkarte = {
    startSec: 76.3,
    durationSec: 3.2,
    fazitText: "",
    fazitPos: P0,
    pillText: "FRAGEN? GERNE MELDEN",
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

        <Sequence from={s(dicht.startSec)} durationInFrames={s(dicht.durationSec)}>
          <DichtScene
            headline={dicht.headline}
            headlinePos={dicht.headlinePos}
            caption={dicht.caption}
            captionPos={dicht.captionPos}
          />
        </Sequence>

        <Sequence from={s(ostWest.startSec)} durationInFrames={s(ostWest.durationSec)}>
          <OstWestScene
            title={ostWest.title}
            titlePos={ostWest.titlePos}
            leftLabel={ostWest.leftLabel}
            rightLabel={ostWest.rightLabel}
            caption={ostWest.caption}
            captionPos={ostWest.captionPos}
            dachPos={ostWest.dachPos}
          />
        </Sequence>

        <Sequence from={s(winkel.startSec)} durationInFrames={s(winkel.durationSec)}>
          <WinkelScene
            value={winkel.value}
            caption={winkel.caption}
            captionPos={winkel.captionPos}
            diagramPos={winkel.diagramPos}
          />
        </Sequence>

        <Sequence from={s(schiene.startSec)} durationInFrames={s(schiene.durationSec)}>
          <SchieneScene
            title={schiene.title}
            titlePos={schiene.titlePos}
            caption={schiene.caption}
            captionPos={schiene.captionPos}
            diagramPos={schiene.diagramPos}
          />
        </Sequence>

        <Sequence from={s(durchstossen.startSec)} durationInFrames={s(durchstossen.durationSec)}>
          <DurchstossenScene
            title={durchstossen.title}
            subline={durchstossen.subline}
            blockPos={durchstossen.blockPos}
          />
        </Sequence>

        <Sequence from={s(auflegen.startSec)} durationInFrames={s(auflegen.durationSec)}>
          <AuflegenScene
            title={auflegen.title}
            titlePos={auflegen.titlePos}
            caption={auflegen.caption}
            captionPos={auflegen.captionPos}
            diagramPos={auflegen.diagramPos}
          />
        </Sequence>

        <Sequence from={s(klemmen.startSec)} durationInFrames={s(klemmen.durationSec)}>
          <KlemmenScene
            heading={klemmen.heading}
            headingPos={klemmen.headingPos}
            row1={klemmen.row1}
            row1Sub={klemmen.row1Sub}
            row2={klemmen.row2}
            row2Sub={klemmen.row2Sub}
            rowsPos={klemmen.rowsPos}
          />
        </Sequence>

        <Sequence from={s(fertig.startSec)} durationInFrames={s(fertig.durationSec)}>
          <FertigScene
            line1={fertig.line1}
            line1Pos={fertig.line1Pos}
            pillText={fertig.pillText}
            pillPos={fertig.pillPos}
          />
        </Sequence>

        <Sequence from={s(sued.startSec)} durationInFrames={s(sued.durationSec)}>
          <SuedScene
            title={sued.title}
            titlePos={sued.titlePos}
            caption={sued.caption}
            captionPos={sued.captionPos}
            diagramPos={sued.diagramPos}
          />
        </Sequence>

        <Sequence from={s(unterschied.startSec)} durationInFrames={s(unterschied.durationSec)}>
          <UnterschiedScene
            heading={unterschied.heading}
            headingPos={unterschied.headingPos}
            caption={unterschied.caption}
            captionPos={unterschied.captionPos}
            diagramPos={unterschied.diagramPos}
          />
        </Sequence>

        <Sequence from={s(windfang.startSec)} durationInFrames={s(windfang.durationSec)}>
          <WindfangScene
            title={windfang.title}
            titlePos={windfang.titlePos}
            caption1={windfang.caption1}
            caption2={windfang.caption2}
            captionPos={windfang.captionPos}
            diagramPos={windfang.diagramPos}
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
          blocked={[dicht, ostWest, winkel, schiene, durchstossen, auflegen, klemmen, fertig, sued, unterschied, windfang, endkarte]}
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
