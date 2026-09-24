// ============================================================
// Hochzeitszauber — Aftermovie 2026, Grafik-Ebene (CI aus dem Messe-Logo)
// 3840×2160 @ 25 fps, Länge = Schnitt (timeline.json aus _intern/entwurf/schnitt.py der Charge; v5: Karten nur mit Kategorie,
// Collagen als deckende Zwischenspiele mit Kachel-Proxys aus public-hochzeitszauber/collage/).
// Gerendert als ProRes 4444 mit Alpha (Entwurf: --scale=0.5 → 1080p), liegt in Resolve auf V2
// über dem Bildschnitt. Elemente: Intro-Lockup (Logo-Typografie), Szenenkarten, Modenschau-Karte, Endcard.
// CI: Taupe #A5A195 · Elfenbein #E6E3DA · Schrift-Schwarz #303030 · Gold-Braun #B48A61 (Website) —
// Playfair Display (Serif des Logos/der Website), Ms Madi (Schreibschrift, nächste Entsprechung zum Logo),
// Source Sans 3 (Fließtext der Website). Vektor-Logo des Kunden folgt (dann Lockup durch das Logo ersetzen).
// Motion: Entrances 0,5–0,9 s ease-out (Luxus/cinematisch), Exits 0,3 s ease-in; Verben RISE, DRAW, FADE.
// ============================================================

import React from "react";
import { AbsoluteFill, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadMsMadi } from "@remotion/google-fonts/MsMadi";
import { loadFont as loadSourceSans } from "@remotion/google-fonts/SourceSans3";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import timeline from "./timeline.json";
import { LogoSVG } from "../../logo";

const ci = loadBrand("hochzeitszauber", brandJson as any);

const { fontFamily: PLAYFAIR } = loadPlayfair("normal", { weights: ["400", "500"], subsets: ["latin", "latin-ext"] });
const { fontFamily: SCRIPT } = loadMsMadi("normal", { weights: ["400"], subsets: ["latin", "latin-ext"] });
const { fontFamily: SANS } = loadSourceSans("normal", { weights: ["400", "600"], subsets: ["latin", "latin-ext"] });

// --- CI ---
const TAUPE = "#A5A195";
const IVORY = "#E6E3DA";
const INK = "#303030";
const GOLD = "#B48A61";
const BROWN = "#473E35";

// --- Layout im 1920×1080-Raster (Stage skaliert auf die Kompositionsgröße) ---
const BASE_W = 1920;
const BASE_H = 1080;
const SAFE_X = 110;
const SAFE_BOTTOM = 130;

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const EASE_IN = Easing.in(Easing.cubic);

type Tile = { src: string; notiz?: string };
type Element = {
  id: string;
  typ: "intro" | "karte" | "modenschau" | "endcard" | "collage" | "wischer" | "album";
  from: number;
  dauer: number;
  text?: string;
  kicker?: string;
  nummer?: number;
  zeilen?: string[];
  layout?: string;
  tiles?: Tile[];
  beat_frames?: number;
  a?: string;
  a_start?: number;
  b?: string;
  b_bild?: string;
  vor?: number;
};

const ELEMENTE = timeline.elemente as Element[];

export const aftermovieSchema = projectPropsSchema.extend({
  vorschauGrund: z.boolean().describe("Nur Studio: dunkle Fläche statt Transparenz, um Lesbarkeit zu prüfen"),
});

export const aftermovieDefaults: z.infer<typeof aftermovieSchema> = {
  format: "landscape-4k",
  fps: 25,
  durationInSeconds: timeline.frames / timeline.fps,
  transparent: true,
  vorschauGrund: false,
  review: { showGuides: false, showSafeZone: true, showFaceZone: false, showGrid: false, guideOpacity: 0.35 },
};

/** Dauer exakt in Frames aus der Schnitt-Timeline (kein Aufrunden über Sekunden). */
export const aftermovieMetadata = ({ props }: { props: z.infer<typeof aftermovieSchema> }) => ({
  width: 3840,
  height: 2160,
  fps: props.fps,
  durationInFrames: timeline.frames,
});

