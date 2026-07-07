// ============================================================
// Template: Product Showcase
// Product name → Tagline → Feature list → CTA
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider, defaultCI } from "../core/ci-provider";
import { productShowcaseSchema } from "../core/schemas";
import { GradientBackground } from "../components/backgrounds/GradientBackground";
import { ParticleField } from "../components/backgrounds/ParticleField";
import { ScaleText } from "../components/text/ScaleText";
import { FadeInText } from "../components/text/FadeInText";
import { StaggerChildren } from "../components/layout/StaggerChildren";
import { FadeIn } from "../components/layout/FadeIn";
import type { CorporateIdentity } from "../core/types";

export type ProductShowcaseProps = z.infer<typeof productShowcaseSchema> & {
  ci?: CorporateIdentity;
};

export const ProductShowcase: React.FC<ProductShowcaseProps> = ({
  productName = "Product Name",
  tagline = "The best solution for your needs",
  features = ["Fast & Reliable", "Easy to Use", "Beautifully Designed"],
  primaryColor,
  accentColor,
  backgroundType = "gradient",
  transparent = false,
  ci,
}) => {
  const { durationInFrames, fps, height, width } = useVideoConfig();

  const usedCI = ci ?? {
    ...defaultCI,
    colors: {
      ...defaultCI.colors,
      ...(primaryColor ? { primary: primaryColor } : {}),
      ...(accentColor ? { accent: accentColor } : {}),
    },
  };

  const scene1End = Math.floor(durationInFrames * 0.25);
  const scene2End = Math.floor(durationInFrames * 0.45);
  const scene3End = Math.floor(durationInFrames * 0.85);

  const renderBackground = () => {
    if (transparent) return null;
    switch (backgroundType) {
      case "gradient":
        return <GradientBackground colors={[usedCI.colors.secondary, "#0a0a1a"]} />;
      case "solid":
        return <AbsoluteFill style={{ backgroundColor: usedCI.colors.secondary }} />;
      case "particles":
        return (
          <>
            <AbsoluteFill style={{ backgroundColor: usedCI.colors.secondary }} />
            <ParticleField color={usedCI.colors.accent} count={30} opacity={0.2} />
          </>
        );
      default:
        return <GradientBackground colors={[usedCI.colors.secondary, "#0a0a1a"]} />;
    }
  };

  return (
    <CIProvider ci={usedCI}>
      <AbsoluteFill>
        {renderBackground()}

        {/* Scene 1: Product Name */}
        <Sequence from={0} durationInFrames={scene1End}>
          <ScaleText
            text={productName}
            fontSizeRatio={0.08}
            color="#FFFFFF"
            fontWeight="900"
            fromScale={0.5}
            toScale={1}
          />
        </Sequence>

        {/* Scene 2: Tagline */}
        <Sequence from={scene1End} durationInFrames={scene2End - scene1End}>
          <FadeInText
            text={tagline}
            mode="word"
            fontSizeRatio={0.04}
            color="rgba(255,255,255,0.9)"
            fontWeight="400"
            stagger={{ delayPerItem: 3, initialDelay: 0 }}
          />
        </Sequence>

        {/* Scene 3: Features */}
        <Sequence from={scene2End} durationInFrames={scene3End - scene2End}>
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              padding: "8%",
            }}
          >
            <StaggerChildren
              delayPerItem={8}
              initialDelay={5}
              direction="up"
              distance={30}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: height * 0.04,
                alignItems: "center",
              }}
            >
              {features.map((feature, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: height * 0.02,
                  }}
                >
                  <div
                    style={{
                      width: height * 0.015,
                      height: height * 0.015,
                      borderRadius: "50%",
                      backgroundColor: usedCI.colors.accent,
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontFamily: usedCI.fonts.body.family,
                      fontSize: height * 0.035,
                      fontWeight: "500",
                      color: "#FFFFFF",
                    }}
                  >
                    {feature}
                  </span>
                </div>
              ))}
            </StaggerChildren>
          </AbsoluteFill>
        </Sequence>

        {/* Scene 4: Logo */}
        <Sequence
          from={scene3End}
          durationInFrames={durationInFrames - scene3End}
        >
          <FadeIn delay={0}>
            <AbsoluteFill
              style={{ justifyContent: "center", alignItems: "center" }}
            >
              <div
                style={{
                  fontFamily: usedCI.fonts.heading.family,
                  fontSize: height * 0.05,
                  fontWeight: "800",
                  color: usedCI.colors.accent,
                  letterSpacing: 3,
                }}
              >
                {productName}
              </div>
            </AbsoluteFill>
          </FadeIn>
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
