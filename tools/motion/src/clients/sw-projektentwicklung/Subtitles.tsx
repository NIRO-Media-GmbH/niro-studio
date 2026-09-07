// ============================================================
// SW Projektentwicklung — Untertitel-Spur fuer die Solar-Wissen-Reels
//
// Zeigt den gesprochenen Text seitenweise (2–5 Woerter) an — aber NUR dann,
// wenn gerade keine Szenen-Animation laeuft. Die Szenen bleiben unveraendert;
// die Spur bekommt ihre Start/Dauer-Werte als Sperrzeiten und rechnet daraus
// die freien Fenster. Innerhalb eines Fensters laeuft der Untertitel, an den
// Fenstergrenzen blendet er kurz ein/aus.
//
// Platz: dieselbe Buehne wie die Grafiken (unterhalb der Gesichts-Zone, ueber
// der Safe-Zone-Unterkante). Fuer den Alpha-Export gilt dasselbe wie fuer die
// Grafiken: kein backdropFilter/mixBlendMode, Kontrast ueber Text-Schatten.
// ============================================================

import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";

export type CaptionToken = { text: string; start: number; end: number };
export type CaptionPage = { start: number; end: number; tokens: CaptionToken[] };
export type CaptionFile = { video: string; source: string; pages: CaptionPage[] };

export const subtitlesSchema = z.object({
  enabled: z.boolean().describe("Untertitel anzeigen"),
  fontSize: z.number().step(1).describe("Schriftgroesse (px)"),
  highlight: z.boolean().describe("Gesprochenes Wort orange hervorheben"),
  minGapSec: z
    .number()
    .step(0.1)
    .describe("Luecken zwischen Animationen, die kuerzer sind, bleiben leer (s)"),
  pos: z.object({
    x: z.number().step(1).describe("X (px)"),
    y: z.number().step(1).describe("Y (px)"),
  }),
});
export type SubtitleSettings = z.infer<typeof subtitlesSchema>;

export const SUBTITLE_DEFAULTS: SubtitleSettings = {
  enabled: true,
  fontSize: 46,
  highlight: true,
  minGapSec: 0.5,
  pos: { x: 0, y: 0 },
};

export type BlockedRange = { startSec: number; durationSec: number };

const ORANGE = "#FF8022";
const WHITE = "#FFFFFF";
const FONT = "Montserrat, sans-serif";

const FADE_FRAMES = 4;
export const MIN_VISIBLE_FRAMES = 10; // kuerzer sichtbare Reste einer Seite fallen weg
const RISE_PX = 10;

// Deckkraft auf glatte 1 schnappen lassen — sonst bleibt in Chrome eine eigene
// Render-Surface bestehen und der Text kann beim Einzelframe-Render flackern
// (Befund Video 03, Protokoll 2026-08-20).
const settle = (v: number) => (v > 0.999 ? 1 : v);

type Window = { from: number; to: number }; // Frames, halboffen [from, to)

// Sperrzeiten -> freie Fenster. Die Sperren werden exakt so in Frames gerechnet
// wie die <Sequence>-Elemente der Szenen (Math.floor auf Start und Dauer), damit
// Untertitel und Grafik sich nie um einen Frame ueberlappen.
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
  // Buehne der Komposition (px): oberhalb liegt die Gesichts-Zone.
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

  // Aktives Wort: das zuletzt begonnene. Nur die Farbe wechselt — ein
  // Gewichtswechsel wuerde die Zeile bei jedem Wort neu umbrechen.
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
          fontFamily: FONT,
          fontSize: settings.fontSize,
          fontWeight: 600,
          lineHeight: 1.18,
          textAlign: "center",
          color: WHITE,
          letterSpacing: 0.2,
          textShadow: "0 2px 6px rgba(0,0,0,0.6), 0 0 22px rgba(0,0,0,0.45)",
          maxWidth: stage.innerWidth,
          textWrap: "balance",
        }}
      >
        {page.tokens.map((tok, i) => (
          <React.Fragment key={i}>
            <span
              style={{
                color: settings.highlight && i === activeIdx ? ORANGE : WHITE,
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