// ------------------------------------------------------------
// Bausteine
// ------------------------------------------------------------

/** Ein-/Ausblendphase relativ zum Elementstart: exit = 1 → 0 über die letzten 0,3 s (ease-in), leicht nach oben. */
const useExit = (dauer: number, sek = 0.3) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = dauer - Math.round(sek * fps);
  const exit = interpolate(frame, [start, dauer - 1], [1, 0], { ...CLAMP, easing: EASE_IN });
  const y = interpolate(frame, [start, dauer - 1], [0, -10], { ...CLAMP, easing: EASE_IN });
  return { frame, fps, exit, y };
};

/** RISE: Zeile gleitet aus einer Maske nach oben (Standard 0,7 s, ease-out). */
const MaskLine: React.FC<{ delay: number; sek?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay,
  sek = 0.7,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [delay, delay + Math.round(sek * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <div style={{ overflow: "hidden", paddingBottom: "0.34em", marginBottom: "-0.34em", paddingTop: "0.12em", marginTop: "-0.12em" }}>
      <div style={{ transform: `translateY(${(1 - p) * 125}%)`, opacity: 0.15 + 0.85 * p, ...style }}>{children}</div>
    </div>
  );
};

/** FADE: Opazität 0 → 1 (Standard 0,5 s). */
const Fade: React.FC<{ delay: number; sek?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay,
  sek = 0.5,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const o = interpolate(frame, [delay, delay + Math.round(sek * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return <div style={{ opacity: o, ...style }}>{children}</div>;
};

/** DRAW: Schreibschrift wird von links freigelegt (clip-path, ohne Reflow). */
const Draw: React.FC<{ delay: number; sek?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay,
  sek = 0.9,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [delay, delay + Math.round(sek * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return <div style={{ clipPath: `inset(-20% ${(1 - p) * 104}% -30% -6%)`, ...style }}>{children}</div>;
};

/** Goldene Linie, die sich von links zeichnet. */
const Linie: React.FC<{ delay: number; breite: number; farbe?: string; sek?: number }> = ({ delay, breite, farbe = GOLD, sek = 0.5 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [delay, delay + Math.round(sek * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return <div style={{ width: breite * p, height: 2, backgroundColor: farbe, opacity: 0.9 }} />;
};

/** Weicher Taupe-Wash (radial, kein Linear-Gradient) als Grund für das Lockup. */
const Wash: React.FC<{ w: number; h: number; alpha: number; style?: React.CSSProperties }> = ({ w, h, alpha, style }) => (
  <div
    style={{
      position: "absolute",
      width: w,
      height: h,
      borderRadius: "50%",
      background: `radial-gradient(ellipse at center, rgba(165,161,149,${alpha}) 0%, rgba(165,161,149,${alpha * 0.85}) 45%, rgba(165,161,149,0) 72%)`,
      ...style,
    }}
  />
);

/** Stiftweg 0–1 für „zauber“ (t, dauer, an, aus in s): konstantes Stifttempo entlang der Bogenlänge des Schreibwegs, weicher
 *  Anlauf und Auslauf als Kosinus-Rampen der Geschwindigkeit (kein Ease über den ganzen Weg, sonst rast die Mitte). */
const stiftweg = (t: number, dauer: number, an = 0.25, aus = 0.35) => {
  if (t <= 0) return 0;
  if (t >= dauer) return 1;
  const v = 1 / (dauer - (an + aus) / 2);                                   // Reisetempo (Anteil des Wegs je s)
  if (t < an) return v * (t / 2 - (an / (2 * Math.PI)) * Math.sin((Math.PI * t) / an));
  if (t <= dauer - aus) return v * (an / 2 + (t - an));
  const u = t - (dauer - aus);
  return v * (an / 2 + (dauer - aus - an) + u / 2 + (aus / (2 * Math.PI)) * Math.sin((Math.PI * u) / aus));
};
const SCHREIB_START = 0.9;   // s nach delay — Container ist dann zu ~98 % eingeblendet
const SCHREIB_ENDE = 3.15;   // s nach delay — vor der Zeile „Arena Hohenlohe“ (Intro, 3,2 s)

/** Kundenlogo (SVG, projects/MN Deko und Verleih/Logo/logo_01.svg): Container blendet ein und steigt leicht (0–1,3 s), ab 0,9 s
 *  schreibt sich „zauber“ in EINEM Zug wie von Hand — eine Wortmaske entlang der Mittellinie (logo.tsx, Schreibweg z → r), ein
 *  Fortschritt für das ganze Wort (Review V3, K1: „in einem sauberen rutsch als würde es ein mensch schreiben“). Breite = Logo-Breite in px. */
const Lockup: React.FC<{ delay: number; breite?: number; serif?: string; script?: string }> = ({ delay, breite = 700, serif = IVORY, script = INK }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = (sek: number) => delay + Math.round(sek * fps);
  const ein = interpolate(frame, [f(0), f(1.3)], [0, 1], { ...CLAMP, easing: EASE_OUT });   // langsamer (K1)
  const schreiben = stiftweg((frame - delay) / fps - SCHREIB_START, SCHREIB_ENDE - SCHREIB_START);
  const svgW = breite / (816 / 1080);              // sichtbares Logo im viewBox ≈ x 134–950
  return (
    <div style={{ width: svgW, height: svgW, opacity: ein, transform: `translateY(${(1 - ein) * 18}px)`,
                  // K2: keine Fläche, nur ein minimaler weicher Schatten — plus ein sehr weicher heller Saum, damit die dunkle
                  // Schreibschrift auch auf dunklem Footage (Drohne) lesbar bleibt
                  filter: "drop-shadow(0 0 18px rgba(230,227,218,0.55)) drop-shadow(0 4px 12px rgba(20,18,16,0.28))" }}>
      <LogoSVG serif={serif} script={script} schreiben={schreiben} style={{ width: svgW, height: svgW, display: "block" }} />
    </div>
  );
};

// ------------------------------------------------------------
// Elemente
// ------------------------------------------------------------

const Intro: React.FC<{ el: Element }> = ({ el }) => {
  const { exit, y, fps } = useExit(el.dauer, 0.35);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit, transform: `translateY(${y}px)` }}>
      <div style={{ position: "absolute", left: BASE_W / 2 - 463, top: 20 }}>
        <Lockup delay={0} breite={700} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 745, textAlign: "center" }}>
        <Fade delay={Math.round(3.2 * fps)} sek={0.6}>
          <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 28, letterSpacing: "0.22em", color: IVORY, textTransform: "uppercase",
                        textShadow: "0 2px 12px rgba(20,18,16,0.5)" }}>
            Arena Hohenlohe · 13. September 2026
          </div>
        </Fade>
      </div>
    </div>
  );
};

/** Szenenkarte unten links: Kategorie-Kicker (Serif, Versalien), Name in Schreibschrift (Größe nach Länge), Goldlinie;
 *  Glyph-Scrim nur textbox-groß (Luminanz-Gate der Doktrin). */
const Karte: React.FC<{ el: Element }> = ({ el }) => {
  const { exit, y, fps } = useExit(el.dauer, 0.3);
  const text = el.text ?? "";
  const kicker = (el.kicker ?? "").toUpperCase();
  const size = Math.max(64, Math.min(132, Math.floor(1500 / (text.length * 0.42))));
  const breite = Math.min(1500, Math.round(text.length * size * 0.42) + 120);
  return (
    <div style={{ position: "absolute", left: SAFE_X, bottom: SAFE_BOTTOM, opacity: exit, transform: `translateY(${y}px)` }}>
      <Fade delay={0} sek={0.4}>
        <div
          style={{
            position: "absolute",
            left: -200,
            top: -150,
            width: breite + 400,
            height: 380,
            borderRadius: "50%",
            background: "radial-gradient(ellipse at center, rgba(20,18,16,0.46) 0%, rgba(20,18,16,0.28) 45%, rgba(20,18,16,0) 70%)",
          }}
        />
      </Fade>
      <div style={{ position: "relative" }}>
        {kicker ? (
          <Fade delay={Math.round(0.15 * fps)} sek={0.5}>
            <div style={{ fontFamily: PLAYFAIR, fontSize: 24, letterSpacing: "0.3em", color: IVORY, whiteSpace: "nowrap",
                          textShadow: "0 2px 10px rgba(0,0,0,0.55), 0 0 2px rgba(0,0,0,0.5)" }}>
              {kicker}
            </div>
          </Fade>
        ) : null}
        <MaskLine delay={Math.round(0.25 * fps)} sek={0.65}>
          <div
            style={{
              fontFamily: SCRIPT,
              fontSize: size,
              lineHeight: 1.05,
              color: IVORY,
              textShadow: "0 4px 26px rgba(0,0,0,0.45)",
              whiteSpace: "nowrap",
              paddingRight: 40,
            }}
          >
            {text}
          </div>
        </MaskLine>
        <div style={{ marginTop: 6 }}>
          <Linie delay={Math.round(0.1 * fps)} breite={220} />
        </div>
      </div>
    </div>
  );
};

/** Modenschau-Karte: zentriert, ohne Fläche dahinter (User 18.09.), nur „Die große“ / Modenschau mit Textschatten. */
const Modenschau: React.FC<{ el: Element }> = ({ el }) => {
  const { exit, y, fps } = useExit(el.dauer, 0.35);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit, transform: `translateY(${y}px)` }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 360, textAlign: "center" }}>
        <MaskLine delay={Math.round(0.2 * fps)} sek={0.6}>
          <div style={{ fontFamily: PLAYFAIR, fontSize: 34, letterSpacing: "0.3em", color: IVORY, textTransform: "uppercase",
                        textShadow: "0 2px 12px rgba(0,0,0,0.6), 0 0 2px rgba(0,0,0,0.5)" }}>Die große</div>
        </MaskLine>
        <div style={{ marginTop: -10 }}>
          <Draw delay={Math.round(0.45 * fps)} sek={1.0}>
            <div style={{ fontFamily: SCRIPT, fontSize: 200, lineHeight: 1.1, color: IVORY, textShadow: "0 6px 30px rgba(0,0,0,0.55), 0 0 3px rgba(0,0,0,0.35)" }}>
              Modenschau
            </div>
          </Draw>
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------
// Collage: weißer Grund, vier Kacheln (Footage-Proxys), Schriftzug — deckt das Bild vollständig (User-Wunsch 18.09.)
// ------------------------------------------------------------
const PAPIER = "#F6F4EF";
type Kachel = { x: number; y: number; w: number; h: number; rot: number; von: "links" | "rechts" | "oben" | "unten" };
const LAYOUTS: Record<string, { kacheln: Kachel[]; wort: { x: number; y: number; size: number; align?: "left" | "right" } }> = {
  A: {
    kacheln: [
      { x: 110, y: 80, w: 430, h: 580, rot: -3, von: "links" },
      { x: 1000, y: 60, w: 780, h: 440, rot: 2, von: "oben" },
      { x: 1460, y: 570, w: 380, h: 380, rot: -2, von: "rechts" },
      { x: 920, y: 640, w: 500, h: 281, rot: 3, von: "unten" },
    ],
    wort: { x: 110, y: 700, size: 150 },
  },
  B: {
    kacheln: [
      { x: 80, y: 100, w: 700, h: 394, rot: 2, von: "links" },
      { x: 860, y: 40, w: 380, h: 500, rot: -3, von: "oben" },
      { x: 1320, y: 130, w: 500, h: 500, rot: 3, von: "rechts" },
      { x: 960, y: 620, w: 520, h: 292, rot: -2, von: "unten" },
    ],
    wort: { x: 110, y: 610, size: 150 },
  },
  D: {
    kacheln: [
      { x: 100, y: 60, w: 400, h: 540, rot: 3, von: "links" },
      { x: 560, y: 120, w: 640, h: 360, rot: -2, von: "oben" },
      { x: 1260, y: 60, w: 560, h: 315, rot: 2, von: "rechts" },
      { x: 1180, y: 460, w: 640, h: 460, rot: -3, von: "unten" },
    ],
    wort: { x: 120, y: 680, size: 170 },
  },
  E: {
    kacheln: [
      { x: 80, y: 80, w: 560, h: 315, rot: -2, von: "links" },
      { x: 720, y: 60, w: 380, h: 500, rot: 3, von: "oben" },
      { x: 1180, y: 100, w: 640, h: 360, rot: -3, von: "rechts" },
      { x: 1120, y: 540, w: 500, h: 400, rot: 2, von: "unten" },
    ],
    wort: { x: 100, y: 560, size: 180 },
  },
  C: {
    kacheln: [
      { x: 60, y: 60, w: 520, h: 520, rot: -4, von: "links" },
      { x: 660, y: 100, w: 640, h: 360, rot: 2, von: "oben" },
      { x: 1380, y: 60, w: 460, h: 620, rot: 3, von: "rechts" },
      { x: 720, y: 600, w: 640, h: 360, rot: -2, von: "unten" },
    ],
    wort: { x: 70, y: 640, size: 190 },
  },
};

