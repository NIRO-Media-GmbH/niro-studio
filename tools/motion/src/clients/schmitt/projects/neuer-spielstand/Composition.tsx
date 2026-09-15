// ============================================================
// Schmitt — „Neuer Spielstand“ (9:16) · Startscreen + Segmente + Ton + HUD
// 1080×1920, 25 fps.
//
// Startscreen „Wähle deinen Weg“: generierter Hallenflug als Hintergrund,
// sechs Figurenkarten (3 × 2), der Auswahlrahmen springt automatisch über
// die Karten und rastet auf „Berufskraftfahrer“ ein. Danach Zoom-through
// (Motion-Doktrin §3) in Shot 1.
// Segmente danach: Clips hängen per harten Schnitt an (Startbild = letztes
// Bild des Vorgängers → Schnitt ohne Sprung); Ladescreens blenden über Schwarz
// ein und aus, die Clips davor und danach blenden mit. Am Ende CTA und Logo.
// Ton: Clip-Ton stumm, dafür Geräusche, saubere Dialogdateien und optional
// Musik mit Drop auf dem Anfahren — alles aus timeline.ts.
// Alle Texte liegen in der Reels-Safe-Zone (y 134–1104, x 54–1026).
// Eigene Game-Oberfläche in Schmitt-Farben — keine GTA-Schriften/-Logos.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  interpolateColors,
  OffthreadVideo,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { getCalculateMetadata } from "../../../../core/format-utils";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { asset, ci, clamp, easeIn, easeOut, fontFamily, sc } from "./shared";
import { LogoCard, Minimap, Subtitles, Toasts } from "./hud";
import { CUES, HUD, MUSIC, SEGMENTS, SOUNDS } from "./timeline";

const segmentSchema = z.object({
  id: z.string().describe("Kennung für Ton, Untertitel und HUD"),
  kind: z.enum(["shot", "ladescreen", "cta", "logo"]).describe("Clip, Ladescreen, CTA oder Logo-Karte"),
  src: z.string().describe("Clip bzw. Standbild (relativ zu Material/Video); Logo leer = Platzhalter"),
  seconds: z.number().describe("Dauer in s (Clip: höchstens Bilder ÷ Clip-fps − trimStart)"),
  trimStart: z.number().optional().describe("Clip: Start im Quellclip in s"),
  kicker: z.string().optional().describe("Ladescreen/CTA: Kicker"),
  title: z.string().optional().describe("Ladescreen: Quest-Titel · CTA: Stellentitel"),
  hint: z.string().optional().describe("Ladescreen: Ziel-Zeile · CTA: Zusatz zum Titel, z. B. (m/w/d)"),
  perks: z.array(z.string()).optional().describe("CTA: Benefits, nur wörtlich laut schmitt.jobs"),
  button: z.string().optional().describe("CTA: Button-Text"),
  url: z.string().optional().describe("CTA/Logo: Adresse"),
});

const soundSchema = z.object({
  type: z.enum(["sfx", "dialog"]),
  seg: z.string(),
  at: z.number(),
  src: z.string(),
  volume: z.number(),
  duration: z.number(),
  fadeIn: z.number(),
  fadeOut: z.number(),
});

const cueSchema = z.object({ seg: z.string(), start: z.number(), end: z.number(), speaker: z.string(), text: z.string() });

const hudSchema = z.object({
  kind: z.enum(["minimap", "toast"]),
  seg: z.string(),
  at: z.number(),
  untilSeg: z.string(),
  until: z.number(),
  kicker: z.string().optional(),
  text: z.string().optional(),
  icon: z.enum(["pin", "key", "truck", "route"]).optional(),
  routeSeg: z.string().optional(),
  routeAt: z.number().optional(),
});

const musicSchema = z.object({
  src: z.string(),
  dropInSong: z.number(),
  hitSeg: z.string(),
  hitAt: z.number(),
  volume: z.number(),
  duckTo: z.number(),
  fadeIn: z.number(),
  fadeOut: z.number(),
});

