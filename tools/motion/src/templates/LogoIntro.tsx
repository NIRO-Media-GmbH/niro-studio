// ============================================================
// Template: Logo Intro
// Clean logo reveal with decorative elements
// Phases: Shapes → Logo Reveal → Company Name → Hold
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider, defaultCI } from "../core/ci-provider";
import { logoIntroSchema } from "../core/schemas";
import { GradientBackground } from "../components/backgrounds/GradientBackground";
import { ParticleField } from "../components/backgrounds/ParticleField";
import { AnimatedCircle } from "../components/shapes/AnimatedCircle";
import { LogoReveal } from "../components/effects/LogoReveal";
import type { CorporateIdentity } from "../core/types";

export type LogoIntroProps = z.infer<typeof logoIntroSchema> & {
  ci?: CorporateIdentity;
};

export const LogoIntro: React.FC<LogoIntroProps> = ({
  companyName = "NIRO",
  tagline,
  revealMode = "scale",
  showParticles = true,
  primaryColor,
  secondaryColor,
  transparent = false,
  ci,
}) => {
  const { durationInFrames, fps } = useVideoConfig();

  const usedCI = ci ?? {
    ...defaultCI,
    name: companyName,
    colors: {
      ...defaultCI.colors,
      ...(primaryColor ? { primary: primaryColor } : {}),
      ...(secondaryColor ? { secondary: secondaryColor } : {}),
    },
  };

  const shapesEnd = Math.floor(durationInFrames * 0.3);
  const logoEnd = Math.floor(durationInFrames * 0.85);

  return (
    <CIProvider ci={usedCI}>
      <AbsoluteFill>
        {/* Background */}
        {!transparent && (
          <GradientBackground
            colors={[usedCI.colors.secondary, "#0a0a1a"]}
            animate={true}
            rotationSpeed={0.3}
          />
        )}

        {/* Particles */}
        {showParticles && (
          <ParticleField
            count={30}
            color={usedCI.colors.accent}
            opacity={0.2}
            speed={0.5}
          />
        )}

        {/* Decorative shapes */}
        <Sequence from={0} durationInFrames={durationInFrames}>
          <AnimatedCircle
            radius={60}
            fill={usedCI.colors.primary}
            stroke={usedCI.colors.accent}
            strokeWidth={2}
            animateIn="scale"
            delay={5}
            x={25}
            y={30}
          />
          <AnimatedCircle
            radius={30}
            fill={usedCI.colors.accent}
            stroke={usedCI.colors.primary}
            strokeWidth={2}
            animateIn="scale"
            delay={10}
            x={75}
            y={25}
          />
          <AnimatedCircle
            radius={45}
            fill={usedCI.colors.secondary}
            stroke={usedCI.colors.accent}
            strokeWidth={2}
            animateIn="scale"
            delay={15}
            x={80}
            y={70}
          />
        </Sequence>

        {/* Logo reveal */}
        <Sequence from={shapesEnd} durationInFrames={logoEnd - shapesEnd}>
          <LogoReveal
            mode={revealMode}
            size={0.3}
            springDamping={10}
            companyNameBelow={companyName}
          />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
