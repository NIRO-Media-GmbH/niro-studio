// ============================================================
// Rappold Video 2 — Grafiken „Freie Typo": blaue Linie zeichnet, Kicker blendet auf,
// Titelzeilen wischen aus einer Maske hoch. Ausstieg 6 Frames; CTA-Karte bleibt stehen.
// ============================================================
import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { Abdunklung } from "../../Abdunklung";
import { BLAU, FONT, RAND_X, SCHATTEN, SCHATTEN_BLAU, WEISS } from "../../lib";
import { GRAFIKEN, type Grafik, type Segment, type TitelZeile } from "./grafik-plan";
import {
  HERO_SPERRUNG,
  KICKER_ABSTAND,
  KICKER_PX,
  KICKER_SPERRUNG,
  LINIE_ABSTAND,
  LINIE_H,
  LINIE_W,
  TITEL_ZEILENHOEHE,
  UNTERZEILE_ABSTAND,
  UNTERZEILE_PX,
  UNTERZEILE_SPERRUNG,
} from "./layout";

const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const AUSSTIEG_FRAMES = 6;

const farbe = (s: Segment) => (s.farbe === "blau" ? { color: BLAU, textShadow: SCHATTEN_BLAU } : { color: WEISS, textShadow: SCHATTEN });

// Nach dem Einstieg ohne Maske, damit der Schatten nicht gekappt wird
const MaskenZeile: React.FC<{ zeile: TitelZeile; start: number; abdunkeln?: number }> = ({ zeile, start, abdunkeln }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, start + 10], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <div style={{ position: "relative", height: zeile.px * TITEL_ZEILENHOEHE, overflow: p < 1 ? "hidden" : "visible" }}>
      <div
        style={{
          transform: `translateY(${(1 - p) * 110}%)`,
          fontWeight: 800,
          fontSize: zeile.px,
          lineHeight: TITEL_ZEILENHOEHE,
          letterSpacing: `${HERO_SPERRUNG}em`,
          whiteSpace: "nowrap",
        }}
      >
        <span style={{ position: "relative", display: "inline-block" }}>
          {abdunkeln ? <Abdunklung staerke={abdunkeln} randX={18} randY={0} weich={14} style={{ top: "16%", bottom: "12%", zIndex: -1 }} /> : null}
          {zeile.segmente.map((s, i) => (
            <span key={i} style={farbe(s)}>
              {s.text}
            </span>
          ))}
        </span>
      </div>
    </div>
  );
};

const Titelblock: React.FC<{ g: Grafik }> = ({ g }) => {
  const frame = useCurrentFrame();
  const f = frame - g.von;
  const rechts = g.ausrichtung === "rechts";
  const linie = interpolate(f, [0, 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const kicker = interpolate(f, [2, 10], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const titelStart = g.von + (g.kicker ? 6 : g.ohneLinie ? 0 : 3);
  const unterStart = titelStart + g.zeilen.length * 3 + 5;
  const unter = interpolate(frame, [unterStart, unterStart + 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const aus = g.stehenBleiben ? 0 : interpolate(frame, [g.bis - AUSSTIEG_FRAMES, g.bis], [0, 1], { ...CLAMP, easing: Easing.in(Easing.cubic) });
  return (
    <div
      style={{
        position: "absolute",
        top: g.y,
        [rechts ? "right" : "left"]: RAND_X,
        textAlign: rechts ? "right" : "left",
        fontFamily: FONT,
        opacity: 1 - aus,
        transform: `translateY(${-12 * aus}px)`,
      }}
    >
      {g.kicker ? (
        <div
          style={{
            position: "relative",
            height: KICKER_PX * 1.2,
            marginBottom: KICKER_ABSTAND,
            fontWeight: 600,
            fontSize: KICKER_PX,
            lineHeight: 1.2,
            letterSpacing: `${KICKER_SPERRUNG}em`,
            color: WEISS,
            textShadow: SCHATTEN,
            whiteSpace: "nowrap",
            opacity: kicker,
            transform: `translateY(${(1 - kicker) * 10}px)`,
          }}
        >
          <span style={{ position: "relative", display: "inline-block" }}>
            {g.abdunkeln ? <Abdunklung staerke={g.abdunkeln} randX={12} randY={2} weich={10} style={{ zIndex: -1 }} /> : null}
            {g.kicker}
          </span>
        </div>
      ) : null}
      {g.ohneLinie ? null : (
        <div
          style={{
            position: "relative",
            width: LINIE_W,
            height: LINIE_H,
            marginBottom: LINIE_ABSTAND,
            marginLeft: rechts ? "auto" : 0,
            background: g.linienFarbe === "weiss" ? WEISS : BLAU,
            boxShadow: "0 2px 10px rgba(0,0,0,0.35)",
            transform: `scaleX(${linie})`,
            transformOrigin: rechts ? "right" : "left",
          }}
        />
      )}
      {g.zeilen.map((z, k) => (
        <MaskenZeile key={k} zeile={z} start={titelStart + k * 3} abdunkeln={g.abdunkeln} />
      ))}
      {g.unterzeile ? (
        <div
          style={{
            position: "relative",
            marginTop: UNTERZEILE_ABSTAND,
            height: UNTERZEILE_PX * 1.25,
            fontWeight: 600,
            fontSize: UNTERZEILE_PX,
            lineHeight: 1.25,
            letterSpacing: `${UNTERZEILE_SPERRUNG}em`,
            whiteSpace: "nowrap",
            opacity: unter,
            transform: `translateY(${(1 - unter) * 10}px)`,
          }}
        >
          <span style={{ position: "relative", display: "inline-block" }}>
            {g.abdunkeln ? <Abdunklung staerke={g.abdunkeln} randX={12} randY={2} weich={10} style={{ zIndex: -1 }} /> : null}
            {g.unterzeile.map((s, i) => (
              <span key={i} style={farbe(s)}>
                {s.text}
              </span>
            ))}
          </span>
        </div>
      ) : null}
    </div>
  );
};

export const Grafiken: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {GRAFIKEN.filter((g) => frame >= g.von && frame < g.bis).map((g) => (
        <Titelblock key={g.id} g={g} />
      ))}
    </>
  );
};