export const schmittNeuerSpielstandSchema = projectPropsSchema.extend({
  bgSrc: z.string().describe("Hallenflug (relativ zu Material/Video)"),
  shots: z.array(segmentSchema).describe("Segmente nach dem Startscreen, in Reihenfolge"),
  sounds: z.array(soundSchema).describe("Geräusche und Dialog"),
  cues: z.array(cueSchema).describe("Untertitel"),
  hud: z.array(hudSchema).describe("Minimap und Hinweise"),
  music: musicSchema.describe("Musik mit Drop"),
  sfx: z.boolean().describe("Geräusche an"),
  clipAudio: z.boolean().describe("Ton der Seedance-Clips (enthält generierte Musik)"),
});

type Props = z.infer<typeof schmittNeuerSpielstandSchema>;
type Segment = z.infer<typeof segmentSchema>;

export const schmittNeuerSpielstandDefaults: Props = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 44.8, // nur Fallback — die Länge rechnet schmittNeuerSpielstandMetadata aus den Segmenten
  transparent: false,
  bgSrc: "startscreen/halle.mp4",
  shots: SEGMENTS,
  sounds: SOUNDS,
  cues: CUES,
  hud: HUD,
  music: MUSIC,
  sfx: true,
  clipAudio: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
};

// ---------- Layout-Konstanten (1080 × 1920, Safe Zone y 134–1104) ----------
const CARD_W = 306;
const CARD_H = 340;
const GAP_X = 18;
const GAP_Y = 24;
const GRID_LEFT = (1080 - (3 * CARD_W + 2 * GAP_X)) / 2; // 63 → rechte Kante 1017 (Safe Zone x 54–1026)
const GRID_TOP = 380; // Unterkante Zeile 2: 380 + 340 + 24 + 340 = 1084
const LABEL_H = 84;
const TOP_LINE = 140; // Kicker bzw. „Spiel starten“
const HEADLINE_TOP = 190;
const LOAD_BOTTOM = 1090; // Ladescreen-Textblock wächst von hier nach oben (Safe Zone bis 1104)

type Card = {
  id: string;
  title: string;
  mwd: boolean;
  img?: string;
  zoom?: number; // Bildausschnitt vergrößern (Ganzkörper-Porträts)
  focus?: string; // transformOrigin bzw. objectPosition
};

// Reihenfolge = Rasterposition (Zeile 1: 0–2, Zeile 2: 3–5)
// Karten im Look A: NPCs 3:4 als Hüftporträt, Luca 9:16 Ganzkörper (Zoom auf Kopf + Oberkörper)
const CARDS: Card[] = [
  { id: "stapler", title: "Staplerfahrer", mwd: true, img: "startscreen/karte_staplerfahrer.jpg", focus: "50% 16%" },
  { id: "bkf", title: "Berufskraftfahrer", mwd: true, img: "startscreen/karte_berufskraftfahrer.jpg", zoom: 1.6, focus: "77% 21%" },
  { id: "dispo", title: "Disposition", mwd: true, img: "startscreen/karte_disposition.jpg", focus: "50% 26%" },
  { id: "schicht", title: "Schichtführung Lager", mwd: true, img: "startscreen/karte_schichtfuehrung.jpg", focus: "50% 9%" },
  { id: "azubi", title: "Ausbildung", mwd: false, img: "startscreen/karte_ausbildung.jpg", focus: "50% 20%" },
  { id: "initiativ", title: "Initiativ", mwd: false },
];
const SELECTED = 1;

const cardPos = (i: number) => ({
  x: GRID_LEFT + (i % 3) * (CARD_W + GAP_X),
  y: GRID_TOP + Math.floor(i / 3) * (CARD_H + GAP_Y),
});

// ---------- Timing (Sekunden) ----------
const T = {
  titleIn: 0.12,
  cardsIn: 0.3,
  cardStagger: 0.07,
  cursorIn: 1.0,
  jumps: [
    { at: 1.0, to: 0 },
    { at: 1.28, to: 2 },
    { at: 1.56, to: 4 },
    { at: 1.84, to: 3 },
    { at: 2.12, to: SELECTED },
  ],
  jumpMove: 0.12,
  lockIn: 2.3,
  zoomOut: 3.0,
  shot1At: 3.3,
  loadFade: 0.3, // Ladescreen über Schwarz ein/aus
  clipFade: 0.25, // Clip vor/nach einem Ladescreen
};

