// ============================================================
// Rappold Video 2 — CTA-Karte (5 s, deckend ab Schnitt-Ende) mit Übergang von Hannes
// Feedback 16.09.: keine Person im Hintergrund, eine Farbfläche. Übergang: Anthrazit-
// und Blau-Fläche schieben sich von unten über die letzte Einstellung (Logo-Farben),
// fertig genau auf dem letzten Schnitt-Frame. Titel/JETZT EINTRAGEN: grafik-plan (g-karte-*).
// ============================================================
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { ANTHRAZIT, BASE_H, BASE_W, FONT, RAND_X, WEISS } from "../../lib";
import { SCHNITT_FRAMES } from "./daten-generiert";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const IN_OUT = Easing.inOut(Easing.cubic);
export const WISCH_START = SCHNITT_FRAMES - 16;

export const Endcard: React.FC<{ url: string; farbe: string }> = ({ url, farbe }) => {
  const frame = useCurrentFrame();
  if (frame < WISCH_START) return null;
  const anthrazit = interpolate(frame, [WISCH_START, WISCH_START + 13], [0, 1], { ...CLAMP, easing: IN_OUT });
  const flaeche = interpolate(frame, [WISCH_START + 3, SCHNITT_FRAMES], [0, 1], { ...CLAMP, easing: IN_OUT });
  const f = frame - SCHNITT_FRAMES;
  const logo = interpolate(f, [2, 16], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const link = interpolate(f, [18, 30], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <AbsoluteFill style={{ width: BASE_W, height: BASE_H, overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: BASE_W, height: BASE_H, background: ANTHRAZIT, transform: `translateY(${(1 - anthrazit) * 100}%)` }} />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: BASE_W,
          height: BASE_H,
          background: farbe,
          boxShadow: "0 -18px 40px rgba(0,0,0,0.22)",
          transform: `translateY(${(1 - flaeche) * 100}%)`,
        }}
      />
      {f >= 0 ? (
        <>
          <Img
            src={staticFile("clients/rappold/rappold-logo-weiss.svg")}
            style={{ position: "absolute", left: RAND_X, top: 380, width: 700, opacity: logo, transform: `translateY(${(1 - logo) * 16}px)` }}
          />
          <div
            style={{
              position: "absolute",
              left: RAND_X,
              top: 1210,
              fontFamily: FONT,
              fontWeight: 600,
              fontSize: 42,
              letterSpacing: "0.02em",
              color: WEISS,
              whiteSpace: "nowrap",
              opacity: link,
              transform: `translateY(${(1 - link) * 10}px)`,
            }}
          >
            {url}
          </div>
        </>
      ) : null}
    </AbsoluteFill>
  );
};
