// ============================================================
// Craiss Untertitel-Mix — Renderer
// Grundzeile (Wort für Wort) · Hero-Wort weiß/rot/blau · Wort-Kasten ·
// Glas-Wort. Nur transform + opacity; Deckkraft linear, SOFT-Feder nur auf
// Transforms. Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CRAISS_BLUE, FONT_BLACK, FONT_BOLD, RED, SOFT, WHITE } from "../lib";
import { resolveBlock, type Align } from "./layout";
import { pageTokensWithoutBox, type CaptionPlan, type PlanCue, type PlanToken, type Zone } from "./plan";
import {
  LEAD_SEC,
  activeTokenIndex,
  cueWindow,
  currentPageIndex,
  freeWindows,
  pageTokenRange,
  revealProgress,
  type BlockedRange,
} from "./timing";

const SHADOW = "0 3px 18px rgba(0,0,0,0.55)";
const CARD_SHADOW = "0 8px 28px rgba(0,0,0,0.35)";
const EXIT_FRAMES = 5;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const FLEX: Record<Align, "center" | "flex-start" | "flex-end"> = { center: "center", left: "flex-start", right: "flex-end" };

// Deckkraft auf glatte 1 schnappen (Flicker-Regel, siehe Subtitles.tsx)
const settle = (v: number) => (v > 0.999 ? 1 : v);
const display = (tokens: PlanToken[]) =>
  tokens.map((t) => t.text).join(" ").replace(/[.,!?;:]+$/, "").toUpperCase();
const appearFrame = (start: number, fps: number) => Math.round((start - LEAD_SEC) * fps);

// --- Grundzeile: jedes Wort erscheint an seinem Anfang (12 px Anstieg) ---
const RailWord: React.FC<{ token: PlanToken }> = ({ token }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = revealProgress(token.start, frame, fps);
  const rise = spring({ frame: frame - appearFrame(token.start, fps), fps, config: SOFT });
  // Unsichtbare Wörter behalten ihren Platz → Zeile springt nicht beim Aufbau
  return (
    <span style={{ display: "inline-block", opacity: settle(p), transform: `translateY(${(1 - rise) * 12}px)` }}>
      {token.text}
    </span>
  );
};

const RailLine: React.FC<{ tokens: PlanToken[]; align: Align }> = ({ tokens, align }) => (
  <div style={{ fontFamily: FONT_BOLD, fontSize: 52, lineHeight: 1.2, color: WHITE, textShadow: SHADOW, textAlign: align }}>
    {tokens.map((t, i) => (
      <React.Fragment key={i}>
        <RailWord token={t} />
        {i < tokens.length - 1 ? " " : null}
      </React.Fragment>
    ))}
  </div>
);

// --- Hero-Wort: landet ruhig am Wortanfang (Skalierung 0,94 → 1, 24 px) ---
const HERO_STYLE: Record<"hero-white" | "hero-red" | "hero-blue", React.CSSProperties> = {
  "hero-white": { fontFamily: FONT_BLACK, fontSize: 130, lineHeight: 1.02, color: WHITE, textShadow: SHADOW },
  "hero-red": {
    fontFamily: FONT_BLACK, fontSize: 96, lineHeight: 1.05, color: WHITE,
    backgroundColor: RED, padding: "10px 26px", borderRadius: 6, boxShadow: CARD_SHADOW,
  },
  "hero-blue": {
    fontFamily: FONT_BOLD, fontSize: 64, lineHeight: 1.1, letterSpacing: 2, color: WHITE,
    backgroundColor: CRAISS_BLUE, padding: "10px 24px", borderRadius: 6, boxShadow: CARD_SHADOW,
  },
};

const HeroWord: React.FC<{ tokens: PlanToken[]; variant: keyof typeof HERO_STYLE }> = ({ tokens, variant }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = appearFrame(tokens[0].start, fps);
  const op = interpolate(frame, [at, at + 5], [0, 1], CLAMP);
  const s = spring({ frame: frame - at, fps, config: SOFT });
  return (
    <div
      style={{
        display: "inline-block",
        opacity: settle(op),
        transform: `translateY(${(1 - s) * 24}px) scale(${0.94 + 0.06 * s})`,
        ...HERO_STYLE[variant],
      }}
    >
      {display(tokens)}
    </div>
  );
};

// --- Wort-Kasten ---
const BOX_WORD_STYLE: React.CSSProperties = { fontFamily: FONT_BLACK, fontSize: 110, lineHeight: 1.1, color: WHITE, textTransform: "uppercase" };

// Aufzählung: ausgewähltes Wort im roten Kasten, ersetzt das vorige
const BoxWord: React.FC<{ token: PlanToken }> = ({ token }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = appearFrame(token.start, fps);
  const op = interpolate(frame, [at, at + 5], [0, 1], CLAMP);
  const s = spring({ frame: frame - at, fps, config: SOFT });
  return (
    <div
      style={{
        display: "inline-block", opacity: settle(op), transform: `scale(${0.94 + 0.06 * s})`,
        backgroundColor: RED, padding: "6px 28px", borderRadius: 6, boxShadow: CARD_SHADOW, ...BOX_WORD_STYLE,
      }}
    >
      {display([token])}
    </div>
  );
};

