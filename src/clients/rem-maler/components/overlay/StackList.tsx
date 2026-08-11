// ============================================================
// REM Overlay — StackList
// Links verankerte vertikale Liste. Optionales Heading (rotes
// kantiges Badge), Items erscheinen einzeln (wortsynchron über
// staggerFrames steuerbar). tone: "pos" = Grün, "neg" = Rot.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import {
  RED,
  GREEN,
  INK,
  WHITE,
  SAFE,
  RADIUS,
  BADGE_RADIUS,
  PUNCH_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import { RemIcon, type RemIconName } from "./RemIcons";

const { fontFamily } = loadFont();

export type ListTone = "default" | "pos" | "neg";

export interface ListItem {
  label: string;
  icon: RemIconName;
  tone?: ListTone;
}

interface StackListProps {
  items: ListItem[];
  heading?: string;
  /** Top anchor as fraction of height (default: 0.26) */
  anchorY?: number;
  /** X offset in pixels */
  offsetX?: number;
  /** Font size as fraction of height (default: 0.04) */
  fontSizeRatio?: number;
  /** Frames between each item's entrance */
  staggerFrames?: number;
}

// Kundenwunsch: negativ = Rot, positiv = Grün
const toneColor = (tone: ListTone | undefined): string =>
  tone === "pos" ? GREEN : RED;

export const StackList: React.FC<StackListProps> = ({
  items,
  heading,
  anchorY = 0.26,
  offsetX = 0,
  fontSizeRatio = 0.04,
  staggerFrames = 7,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const badge = Math.round(fontSize * 1.5);
  const rowPadV = Math.round(fontSize * 0.4);
  const rowPadH = Math.round(fontSize * 0.55);
  const rowGap = Math.round(fontSize * 0.5);
  const maxWidth = Math.round(width * 0.44);

  const headingProg = spring({ frame, fps, config: SMOOTH_SPRING });

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: Math.round(width * SAFE.left) + offsetX,
        maxWidth,
        display: "flex",
        flexDirection: "column",
        gap: Math.round(fontSize * 0.35),
        opacity: exitOpacity,
        transform: `translateY(${exitSlide}px)`,
      }}
    >
      {heading && (
        <div
          style={{
            fontFamily,
            fontSize: Math.round(fontSize * 0.62),
            fontWeight: 800,
            color: WHITE,
            textTransform: "uppercase",
            letterSpacing: Math.round(fontSize * 0.06),
            padding: `${Math.round(fontSize * 0.25)}px ${Math.round(fontSize * 0.55)}px`,
            background: RED,
            borderRadius: BADGE_RADIUS,
            alignSelf: "flex-start",
            marginBottom: Math.round(fontSize * 0.2),
            opacity: headingProg,
            transform: `translateX(${interpolate(headingProg, [0, 1], [-24, 0])}px)`,
            boxShadow: `0 8px 22px ${RED}55`,
          }}
        >
          {heading}
        </div>
      )}

      {items.map((item, i) => {
        const delay = (heading ? 4 : 0) + i * staggerFrames;
        const enter = spring({ frame: frame - delay, fps, config: PUNCH_SPRING });
        const opacity = interpolate(enter, [0, 0.5], [0, 1], {
          extrapolateRight: "clamp",
        });
        const slideX = interpolate(enter, [0, 1], [-36, 0]);
        const scale = interpolate(enter, [0, 1], [0.9, 1]);
        const color = toneColor(item.tone);

        return (
          <div
            key={i}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: rowGap,
              alignSelf: "flex-start",
              padding: `${rowPadV}px ${Math.round(rowPadH * 1.2)}px ${rowPadV}px ${rowPadH}px`,
              backgroundColor: "rgba(255,255,255,0.95)",
              borderRadius: RADIUS,
              boxShadow:
                "0 12px 32px rgba(26,26,46,0.26), 0 3px 9px rgba(26,26,46,0.14)",
              opacity,
              transform: `translateX(${slideX}px) scale(${scale})`,
              transformOrigin: "left center",
            }}
          >
            <div
              style={{
                width: badge,
                height: badge,
                borderRadius: BADGE_RADIUS,
                backgroundColor: color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                boxShadow: `0 5px 14px ${color}55`,
              }}
            >
              <RemIcon
                name={item.icon}
                size={Math.round(badge * 0.58)}
                color={WHITE}
                strokeWidth={2.2}
              />
            </div>
            <span
              style={{
                fontFamily,
                fontSize,
                fontWeight: 700,
                color: INK,
                letterSpacing: -Math.round(fontSize * 0.01),
                whiteSpace: "nowrap",
              }}
            >
              {item.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};
