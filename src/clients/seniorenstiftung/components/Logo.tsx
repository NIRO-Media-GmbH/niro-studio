// ============================================================
// Seniorenstiftung — Logo (teal wordmark from public/)
// ============================================================

import React from "react";
import { Img, staticFile } from "remotion";

interface LogoProps {
  /** Rendered width in px (height auto). Default 520. */
  width?: number;
  style?: React.CSSProperties;
}

export const Logo: React.FC<LogoProps> = ({ width = 520, style }) => {
  return (
    <Img
      src={staticFile("seniorenstiftung/logo.svg")}
      style={{ width, height: "auto", display: "block", ...style }}
    />
  );
};