// Jeder Clip läuft bis zu seinem letzten Bild (abrunden), damit der Anschluss-Shot nahtlos übernimmt
const segFrames = (seconds: number, fps: number) => Math.floor(seconds * fps);
const segStarts = (segs: Segment[], fps: number) => {
  let from = Math.round(T.shot1At * fps);
  return segs.map((s) => {
    const start = from;
    from += segFrames(s.seconds, fps);
    return start;
  });
};
const endFrame = (segs: Segment[], fps: number) => {
  const starts = segStarts(segs, fps);
  const last = segs.length - 1;
  return last >= 0 ? starts[last] + segFrames(segs[last].seconds, fps) : Math.round(T.shot1At * fps) + 1;
};

export const schmittNeuerSpielstandMetadata = ({ props }: { props: Props }) => {
  const base = getCalculateMetadata(props);
  return { ...base, durationInFrames: endFrame(props.shots, props.fps) };
};

// Auswahlrahmen: ein Element, das zwischen den Kartenpositionen springt
const cursorXY = (t: number) => {
  let from = cardPos(T.jumps[0].to);
  for (let k = 1; k < T.jumps.length; k++) {
    const j = T.jumps[k];
    const target = cardPos(j.to);
    if (t < j.at) return from;
    if (t < j.at + T.jumpMove) {
      const p = easeOut((t - j.at) / T.jumpMove);
      return { x: from.x + (target.x - from.x) * p, y: from.y + (target.y - from.y) * p };
    }
    from = target;
  }
  return from;
};

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const enter = interpolate(t, [T.titleIn, T.titleIn + 0.45], [0, 1], { ...clamp, easing: easeOut });
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: 60,
          top: TOP_LINE,
          width: 960,
          fontFamily,
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: "0.22em",
          color: ci.colors.accent,
          textTransform: "uppercase",
          opacity: enter * interpolate(t, [T.lockIn, T.lockIn + 0.2], [1, 0], clamp),
        }}
      >
        Schmitt Gruppe · Neuer Spielstand
      </div>
      <div
        style={{
          position: "absolute",
          left: 60,
          top: HEADLINE_TOP,
          width: 960,
          fontFamily,
          fontSize: 120,
          fontWeight: 800,
          lineHeight: 1,
          letterSpacing: "-0.015em",
          textTransform: "uppercase",
          color: ci.colors.text,
          textShadow: "0 6px 30px rgba(0,0,0,0.45)",
          opacity: enter,
          translate: `0px ${interpolate(t, [T.titleIn, T.titleIn + 0.5], [36, 0], { ...clamp, easing: easeOut })}px`,
        }}
      >
        Wähle deinen Weg
      </div>
    </>
  );
};

