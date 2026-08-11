// ============================================================
// Client: NIRO Demo — Project: Launch Ad
// A branded social media launch advertisement
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { zTextarea } from "@remotion/zod-types";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import brandJson from "../../brand.json";

const ci = loadBrand("niro-demo", brandJson as any);
import { projectPropsSchema } from "../../../../core/schemas";
import { GradientBackground } from "../../../../components/backgrounds/GradientBackground";
import { ParticleField } from "../../../../components/backgrounds/ParticleField";
import { FadeInText } from "../../../../components/text/FadeInText";
import { SlideInText } from "../../../../components/text/SlideInText";
import { ScaleText } from "../../../../components/text/ScaleText";
import { LogoReveal } from "../../../../components/effects/LogoReveal";
import { AnimatedCircle } from "../../../../components/shapes/AnimatedCircle";
import { FadeIn } from "../../../../components/layout/FadeIn";

export const launchAdSchema = projectPropsSchema.extend({
  headline: zTextarea(),
  subheadline: zTextarea(),
  ctaText: z.string(),
});

type LaunchAdProps = z.infer<typeof launchAdSchema>;

export const LaunchAd: React.FC<LaunchAdProps> = ({
  headline = "Motion Graphics\nMade Simple",
  subheadline = "Create stunning animations with code",
  ctaText = "Get Started Today",
  transparent = false,
}) => {
  const { durationInFrames, fps, height, width } = useVideoConfig();

  const introEnd = Math.floor(durationInFrames * 0.3);
  const bodyEnd = Math.floor(durationInFrames * 0.55);
  const ctaEnd = Math.floor(durationInFrames * 0.75);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {/* Background */}
        {!transparent && (
          <>
            <GradientBackground
              colors={[ci.colors.secondary, "#0d0d24"]}
              animate={true}
              rotationSpeed={0.3}
            />
            <ParticleField
              count={35}
              color={ci.colors.accent}
              opacity={0.15}
              speed={0.5}
            />
          </>
        )}

        {/* Decorative shapes */}
        <AnimatedCircle
          radius={100}
          fill="transparent"
          stroke={ci.colors.primary}
          strokeWidth={2}
          animateIn="draw"
          delay={0}
          x={80}
          y={15}
        />
        <AnimatedCircle
          radius={50}
          fill={ci.colors.accent}
          stroke="transparent"
          animateIn="scale"
          delay={10}
          x={15}
          y={80}
        />

        {/* Scene 1: Headline */}
        <Sequence from={0} durationInFrames={introEnd}>
          <FadeInText
            text={headline}
            mode="word"
            fontSizeRatio={0.055}
            color="#FFFFFF"
            fontWeight="800"
            stagger={{ delayPerItem: 3, initialDelay: 10 }}
          />
        </Sequence>

        {/* Scene 2: Subheadline */}
        <Sequence from={introEnd} durationInFrames={bodyEnd - introEnd}>
          <SlideInText
            text={subheadline}
            direction="up"
            fontSizeRatio={0.032}
            color="rgba(255,255,255,0.8)"
            fontWeight="400"
            distance={60}
          />
        </Sequence>

        {/* Scene 3: CTA Button */}
        <Sequence from={bodyEnd} durationInFrames={ctaEnd - bodyEnd}>
          <AbsoluteFill
            style={{ justifyContent: "center", alignItems: "center" }}
          >
            <FadeIn delay={5} direction="up" distance={20}>
              <div
                style={{
                  backgroundColor: ci.colors.primary,
                  paddingLeft: height * 0.04,
                  paddingRight: height * 0.04,
                  paddingTop: height * 0.018,
                  paddingBottom: height * 0.018,
                  borderRadius: ci.style.borderRadius,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    fontFamily: ci.fonts.heading.family,
                    fontSize: height * 0.035,
                    fontWeight: "700",
                    color: "#FFFFFF",
                  }}
                >
                  {ctaText}
                </span>
              </div>
            </FadeIn>
          </AbsoluteFill>
        </Sequence>

        {/* Scene 4: Logo Outro */}
        <Sequence
          from={ctaEnd}
          durationInFrames={durationInFrames - ctaEnd}
        >
          <LogoReveal
            mode="scale"
            size={0.2}
            springDamping={10}
            companyNameBelow="NIRO"
          />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
