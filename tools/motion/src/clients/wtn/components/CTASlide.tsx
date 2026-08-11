// ============================================================
// WTN — CTASlide (end card, brand look)
// Dark navy card, centered in the reels safe zone: a LIME eyebrow
// pill, off-white headline with a lime emphasis + shimmer sweep, the
// white WTN logo, and the claim. Behind the card, slanted lime/blue
// signet bars rise (deterministic) — a nod to the WTN mark.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { FONT } from "./fonts";
import {
  LIME,
  BLUE,
  OFF_BLACK,
  OFF_WHITE,
  LIGHT_BLUE,
  SIGNET_SKEW,
  PUNCH_SPRING,
  SMOOTH_SPRING,
  CARD_BG,
  CARD_SHADOW,
} from "./constants";
import { useExit } from "./useExit";
import { Logo } from "./Logo";

interface CTASlideProps {
  /** Main line, e.g. "Werde Teil der WTN Familie". */
  headline: string;
  /** Eyebrow / action line, e.g. "Jetzt bewerben". */
  sub: string;
  /** Optional lime-highlighted substring of headline. */
  emphasis?: string;
  /** Claim line under the logo. Default the WTN claim. */
  claim?: string;
  /** Vertical CENTER of the card as fraction of height. Default 0.3226 =
   *  the vertical middle of the reels safe zone. */
  anchorY?: number;
}

// Deterministic slanted-bar field (index-based, loops slowly upward)
const BARS = Array.from({ length: 8 }, (_, i) => ({
  xPct: 5 + ((i * 41) % 90),
  w: 7 + ((i * 11) % 9),
  h: 28 + ((i * 29) % 44),
  speed: 0.5 + ((i * 7) % 10) / 16,
  phase: (i * 53) % 100,
  opacity: 0.14 + ((i * 13) % 8) / 46,
  lime: i % 3 === 0, // ~1/3 lime, rest blue
}));

export const CTASlide: React.FC<CTASlideProps> = ({
  headline,
  sub,
  emphasis,
  claim = "Know-how perfektioniert.",
  anchorY = 0.3226,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // Compact end card — deliberately small so it covers less footage.
  const headSize = Math.round(height * 0.042);
  const pad = Math.round(headSize * 0.7);
  const maxWidth = Math.round(width * 0.72);

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.45], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [40, 0]);

  const subProg = spring({ frame: frame - 6, fps, config: SMOOTH_SPRING });
  const logoProg = spring({ frame: frame - 16, fps, config: SMOOTH_SPRING });
  const claimProg = spring({ frame: frame - 28, fps, config: SMOOTH_SPRING });

  // Lime shimmer sweep across the headline via background-clip:text.
  const sweep = interpolate(
    frame,
    [18, 18 + Math.round(fps * 1.05)],
    [-40, 140],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Mixed weights: base line in Semibold, the emphasis word in Black.
  // `colored=false` variant (same weights, transparent) drives the
  // shimmer so the lime sweep aligns exactly with the glyphs.
  const ei = emphasis && headline.includes(emphasis) ? headline.indexOf(emphasis) : -1;
  const renderHead = (colored: boolean): React.ReactNode =>
    ei >= 0 && emphasis ? (
      <>
        {headline.slice(0, ei)}
        <span style={{ color: colored ? LIME : undefined, fontWeight: 800 }}>
          {emphasis}
        </span>
        {headline.slice(ei + emphasis.length)}
      </>
    ) : (
      headline
    );

  const travelRange = Math.round(height * 0.34);

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: "50%",
        transform: `translate(-50%, -50%) translateY(${y + exitSlide}px)`,
        opacity: opacity * exitOpacity,
        width: maxWidth,
      }}
    >
      {/* Slanted signet bars rising behind the card */}
      <div
        style={{
          position: "absolute",
          inset: -Math.round(headSize * 1.2),
          overflow: "hidden",
          borderRadius: Math.round(headSize * 0.7),
          pointerEvents: "none",
        }}
      >
        {BARS.map((b, i) => {
          const travel = (frame * b.speed + b.phase * 4) % (travelRange + 80);
          const by = travelRange + 40 - travel;
          const fade =
            Math.sin(
              Math.min(Math.max(travel / (travelRange + 80), 0), 1) * Math.PI,
            ) * b.opacity;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${b.xPct}%`,
                top: by,
                width: b.w,
                height: b.h,
                transform: `skewX(${SIGNET_SKEW}deg)`,
                borderRadius: 2,
                background: b.lime
                  ? `linear-gradient(180deg, ${LIME}, ${LIME})`
                  : `linear-gradient(180deg, ${LIGHT_BLUE}, ${BLUE})`,
                opacity: fade,
              }}
            />
          );
        })}
      </div>

      <div
        style={{
          position: "relative",
          padding: `${Math.round(pad * 1.25)}px ${pad}px`,
          backgroundColor: CARD_BG,
          borderRadius: Math.round(headSize * 0.4),
          boxShadow: CARD_SHADOW,
          textAlign: "center",
        }}
      >
        {/* LIME eyebrow pill */}
        <div
          style={{
            display: "inline-block",
            marginBottom: Math.round(headSize * 0.32),
            padding: `${Math.round(headSize * 0.16)}px ${Math.round(headSize * 0.42)}px`,
            backgroundColor: LIME,
            borderRadius: 999,
            opacity: subProg,
            transform: `translateY(${interpolate(subProg, [0, 1], [10, 0])}px)`,
          }}
        >
          <div
            style={{
              fontFamily: FONT,
              fontSize: Math.round(headSize * 0.34),
              fontWeight: 800,
              color: OFF_BLACK,
              textTransform: "uppercase",
              letterSpacing: Math.round(headSize * 0.04),
            }}
          >
            {sub}
          </div>
        </div>
        <div style={{ position: "relative", display: "inline-block" }}>
          <div
            style={{
              fontFamily: FONT,
              fontSize: headSize,
              fontWeight: 600,
              color: OFF_WHITE,
              lineHeight: 1.2,
              letterSpacing: -Math.round(headSize * 0.012),
            }}
          >
            {renderHead(true)}
          </div>
          {/* Lime shimmer band clipped to the headline text (same weights) */}
          <div
            aria-hidden
            style={{
              position: "absolute",
              inset: 0,
              fontFamily: FONT,
              fontSize: headSize,
              fontWeight: 600,
              lineHeight: 1.2,
              letterSpacing: -Math.round(headSize * 0.012),
              backgroundImage: `linear-gradient(105deg, transparent ${sweep - 12}%, ${LIME} ${sweep}%, transparent ${sweep + 12}%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              pointerEvents: "none",
            }}
          >
            {renderHead(false)}
          </div>
        </div>
        <div
          style={{
            marginTop: Math.round(headSize * 0.6),
            display: "flex",
            justifyContent: "center",
            opacity: logoProg,
            transform: `translateY(${interpolate(logoProg, [0, 1], [12, 0])}px)`,
          }}
        >
          <Logo variant="white" width={Math.round(width * 0.4)} />
        </div>
        <div
          style={{
            marginTop: Math.round(headSize * 0.4),
            fontFamily: FONT,
            fontSize: Math.round(headSize * 0.4),
            fontWeight: 600,
            fontStyle: "italic",
            color: LIGHT_BLUE,
            opacity: claimProg,
          }}
        >
          {claim}
        </div>
      </div>
    </div>
  );
};