const CardView: React.FC<{ card: Card; index: number }> = ({ card, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const start = T.cardsIn + index * T.cardStagger;
  const pos = cardPos(index);
  const isSel = index === SELECTED;
  const dim = isSel ? 1 : interpolate(t, [T.lockIn, T.lockIn + 0.35], [1, 0.32], { ...clamp, easing: easeOut });
  const lock = isSel ? interpolate(t, [T.lockIn, T.lockIn + 0.2], [0, 1], clamp) : 0;

  return (
    <div
      style={{
        position: "absolute",
        left: pos.x,
        top: pos.y,
        width: CARD_W,
        height: CARD_H,
        opacity: interpolate(t, [start, start + 0.3], [0, 1], { ...clamp, easing: easeOut }) * dim,
        translate: `0px ${interpolate(t, [start, start + 0.4], [40, 0], { ...clamp, easing: easeOut })}px`,
        scale: sc(isSel ? interpolate(t, [T.lockIn, T.lockIn + 0.4], [1, 1.07], { ...clamp, easing: easeOut }) : 1),
        zIndex: isSel ? 2 : 1,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: ci.colors.secondary,
          borderRadius: 6,
          overflow: "hidden",
          boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
        }}
      >
        <div style={{ position: "absolute", left: 0, top: 0, width: CARD_W, height: CARD_H - LABEL_H, overflow: "hidden" }}>
          {card.img ? (
            <Img
              src={asset(card.img)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: card.focus ?? "50% 25%",
                scale: sc(card.zoom ?? 1),
                transformOrigin: card.focus ?? "50% 25%",
              }}
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily,
                fontWeight: 800,
                fontSize: 160,
                color: "rgba(255,255,255,0.22)",
              }}
            >
              ?
            </div>
          )}
        </div>
        <div
          style={{
            position: "absolute",
            left: 0,
            bottom: 0,
            width: CARD_W,
            height: LABEL_H,
            backgroundColor: interpolateColors(lock, [0, 1], ["rgba(14,20,34,0.92)", ci.colors.accent]),
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "0 16px",
            fontFamily,
            color: interpolateColors(lock, [0, 1], ["#FFFFFF", "#131B2E"]),
          }}
        >
          <div
            style={{
              fontSize: card.title.length > 16 ? 27 : 33,
              fontWeight: 700,
              lineHeight: 1,
              textTransform: "uppercase",
              letterSpacing: "0.01em",
              whiteSpace: "nowrap",
            }}
          >
            {card.title}
          </div>
          {card.mwd && <div style={{ fontSize: 21, fontWeight: 500, marginTop: 5, opacity: 0.8 }}>(m/w/d)</div>}
        </div>
      </div>
    </div>
  );
};

const Cursor: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { x, y } = cursorXY(t);
  const pad = 9;
  return (
    <div
      style={{
        position: "absolute",
        left: x - pad,
        top: y - pad,
        width: CARD_W + 2 * pad,
        height: CARD_H + 2 * pad,
        opacity: interpolate(t, [T.cursorIn - 0.08, T.cursorIn + 0.08], [0, 1], clamp),
        scale: sc(interpolate(t, [T.lockIn, T.lockIn + 0.4], [1, 1.07], { ...clamp, easing: easeOut })),
        zIndex: 3,
      }}
    >
      {/* Rahmen aus vier Flächen statt border (Alpha-Falle, WORKFLOW-Motion) */}
      {[
        { left: 0, top: 0, width: "100%", height: 6 },
        { left: 0, bottom: 0, width: "100%", height: 6 },
        { left: 0, top: 0, width: 6, height: "100%" },
        { right: 0, top: 0, width: 6, height: "100%" },
      ].map((s, i) => (
        <div key={i} style={{ position: "absolute", backgroundColor: ci.colors.accent, ...s }} />
      ))}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: -24,
          width: 0,
          height: 0,
          marginLeft: -15,
          borderLeft: "15px solid transparent",
          borderRight: "15px solid transparent",
          borderTop: `18px solid ${ci.colors.accent}`,
        }}
      />
    </div>
  );
};

const StartPrompt: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        top: TOP_LINE - 12,
        display: "flex",
        alignItems: "center",
        gap: 16,
        fontFamily,
        fontWeight: 700,
        fontSize: 40,
        letterSpacing: "0.16em",
        textTransform: "uppercase",
        color: ci.colors.text,
        opacity: interpolate(t, [T.lockIn + 0.1, T.lockIn + 0.3], [0, 1], { ...clamp, easing: easeOut }),
      }}
    >
      <span
        style={{
          display: "inline-block",
          padding: "6px 16px 4px",
          backgroundColor: ci.colors.accent,
          color: "#131B2E",
          borderRadius: 4,
          letterSpacing: 0,
        }}
      >
        A
      </span>
      Spiel starten
    </div>
  );
};

