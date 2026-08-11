// ============================================================
// Template: Minimal Typography
// Clean, minimal kinetic typography animation
// Each line animates in sequence with configurable style
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider, defaultCI } from "../core/ci-provider";
import { minimalTypographySchema } from "../core/schemas";
import { FadeInText } from "../components/text/FadeInText";
import { SlideInText } from "../components/text/SlideInText";
import { ScaleText } from "../components/text/ScaleText";
import { TypewriterText } from "../components/text/TypewriterText";
import type { CorporateIdentity } from "../core/types";

export type MinimalTypographyProps = z.infer<
  typeof minimalTypographySchema
> & {
  ci?: CorporateIdentity;
};

export const MinimalTypography: React.FC<MinimalTypographyProps> = ({
  lines = ["Think", "Create", "Inspire"],
  fontWeight = "900",
  textColor,
  backgroundColor,
  animationStyle = "fade",
  transparent = false,
  ci,
}) => {
  const { durationInFrames, height } = useVideoConfig();

  const usedCI = ci ?? defaultCI;
  const bgColor = backgroundColor ?? usedCI.colors.secondary;
  const fgColor = textColor ?? "#FFFFFF";

  const lineCount = lines.length;
  const framesPerLine = Math.floor(durationInFrames / lineCount);

  const renderLine = (text: string, style: string) => {
    switch (style) {
      case "slide":
        return (
          <SlideInText
            text={text}
            direction="left"
            fontSizeRatio={0.09}
            color={fgColor}
            fontWeight={fontWeight}
            distance={300}
          />
        );
      case "scale":
        return (
          <ScaleText
            text={text}
            fontSizeRatio={0.09}
            color={fgColor}
            fontWeight={fontWeight}
            fromScale={0}
            toScale={1}
          />
        );
      case "typewriter":
        return (
          <TypewriterText
            text={text}
            fontSizeRatio={0.09}
            color={fgColor}
            fontWeight={fontWeight}
            charsPerSecond={20}
            cursorColor={usedCI.colors.accent}
          />
        );
      case "fade":
      default:
        return (
          <FadeInText
            text={text}
            mode="character"
            fontSizeRatio={0.09}
            color={fgColor}
            fontWeight={fontWeight}
            stagger={{ delayPerItem: 2, initialDelay: 0 }}
          />
        );
    }
  };

  return (
    <CIProvider ci={usedCI}>
      <AbsoluteFill>
        {/* Background */}
        {!transparent && (
          <AbsoluteFill style={{ backgroundColor: bgColor }} />
        )}

        {/* Lines */}
        {lines.map((line, i) => (
          <Sequence
            key={i}
            from={i * framesPerLine}
            durationInFrames={framesPerLine}
          >
            {renderLine(line, animationStyle)}
          </Sequence>
        ))}
      </AbsoluteFill>
    </CIProvider>
  );
};
