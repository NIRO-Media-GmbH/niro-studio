// ============================================================
// AmbientBackground — Persistent background layer
// Subtle floating particles + vignette to fill empty space
// ============================================================

import React from "react";
import { W, H } from "../constants";

export const AmbientBackground: React.FC = () => {
  return (
    <g>
      {/* Vignette — darker edges */}
      <defs>
        <radialGradient id="bgVignette" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="transparent" stopOpacity="0" />
          <stop offset="70%" stopColor="transparent" stopOpacity="0" />
          <stop offset="100%" stopColor="#000000" stopOpacity="0.4" />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#bgVignette)" />
    </g>
  );
};