const Startscreen: React.FC<{ bgSrc: string }> = ({ bgSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const focusX = cardPos(SELECTED).x + CARD_W / 2;
  const focusY = cardPos(SELECTED).y + CARD_H / 2;
  return (
    <AbsoluteFill style={{ backgroundColor: ci.colors.background }}>
      <AbsoluteFill style={{ opacity: interpolate(t, [0, 0.35], [0, 1], { ...clamp, easing: easeOut }) }}>
        <OffthreadVideo
          src={asset(bgSrc)}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.6) saturate(1.05)" }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse 85% 60% at 50% 35%, rgba(14,20,34,0.25) 0%, rgba(14,20,34,0.8) 100%)",
        }}
      />
      {/* UI-Ebene: beim Zoom-through gemeinsam auf die gewählte Karte skaliert */}
      <AbsoluteFill
        style={{
          transformOrigin: `${focusX}px ${focusY}px`,
          scale: sc(interpolate(t, [T.zoomOut, T.shot1At], [1, 1.6], { ...clamp, easing: easeIn })),
          opacity: interpolate(t, [T.zoomOut + 0.12, T.shot1At], [1, 0], { ...clamp, easing: easeIn }),
          filter: `blur(${interpolate(t, [T.zoomOut, T.shot1At], [0, 18], { ...clamp, easing: easeIn })}px)`,
        }}
      >
        <Title />
        {CARDS.map((c, i) => (
          <CardView key={c.id} card={c} index={i} />
        ))}
        <Cursor />
        <StartPrompt />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Clip-Segment. Shot 1 landet aus dem Zoom-through (Skalierung, Unschärfe, Lichtblitz);
// vor/nach einem Ladescreen blendet der Clip über Schwarz.
const ShotClip: React.FC<{
  src: string;
  frames: number;
  trimStart: number;
  muted: boolean;
  landing: boolean;
  fadeIn: boolean;
  fadeOut: boolean;
}> = ({ src, frames, trimStart, muted, landing, fadeIn, fadeOut }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const total = frames / fps;
  const fade = (x: number) =>
    (fadeIn ? interpolate(x, [0, T.clipFade], [0, 1], clamp) : 1) *
    (fadeOut ? interpolate(x, [total - T.clipFade, total], [1, 0], clamp) : 1);
  const video = (
    <OffthreadVideo
      src={asset(src)}
      muted={muted}
      trimBefore={trimStart > 0 ? Math.round(trimStart * fps) : undefined}
      volume={muted ? undefined : (f) => fade(f / fps)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  );
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {landing ? (
        <AbsoluteFill
          style={{
            scale: sc(interpolate(t, [0, 0.5], [1.22, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) })),
            filter: `blur(${interpolate(t, [0, 0.35], [16, 0], { ...clamp, easing: easeOut })}px)`,
          }}
        >
          {video}
        </AbsoluteFill>
      ) : (
        video
      )}
      {landing && (
        // kurzer Lichtblitz am Übergang
        <AbsoluteFill
          style={{
            backgroundColor: "#FFF6DD",
            opacity: interpolate(t, [0, 0.06, 0.28], [0.85, 0.5, 0], clamp),
          }}
        />
      )}
      {(fadeIn || fadeOut) && <AbsoluteFill style={{ backgroundColor: "#000", opacity: 1 - fade(t) }} />}
    </AbsoluteFill>
  );
};

