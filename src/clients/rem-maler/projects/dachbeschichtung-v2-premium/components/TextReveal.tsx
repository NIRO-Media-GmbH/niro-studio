// ============================================================
// TextReveal — Per-word staggered text fade-up animation
// Apple-style minimalist text reveal for SVG
// ============================================================

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { W } from "../constants";

// --- Config ---
const ENTER_DURATION = 22;
const EXIT_DURATION = 20;
const DEFAULT_STAGGER = 12;
const ENTER_OFFSET_Y = 25;
const FONT_FAMILY = "Inter, system-ui, -apple-system, sans-serif";

// Approximate character width as a fraction of fontSize.
// Slightly generous to account for uppercase-heavy words.
const CHAR_WIDTH_RATIO = 0.6;
const SPACE_WIDTH_RATIO = 0.5;

interface TextRevealProps {
  words: readonly string[];
  startFrame: number;
  staggerFrames?: number;
  fontSize: number;
  color?: string;
  y: number;
  x?: number;
  exitFrame?: number;
  fontWeight?: number;
  glow?: boolean;
  glowColor?: string;
  letterSpacing?: number;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  words,
  startFrame,
  staggerFrames = DEFAULT_STAGGER,
  fontSize,
  color = "#FFFFFF",
  y,
  x,
  exitFrame,
  fontWeight = 400,
  glow = false,
  glowColor,
  letterSpacing = 0,
}) => {
  const frame = useCurrentFrame();
  const isLeftAligned = x != null;
  const anchorX = isLeftAligned ? x : W / 2;
  const textAnchor = isLeftAligned ? "start" as const : "middle" as const;

  // If only one word or stagger is 0, render as a single line
  const singleLine = words.length === 1 || staggerFrames === 0;

  if (singleLine) {
    const text = words.join(" ");
    const enterStart = startFrame;

    // Enter animation
    const enterProgress = interpolate(
      frame,
      [enterStart, enterStart + ENTER_DURATION],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.appleEase },
    );

    const opacity = exitFrame != null
      ? enterProgress * interpolate(
          frame,
          [exitFrame, exitFrame + EXIT_DURATION],
          [1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.appleEase },
        )
      : enterProgress;

    const translateY = (1 - enterProgress) * ENTER_OFFSET_Y;
    const filterId = glow ? "textGlow_single" : undefined;

    return (
      <g>
        {glow && (
          <defs>
            <filter id="textGlow_single" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
        )}
        <text
          x={anchorX}
          y={y}
          textAnchor={textAnchor}
          dominantBaseline="middle"
          fill={color}
          fontSize={fontSize}
          fontFamily={FONT_FAMILY}
          fontWeight={fontWeight}
          letterSpacing={letterSpacing}
          opacity={opacity}
          transform={`translate(0, ${translateY})`}
          filter={filterId ? `url(#${filterId})` : undefined}
        >
          {text}
        </text>
      </g>
    );
  }

  // Per-word stagger: render each word as a separate <text> element
  // Calculate approximate widths for centering
  const wordWidths = words.map(
    (word) => word.length * fontSize * CHAR_WIDTH_RATIO + letterSpacing * word.length,
  );
  const spaceWidth = fontSize * SPACE_WIDTH_RATIO;
  const totalWidth =
    wordWidths.reduce((sum, w) => sum + w, 0) + spaceWidth * (words.length - 1);
  const startX = isLeftAligned ? anchorX : anchorX - totalWidth / 2;

  const glowFilterId = glow ? "textGlow_stagger" : undefined;

  return (
    <g>
      {glow && (
        <defs>
          <filter id="textGlow_stagger" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur
              in="SourceGraphic"
              stdDeviation="12"
              result="blur"
            />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      )}
      {words.map((word, i) => {
        const wordEnterStart = startFrame + i * staggerFrames;

        // Enter
        const enterProgress = interpolate(
          frame,
          [wordEnterStart, wordEnterStart + ENTER_DURATION],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.appleEase },
        );

        // Exit (all words exit together)
        const exitOpacity =
          exitFrame != null
            ? interpolate(
                frame,
                [exitFrame, exitFrame + EXIT_DURATION],
                [1, 0],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.appleEase },
              )
            : 1;

        const opacity = enterProgress * exitOpacity;
        const translateY = (1 - enterProgress) * ENTER_OFFSET_Y;

        // Calculate x position: sum of previous word widths + spaces
        const xOffset = wordWidths.slice(0, i).reduce((sum, w) => sum + w, 0) + i * spaceWidth;
        const wordX = isLeftAligned
          ? startX + xOffset
          : startX + xOffset + wordWidths[i] / 2;

        return (
          <text
            key={i}
            x={wordX}
            y={y}
            textAnchor={isLeftAligned ? "start" : "middle"}
            dominantBaseline="middle"
            fill={glow ? (glowColor ?? color) : color}
            fontSize={fontSize}
            fontFamily={FONT_FAMILY}
            fontWeight={fontWeight}
            letterSpacing={letterSpacing}
            opacity={opacity}
            transform={`translate(0, ${translateY})`}
            filter={glowFilterId ? `url(#${glowFilterId})` : undefined}
          >
            {word}
          </text>
        );
      })}
    </g>
  );
};