const KachelView: React.FC<{ k: Kachel; src: string; einFrame: number; gesamt: number }> = ({ k, src, einFrame, gesamt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [einFrame, einFrame + Math.round(0.55 * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const weg = 260;
  const dx = k.von === "links" ? -weg : k.von === "rechts" ? weg : 0;
  const dy = k.von === "oben" ? -weg : k.von === "unten" ? weg : 0;
  const kb = interpolate(frame, [0, gesamt], [1, 1.07], CLAMP); // Ken Burns in der Kachel
  return (
    <div
      style={{
        position: "absolute",
        left: k.x,
        top: k.y,
        width: k.w,
        height: k.h,
        opacity: p,
        transform: `translate(${(1 - p) * dx}px, ${(1 - p) * dy}px) rotate(${k.rot - (1 - p) * 6}deg) scale(${0.86 + 0.14 * p})`,
        transformOrigin: "50% 50%",
        boxShadow: "0 24px 60px rgba(48,48,48,0.22), 0 2px 6px rgba(48,48,48,0.12)",
        border: `3px solid ${IVORY}`,
        backgroundColor: TAUPE,
        overflow: "hidden",
      }}
    >
      <OffthreadVideo
        src={staticFile(src)}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }}
      />
    </div>
  );
};

const Collage: React.FC<{ el: Element }> = ({ el }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lay = LAYOUTS[el.layout ?? "A"] ?? LAYOUTS.A;
  const beat = el.beat_frames ?? 12.3;
  const tiles = el.tiles ?? [];
  const push = interpolate(frame, [0, el.dauer], [1, 1.035], CLAMP);
  return (
    <div style={{ position: "absolute", inset: 0, backgroundColor: PAPIER, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${push})`, transformOrigin: "50% 50%" }}>
        {lay.kacheln.map((k, i) =>
          tiles[i] ? <KachelView key={i} k={k} src={tiles[i].src} einFrame={Math.round(i * beat * 0.75)} gesamt={el.dauer} /> : null,
        )}
        <div style={{ position: "absolute", left: lay.wort.x, top: lay.wort.y }}>
          <Draw delay={Math.round(1.6 * beat)} sek={0.9}>
            <div style={{ fontFamily: SCRIPT, fontSize: lay.wort.size, lineHeight: 1.1, color: INK, whiteSpace: "nowrap",
                          textShadow: "0 6px 24px rgba(246,244,239,0.9)" }}>
              {el.text}
            </div>
          </Draw>
          <div style={{ marginTop: -6, marginLeft: 10 }}>
            <Linie delay={Math.round(2.4 * beat)} breite={200} />
          </div>
          {el.kicker ? (
            <Fade delay={Math.round(3.0 * beat)} sek={0.5}>
              <div style={{ marginTop: 14, marginLeft: 10, fontFamily: PLAYFAIR, fontSize: 24, letterSpacing: "0.3em", color: BROWN, textTransform: "uppercase", whiteSpace: "nowrap" }}>
                {el.kicker}
              </div>
            </Fade>
          ) : null}
        </div>
        <div style={{ position: "absolute", right: 60, bottom: 40, fontFamily: PLAYFAIR, fontSize: 18, letterSpacing: "0.34em", color: TAUPE, textTransform: "uppercase" }}>
          Hochzeitszauber 2026
        </div>
      </div>
    </div>
  );
};

/** Endcard: Taupe-Wash über das Finale, Lockup, Dank, Website/Instagram, Veranstalter. */
const Endcard: React.FC<{ el: Element }> = ({ el }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const washIn = interpolate(frame, [0, Math.round(0.8 * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const zeilen = el.zeilen ?? [];
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: washIn,
          background: `radial-gradient(ellipse at 50% 45%, rgba(165,161,149,0.96) 0%, rgba(165,161,149,0.9) 55%, rgba(150,146,135,0.86) 100%)`,
        }}
      />
      <div style={{ position: "absolute", left: BASE_W / 2 - 344, top: 10 }}>
        <Lockup delay={Math.round(0.3 * fps)} breite={520} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 580, textAlign: "center" }}>
        <MaskLine delay={Math.round(1.1 * fps)} sek={0.7}>
          <div style={{ fontFamily: PLAYFAIR, fontSize: 46, color: INK, letterSpacing: "0.02em" }}>{zeilen[0]}</div>
        </MaskLine>
        <div style={{ display: "flex", justifyContent: "center", marginTop: 26 }}>
          <Linie delay={Math.round(1.4 * fps)} breite={160} farbe={INK} />
        </div>
        <Fade delay={Math.round(1.6 * fps)} sek={0.6}>
          <div style={{ marginTop: 26, fontFamily: SANS, fontWeight: 600, fontSize: 30, letterSpacing: "0.12em", color: BROWN }}>
            {zeilen[1]}
          </div>
        </Fade>
        <Fade delay={Math.round(2.0 * fps)} sek={0.6}>
          <div style={{ marginTop: 34, fontFamily: SANS, fontWeight: 400, fontSize: 22, letterSpacing: "0.1em", color: BROWN, opacity: 0.85 }}>
            {zeilen[2]}
          </div>
        </Fade>
      </div>
    </div>
  );
};

/** Wischer (K8): ein weicher Elfenbein-Streifen mit Goldlinie zieht diagonal von links nach rechts über den Schnitt (16 Frames). */
const Wischer: React.FC<{ el: Element }> = ({ el }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, el.dauer - 1], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const breite = 620;
  const x = -breite - 200 + p * (BASE_W + breite + 400);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: -200,
          left: x,
          width: breite,
          height: BASE_H + 400,
          transform: "skewX(-14deg)",
          background: `linear-gradient(90deg, rgba(230,227,218,0) 0%, rgba(230,227,218,0.92) 35%, rgba(230,227,218,0.92) 65%, rgba(230,227,218,0) 100%)`,
        }}
      />
      <div style={{ position: "absolute", top: -200, left: x + breite * 0.66, width: 3, height: BASE_H + 400, transform: "skewX(-14deg)", backgroundColor: GOLD, opacity: 0.9 }} />
    </div>
  );
};

/** Fotoalbum-Übergang (Review 2, K2): der auslaufende Shot zoomt auf den weißen Grund heraus und wird zur Kachel links, daneben
 *  erscheint der einlaufende Shot als Kachel; dann fährt die „Kamera“ in die rechte Kachel, bis sie das Bild füllt — exakt auf dem
 *  Schnitt. Kacheln = Proxys der Entwurfs-Segmente (uebergang/sNNN.mp4), Bild A hält am Ende sein letztes Frame. */
const Album: React.FC<{ el: Element }> = ({ el }) => {
  const frame = useCurrentFrame();
  const vor = el.vor ?? 15;
  const nach = el.dauer - vor;
  const A = { x: 130, y: 250, w: 800, h: 450, rot: -2.5 };   // Kachel des auslaufenden Shots
  const B = { x: 1010, y: 330, w: 800, h: 450, rot: 2 };     // Kachel des einlaufenden Shots
  const ease = Easing.inOut(Easing.cubic);
  // Phase 1: A von Vollbild zur Kachel (0 … vor)
  const p1 = interpolate(frame, [0, vor - 1], [0, 1], { ...CLAMP, easing: ease });
  const sA = 1 - p1 * (1 - A.w / BASE_W);
  const ax = p1 * A.x, ay = p1 * A.y, ar = p1 * A.rot;
  // B erscheint ab 45 % der Phase 1
  const pb = interpolate(frame, [Math.round(vor * 0.45), vor - 1], [0, 1], { ...CLAMP, easing: EASE_OUT });
  // Phase 2: Kamera fährt in B (vor … dauer): Skalierung k 1 → BASE_W / B.w um Bs Ecke, B-Rotation → 0
  const p2 = interpolate(frame, [vor, el.dauer - 1], [0, 1], { ...CLAMP, easing: ease });
  const kEnd = BASE_W / B.w;
  const k = 1 + p2 * (kEnd - 1);
  const brot = B.rot * (1 - p2);
  // Bs linke obere Ecke wandert von (B.x, B.y) nach (0, 0), während das Board um k wächst
  const boardX = B.x * (1 - p2) - B.x * k, boardY = B.y * (1 - p2) - B.y * k;
  // Grund: weiß, erscheint sofort (A deckt anfangs das Bild), verschwindet am Ende hart (B füllt das Bild)
  return (
    <div style={{ position: "absolute", inset: 0, backgroundColor: PAPIER, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${boardX}px, ${boardY}px) scale(${k})`, transformOrigin: "0 0" }}>
        {/* B — Standbild bis zum Schnitt, dann das Video ab Frame 0 */}
        {pb > 0 ? (
          <div
            style={{
              position: "absolute", left: B.x, top: B.y, width: B.w, height: B.h, opacity: pb,
              transform: `rotate(${brot}deg) scale(${0.9 + 0.1 * pb})`, transformOrigin: "50% 50%", overflow: "hidden",
              boxShadow: p2 < 0.98 ? "0 24px 60px rgba(48,48,48,0.22)" : "none", border: p2 < 0.98 ? `3px solid ${IVORY}` : "none", backgroundColor: TAUPE,
            }}
          >
            {frame < vor ? (
              <Img src={staticFile(el.b_bild ?? "")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <Sequence from={vor} layout="none">
                <OffthreadVideo src={staticFile(el.b ?? "")} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </Sequence>
            )}
          </div>
        ) : null}
        {/* A — Video läuft weiter (mit Standbild-Nachlauf im Proxy) */}
        <div
          style={{
            position: "absolute", left: ax, top: ay, width: BASE_W, height: BASE_H,
            transform: `rotate(${ar}deg) scale(${sA})`, transformOrigin: "0 0", overflow: "hidden",
            boxShadow: p1 > 0.05 ? "0 24px 60px rgba(48,48,48,0.22)" : "none", border: p1 > 0.05 ? `${3 / sA}px solid ${IVORY}` : "none",
          }}
        >
          <OffthreadVideo src={staticFile(el.a ?? "")} startFrom={el.a_start ?? 0} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------
// Komposition
// ------------------------------------------------------------

export const HochzeitszauberAftermovie: React.FC<z.infer<typeof aftermovieSchema>> = ({ review, vorschauGrund }) => {
  const { width } = useVideoConfig();
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: vorschauGrund ? "#5a5650" : "transparent" }}>
        <div style={{ position: "absolute", width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "0 0" }}>
          {ELEMENTE.map((el) => (
            <Sequence key={el.id} from={el.from} durationInFrames={el.dauer} layout="none">
              {el.typ === "intro" && <Intro el={el} />}
              {el.typ === "karte" && <Karte el={el} />}
              {el.typ === "modenschau" && <Modenschau el={el} />}
              {el.typ === "endcard" && <Endcard el={el} />}
              {el.typ === "collage" && <Collage el={el} />}
              {el.typ === "wischer" && <Wischer el={el} />}
              {el.typ === "album" && <Album el={el} />}
            </Sequence>
          ))}
        </div>
        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            showFaceZone={review.showFaceZone ?? false}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
