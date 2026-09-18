// ============================================================
// Video 03 — Begrüßungs-Intro: Flaggen-Wischer (unten), darüber groß HALLO
// und der Begrüßungs-Chip, dessen Text unter voll deckender Flagge wechselt.
// Frames absolut ab Video-Start (Sequence from 0).
// ============================================================
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { CHIP_BOX_STYLE, FONT_BLACK, WHITE } from "../lib";
import { FlagPanel } from "./FlagWipe";
import { greetingIndexAt, wipeOffset, type IntroLayout } from "./wipeTiming";

const HELLO_TOP = 900; // Basis 1920: Bereich der alten Headline (Hook „lower" 940)

export const GreetingIntro: React.FC<{ layout: IntroLayout }> = ({ layout }) => {
  const frame = useCurrentFrame();
  const g = greetingIndexAt(frame, layout.greetings);
  const op = interpolate(frame, [layout.helloToFrame - 4, layout.helloToFrame], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <>
      {layout.wipes.map((w) => {
        const off = wipeOffset(frame, w);
        return off === null ? null : <FlagPanel key={w.country} country={w.country} offset={off} />;
      })}
      {g >= 0 && op > 0 ? (
        <div
          style={{
            position: "absolute",
            top: HELLO_TOP,
            left: 0,
            right: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 22,
            opacity: op,
          }}
        >
          <div
            style={{
              fontFamily: FONT_BLACK,
              fontSize: 150,
              lineHeight: 1,
              color: WHITE,
              textTransform: "uppercase",
              textShadow: "0 4px 26px rgba(0,0,0,0.55)",
            }}
          >
            HALLO
          </div>
          <div style={CHIP_BOX_STYLE}>{layout.greetings[g].text}</div>
        </div>
      ) : null}
    </>
  );
};
