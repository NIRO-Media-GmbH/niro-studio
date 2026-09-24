// ============================================================
// akut med — Recruiting-Ads vom Dreh 11./12.08.2026 (KA-Kurz-Ads)
// Grafik und Untertitel als getrennte Alpha-Overlays, 1080 × 1920, 25 fps.
// t = 0 ist der erste Frame der Timeline „<Nr> - <Titel>_V<n>“ in Resolve
// (Projekt „Akut-12.08.26 Ads“). Alle Zeiten kommen aus data/<nr>.json,
// erzeugt von projects/akut/Recruiting-Videos/2026-08 Ad Dreh/_intern/ads/
// overlay_daten.py aus den zurückgelesenen Schnittpositionen — Timings dort
// ändern, nicht hier.
//
// CI (Website akut-med.de, Stand 09/2026): Rot #E3000F, Dunkellila #291A48,
// Lavendel #8D85DD; Montserrat ExtraBold für Karten, Inter für Untertitel;
// Logo-Herz mit Haken als Aufzählungszeichen.
// Regeln: Grafiken erst ab 34 % Bildhöhe (Gesicht liegt bei 12–30 %),
// Untertitel einzeilig bei 62 %, keine Untertitel, solange eine Grafik steht
// (in den Daten schon herausgerechnet). Übergaben per Unmount, Deckkraft nur
// linear und nur auf dem Element selbst (keine Feder-Deckkraft auf Containern).
// ============================================================

import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { getCalculateMetadata } from "../../../../core/format-utils";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import { DATEN, NUMMERN } from "./data";

const { fontFamily: MONTSERRAT } = loadMontserrat("normal", { weights: ["800"], subsets: ["latin", "latin-ext"] });
const { fontFamily: INTER } = loadInter("normal", { weights: ["700", "800"], subsets: ["latin", "latin-ext"] });

const ci = loadBrand("akut", brandJson as any);
const RED = ci.colors.primary; // #E3000F
const PURPLE = ci.colors.secondary; // #291A48
const LAVENDER = ci.colors.accent; // #8D85DD
const WHITE = "#FFFFFF";
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const CARD_SHADOW = "0 14px 38px rgba(41,26,72,0.30), 0 3px 8px rgba(41,26,72,0.18)";
const SUB_SHADOW = [
  "0 0 3px rgba(20,12,36,0.95)",
  "0 3px 6px rgba(20,12,36,0.85)",
  "0 8px 24px rgba(20,12,36,0.55)",
].join(", ");
// Interview-Ads: Nico trägt ein weißes Shirt — Untertitel brauchen dort eine dichtere dunkle Kontur
const SUB_SHADOW_STARK = [
  "0 0 2px rgba(20,12,36,1)",
  "0 0 4px rgba(20,12,36,1)",
  "0 0 9px rgba(20,12,36,0.9)",
  "0 3px 7px rgba(20,12,36,0.9)",
  "0 10px 28px rgba(20,12,36,0.6)",
].join(", ");

// ---------------- Datentypen ----------------

type Item = { text: string; at: number; icon?: "herz" | "kreuz" };
type Beat = {
  typ: "karte" | "worte" | "stapel" | "chat" | "cta" | "duo" | "mythos";
  id: string;
  y: number;
  t_in: number;
  t_out: number;
  text?: string;
  variante?: "hell" | "rot" | "lila";
  groesse?: number;
  sub?: string;
  label?: string;
  button?: string;
  items?: Item[];
  einordnung?: string;
  stempel_at?: number;
};
type Page = { startSec: number; endSec: number; text: string };
export type AkutAdData = {
  nr: string;
  titel: string;
  fps: number;
  durationSec: number;
  band: number;
  ut?: "normal" | "stark";
  pages: Page[];
  beats: Beat[];
};

export const AKUT_AD_DATA: Record<string, AkutAdData> = DATEN as unknown as Record<string, AkutAdData>;
export const AKUT_NUMMERN = NUMMERN;

// ---------------- Zeit-Helfer ----------------

function useT(tIn: number) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return { t: frame / fps - tIn, fps };
}

