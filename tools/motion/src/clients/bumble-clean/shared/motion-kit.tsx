// ============================================================
// BumbleClean — Shared Motion-Kit für die Schnittplan-Social-Serie
// Extrahiert aus V1LackEdit (2026-08-09) für V2–V7. V1 nutzt noch
// lokale Kopien (gerendert + abgenommen — bei nächster Änderung
// dort auf dieses Kit umziehen).
// Design-Raum aller Overlays: 1080×1920, Stage skaliert auf Canvas.
// ============================================================

import React from "react";
import { interpolate, useVideoConfig, Easing } from "remotion";

// --- CI (bumble-clean.de / brand.json) ---
export const GOLD = "#FFD700";
export const GOLD_TIEF = "#C9A227";
export const MUTED = "#CFCFCF";
export const GLASS = "rgba(10,10,10,0.38)";
export const GLASS_BORDER = "rgba(255,255,255,0.22)";
export const RADIUS = 24;

export const BASE_W = 1080;
export const BASE_H = 1920;

export const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;
export const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
export const POP = { damping: 14, stiffness: 160, mass: 1 };

/** Stage skaliert den 1080×1920-Design-Raum auf die echte Canvas. */
export const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  const scale = Math.min(width / BASE_W, height / BASE_H);
  return (
    <div
      style={{
        position: "absolute",
        width: BASE_W,
        height: BASE_H,
        left: (width - BASE_W * scale) / 2,
        top: (height - BASE_H * scale) / 2,
        transform: `scale(${scale})`,
        transformOrigin: "top left",
      }}
    >
      {children}
    </div>
  );
};

// --- Hexagon-Bausteine (Waben-Motiv aus dem Logo) ---

export const hexPath = (cx: number, cy: number, r: number) => {
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
  });
  return `M ${pts.join(" L ")} Z`;
};

export const hexUmfang = (r: number) => 6 * r;

/** 7-Zellen-Logo-Wabe; zeichnet sich Zelle für Zelle (Stroke-Draw). */
export const WabenEmblemDraw: React.FC<{
  r: number;
  progressFrame: number;
  stagger?: number;
  stroke?: string;
  strokeWidth?: number;
}> = ({ r, progressFrame, stagger = 3, stroke = GOLD_TIEF, strokeWidth = 3 }) => {
  const d = r * 1.78;
  const zellen = [
    [0, 0],
    [0, -d],
    [0, d],
    [d * 0.87, -d * 0.5],
    [d * 0.87, d * 0.5],
    [-d * 0.87, -d * 0.5],
    [-d * 0.87, d * 0.5],
  ];
  const umfang = hexUmfang(r * 0.82);
  return (
    <svg
      width={r * 6}
      height={r * 6}
      viewBox={`${-r * 3} ${-r * 3} ${r * 6} ${r * 6}`}
      style={{ display: "block" }}
    >
      {zellen.map(([x, y], i) => {
        const p = interpolate(progressFrame - i * stagger, [0, 14], [0, 1], {
          ...CLAMP,
          easing: Easing.out(Easing.cubic),
        });
        return (
          <path
            key={i}
            d={hexPath(x, y, r * 0.82)}
            fill="none"
            stroke={stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={umfang}
            strokeDashoffset={umfang * (1 - p)}
            opacity={p > 0 ? 0.95 : 0}
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
};

/** Statisches 7-Zellen-Emblem. */
export const WabenEmblem: React.FC<{ r: number; stroke?: string; strokeWidth?: number }> = ({
  r,
  stroke = GOLD,
  strokeWidth = 3,
}) => (
  <WabenEmblemDraw r={r} progressFrame={999} stagger={0} stroke={stroke} strokeWidth={strokeWidth} />
);

/** Kleines Hexagon-Icon für Chips. */
export const HexIcon: React.FC<{ size: number; color?: string }> = ({ size, color = GOLD }) => (
  <svg width={size} height={size} viewBox="-12 -12 24 24" style={{ display: "block" }}>
    <path d={hexPath(0, 0, 9)} fill="none" stroke={color} strokeWidth={2.2} />
  </svg>
);

/** Hexagon-Puls für Drop-Momente (Haupt-Wabe + Echo).
 *  `t` = Frames seit Puls-Start (Start 3 Frames VOR dem Beat setzen). */
export const HexPuls: React.FC<{ t: number }> = ({ t }) => {
  const scale = interpolate(t, [0, 14], [0.72, 1.3], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const op = interpolate(t, [0, 3, 14], [0, 0.55, 0], CLAMP);
  const scale2 = interpolate(t, [2, 16], [1.15, 0.85], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const op2 = interpolate(t, [2, 5, 16], [0, 0.28, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: BASE_W / 2 - 400,
        top: BASE_H / 2 - 400,
        width: 800,
        height: 800,
      }}
    >
      <svg width={800} height={800} viewBox="-400 -400 800 800" style={{ position: "absolute" }}>
        <path
          d={hexPath(0, 0, 340)}
          fill="none"
          stroke={GOLD}
          strokeWidth={4}
          opacity={op}
          transform={`scale(${scale})`}
        />
        <path
          d={hexPath(0, 0, 340)}
          fill="none"
          stroke={GOLD_TIEF}
          strokeWidth={2.5}
          opacity={op2}
          transform={`scale(${scale2})`}
        />
      </svg>
    </div>
  );
};

/** Glass-Chip mit Hex-Icon (Alpha-sicher: kein overflow:hidden). */
export const GlassChip: React.FC<{
  text: string;
  opacity: number;
  translateY?: number;
  fontSize?: number;
  iconSize?: number;
  fontFamily: string;
}> = ({ text, opacity, translateY = 0, fontSize = 30, iconSize = 30, fontFamily }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 14,
      padding: "16px 26px",
      background: GLASS,
      border: `1px solid ${GLASS_BORDER}`,
      borderRadius: RADIUS,
      opacity,
      transform: `translateY(${translateY}px)`,
    }}
  >
    <HexIcon size={iconSize} />
    <span
      style={{
        fontFamily,
        fontWeight: 600,
        fontSize,
        letterSpacing: 3,
        color: "rgba(255,255,255,0.94)",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  </div>
);
