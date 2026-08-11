// ============================================================
// SlideText — Structured slide layout: tag + headline + bullets
// Apple-style staggered reveal animation
// ============================================================

import React, { useRef, useState, useLayoutEffect } from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { WHITE } from "../constants";

const appleEase = EASING_PRESETS.appleEase;

// Layout constants
const TAG_FONT = 56;
const HEADLINE_FONT = 180;
const HEADLINE_LH = 210;
const BULLET_FONT = 80;
const BULLET_LH = 120;
const GAP_TAG_HEADLINE = 180;
const GAP_HEADLINE_BULLETS = 100;

const ENTER_DUR = 14;
const EXIT_DUR = 15;
const SLIDE_UP = 50;

export interface SlideTextProps {
  tag: string;
  headline: string[];
  bullets: string[];
  startFrame: number;
  exitFrame?: number;
  x: number;
  y: number;
  // Absolute Startframes je Bullet (wortsynchron zum O-Ton);
  // fehlt der Eintrag, greift der Standard-Stagger.
  bulletFrames?: number[];
}

export const SlideText: React.FC<SlideTextProps> = ({
  tag,
  headline,
  bullets,
  startFrame,
  exitFrame,
  x,
  y,
  bulletFrames,
}) => {
  const frame = useCurrentFrame();
  const tagRef = useRef<SVGTextElement>(null);
  const [tagW, setTagW] = useState(0);

  const tagLabel = tag.toUpperCase();

  // Measure actual rendered tag text width
  useLayoutEffect(() => {
    if (tagRef.current) {
      setTagW(tagRef.current.getComputedTextLength());
    }
  }, [tagLabel]);

  // Element reveal: fade in + slide up
  const reveal = (start: number) => {
    const t = interpolate(frame, [start, start + ENTER_DUR], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: appleEase,
    });
    return { opacity: t, dy: (1 - t) * SLIDE_UP };
  };

  // Exit fade
  const exitOp =
    exitFrame != null
      ? interpolate(frame, [exitFrame, exitFrame + EXIT_DUR], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: appleEase,
        })
      : 1;

  if (exitOp <= 0.01) return null;

  // Vertical positions (y = tag baseline)
  const headlineBaseY = y + GAP_TAG_HEADLINE;
  const bulletsBaseY =
    headlineBaseY + headline.length * HEADLINE_LH + GAP_HEADLINE_BULLETS;

  // Stagger timing
  const tagR = reveal(startFrame);

  const tagPadX = 24;
  const tagPadY = 14;

  return (
    <g opacity={exitOp}>
      {/* Tag with subtle background */}
      <g opacity={tagR.opacity} transform={`translate(0 ${tagR.dy})`}>
        {tagW > 0 && (
          <rect
            x={x - tagPadX}
            y={y - 75 - TAG_FONT + 2}
            width={tagW + tagPadX * 2}
            height={TAG_FONT + tagPadY * 2 + 4}
            rx={4}
            fill="rgba(255,255,255,0.07)"
          />
        )}
        <text
          ref={tagRef}
          x={x}
          y={y - 75 + tagPadY}
          fill="rgba(255,255,255,0.55)"
          fontSize={TAG_FONT}
          fontFamily="Inter, system-ui, -apple-system, sans-serif"
          fontWeight={500}
          letterSpacing="4"
        >
          {tagLabel}
        </text>
      </g>

      {/* Headline lines */}
      {headline.map((line, i) => {
        const r = reveal(startFrame + 6 + i * 7);
        return (
          <g
            key={`h-${i}`}
            opacity={r.opacity}
            transform={`translate(0 ${r.dy})`}
          >
            <text
              x={x}
              y={headlineBaseY + i * HEADLINE_LH}
              fill={WHITE}
              fontSize={HEADLINE_FONT}
              fontFamily="Inter, system-ui, -apple-system, sans-serif"
              fontWeight={700}
            >
              {line}
            </text>
          </g>
        );
      })}

      {/* Bullet items */}
      {bullets.map((bullet, i) => {
        const r = reveal(bulletFrames?.[i] ?? startFrame + 28 + i * 8);
        return (
          <g
            key={`b-${i}`}
            opacity={r.opacity}
            transform={`translate(0 ${r.dy})`}
          >
            <text
              x={x}
              y={bulletsBaseY + i * BULLET_LH}
              fill="rgba(255,255,255,0.7)"
              fontSize={BULLET_FONT}
              fontFamily="Inter, system-ui, -apple-system, sans-serif"
              fontWeight={400}
            >
              {bullet}
            </text>
          </g>
        );
      })}
    </g>
  );
};