// Ladescreen: Artwork mit langsamem Zoom, Quest-Block, Fortschrittsbalken und Lade-Kreis
const Ladescreen: React.FC<{ seg: Segment; frames: number }> = ({ seg, frames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const total = frames / fps;
  const visible =
    interpolate(t, [0, T.loadFade], [0, 1], { ...clamp, easing: easeOut }) *
    interpolate(t, [total - T.loadFade, total], [1, 0], { ...clamp, easing: easeIn });
  const textIn = interpolate(t, [0.2, 0.6], [0, 1], { ...clamp, easing: easeOut });
  const progress = interpolate(t, [0.3, total - T.loadFade], [0, 1], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) });
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <AbsoluteFill style={{ opacity: visible }}>
        <AbsoluteFill
          style={{ scale: sc(interpolate(t, [0, total], [1.04, 1.1])), transformOrigin: "50% 35%" }}
        >
          <Img src={asset(seg.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </AbsoluteFill>
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(180deg, rgba(8,12,22,0) 26%, rgba(8,12,22,0.55) 40%, rgba(8,12,22,0.86) 62%, rgba(8,12,22,0.94) 100%)",
          }}
        />
        {/* weiche Abdunklung hinter dem Textblock: Kicker und Titel bleiben auch über hellen Motivstellen lesbar */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: LOAD_BOTTOM - 530,
            width: 1080,
            height: 700,
            background:
              "radial-gradient(ellipse 75% 48% at 22% 50%, rgba(8,12,22,0.78) 0%, rgba(8,12,22,0.45) 55%, rgba(8,12,22,0) 100%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 60,
            bottom: 1920 - LOAD_BOTTOM,
            width: 960,
            fontFamily,
            opacity: textIn,
            translate: `0px ${interpolate(textIn, [0, 1], [28, 0])}px`,
          }}
        >
          {seg.kicker && (
            <div
              style={{
                fontSize: 34,
                fontWeight: 700,
                letterSpacing: "0.22em",
                textTransform: "uppercase",
                color: ci.colors.accent,
                textShadow: "0 2px 14px rgba(0,0,0,0.6)",
              }}
            >
              {seg.kicker}
            </div>
          )}
          {seg.title && (
            <div
              style={{
                marginTop: 8,
                fontSize: 96,
                fontWeight: 800,
                lineHeight: 0.95,
                letterSpacing: "-0.01em",
                textTransform: "uppercase",
                color: ci.colors.text,
                textShadow: "0 6px 30px rgba(0,0,0,0.5)",
              }}
            >
              {seg.title}
            </div>
          )}
          {seg.hint && (
            <div style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 12, fontSize: 36, fontWeight: 600, color: "rgba(255,255,255,0.88)" }}>
              <svg width={26} height={32} viewBox="0 0 24 30">
                <path
                  d="M12 0C5.4 0 0 5.2 0 11.7 0 20.5 12 30 12 30s12-9.5 12-18.3C24 5.2 18.6 0 12 0zm0 16.5a4.8 4.8 0 1 1 0-9.6 4.8 4.8 0 0 1 0 9.6z"
                  fill={ci.colors.accent}
                />
              </svg>
              {seg.hint}
            </div>
          )}
          {/* Fortschrittsbalken und Lade-Indikator in einer Zeile */}
          <div style={{ marginTop: 30, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div
              style={{
                width: 520,
                height: 8,
                borderRadius: 4,
                overflow: "hidden",
                backgroundColor: "rgba(255,255,255,0.18)",
              }}
            >
              <div style={{ width: `${progress * 100}%`, height: "100%", backgroundColor: ci.colors.accent }} />
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                fontSize: 30,
                fontWeight: 700,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.85)",
              }}
            >
              Lädt
              <svg width={44} height={44} viewBox="0 0 44 44" style={{ rotate: `${(t * 320) % 360}deg` }}>
                <circle cx="22" cy="22" r="18" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="5" />
                <circle
                  cx="22"
                  cy="22"
                  r="18"
                  fill="none"
                  stroke={ci.colors.accent}
                  strokeWidth="5"
                  strokeLinecap="round"
                  strokeDasharray="34 200"
                />
              </svg>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Abschluss-CTA: eingefrorenes Luftbild, Stellentitel, Benefits wie Freischaltungen,
