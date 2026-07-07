import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, DARK_BG, SAFE } from "./constants";
import { useExit } from "./useExit";

/** Ingredient list popup */
export const IngredientList: React.FC<{
  items: string[];
  title?: string;
}> = ({ items, title = "Zutaten" }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide } = useExit(12);

  const panelProg = spring({
    frame: frame - 2,
    fps,
    config: { damping: 12, stiffness: 140 },
  });

  const titleProg = spring({
    frame: frame - 5,
    fps,
    config: { damping: 10, stiffness: 160 },
  });

  const borderHeight = interpolate(panelProg, [0.2, 1], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const panelWidth = width * 0.44;
  const safeRight = width * SAFE.right;

  return (
    <div
      style={{
        position: "absolute",
        right: width - safeRight,
        top: height * SAFE.top,
        width: panelWidth,
        opacity: panelProg * exitProg,
        transform: `translateX(${interpolate(panelProg, [0, 1], [50, 0])}px) translateY(${exitSlide}px)`,
      }}
    >
      <div
        style={{
          backgroundColor: DARK_BG,
          borderRadius: 8,
          padding: `${height * 0.018}px ${height * 0.022}px`,
          borderLeft: `3px solid ${GOLD}`,
          backdropFilter: `blur(${interpolate(panelProg, [0, 1], [0, 14])}px)`,
          boxShadow: "0 4px 30px rgba(0,0,0,0.5)",
          clipPath: `inset(0 0 ${100 - borderHeight}% 0)`,
        }}
      >
        <div
          style={{
            opacity: titleProg,
            transform: `translateX(${interpolate(titleProg, [0, 1], [12, 0])}px) scale(${interpolate(titleProg, [0, 1], [0.9, 1])})`,
            transformOrigin: "left center",
            fontFamily: "Bitter, serif",
            fontSize: height * 0.024,
            fontWeight: 800,
            color: GOLD,
            letterSpacing: 2.5,
            textTransform: "uppercase",
            marginBottom: height * 0.012,
          }}
        >
          {title}
        </div>

        {items.map((item, i) => {
          const itemDelay = 8 + i * 2;
          const itemProg = spring({
            frame: frame - itemDelay,
            fps,
            config: { damping: 10, stiffness: 180 },
          });

          const dotScale = spring({
            frame: frame - itemDelay,
            fps,
            config: { damping: 6, stiffness: 250 },
          });

          return (
            <div
              key={i}
              style={{
                opacity: itemProg,
                transform: `translateX(${interpolate(itemProg, [0, 1], [25, 0])}px)`,
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: height * 0.007,
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  backgroundColor: GOLD,
                  borderRadius: "50%",
                  flexShrink: 0,
                  transform: `scale(${dotScale})`,
                  boxShadow: `0 0 ${6 * dotScale}px ${GOLD}70`,
                }}
              />
              <span
                style={{
                  fontFamily: "Montserrat, sans-serif",
                  fontSize: height * 0.019,
                  fontWeight: 600,
                  color: "#FFFFFF",
                  textShadow: "0 1px 6px rgba(0,0,0,0.7)",
                }}
              >
                {item}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