/** Ein: Feder nur auf Transform, Deckkraft linear bis exakt 1. Aus: 0,16 s linear, danach Unmount. */
function envelope(t: number, dur: number, fps: number) {
  const inS = spring({ frame: Math.max(0, Math.round(t * fps)), fps, config: { damping: 16, stiffness: 210, mass: 0.75 } });
  const opIn = interpolate(t, [0, 0.12], [0, 1], CLAMP);
  const opOut = interpolate(t, [dur - 0.16, dur], [1, 0], CLAMP);
  return { inS, op: Math.min(opIn, opOut), visible: t >= 0 && t < dur };
}

/** Textbreite per Canvas (Webfonts sind beim Rendern geladen); lange Wörter werden so auf eine Maximalbreite verkleinert. */
let MESS: CanvasRenderingContext2D | null = null;
function textBreite(text: string, fs: number, family: string, weight: number, spacingEm = 0) {
  if (typeof document === "undefined") return 0;
  MESS = MESS ?? document.createElement("canvas").getContext("2d");
  if (!MESS) return 0;
  MESS.font = `${weight} ${fs}px ${family}`;
  return MESS.measureText(text).width + spacingEm * fs * text.length;
}
function passend(zeilen: string[], fs: number, maxBreite: number, family: string, weight: number, spacingEm = 0) {
  const breit = Math.max(...zeilen.map((z) => textBreite(z, fs, family, weight, spacingEm)));
  return breit > maxBreite ? fs * (maxBreite / breit) : fs;
}

// ---------------- Bausteine ----------------

const Herz: React.FC<{ size: number }> = ({ size }) => (
  <Img src={staticFile("clients/akut/akut-herz.svg")} style={{ width: size, height: size, display: "block" }} />
);

const Kreuz: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{ display: "block" }}>
    <circle cx="50" cy="50" r="46" fill={RED} />
    <path d="M33 33 L67 67 M67 33 L33 67" stroke={WHITE} strokeWidth="11" strokeLinecap="round" />
  </svg>
);

const farben = (v: Beat["variante"]) =>
  v === "rot" ? { bg: RED, fg: WHITE } : v === "lila" ? { bg: PURPLE, fg: WHITE } : { bg: WHITE, fg: PURPLE };

const Karte: React.FC<{ text: string; variante?: Beat["variante"]; groesse?: number; sub?: string; op: number; inS: number }> = ({
  text,
  variante,
  groesse,
  sub,
  op,
  inS,
}) => {
  const { height: H, width: W } = useVideoConfig();
  const { bg, fg } = farben(variante);
  const fs = passend(text.toUpperCase().split("\n"), H * (groesse ?? 0.036), W * 0.72, MONTSERRAT, 800, -0.01);
  return (
    <div
      style={{
        opacity: op,
        transform: `translateY(${interpolate(inS, [0, 1], [H * 0.02, 0])}px) scale(${interpolate(inS, [0, 1], [0.86, 1])})`,
        background: bg,
        color: fg,
        borderRadius: H * 0.012,
        padding: `${fs * 0.42}px ${fs * 0.7}px ${fs * 0.46}px`,
        boxShadow: CARD_SHADOW,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: fs * 0.18,
        maxWidth: H * 0.5,
      }}
    >
      <div style={{ fontFamily: MONTSERRAT, fontWeight: 800, fontSize: fs, lineHeight: 1.08, letterSpacing: "-0.01em", textAlign: "center", textTransform: "uppercase", whiteSpace: "pre-line" }}>
        {text}
      </div>
      {sub && (
        <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: fs * 0.46, lineHeight: 1.1, color: variante === "hell" || !variante ? RED : WHITE, textAlign: "center" }}>
          {sub}
        </div>
      )}
    </div>
  );
};

const KarteBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const { t, fps } = useT(b.t_in);
  const { inS, op, visible } = envelope(t, b.t_out - b.t_in, fps);
  if (!visible) return null;
  return <Karte text={b.text ?? ""} variante={b.variante} groesse={b.groesse} sub={b.sub} op={op} inS={inS} />;
};

