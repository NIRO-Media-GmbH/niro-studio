import React from "react";
import { AbsoluteFill, Img, useCurrentFrame, useVideoConfig, interpolate, staticFile } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface LogoRevealProps {
  mode?: "scale" | "fade" | "mask" | "slide";
  delay?: number;
  size?: number;
  springDamping?: number;
  logoOverride?: string;
  showCompanyName?: boolean;
  companyNameBelow?: string;
}

export const LogoReveal: React.FC<LogoRevealProps> = ({
  mode = "scale",
  delay = 0,
  size = 0.25,
  springDamping = 12,
  logoOverride,
  showCompanyName = true,
  companyNameBelow,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, {
    delay,
    damping: springDamping,
  });

  const logoPath = logoOverride ?? ci.logo.path;
  const logoSize = Math.min(width, height) * size;
  const displayName = companyNameBelow ?? ci.name;

  let logoStyle: React.CSSProperties = {};
  let containerStyle: React.CSSProperties = {};

  switch (mode) {
    case "scale":
      logoStyle = {
        transform: `scale(${interpolate(progress, [0, 1], [0, 1])})`,
        opacity: interpolate(progress, [0, 0.2], [0, 1], {
          extrapolateRight: "clamp",
        }),
      };
      break;
    case "fade":
      logoStyle = { opacity: progress };
      break;
    case "mask": {
      const radius = interpolate(progress, [0, 1], [0, 150]);
      containerStyle = {
        clipPath: `circle(${radius}% at 50% 50%)`,
      };
      break;
    }
    case "slide":
      logoStyle = {
        transform: `translateY(${interpolate(progress, [0, 1], [100, 0])}px)`,
        opacity: progress,
      };
      break;
  }

  // Text entrance (delayed after logo)
  const textProgress = motionSpring(frame, fps, {
    delay: delay + 15,
    damping: 16,
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        ...containerStyle,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: height * 0.02,
        }}
      >
        {/* Logo */}
        {logoPath ? (
          <div style={{ ...logoStyle, width: logoSize, height: logoSize }}>
            <Img
              src={staticFile(logoPath)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
              }}
            />
          </div>
        ) : (
          // Placeholder logo (circle with initial)
          <div
            style={{
              ...logoStyle,
              width: logoSize,
              height: logoSize,
              borderRadius: "50%",
              backgroundColor: ci.colors.primary,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              fontSize: logoSize * 0.4,
              fontWeight: "800",
              color: ci.colors.background,
              fontFamily: ci.fonts.heading.family,
            }}
          >
            {ci.name.charAt(0).toUpperCase()}
          </div>
        )}

        {/* Company name */}
        {showCompanyName && (
          <div
            style={{
              opacity: textProgress,
              transform: `translateY(${interpolate(textProgress, [0, 1], [20, 0])}px)`,
              fontFamily: ci.fonts.heading.family,
              fontSize: height * 0.04,
              fontWeight: ci.fonts.heading.weight,
              color: ci.colors.text,
              letterSpacing: 2,
            }}
          >
            {displayName}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
