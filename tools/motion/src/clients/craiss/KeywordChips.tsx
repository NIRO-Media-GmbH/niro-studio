// ============================================================
// Craiss Schlagwort-Chips — Ebene über dem Schnitt (Spec 2026-09-16).
// Ersetzt in der Lieferung die Satz-Untertitel; je Chip eine Sequence.
// ============================================================
import React from "react";
import { Sequence, useVideoConfig } from "remotion";
import { BASE_H, BASE_W, RedChip } from "./lib";
import type { Keyword } from "./captionMix/keywords";

export const KeywordChipsLayer: React.FC<{ keywords: Keyword[] }> = ({ keywords }) => {
  const { fps, width } = useVideoConfig();
  const f = (sec: number) => Math.round(sec * fps);
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: BASE_W,
        height: BASE_H,
        transform: `scale(${width / BASE_W})`,
        transformOrigin: "top left",
      }}
    >
      {keywords.map((k) => (
        <Sequence
          key={`${k.text}-${k.startSec}`}
          from={f(k.startSec)}
          durationInFrames={f(k.endSec) - f(k.startSec)}
          name={`Schlagwort: ${k.text}`}
        >
          <RedChip chip={k} />
        </Sequence>
      ))}
    </div>
  );
};