/** Wortkarten, die sich auf den Wortzeiten ablösen (je Wort ein eigener Mount, kein Rest des vorigen) */
const WorteBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const dur = b.t_out - b.t_in;
  if (now < b.t_in || now >= b.t_out) return null;
  const items = (b.items ?? []).filter((it) => it.at <= now);
  if (!items.length) return null;
  const aktuell = items[items.length - 1];
  const tItem = now - aktuell.at;
  const inS = spring({ frame: Math.round(tItem * fps), fps, config: { damping: 15, stiffness: 240, mass: 0.7 } });
  // Nur das erste Wort blendet ein; Folgewörter lösen hart ab (sonst ein Frame fast leer zwischen zwei Karten)
  const opIn = items.length === 1 ? interpolate(tItem, [0, 0.08], [0, 1], CLAMP) : 1;
  const opOut = interpolate(now - b.t_in, [dur - 0.16, dur], [1, 0], CLAMP);
  return (
    <div key={aktuell.text + aktuell.at}>
      <Karte text={aktuell.text} variante={b.variante} groesse={b.groesse} op={Math.min(opIn, opOut)} inS={inS} />
    </div>
  );
};

/** Zwei Karten übereinander, die zweite kommt auf ihrem Wort dazu */
const DuoBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const frame = useCurrentFrame();
  const { fps, height: H } = useVideoConfig();
  const now = frame / fps;
  const dur = b.t_out - b.t_in;
  if (now < b.t_in || now >= b.t_out) return null;
  const opOut = interpolate(now - b.t_in, [dur - 0.16, dur], [1, 0], CLAMP);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", rowGap: H * 0.018 }}>
      {(b.items ?? []).map((it, i) => {
        const ti = now - it.at;
        if (ti < 0) return null;
        const inS = spring({ frame: Math.round(ti * fps), fps, config: { damping: 15, stiffness: 240, mass: 0.7 } });
        const op = Math.min(interpolate(ti, [0, 0.1], [0, 1], CLAMP), opOut);
        return <Karte key={i} text={it.text} variante={i % 2 === 0 ? b.variante : b.variante === "rot" ? "hell" : "rot"} groesse={b.groesse} op={op} inS={inS} />;
      })}
    </div>
  );
};

/** Liste mit Herz-Haken (positiv) oder rotem Kreuz (Pain), Zeilen auf ihren Wortzeiten */
const StapelBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const frame = useCurrentFrame();
  const { fps, height: H, width: W } = useVideoConfig();
  const now = frame / fps;
  const dur = b.t_out - b.t_in;
  if (now < b.t_in || now >= b.t_out) return null;
  const opOut = interpolate(now - b.t_in, [dur - 0.16, dur], [1, 0], CLAMP);
  const grund = H * (b.groesse ?? 0.027);
  // alle Zeilen gleich groß; die längste passt samt Icon und Innenabstand in 86 % der Bildbreite
  const fs = Math.min(...(b.items ?? []).map((it) => passend([it.text.toUpperCase()], grund, W * 0.86 - 3.2 * grund, MONTSERRAT, 800, -0.01)));
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "stretch", rowGap: H * 0.012 }}>
      {(b.items ?? []).map((it, i) => {
        const ti = now - it.at;
        if (ti < 0) return null;
        const inS = spring({ frame: Math.round(ti * fps), fps, config: { damping: 16, stiffness: 230, mass: 0.7 } });
        const op = Math.min(interpolate(ti, [0, 0.1], [0, 1], CLAMP), opOut);
        const dir = i % 2 === 0 ? -1 : 1;
        return (
          <div
            key={i}
            style={{
              opacity: op,
              transform: `translateX(${interpolate(inS, [0, 1], [dir * H * 0.04, 0])}px)`,
              background: b.variante === "lila" ? PURPLE : WHITE,
              borderRadius: H * 0.011,
              boxShadow: CARD_SHADOW,
              padding: `${fs * 0.42}px ${fs * 0.8}px ${fs * 0.42}px ${fs * 0.5}px`,
              display: "flex",
              alignItems: "center",
              columnGap: fs * 0.5,
            }}
          >
            {it.icon === "kreuz" ? <Kreuz size={fs * 1.25} /> : <Herz size={fs * 1.35} />}
            <div style={{ fontFamily: MONTSERRAT, fontWeight: 800, fontSize: fs, color: b.variante === "lila" ? WHITE : PURPLE, textTransform: "uppercase", whiteSpace: "nowrap", lineHeight: 1.05, letterSpacing: "-0.01em" }}>
              {it.text}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/** Eingehende Nachricht: Tipp-Punkte, dann Text */
const ChatBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const { t, fps } = useT(b.t_in);
  const { height: H } = useVideoConfig();
  const dur = b.t_out - b.t_in;
  const { inS, op, visible } = envelope(t, dur, fps);
  if (!visible) return null;
  const fs = H * 0.03;
  const tippen = t < 0.35;
  return (
    <div style={{ opacity: op, transform: `translateY(${interpolate(inS, [0, 1], [H * 0.05, 0])}px)`, display: "flex", flexDirection: "column", alignItems: "flex-start", rowGap: H * 0.008, width: H * 0.46 }}>
      <div style={{ display: "flex", alignItems: "center", columnGap: H * 0.008, marginLeft: H * 0.012 }}>
        <div style={{ width: H * 0.026, height: H * 0.026, borderRadius: "50%", background: LAVENDER }} />
        <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: fs * 0.62, color: WHITE, textShadow: SUB_SHADOW }}>{b.label ?? "Neue Nachricht"}</div>
      </div>
      <div style={{ background: WHITE, borderRadius: `${H * 0.022}px ${H * 0.022}px ${H * 0.022}px ${H * 0.006}px`, boxShadow: CARD_SHADOW, padding: `${fs * 0.55}px ${fs * 0.75}px` }}>
        {tippen ? (
          <div style={{ display: "flex", columnGap: fs * 0.25, padding: `${fs * 0.2}px 0` }}>
            {[0, 1, 2].map((k) => (
              <div key={k} style={{ width: fs * 0.32, height: fs * 0.32, borderRadius: "50%", background: LAVENDER, transform: `translateY(${Math.sin((t * 12) - k) * fs * 0.08}px)` }} />
            ))}
          </div>
        ) : (
          <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: fs, lineHeight: 1.22, color: PURPLE }}>{b.text}</div>
        )}
      </div>
    </div>
  );
};

