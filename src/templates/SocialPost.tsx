// ============================================================
// Template: Social Post
// Multi-scene social media animation
// Scenes: Headline → Body → CTA → Logo Outro
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider, defaultCI } from "../core/ci-provider";
import { socialPostSchema } from "../core/schemas";
import { GradientBackground } from "../components/backgrounds/GradientBackground";
import { ParticleField } from "../components/backgrounds/ParticleField";
import { WaveBackground } from "../components/backgrounds/WaveBackground";
import { FadeInText } from "../components/text/FadeInText";
import { SlideInText } from "../components/text/SlideInText";
import { ScaleText } from "../components/text/ScaleText";
import { LogoReveal } from "../components/effects/LogoReveal";
import { FadeIn } from "../components/layout/FadeIn";
import type { CorporateIdentity } from "../core/types";

export type SocialPostProps = z.infer<typeof socialPostSchema> & {
  ci?: CorporateIdentity;
};

export const SocialPost: React.FC<SocialPostProps> = ({
  headline = "Your Headline Here",
  bodyText = "Supporting text with key details for your audience.",
  ctaText = "Learn More",
  backgroundType = "gradient",
  primaryColor,
  secondaryColor,
  accentColor,
  transparent = false,
  ci,
}) => {
  const { durationInFrames, fps, height } = useVideoConfig();

  // Scene timing proportions
  const introEnd = Math.floor(durationInFrames * 0.3);
  const bodyEnd = Math.floor(durationInFrames * 0.6);
  const ctaEnd = Math.floor(durationInFrames * 0.8);

  const usedCI = ci ?? {
    ...defaultCI,
    colors: {
      ...defaultCI.colors,
      ...(primaryColor ? { primary: primaryColor } : {}),
      ...(secondaryColor ? { secondary: secondaryColor } : {}),
      ...(accentColor ? { accent: accentColor } : {}),
    },
  };

  const renderBackground = () => {
    if (transparent) return null;
    switch (backgroundType) {
      case "gradient":
        return <GradientBackground colors={[usedCI.colors.secondary, usedCI.colors.primary]} />;
      case "solid":
        return <AbsoluteFill style={{ backgroundColor: usedCI.colors.background }} />;
      case "particles":
        return (
          <>
            <AbsoluteFill style={{ backgroundColor: usedCI.colors.secondary }} />
            <ParticleField color={usedCI.colors.accent} count={40} opacity={0.3} />
          </>
        );
      case "wave":
        return <WaveBackground colors={[usedCI.colors.primary, usedCI.colors.secondary, usedCI.colors.accent]} />;
      default:
        return <GradientBackground />;
    }
  };

  // Text color for readability on dark backgrounds
  const textOnBg = backgroundType === "solid" ? usedCI.colors.text : "#FFFFFF";

  return (
    <CIProvider ci={usedCI}>
      <AbsoluteFill>
        {/* Background */}
        {renderBackground()}

        {/* Scene 1: Headline */}
        <Sequence from={0} durationInFrames={introEnd}>
          <FadeInText
            text={headline}
            mode="word"
            fontSizeRatio={0.06}
            color={textOnBg}
            fontWeight="800"
            stagger={{ delayPerItem: 3, initialDelay: 5 }}
          />
        </Sequence>

        {/* Scene 2: Body Text */}
        <Sequence from={introEnd} durationInFrames={bodyEnd - introEnd}>
          <SlideInText
            text={bodyText}
            direction="up"
            fontSizeRatio={0.035}
            color={textOnBg}
            fontWeight="400"
          />
        </Sequence>

        {/* Scene 3: CTA */}
        <Sequence from={bodyEnd} durationInFrames={ctaEnd - bodyEnd}>
          <AbsoluteFill
            style={{ justifyContent: "center", alignItems: "center" }}
          >
            <FadeIn delay={5} direction="up">
              <div
                style={{
                  backgroundColor: usedCI.colors.accent,
                  paddingLeft: height * 0.04,
                  paddingRight: height * 0.04,
                  paddingTop: height * 0.015,
                  paddingBottom: height * 0.015,
                  borderRadius: usedCI.style.borderRadius,
                }}
              >
                <ScaleText
                  text={ctaText}
                  fontSizeRatio={0.04}
                  color="#FFFFFF"
                  fontWeight="700"
                  fromScale={0.8}
                  toScale={1}
                />
              </div>
            </FadeIn>
          </AbsoluteFill>
        </Sequence>

        {/* Scene 4: Logo Outro */}
        <Sequence from={ctaEnd} durationInFrames={durationInFrames - ctaEnd}>
          <LogoReveal mode="scale" size={0.2} />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
