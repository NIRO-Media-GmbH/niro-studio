// ============================================================
// Template: Text Slideshow
// Cycles through multiple text slides with transitions
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider, defaultCI } from "../core/ci-provider";
import { textSlideshowSchema } from "../core/schemas";
import { GradientBackground } from "../components/backgrounds/GradientBackground";
import { FadeInText } from "../components/text/FadeInText";
import { SlideInText } from "../components/text/SlideInText";
import type { CorporateIdentity } from "../core/types";

export type TextSlideshowProps = z.infer<typeof textSlideshowSchema> & {
  ci?: CorporateIdentity;
};

export const TextSlideshow: React.FC<TextSlideshowProps> = ({
  slides = [
    { text: "First Slide", subtext: "Supporting text" },
    { text: "Second Slide", subtext: "More details" },
    { text: "Third Slide", subtext: "Final thoughts" },
  ],
  transitionType = "fade",
  primaryColor,
  accentColor,
  transparent = false,
  ci,
}) => {
  const { durationInFrames, height } = useVideoConfig();

  const usedCI = ci ?? {
    ...defaultCI,
    colors: {
      ...defaultCI.colors,
      ...(primaryColor ? { primary: primaryColor } : {}),
      ...(accentColor ? { accent: accentColor } : {}),
    },
  };

  const slideCount = slides.length;
  const framesPerSlide = Math.floor(durationInFrames / slideCount);

  return (
    <CIProvider ci={usedCI}>
      <AbsoluteFill>
        {/* Background */}
        {!transparent && (
          <GradientBackground
            colors={[usedCI.colors.secondary, usedCI.colors.primary]}
            animate={true}
            rotationSpeed={0.2}
          />
        )}

        {/* Slides */}
        {slides.map((slide, i) => {
          const slideFrom = i * framesPerSlide;
          const slideDuration = framesPerSlide;

          return (
            <Sequence
              key={i}
              from={slideFrom}
              durationInFrames={slideDuration}
            >
              <AbsoluteFill
                style={{
                  justifyContent: "center",
                  alignItems: "center",
                  flexDirection: "column",
                  gap: height * 0.03,
                }}
              >
                {/* Main text */}
                <FadeInText
                  text={slide.text}
                  mode="word"
                  fontSizeRatio={0.065}
                  color="#FFFFFF"
                  fontWeight="800"
                  stagger={{ delayPerItem: 3, initialDelay: 5 }}
                />

                {/* Subtext */}
                {slide.subtext && (
                  <Sequence from={15}>
                    <SlideInText
                      text={slide.subtext}
                      direction="up"
                      fontSizeRatio={0.03}
                      color="rgba(255,255,255,0.7)"
                      fontWeight="400"
                      distance={30}
                    />
                  </Sequence>
                )}
              </AbsoluteFill>
            </Sequence>
          );
        })}
      </AbsoluteFill>
    </CIProvider>
  );
};