/** CTA: Logo-Karte + roter Button + Pfeil nach unten (auf den Button der Anzeige) */
const CtaBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const { t, fps } = useT(b.t_in);
  const { height: H, width: W } = useVideoConfig();
  const dur = b.t_out - b.t_in;
  if (t < 0 || t >= dur) return null;
  const logoS = spring({ frame: Math.max(0, Math.round(t * fps)), fps, config: { damping: 16, stiffness: 200, mass: 0.8 } });
  const tBtn = t - 0.18;
  const btnS = spring({ frame: Math.max(0, Math.round(tBtn * fps)), fps, config: { damping: 13, stiffness: 220, mass: 0.7 } });
  const fs = passend([(b.button ?? "").toUpperCase()], H * 0.027, W * 0.66, MONTSERRAT, 800, -0.005);
  const pfeil = Math.sin(Math.max(0, t - 0.5) * 5.5) * H * 0.006;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", rowGap: H * 0.014 }}>
      <div style={{ opacity: interpolate(t, [0, 0.12], [0, 1], CLAMP), transform: `scale(${interpolate(logoS, [0, 1], [0.8, 1])})`, background: b.variante === "lila" ? PURPLE : WHITE, borderRadius: H * 0.012, boxShadow: CARD_SHADOW, padding: `${H * 0.012}px ${H * 0.022}px` }}>
        <Img src={staticFile(b.variante === "lila" ? "clients/akut/akut-med-logo-weiss.svg" : "clients/akut/akut-med-logo.svg")} style={{ height: H * 0.034, display: "block" }} />
      </div>
      {tBtn >= 0 && (
        <div style={{ opacity: interpolate(tBtn, [0, 0.1], [0, 1], CLAMP), transform: `scale(${interpolate(btnS, [0, 1], [0.7, 1])})`, background: RED, borderRadius: H * 0.05, boxShadow: "0 12px 30px rgba(227,0,15,0.35), 0 3px 8px rgba(41,26,72,0.25)", padding: `${fs * 0.62}px ${fs * 1.2}px`, display: "flex", flexDirection: "column", alignItems: "center", rowGap: fs * 0.12 }}>
          <div style={{ fontFamily: MONTSERRAT, fontWeight: 800, fontSize: fs, color: WHITE, textTransform: "uppercase", whiteSpace: "nowrap", letterSpacing: "-0.005em" }}>{b.button}</div>
          {b.sub && <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: fs * 0.7, color: WHITE, whiteSpace: "nowrap" }}>{b.sub}</div>}
        </div>
      )}
      {tBtn >= 0.25 && (
        <svg width={H * 0.04} height={H * 0.04} viewBox="0 0 100 100" style={{ transform: `translateY(${pfeil}px)`, opacity: interpolate(tBtn, [0.25, 0.35], [0, 1], CLAMP), filter: "drop-shadow(0 4px 10px rgba(20,12,36,0.6))" }}>
          <path d="M20 35 L50 65 L80 35" stroke={b.variante === "lila" ? RED : WHITE} strokeWidth="14" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      )}
    </div>
  );
};

