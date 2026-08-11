import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { ACCENT, SAFE } from "./constants";
import { useExit } from "./useExit";

/** Word-by-word animated caption — centered in safe zone */
export const WordByWord: React.FC<{
  text: string;
  highlightColor?: string;
  position?: "center" | "lower";
}> = ({ text, highlightColor = ACCENT, position = "center" }) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitProg } = useExit(8);

  const words = text.split(" ");
  const framesPerWord = Math.max(3, Math.floor((durationInFrames - 10) / words.length));

  const safeLeft = width * SAFE.left;
  const safeRight = width * SAFE.right;
  const safeCenterX = (safeLeft + safeRight) / 2;
  const posY =
    position === "center"
      ? ((SAFE.top + SAFE.bottom) / 2) * height
      : SAFE.bottom * height - height * 0.04;

  return (
    <div
      style={{
        position: "absolute",
        top: posY,
        left: safeCenterX,
        transform: "translate(-50%, -50%)",
        opacity: exitProg,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: width * 0.018,
        maxWidth: (safeRight - safeLeft) * 0.95,
      }}
    >
      {words.map((word, i) => {
        const wordStart = i * framesPerWord;
        const isActive = frame >= wordStart;
        const isCurrent = frame >= wordStart && frame < wordStart + framesPerWord;

        const popProg = isActive
          ? spring({
              frame: frame - wordStart,
              fps,
              config: { damping: 8, stiffness: 200 },
            })
          : 0;

        const wordScale = isCurrent
          ? interpolate(popProg, [0, 1], [1.3, 1.05])
          : isActive
            ? 1
            : 0.8;

        return (
          <span
            key={i}
            style={{
              fontFamily: "Montserrat, sans-serif",
              fontSize: height * 0.038,
              fontWeight: 900,
              color: isCurrent ? highlightColor : isActive ? "rgba(255,255,255,0.55)" : "transparent",
              transform: `scale(${popProg > 0 ? wordScale : 0.8})`,
              opacity: isActive ? popProg : 0,
              textShadow: isCurrent
                ? "0 2px 20px rgba(0,0,0,0.95), 0 0 40px rgba(0,0,0,0.6)"
                : "0 1px 10px rgba(0,0,0,0.8)",
              transition: "color 0.1s",
              display: "inline-block",
              lineHeight: 1.3,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
