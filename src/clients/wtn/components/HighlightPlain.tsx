// ============================================================
// WTN — HighlightPlain (word-synced, brand look)
// A deliberately DIFFERENT animation from the boxed HighlightPop —
// used for variety. No box, no clip-underline. Instead:
//   • non-emphasis words POP in one-by-one (staggered spring)
//   • the emphasis word is drawn by a LIME HIGHLIGHTER that wipes in
//     L→R, with dark text on the marker (like the WTN posts)
// Free text on the footage with a legibility drop-shadow. Below face zone.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { FONT } from "./fonts";
import {
  LIME,
  OFF_BLACK,
  OFF_WHITE,
  CONTENT_BOTTOM,
  SIGNET_SKEW,
  PUNCH_SPRING,
} from "./constants";
import { useExit } from "./useExit";

interface HighlightPlainProps {
  text: string;
  /** Substring highlighted with the lime marker. Verbatim in text. */
  emphasis?: string;
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.05 (a touch bigger). */
  fontSizeRatio?: number;
}

const STAGGER = 4; // frames between words

export const HighlightPlain: React.FC<HighlightPlainProps> = ({
  text,
  emphasis,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.05,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const bottomPx = Math.round(height * bottomRatio);
  const shadow = "0 3px 14px rgba(0,0,0,0.6), 0 1px 4px rgba(0,0,0,0.65)";

  // Tokenize into words, flagging which fall inside the emphasis span.
  const ei = emphasis && text.includes(emphasis) ? text.indexOf(emphasis) : -1;
  const ej = ei >= 0 && emphasis ? ei + emphasis.length : -1;
  let idx = 0;
  const tokens = text.split(" ").map((w) => {
    const ws = idx;
    const we = idx + w.length;
    idx = we + 1;
    return { w, emph: ei >= 0 && ws < ej && we > ei };
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        left: "50%",
        width: Math.round(width * 0.9),
        transform: `translateX(-50%) translateY(${-exitSlide}px)`,
        opacity: exitOpacity,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: `${Math.round(fontSize * 0.34)}px ${Math.round(fontSize * 0.28)}px`,
        fontFamily: FONT,
        fontSize,
        lineHeight: 1.1,
      }}
    >
      {tokens.map((t, i) => {
        const p = spring({
          frame: frame - i * STAGGER,
          fps,
          config: PUNCH_SPRING,
        });

        if (t.emph) {
          // Highlighter wipe: marker + dark text revealed together L→R.
          const wipe = interpolate(
            frame - i * STAGGER,
            [0, Math.round(fps * 0.32)],
            [0, 100],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            },
          );
          return (
            <span
              key={i}
              style={{
                position: "relative",
                display: "inline-flex",
                alignItems: "center",
                padding: `${Math.round(fontSize * 0.05)}px ${Math.round(fontSize * 0.16)}px`,
                clipPath: `inset(0 ${100 - wipe}% 0 0)`,
              }}
            >
              <span
                aria-hidden
                style={{
                  position: "absolute",
                  inset: 0,
                  backgroundColor: LIME,
                  borderRadius: Math.round(fontSize * 0.12),
                  transform: `skewX(${SIGNET_SKEW}deg)`,
                }}
              />
              <span
                style={{
                  position: "relative",
                  color: OFF_BLACK,
                  fontWeight: 800,
                  whiteSpace: "nowrap",
                }}
              >
                {t.w}
              </span>
            </span>
          );
        }

        // Non-emphasis word: staggered pop-in.
        const opacity = interpolate(p, [0, 0.5], [0, 1], {
          extrapolateRight: "clamp",
        });
        const y = interpolate(p, [0, 1], [26, 0]);
        const scale = interpolate(p, [0, 1], [0.72, 1]);
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              color: OFF_WHITE,
              fontWeight: 600,
              whiteSpace: "nowrap",
              textShadow: shadow,
              opacity,
              transform: `translateY(${y}px) scale(${scale})`,
            }}
          >
            {t.w}
          </span>
        );
      })}
    </div>
  );
};