/** Mythos oder Fakt (RL-25): Aussage-Karte lila mit Kopfzeile, Stempel „Stimmt nicht / Stimmt / Jein“ auf Nicos Antwort-Wort */
const MythosBeat: React.FC<{ b: Beat }> = ({ b }) => {
  const { t, fps } = useT(b.t_in);
  const { height: H, width: W } = useVideoConfig();
  const dur = b.t_out - b.t_in;
  const { inS, op, visible } = envelope(t, dur, fps);
  if (!visible) return null;
  const fs = passend((b.text ?? "").toUpperCase().split("\n"), H * 0.032, W * 0.7, MONTSERRAT, 800, -0.01);
  const ts = t - ((b.stempel_at ?? b.t_out) - b.t_in);
  const stempelS = spring({ frame: Math.max(0, Math.round(ts * fps)), fps, config: { damping: 11, stiffness: 260, mass: 0.6 } });
  const farbe = b.einordnung === "Stimmt nicht" ? { bg: RED, fg: WHITE } : b.einordnung === "Jein" ? { bg: LAVENDER, fg: WHITE } : { bg: WHITE, fg: RED };
  return (
    <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div
        style={{
          opacity: op,
          transform: `translateY(${interpolate(inS, [0, 1], [H * 0.02, 0])}px) scale(${interpolate(inS, [0, 1], [0.86, 1])})`,
          background: PURPLE,
          color: WHITE,
          borderRadius: H * 0.012,
          padding: `${fs * 0.45}px ${fs * 0.75}px ${fs * 0.6}px`,
          boxShadow: CARD_SHADOW,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          rowGap: fs * 0.25,
        }}
      >
        <div style={{ fontFamily: INTER, fontWeight: 800, fontSize: fs * 0.42, letterSpacing: "0.14em", color: LAVENDER, textTransform: "uppercase" }}>Mythos oder Fakt?</div>
        <div style={{ fontFamily: MONTSERRAT, fontWeight: 800, fontSize: fs, lineHeight: 1.08, letterSpacing: "-0.01em", textAlign: "center", textTransform: "uppercase", whiteSpace: "pre-line" }}>{b.text}</div>
      </div>
      {ts >= 0 && (
        <div
          style={{
            position: "absolute",
            right: -H * 0.012,
            bottom: -H * 0.034,
            opacity: Math.min(interpolate(ts, [0, 0.06], [0, 1], CLAMP), op),
            transform: `rotate(-7deg) scale(${interpolate(stempelS, [0, 1], [1.7, 1])})`,
            background: farbe.bg,
            color: farbe.fg,
            border: `${H * 0.003}px solid ${farbe.fg}`,
            borderRadius: H * 0.008,
            padding: `${H * 0.006}px ${H * 0.016}px`,
            fontFamily: MONTSERRAT,
            fontWeight: 800,
            fontSize: H * 0.027,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            boxShadow: CARD_SHADOW,
          }}
        >
          {b.einordnung}
        </div>
      )}
    </div>
  );
};

const BEAT_VIEWS: Record<Beat["typ"], React.FC<{ b: Beat }>> = {
  mythos: MythosBeat,
  karte: KarteBeat,
  worte: WorteBeat,
  duo: DuoBeat,
  stapel: StapelBeat,
  chat: ChatBeat,
  cta: CtaBeat,
};

// ---------------- Untertitel ----------------

