// ============================================================
// WTN — Logo (official WTN-Logo.svg from public/wtn/)
// variant "color" = original (blue signet + gray wordmark)
// variant "white" = all-white (for dark navy cards, like the posts)
// Native aspect 2.5:1 (viewBox 10000×4000).
// ============================================================

import React from "react";
import { Img, staticFile } from "remotion";

interface LogoProps {
  /** Rendered width in px (height auto). Default 520. */
  width?: number;
  /** "white" recolors the whole logo to solid white via filter. */
  variant?: "color" | "white";
  style?: React.CSSProperties;
}

export const Logo: React.FC<LogoProps> = ({
  width = 520,
  variant = "color",
  style,
}) => {
  return (
    <Img
      src={staticFile("wtn/logo.svg")}
      style={{
        width,
        height: "auto",
        display: "block",
        filter: variant === "white" ? "brightness(0) invert(1)" : undefined,
        ...style,
      }}
    />
  );
};
