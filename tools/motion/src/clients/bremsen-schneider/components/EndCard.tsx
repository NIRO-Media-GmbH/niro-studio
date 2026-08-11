// ============================================================
// Bremsen Schneider — EndCard
// Semi-transparent blue background, logo, CTA button
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Img,
  staticFile,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import {
  BLUE,
  DARK_BLUE,
  YELLOW,
  WHITE,
  SMOOTH_SPRING,
  PUNCH_SPRING,
  GENTLE_SPRING,
} from "./constants";

const { fontFamily } = loadFont();

interface EndCardProps {
  ctaText?: string;
  website?: string;
  phone?: string;
  showLogo?: boolean;
}

export const EndCard: React.FC<EndCardProps> = ({
  ctaText = "Jetzt bewerben!",
  website = "bremsen-schneider.de",
  phone,
  showLogo = true,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();

  // Background fade in
  const bgProg = spring({ frame, fps, config: GENTLE_SPRING });
  const bgOpacity = interpolate(bgProg, [0, 1], [0, 0.88]);

  // Logo
  const logoProg = spring({ frame: frame - 5, fps, config: SMOOTH_SPRING });
  const logoScale = interpolate(logoProg, [0, 1], [0.7, 1]);
  const logoOpacity = interpolate(logoProg, [0, 1], [0, 1]);

  // CTA button
  const ctaProg = spring({ frame: frame - 14, fps, config: PUNCH_SPRING });
  const ctaScale = interpolate(ctaProg, [0, 1], [0.8, 1]);
  const ctaOpacity = interpolate(ctaProg, [0, 1], [0, 1]);

  // Pill background (scaleX reveal)
  const pillProg = spring({ frame: frame - 16, fps, config: SMOOTH_SPRING });

  // Contact info
  const contactProg = spring({ frame: frame - 22, fps, config: GENTLE_SPRING });
  const contactOpacity = interpolate(contactProg, [0, 1], [0, 1]);
  const contactSlide = interpolate(contactProg, [0, 1], [20, 0]);

  const logoSize = Math.round(width * 0.38);
  const ctaFontSize = Math.round(height * 0.028);
  const contactFontSize = Math.round(height * 0.02);

  return (
    <AbsoluteFill>
      {/* Semi-transparent blue background */}
      <AbsoluteFill
        style={{
          backgroundColor: BLUE,
          opacity: bgOpacity,
        }}
      />

      {/* Subtle grid overlay */}
      <AbsoluteFill
        style={{
          opacity: bgOpacity * 0.3,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
          `,
          backgroundSize: `${Math.round(width * 0.074)}px ${Math.round(width * 0.074)}px`,
        }}
      />

      {/* Content container */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(height * 0.03),
        }}
      >
        {/* Logo */}
        {showLogo && (
          <div
            style={{
              opacity: logoOpacity,
              transform: `scale(${logoScale})`,
            }}
          >
            <Img
              src={staticFile("clients/bremsen-schneider/logo.png")}
              style={{
                width: logoSize,
                height: "auto",
                filter: "drop-shadow(0 4px 30px rgba(0,0,0,0.3))",
              }}
            />
          </div>
        )}

        {/* CTA Button */}
        <div
          style={{
            position: "relative",
            opacity: ctaOpacity,
            transform: `scale(${ctaScale})`,
            marginTop: Math.round(height * 0.02),
          }}
        >
          {/* Pill background */}
          <div
            style={{
              position: "absolute",
              inset: `${-Math.round(ctaFontSize * 0.5)}px ${-Math.round(ctaFontSize * 1.2)}px`,
              backgroundColor: YELLOW,
              borderRadius: 999,
              transform: `scaleX(${pillProg})`,
              boxShadow: `0 4px 40px ${YELLOW}44, 0 0 80px ${YELLOW}22`,
            }}
          />
          <div
            style={{
              position: "relative",
              fontFamily,
              fontSize: ctaFontSize,
              fontWeight: 900,
              color: DARK_BLUE,
              letterSpacing: Math.round(ctaFontSize * 0.04),
              textTransform: "uppercase",
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {ctaText}
          </div>
        </div>

        {/* Contact info */}
        <div
          style={{
            opacity: contactOpacity,
            transform: `translateY(${contactSlide}px)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: Math.round(height * 0.008),
            marginTop: Math.round(height * 0.015),
          }}
        >
          {website && (
            <div
              style={{
                fontFamily,
                fontSize: contactFontSize,
                fontWeight: 600,
                color: WHITE,
                letterSpacing: Math.round(contactFontSize * 0.08),
              }}
            >
              {website}
            </div>
          )}
          {phone && (
            <div
              style={{
                fontFamily,
                fontSize: Math.round(contactFontSize * 0.9),
                fontWeight: 400,
                color: `${WHITE}BB`,
                letterSpacing: Math.round(contactFontSize * 0.06),
              }}
            >
              {phone}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