const PageView: React.FC<{ page: Page; size: number; stark?: boolean }> = ({ page, size: grund, stark }) => {
  const frame = useCurrentFrame();
  const { fps, width: W } = useVideoConfig();
  const size = passend([page.text], grund, W * 0.86, INTER, 800, -0.005);
  const t = frame / fps - page.startSec;
  const dur = page.endSec - page.startSec;
  if (t < 0 || t >= dur) return null;
  const inS = spring({ frame: Math.round(t * fps), fps, config: { damping: 22, stiffness: 260, mass: 0.6 } });
  return (
    <div
      style={{
        // keine Einblende: Seiten folgen lückenlos aufeinander, ein Fade ließe beim Wechsel einen leeren Frame
        transform: `translateY(${interpolate(inS, [0, 1], [size * 0.18, 0])}px)`,
        fontFamily: INTER,
        fontWeight: 800,
        fontSize: size,
        lineHeight: 1.1,
        color: WHITE,
        textShadow: stark ? SUB_SHADOW_STARK : SUB_SHADOW,
        whiteSpace: "nowrap",
        letterSpacing: "-0.005em",
      }}
    >
      {page.text}
    </div>
  );
};

// ---------------- Schema / Komposition ----------------

export const akutAdSchema = projectPropsSchema.extend({
  nr: z.enum(NUMMERN as unknown as [string, ...string[]]).describe("Video-Nr. laut Konzept"),
  fontSizePx: z.number().min(30).max(120).step(1).describe("Untertitel-Schriftgrad"),
  showSubtitles: z.boolean().describe("Untertitel einblenden"),
  showAnimations: z.boolean().describe("Animationen einblenden"),
  onlyBeat: z.string().describe("nur dieses Element (id), leer = alle"),
});

export type AkutAdProps = z.infer<typeof akutAdSchema>;

/** Dauer exakt wie die Resolve-Timeline (gerundet statt aufgerundet: 17,44 s × 25 ergibt in Fließkomma 436,00000000000006). */
export const calculateAkutAd = ({ props }: { props: AkutAdProps }) => ({
  ...getCalculateMetadata(props),
  durationInFrames: Math.round(AKUT_AD_DATA[props.nr].durationSec * props.fps),
});

export const akutAdDefaults = (nr: AkutAdProps["nr"]): AkutAdProps => ({
  format: "portrait",
  fps: 25,
  durationInSeconds: AKUT_AD_DATA[nr].durationSec,
  transparent: true,
  nr,
  fontSizePx: 56,
  showSubtitles: true,
  showAnimations: true,
  onlyBeat: "",
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.1, bottom: 0.33, left: 0.2, right: 0.8 },
    guideOpacity: 0.35,
  },
});

export const AkutAd: React.FC<AkutAdProps> = ({ nr, fontSizePx, showSubtitles, showAnimations, onlyBeat, review }) => {
  const { width, height } = useVideoConfig();
  const data = AKUT_AD_DATA[nr];
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {showAnimations &&
          data.beats
            .filter((b) => !onlyBeat || b.id === onlyBeat)
            .map((b) => {
              const View = BEAT_VIEWS[b.typ];
              return (
                <div key={b.id} style={{ position: "absolute", left: 0, right: 0, top: Math.round(height * b.y), display: "flex", justifyContent: "center", alignItems: "flex-start" }}>
                  <View b={b} />
                </div>
              );
            })}
        {showSubtitles && (
          <div style={{ position: "absolute", left: width * 0.05, right: width * 0.05, top: Math.round(height * data.band), transform: "translateY(-50%)", display: "flex", justifyContent: "center" }}>
            {data.pages.map((page, i) => (
              <div key={i} style={{ position: "absolute", left: 0, right: 0, display: "flex", justifyContent: "center" }}>
                <PageView page={page} size={fontSizePx} stark={data.ut === "stark"} />
              </div>
            ))}
          </div>
        )}
        {review?.showGuides && (
          <ReviewOverlay showSafeZone={review.showSafeZone ?? true} showFaceZone={review.showFaceZone ?? true} showGrid={review.showGrid ?? false} faceZone={review.faceZone} guideOpacity={review.guideOpacity ?? 0.35} />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