// Button im Stil von „A Spiel starten“ aus dem Startscreen. Texte in der Safe Zone (y 170–1092).
// Der Button-Klick liegt als Geräusch in timeline.ts.
const Cta: React.FC<{ seg: Segment; frames: number }> = ({ seg, frames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const total = frames / fps;
  const inAt = (at: number, dur = 0.4) => interpolate(t, [at, at + dur], [0, 1], { ...clamp, easing: easeOut });
  const dim = inAt(0, 0.6);
  const kickerIn = inAt(0.15);
  const titleIn = inAt(0.3, 0.5);
  const buttonIn = inAt(1.7, 0.45);
  const press = interpolate(t, [2.6, 2.68, 2.85], [1, 0.94, 1], clamp);
  const perks = seg.perks ?? [];
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <AbsoluteFill style={{ scale: sc(interpolate(t, [0, total], [1, 1.06])), transformOrigin: "50% 55%" }}>
        <Img src={asset(seg.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      {/* Abdunklung: oben kräftig für Titel und Benefits, Mitte frei fürs Gebäude, unten für Button und Adresse */}
      <AbsoluteFill
        style={{
          opacity: dim,
          background:
            "linear-gradient(180deg, rgba(8,12,22,0.84) 0%, rgba(8,12,22,0.66) 22%, rgba(8,12,22,0.2) 32%, rgba(8,12,22,0.06) 42%, rgba(8,12,22,0.3) 49%, rgba(8,12,22,0.72) 56%, rgba(8,12,22,0.86) 100%)",
        }}
      />
      <div style={{ position: "absolute", left: 60, top: 170, width: 960, fontFamily }}>
        {seg.kicker && (
          <div
            style={{
              fontSize: 34,
              fontWeight: 700,
              letterSpacing: "0.22em",
              textTransform: "uppercase",
              color: ci.colors.accent,
              opacity: kickerIn,
              translate: `0px ${interpolate(kickerIn, [0, 1], [20, 0])}px`,
            }}
          >
            {seg.kicker}
          </div>
        )}
        {seg.title && (
          <div
            style={{
              marginTop: 10,
              fontSize: 104,
              fontWeight: 800,
              lineHeight: 0.95,
              letterSpacing: "-0.01em",
              textTransform: "uppercase",
              color: ci.colors.text,
              textShadow: "0 6px 30px rgba(0,0,0,0.5)",
              opacity: titleIn,
              translate: `0px ${interpolate(titleIn, [0, 1], [30, 0])}px`,
            }}
          >
            {seg.title}
          </div>
        )}
        {seg.hint && (
          <div style={{ marginTop: 6, fontSize: 44, fontWeight: 600, color: "rgba(255,255,255,0.85)", opacity: titleIn }}>
            {seg.hint}
          </div>
        )}
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 18 }}>
          {perks.map((p, k) => {
            const v = inAt(0.9 + k * 0.15, 0.35);
            return (
              <div
                key={p}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 18,
                  opacity: v,
                  translate: `${interpolate(v, [0, 1], [-24, 0])}px 0px`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 22,
                    backgroundColor: ci.colors.accent,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    scale: sc(interpolate(v, [0, 1], [0.6, 1])),
                  }}
                >
                  <svg width={24} height={24} viewBox="0 0 24 24">
                    <path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#131B2E" strokeWidth={3.4} strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <span style={{ fontSize: 46, fontWeight: 700, color: ci.colors.text, textShadow: "0 3px 16px rgba(0,0,0,0.5)" }}>
                  {p}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      {seg.button && (
        <div
          style={{
            position: "absolute",
            left: 60,
            top: 930,
            width: 960,
            fontFamily,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: buttonIn,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              padding: "16px 40px 16px 18px",
              borderRadius: 60,
              backgroundColor: ci.colors.accent,
              scale: sc(interpolate(buttonIn, [0, 1], [0.85, 1]) * press),
              boxShadow: "0 14px 40px rgba(0,0,0,0.45)",
            }}
          >
            <span
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                backgroundColor: "#131B2E",
                color: ci.colors.accent,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 40,
                fontWeight: 800,
              }}
            >
              A
            </span>
            <span style={{ fontSize: 50, fontWeight: 800, letterSpacing: "0.04em", textTransform: "uppercase", color: "#131B2E" }}>
              {seg.button}
            </span>
          </div>
          {seg.url && (
            <div
              style={{
                marginTop: 18,
                fontSize: 40,
                fontWeight: 700,
                letterSpacing: "0.06em",
                color: ci.colors.text,
                textShadow: "0 3px 16px rgba(0,0,0,0.6)",
              }}
            >
              {seg.url}
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

export const SchmittNeuerSpielstand: React.FC<Props> = ({ bgSrc, shots, sounds, cues, hud, music, sfx, clipAudio, review }) => {
  const { fps } = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const starts = segStarts(shots, fps);
  const videoEnd = endFrame(shots, fps) / fps;

  // Segment-Kennung → Startsekunde im Video („start“ = Startscreen)
  const segSec = (id: string) => {
    if (id === "start") return 0;
    const i = shots.findIndex((s) => s.id === id);
    if (i < 0) throw new Error(`Segment „${id}“ fehlt in shots`);
    return starts[i] / fps;
  };

  const cueWindows = cues.map((c) => ({ from: segSec(c.seg) + c.start, to: segSec(c.seg) + c.end, speaker: c.speaker, text: c.text }));
  const minimaps = hud
    .filter((h) => h.kind === "minimap")
    .map((h) => ({
      from: segSec(h.seg) + h.at,
      to: segSec(h.untilSeg) + h.until,
      routeFrom: h.routeSeg !== undefined ? segSec(h.routeSeg) + (h.routeAt ?? 0) : undefined,
    }));
  const toasts = hud
    .filter((h) => h.kind === "toast")
    .map((h) => ({
      from: segSec(h.seg) + h.at,
      to: segSec(h.untilSeg) + h.until,
      kicker: h.kicker ?? "",
      text: h.text ?? "",
      icon: h.icon ?? "pin",
    }));

  // Musik: Drop auf hitSeg + hitAt; unter Dialog abgesenkt, am Anfang und Ende weich
  const hit = segSec(music.hitSeg) + music.hitAt;
  const songOffset = music.dropInSong - hit; // Song-Sekunde bei Video-Sekunde 0
  const musicFrom = songOffset < 0 ? f(-songOffset) : 0;
  const musicTrim = songOffset > 0 ? f(songOffset) : 0;
  const musicVolume = (t: number) => {
    const ramp =
      interpolate(t, [musicFrom / fps, musicFrom / fps + music.fadeIn], [0, 1], clamp) *
      interpolate(t, [videoEnd - music.fadeOut, videoEnd], [1, 0], clamp);
    const duck = cueWindows.reduce(
      (m, c) => Math.min(m, interpolate(t, [c.from - 0.25, c.from, c.to, c.to + 0.35], [1, music.duckTo, music.duckTo, 1], clamp)),
      1,
    );
    return music.volume * ramp * duck;
  };

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: ci.colors.background }}>
        <Sequence from={0} durationInFrames={f(T.shot1At) + 1} name="Startscreen">
          <Startscreen bgSrc={bgSrc} />
        </Sequence>
        {shots.map((s, i) => {
          const frames = segFrames(s.seconds, fps);
          return (
            <Sequence key={s.id} from={starts[i]} durationInFrames={frames} name={s.id}>
              {s.kind === "ladescreen" ? (
                <Ladescreen seg={s} frames={frames} />
              ) : s.kind === "cta" ? (
                <Cta seg={s} frames={frames} />
              ) : s.kind === "logo" ? (
                <LogoCard src={s.src} url={s.url} frames={frames} />
              ) : (
                <ShotClip
                  src={s.src}
                  frames={frames}
                  trimStart={s.trimStart ?? 0}
                  muted={!clipAudio}
                  landing={i === 0}
                  fadeIn={shots[i - 1]?.kind === "ladescreen"}
                  fadeOut={shots[i + 1]?.kind === "ladescreen"}
                />
              )}
            </Sequence>
          );
        })}

        <Minimap windows={minimaps} />
        <Toasts items={toasts} />
        <Subtitles cues={cueWindows} />

        {/* Ton: jedes Geräusch in eigener Sequenz, so lang wie die Datei, mit weichen Rampen (nichts wird abgehackt) */}
        {sounds
          .filter((s) => sfx || s.type === "dialog")
          .map((s, i) => {
            const from = f(segSec(s.seg) + s.at);
            const dur = Math.max(2, f(s.duration));
            return (
              <Sequence key={`ton-${i}`} from={from} durationInFrames={dur} name={`${s.type}: ${s.src}`} layout="none">
                <Audio
                  src={asset(s.src)}
                  volume={(fr) => {
                    const x = fr / fps;
                    return (
                      s.volume *
                      interpolate(x, [0, Math.max(0.005, s.fadeIn)], [0, 1], clamp) *
                      interpolate(x, [s.duration - Math.max(0.005, s.fadeOut), s.duration], [1, 0], clamp)
                    );
                  }}
                />
              </Sequence>
            );
          })}
        {music.src !== "" && (
          <Sequence from={musicFrom} name="Musik" layout="none">
            <Audio src={asset(music.src)} trimBefore={musicTrim} volume={(fr) => musicVolume((musicFrom + fr) / fps)} />
          </Sequence>
        )}

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
