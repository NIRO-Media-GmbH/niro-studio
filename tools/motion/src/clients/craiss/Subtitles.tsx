// ============================================================
// Craiss Generation Logistik — Untertitel-Spur (Video 01, V3-Schnitt)
//
// Rail-Stil (docs/cinematic-captions.md Abschnitt 11): schlichte
// Untertitel-Leiste, 2-5 Woerter pro Seite, knapp unter der Bildmitte, fuer
// ALLE Cues die gleiche Hoehe (David-Feedback 2026-09-07: konsistente Hoehe
// ist fuer Social Media wichtiger als jede Einstellung einzeln kinnfrei zu
// bekommen). Das generische ReelsSafeZone-Band (45–57,5 %) faellt in den
// engsten Naheinstellungen dieses Videos auf Kinn/Kragen/Hals — genau die
// Zone, ueber die der Kunde sich bei frueheren Elementen beschwert hat;
// die gewaehlte Hoehe liegt knapp darueber und trifft nur in den zwei
// knappsten Nahaufnahmen (8,6s/14,06s) kurz den Kragenbereich, nie das
// Gesicht selbst.
//
// Gleiche Sperrzeiten-/Fenster-Logik wie
// clients/sw-projektentwicklung/Subtitles.tsx (Untertitel nur ausserhalb
// Hook/CTA).
// ============================================================

import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { FONT_BOLD, WHITE } from "./lib";

// Helleres Rot als das Marken-Rot (#CD202C) fuer die Wort-Hervorhebung —
// das dunklere Markenrot wirkt auf dunklem/schattigem Footage matt
// (David-Feedback 2026-09-07). Nur hier, nicht markenweit.
const HIGHLIGHT_RED = "#E5484F";

export type CaptionToken = { text: string; start: number; end: number };
export type CaptionPage = { start: number; end: number; tokens: CaptionToken[] };
export type CaptionFile = { video: string; source: string; pages: CaptionPage[] };

export const subtitlesSchema = z.object({
  enabled: z.boolean().describe("Untertitel anzeigen"),
  fontSize: z.number().step(1).describe("Schriftgroesse (px)"),
  highlight: z.boolean().describe("Gesprochenes Wort rot hervorheben"),
  minGapSec: z
    .number()
    .step(0.1)
    .describe("Luecken zwischen Hook/CTA, die kuerzer sind, bleiben leer (s)"),
  pos: z.object({
    x: z.number().step(1).describe("X (px)"),
    y: z.number().step(1).describe("Y (px)"),
  }),
});
export type SubtitleSettings = z.infer<typeof subtitlesSchema>;

export const SUBTITLE_DEFAULTS: SubtitleSettings = {
  enabled: true,
  fontSize: 48,
  highlight: true,
  minGapSec: 0.5,
  pos: { x: 0, y: 0 },
};

export type BlockedRange = { startSec: number; durationSec: number };

const FADE_FRAMES = 4;
export const MIN_VISIBLE_FRAMES = 10;
const RISE_PX = 10;

// Deckkraft auf glatte 1 schnappen lassen (Flicker-Regel, siehe SW-Subtitles).
const settle = (v: number) => (v > 0.999 ? 1 : v);

type Window = { from: number; to: number };

export const freeWindows = (
  blocked: BlockedRange[],
  fps: number,
  durationInFrames: number,
  minGapFrames: number,
): Window[] => {
  const ranges = blocked
    .map((b) => {
      const from = Math.floor(b.startSec * fps);
      return { from, to: from + Math.floor(b.durationSec * fps) };
    })
    .filter((r) => r.to > r.from)
    .sort((a, b) => a.from - b.from);

  const merged: Window[] = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r.from <= last.to) last.to = Math.max(last.to, r.to);
    else merged.push({ ...r });
  }

  const free: Window[] = [];
  let cursor = 0;
  for (const r of merged) {
    if (r.from > cursor) free.push({ from: cursor, to: r.from });
    cursor = Math.max(cursor, r.to);
  }
  if (cursor < durationInFrames) free.push({ from: cursor, to: durationInFrames });
  return free.filter((w) => w.to - w.from >= minGapFrames);
};

export const SubtitleTrack: React.FC<{
  pages: CaptionPage[];
  blocked: BlockedRange[];
  settings: SubtitleSettings;
  // Buehne der Komposition (px, Basis 1080x1920): tief im Frame, s. Kommentar oben.
  stage: { top: number; height: number; left: number; innerWidth: number };
}> = ({ pages, blocked, settings, stage }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  if (!settings.enabled) return null;

  const windows = freeWindows(blocked, fps, durationInFrames, Math.round(settings.minGapSec * fps));
  const win = windows.find((w) => frame >= w.from && frame < w.to);
  if (!win) return null;

  const t = frame / fps;
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;

  const visFrom = Math.max(Math.round(page.start * fps), win.from);
  const visTo = Math.min(Math.round(page.end * fps), win.to);
  if (visTo - visFrom < MIN_VISIBLE_FRAMES) return null;

  const fadeIn = interpolate(frame, [visFrom, visFrom + FADE_FRAMES], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [visTo - FADE_FRAMES, visTo], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = settle(Math.min(fadeIn, fadeOut));
  const rise = (1 - fadeIn) * RISE_PX;

  let activeIdx = -1;
  page.tokens.forEach((tok, i) => {
    if (t >= tok.start - 0.02) activeIdx = i;
  });

  return (
    <div
      style={{
        position: "absolute",
        top: stage.top + settings.pos.y,
        left: stage.left + settings.pos.x,
        width: stage.innerWidth,
        height: stage.height,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "relative",
          top: rise,
          opacity,
          fontFamily: FONT_BOLD,
          fontSize: settings.fontSize,
          fontWeight: 400,
          lineHeight: 1.2,
          textAlign: "center",
          color: WHITE,
          letterSpacing: 0.2,
          textShadow: "0 2px 6px rgba(0,0,0,0.65), 0 0 22px rgba(0,0,0,0.5)",
          maxWidth: stage.innerWidth,
          textWrap: "balance",
        }}
      >
        {page.tokens.map((tok, i) => (
          <React.Fragment key={i}>
            <span
              style={{
                color: settings.highlight && i === activeIdx ? HIGHLIGHT_RED : WHITE,
              }}
            >
              {tok.text}
            </span>
            {i < page.tokens.length - 1 ? " " : null}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