// Hervorhebung: alle Wörter groß, Kasten blendet in 6 Frames zum gesprochenen Wort
const HighlightWord: React.FC<{ token: PlanToken; next?: PlanToken }> = ({ token, next }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const on = appearFrame(token.start, fps);
  const wordOp = interpolate(frame, [on, on + 5], [0, 1], CLAMP);
  const boxIn = interpolate(frame, [on, on + 6], [0, 1], CLAMP);
  const off = next ? appearFrame(next.start, fps) : null;
  const boxOut = off === null ? 0 : interpolate(frame, [off, off + 6], [0, 1], CLAMP);
  const boxOp = boxIn * (1 - boxOut);
  return (
    <span style={{ position: "relative", display: "inline-block", padding: "2px 16px", margin: "4px 0" }}>
      <span
        style={{
          position: "absolute", inset: 0, backgroundColor: RED, borderRadius: 6,
          opacity: settle(boxOp), transform: `scaleX(${0.92 + 0.08 * boxOp})`,
        }}
      />
      <span style={{ position: "relative", opacity: settle(wordOp), textShadow: boxOp > 0.5 ? "none" : SHADOW }}>
        {token.text.replace(/[.,!?;:]+$/, "")}
      </span>
    </span>
  );
};

const WordBoxContent: React.FC<{ cue: PlanCue; from: number; to: number; t: number; align: Align }> = ({ cue, from, to, t, align }) => {
  const page = cue.tokens.slice(from, to);
  if (cue.boxIndices && cue.boxIndices.length > 0) {
    const active = [...cue.boxIndices].reverse().find((i) => t >= cue.tokens[i].start - LEAD_SEC);
    return (
      <>
        <RailLine tokens={pageTokensWithoutBox(cue, from, to)} align={align} />
        {active !== undefined ? <BoxWord key={active} token={cue.tokens[active]} /> : null}
      </>
    );
  }
  return (
    <div style={{ ...BOX_WORD_STYLE, textAlign: align }}>
      {page.map((tok, i) => (
        <React.Fragment key={i}>
          <HighlightWord token={tok} next={page[i + 1]} />
          {i < page.length - 1 ? " " : null}
        </React.Fragment>
      ))}
    </div>
  );
};

// --- Inhalt eines Satzes: aktuelle Seite je nach Treatment ---
const CueContent: React.FC<{ cue: PlanCue; t: number; align: Align }> = ({ cue, t, align }) => {
  const pageIdx = currentPageIndex(cue.pages, cue.tokens, t);
  const [a, b] = pageTokenRange(cue.pages, cue.tokens.length, pageIdx);
  const page = cue.tokens.slice(a, b);

  if (cue.treatment === "wordbox") return <WordBoxContent cue={cue} from={a} to={b} t={t} align={align} />;

  if (cue.treatment !== "rail" && cue.heroIndex !== undefined) {
    const h0 = cue.heroIndex;
    const h1 = h0 + (cue.heroCount ?? 1);
    if (h0 >= a && h1 <= b) {
      const before = cue.tokens.slice(a, h0);
      const after = cue.tokens.slice(h1, b);
      return (
        <>
          {before.length > 0 ? <RailLine tokens={before} align={align} /> : null}
          <HeroWord tokens={cue.tokens.slice(h0, h1)} variant={cue.treatment} />
          {after.length > 0 ? <RailLine tokens={after} align={align} /> : null}
        </>
      );
    }
  }
  return <RailLine tokens={page} align={align} />;
};

// --- Glas-Wort: groß, 40 % Weiß mit feinem Rand, in freier Fläche ---
const GlassWord: React.FC<{ text: string; startSec: number; zone: Zone; y?: number; exitOp: number }> = ({ text, startSec, zone, y, exitOp }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = Math.round(startSec * fps);
  const op = interpolate(frame, [at, at + 10], [0, 1], CLAMP);
  const scale = interpolate(frame, [at, at + 10], [1.02, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const box = resolveBlock(zone, y);
  return (
    <div style={{ position: "absolute", top: box.top, left: box.left, width: box.width, textAlign: box.align, opacity: settle(op * exitOp) }}>
      <span
        style={{
          display: "inline-block", fontFamily: FONT_BLACK, fontSize: 230, lineHeight: 1,
          color: "rgba(255,255,255,0.4)", WebkitTextStroke: "1.5px rgba(255,255,255,0.75)",
          textTransform: "uppercase", transform: `scale(${scale})`,
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const CaptionMixTrack: React.FC<{ plan: CaptionPlan; blocked: BlockedRange[]; minGapSec?: number }> = ({
  plan,
  blocked,
  minGapSec = 0.5,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const windows = freeWindows(blocked, fps, durationInFrames, Math.round(minGapSec * fps));
  const t = frame / fps;

  const cue = plan.cues.find((c) => t >= c.start && t < c.end);
  if (!cue) return null;
  const win = cueWindow(cue, windows, fps);
  if (!win || frame < win.from || frame >= win.to) return null;

  const exitOp = interpolate(frame, [win.to - EXIT_FRAMES, win.to], [1, 0], CLAMP);
  const box = resolveBlock(cue.zone, cue.y);

  return (
    <>
      {cue.glass && t >= cue.glass.startSec ? (
        <GlassWord text={cue.glass.text} startSec={cue.glass.startSec} zone={cue.glass.zone} y={cue.glass.y} exitOp={exitOp} />
      ) : null}
      <div
        style={{
          position: "absolute", top: box.top, left: box.left, width: box.width,
          display: "flex", flexDirection: "column", alignItems: FLEX[box.align], gap: 14,
          textAlign: box.align, opacity: settle(exitOp),
        }}
      >
        <CueContent cue={cue} t={t} align={box.align} />
      </div>
    </>
  );
};
