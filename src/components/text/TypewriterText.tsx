import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";

interface TypewriterTextProps {
  text: string;
  charsPerSecond?: number;
  cursorColor?: string;
  cursorWidth?: number;
  showCursorAfterComplete?: boolean;
  fontSizeRatio?: number;
  color?: string;
  fontWeight?: string;
}

export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text = "Type your message here...",
  charsPerSecond = 15,
  cursorColor,
  cursorWidth = 3,
  showCursorAfterComplete = false,
  fontSizeRatio = 0.045,
  color,
  fontWeight = "600",
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ci = useCI();

  const framesPerChar = fps / charsPerSecond;
  const totalCharsFrames = text.length * framesPerChar;

  const charsToShow = Math.floor(
    interpolate(frame, [0, totalCharsFrames], [0, text.length], {
      extrapolateRight: "clamp",
    })
  );

  const isComplete = charsToShow >= text.length;
  const showCursor = !isComplete || showCursorAfterComplete;
  const cursorOpacity = showCursor ? (Math.sin(frame * 0.3) > 0 ? 1 : 0) : 0;

  const fontSize = height * fontSizeRatio;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "5%",
      }}
    >
      <div
        style={{
          fontFamily: ci.fonts.body.family,
          fontSize,
          fontWeight,
          color: color ?? ci.colors.text,
          display: "flex",
          alignItems: "center",
        }}
      >
        <span>{text.slice(0, charsToShow)}</span>
        <span
          style={{
            display: "inline-block",
            width: cursorWidth,
            height: fontSize * 1.1,
            backgroundColor: cursorColor ?? ci.colors.primary,
            marginLeft: 2,
            opacity: cursorOpacity,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
