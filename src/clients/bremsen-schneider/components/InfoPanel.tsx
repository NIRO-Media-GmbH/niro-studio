// ============================================================
// Bremsen Schneider — InfoPanel
// Frosted glass panel with yellow accent line
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import {
  BLUE,
  YELLOW,
  WHITE,
  SAFE,
  SMOOTH_SPRING,
  GENTLE_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import type { OverlayPosition } from "./KeywordReveal";

const { fontFamily } = loadFont();

interface InfoPanelProps {
  title: string;
  items?: string[];
  body?: string;
  position: OverlayPosition;
  accentSide?: "left" | "top";
  offsetY?: number;
  offsetX?: number;
}

export const InfoPanel: React.FC<InfoPanelProps> = ({
  title,
  items,
  body,
  position,
  accentSide = "left",
  offsetY = 0,
  offsetX = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // Panel entrance: scale + fade
  const enterProg = spring({ frame, fps, config: SMOOTH_SPRING });
  const panelScale = interpolate(enterProg, [0, 1], [0.92, 1]);
  const panelOpacity = interpolate(enterProg, [0, 1], [0, 1]);

  // Title entrance
  const titleProg = spring({ frame: frame - 4, fps, config: SMOOTH_SPRING });

  // Items stagger
  const itemCount = items?.length ?? 0;

  const pad = Math.round(height * 0.02);
  const panelWidth = width * (SAFE.right - SAFE.left) - Math.round(width * 0.04);
  const fontSize = Math.round(height * 0.022);
  const titleSize = Math.round(height * 0.028);
  const accentWidth = Math.round(height * 0.003);

  // Position Y
  const safeTop = height * SAFE.top;
  const safeBottom = height * SAFE.bottom;
  const safeMid = (safeTop + safeBottom) / 2;

  const posY: Record<OverlayPosition, number> = {
    top: safeTop + height * 0.02,
    center: safeMid - height * 0.08,
    bottom: safeBottom - height * 0.18,
  };

  const y = posY[position] + offsetY;
  const x = width * SAFE.left + Math.round(width * 0.02) + offsetX;

  return (
    <div
      style={{
        position: "absolute",
        top: y,
        left: x,
        width: panelWidth,
        opacity: panelOpacity * exitOpacity,
        transform: `scale(${panelScale}) translateY(${exitSlide}px)`,
        transformOrigin: position === "bottom" ? "bottom left" : "top left",
      }}
    >
      <div
        style={{
          position: "relative",
          backgroundColor: "rgba(0, 107, 187, 0.18)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderRadius: 16,
          border: "1.5px solid rgba(255, 255, 255, 0.12)",
          padding: `${pad}px ${pad * 1.5}px`,
          overflow: "hidden",
        }}
      >
        {/* Accent line */}
        {accentSide === "left" && (
          <div
            style={{
              position: "absolute",
              top: pad,
              left: 0,
              bottom: pad,
              width: accentWidth,
              backgroundColor: YELLOW,
              borderRadius: accentWidth,
              boxShadow: `0 0 16px ${YELLOW}88`,
            }}
          />
        )}
        {accentSide === "top" && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: pad,
              right: pad,
              height: accentWidth,
              backgroundColor: YELLOW,
              borderRadius: accentWidth,
              boxShadow: `0 0 16px ${YELLOW}88`,
            }}
          />
        )}

        {/* Title */}
        <div
          style={{
            fontFamily,
            fontSize: titleSize,
            fontWeight: 800,
            color: WHITE,
            textTransform: "uppercase",
            letterSpacing: Math.round(titleSize * 0.04),
            marginBottom: Math.round(pad * 0.6),
            marginLeft: accentSide === "left" ? pad * 0.6 : 0,
            marginTop: accentSide === "top" ? pad * 0.4 : 0,
            opacity: titleProg,
            transform: `translateX(${interpolate(titleProg, [0, 1], [15, 0])}px)`,
          }}
        >
          {title}
        </div>

        {/* Items list */}
        {items?.map((item, i) => {
          const itemProg = spring({
            frame: frame - 8 - i * 4,
            fps,
            config: GENTLE_SPRING,
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: Math.round(pad * 0.5),
                marginBottom: Math.round(pad * 0.4),
                marginLeft: accentSide === "left" ? pad * 0.6 : 0,
                opacity: itemProg,
                transform: `translateX(${interpolate(itemProg, [0, 1], [20, 0])}px)`,
              }}
            >
              <div
                style={{
                  width: Math.round(fontSize * 0.4),
                  height: Math.round(fontSize * 0.4),
                  borderRadius: "50%",
                  backgroundColor: YELLOW,
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize,
                  fontWeight: 500,
                  color: `${WHITE}DD`,
                  lineHeight: 1.4,
                }}
              >
                {item}
              </span>
            </div>
          );
        })}

        {/* Body text */}
        {body && (
          <div
            style={{
              fontFamily,
              fontSize,
              fontWeight: 400,
              color: `${WHITE}CC`,
              lineHeight: 1.5,
              marginLeft: accentSide === "left" ? pad * 0.6 : 0,
              marginTop: accentSide === "top" ? pad * 0.3 : 0,
              opacity: titleProg,
            }}
          >
            {body}
          </div>
        )}
      </div>
    </div>
  );
};
