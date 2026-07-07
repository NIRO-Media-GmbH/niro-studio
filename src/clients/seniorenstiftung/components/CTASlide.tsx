// ============================================================
// Seniorenstiftung — CTASlide (v2, end card)
// Frosted white card in the lower-mid band: eyebrow, role
// headline with a shimmer sweep, logo reveal with soft glow,
// and the brand claim. Six subtle teal bokeh particles rise
// behind the card (deterministic, no randomness).
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Mulish";
import {
  TEAL,
  TEAL_DARK,
  TEAL_LIGHT,
  INK,
  WARM_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import { Logo } from "./Logo";

const { fontFamily } = loadFont();

interface CTASlideProps {
  /** Main line, e.g. "Werde Pflegefachkraft". */
  headline: string;
  /** Eyebrow / action line, e.g. "Jetzt bewerben". */
  sub: string;
  /** Optional teal-highlighted substring of headline. */
  emphasis?: string;
  /** Top anchor of the card as fraction of height. Default 0.34. */
  anchorY?: number;
}

// Deterministic particle field (index-based, loops slowly upward)
const PARTICLES = Array.from({ length: 6 }, (_, i) => ({
  xPct: 8 + ((i * 37) % 84), // spread across the card width
  size: 14 + ((i * 23) % 26),
  speed: 0.55 + ((i * 7) % 10) / 18,
  phase: (i * 53) % 100,
  opacity: 0.12 + ((i * 13) % 10) / 60,
}));

export const CTASlide: React.FC<CTASlideProps> = ({
  headline,
  sub,
  emphasis,
  anchorY = 0.34,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const headSize = Math.round(height * 0.05);
  const pad = Math.round(headSize * 0.7);
  const maxWidth = Math.round(width * 0.84);

  const enter = spring({ frame, fps, config: WARM_SPRING });
  const opacity = interpolate(enter, [0, 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [36, 0]);

  const logoProg = spring({ frame: frame - 14, fps, config: SMOOTH_SPRING });
  const claimProg = spring({ frame: frame - 26, fps, config: SMOOTH_SPRING });

  // Shimmer sweep across the headline: a moving highlight band via
  // background-clip:text. Sweeps once shortly after entrance, then rests.
  const sweep = interpolate(
    frame,
    [16, 16 + Math.round(fps * 1.1)],
    [-40, 140],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  let head: React.ReactNode = headline;
  if (emphasis && headline.includes(emphasis)) {
    const i = headline.indexOf(emphasis);
    head = (
      <>
        {headline.slice(0, i)}
        <span style={{ color: TEAL }}>{emphasis}</span>
        {headline.slice(i + emphasis.length)}
      </>
    );
  }

  const cardHeightEst = Math.round(height * 0.34); // particle travel range

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: "50%",
        transform: `translateX(-50%) translateY(${y + exitSlide}px)`,
        opacity: opacity * exitOpacity,
        width: maxWidth,
      }}
    >
      {/* Bokeh particles rising behind the card */}
      <div
        style={{
          position: "absolute",
          inset: -Math.round(headSize * 1.2),
          overflow: "hidden",
          borderRadius: Math.round(headSize * 0.9),
          pointerEvents: "none",
        }}
      >
        {PARTICLES.map((p, i) => {
          const travel =
            (frame * p.speed + p.phase * 4) % (cardHeightEst + 80);
          const py = cardHeightEst + 40 - travel;
          const fade =
            Math.sin(
              Math.min(Math.max(travel / (cardHeightEst + 80), 0), 1) *
                Math.PI,
            ) * p.opacity;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${p.xPct}%`,
                top: py,
                width: p.size,
                height: p.size,
                borderRadius: "50%",
                background: `radial-gradient(circle, ${TEAL_LIGHT} 0%, transparent 70%)`,
                opacity: fade,
              }}
            />
          );
        })}
      </div>

      <div
        style={{
          position: "relative",
          padding: `${Math.round(pad * 1.3)}px ${pad}px`,
          backgroundColor: "rgba(255,255,255,0.97)",
          borderRadius: Math.round(headSize * 0.5),
          boxShadow:
            "0 26px 64px rgba(14,60,90,0.34), 0 6px 18px rgba(14,60,90,0.2)",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: Math.round(headSize * 0.36),
            fontWeight: 900,
            color: TEAL,
            textTransform: "uppercase",
            letterSpacing: Math.round(headSize * 0.06),
            marginBottom: Math.round(headSize * 0.28),
          }}
        >
          {sub}
        </div>
        <div style={{ position: "relative", display: "inline-block" }}>
          <div
            style={{
              fontFamily,
              fontSize: headSize,
              fontWeight: 900,
              color: INK,
              lineHeight: 1.15,
              letterSpacing: -Math.round(headSize * 0.015),
            }}
          >
            {head}
          </div>
          {/* Shimmer band clipped to the headline text */}
          <div
            aria-hidden
            style={{
              position: "absolute",
              inset: 0,
              fontFamily,
              fontSize: headSize,
              fontWeight: 900,
              lineHeight: 1.15,
              letterSpacing: -Math.round(headSize * 0.015),
              backgroundImage: `linear-gradient(105deg, transparent ${sweep - 14}%, rgba(255,255,255,0.85) ${sweep}%, transparent ${sweep + 14}%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              pointerEvents: "none",
            }}
          >
            {headline}
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
          <Logo width={Math.round(width * 0.52)} />
        </div>
        <div
          style={{
            marginTop: Math.round(headSize * 0.4),
            fontFamily,
            fontSize: Math.round(headSize * 0.4),
            fontWeight: 700,
            fontStyle: "italic",
            color: TEAL_DARK,
            opacity: claimProg,
          }}
        >
          Geborgen in guten Händen
        </div>
      </div>
    </div>
  );
};
