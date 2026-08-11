// ============================================================
// WTN — Chip Icons
// Inline stroke icons for ChipRow badges + stat cards. 24×24
// viewBox, stroke-based, color/size via props. Set themed for a
// precision-tooling / metal-forming recruiting context.
// ============================================================

import React from "react";

export type ChipIconName =
  | "zahnrad" // gear / mechanics
  | "werkzeug" // wrench / hands-on
  | "praezision" // crosshair / precision
  | "drucker3d" // 3D metal printing
  | "funke" // spark / PECM, energy
  | "technik" // chip / high-tech
  | "haende" // support / together
  | "team" // team / family
  | "check" // clear / structured
  | "buch" // learning / Ausbildung
  | "rakete" // growth / career
  | "herz" // passion
  | "blitz" // energy / fast
  | "schild" // safety / security
  | "uhr" // time / flexibility
  | "diamant"; // quality / value

interface ChipIconProps {
  name: ChipIconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export const ChipIcon: React.FC<ChipIconProps> = ({
  name,
  size = 24,
  color = "#FFFFFF",
  strokeWidth = 2,
}) => {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (name) {
    case "zahnrad":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3.2" />
          <path d="M12 2.5v2.4M12 19.1v2.4M21.5 12h-2.4M4.9 12H2.5M18.7 5.3l-1.7 1.7M7 17l-1.7 1.7M18.7 18.7 17 17M7 7 5.3 5.3" />
        </svg>
      );
    case "werkzeug":
      return (
        <svg {...common}>
          <path d="M14.5 6.2a3.6 3.6 0 0 0 4.7 4.7l-2.1-2.1 1.4-1.4 2.1 2.1a3.6 3.6 0 0 1-4.9 4.9L7.4 20.7a2 2 0 0 1-2.8-2.8l6.3-6.3a3.6 3.6 0 0 1 3.6-5.4Z" />
        </svg>
      );
    case "praezision":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <circle cx="12" cy="12" r="3.4" />
          <path d="M12 1.5v3M12 19.5v3M22.5 12h-3M4.5 12h-3" />
        </svg>
      );
    case "drucker3d":
      return (
        <svg {...common}>
          <path d="M4 8.5 12 4l8 4.5v7L12 20l-8-4.5v-7Z" />
          <path d="M12 20v-7.5M4 8.5 12 12.5l8-4" />
        </svg>
      );
    case "funke":
      return (
        <svg {...common}>
          <path d="M13 2 4.5 13.2h6.2L10 22l8.6-11.4h-6.3L13 2Z" />
        </svg>
      );
    case "technik":
      return (
        <svg {...common}>
          <rect x="7" y="7" width="10" height="10" rx="1.6" />
          <path d="M9.5 2.5v3M14.5 2.5v3M9.5 18.5v3M14.5 18.5v3M2.5 9.5h3M2.5 14.5h3M18.5 9.5h3M18.5 14.5h3" />
        </svg>
      );
    case "haende":
      return (
        <svg {...common}>
          <path d="M3 12.5 7 9c.8-.7 2-.6 2.7.2L12 12" />
          <path d="M21 12.5 17 9c-.8-.7-2-.6-2.7.2L12 12l1.6 1.7c.7.8 1.9.9 2.7.2" />
          <path d="M4.5 13.5 9 18c.9.9 2.3 1 3.3.2l4.2-3.3" />
        </svg>
      );
    case "team":
      return (
        <svg {...common}>
          <circle cx="8.5" cy="8.5" r="3" />
          <path d="M2.5 19c.6-3 3-4.5 6-4.5s5.4 1.5 6 4.5" />
          <circle cx="16.5" cy="9.5" r="2.4" />
          <path d="M16.8 14.6c2.4.2 4.2 1.5 4.7 4" />
        </svg>
      );
    case "check":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="m8 12.5 2.7 2.7L16.5 9" />
        </svg>
      );
    case "buch":
      return (
        <svg {...common}>
          <path d="M12 6.5C10.5 5 8.5 4.5 6 4.5c-1 0-2 .1-3 .4v14c1-.3 2-.4 3-.4 2.5 0 4.5.5 6 2 1.5-1.5 3.5-2 6-2 1 0 2 .1 3 .4v-14c-1-.3-2-.4-3-.4-2.5 0-4.5.5-6 2Z" />
          <path d="M12 6.5v14" />
        </svg>
      );
    case "rakete":
      return (
        <svg {...common}>
          <path d="M12 3c3 1 5 4 5 8l-2.2 2.2h-5.6L7 11c0-4 2-7 5-8Z" />
          <circle cx="12" cy="9.5" r="1.4" />
          <path d="M9.2 15.5c-1.6.7-2.4 2.3-2.4 4.5 2.2 0 3.8-.8 4.5-2.4M14.8 15.5c1.6.7 2.4 2.3 2.4 4.5-2.2 0-3.8-.8-4.5-2.4" />
        </svg>
      );
    case "herz":
      return (
        <svg {...common}>
          <path d="M12 20.5C7 16.5 3.5 13.2 3.5 9.4 3.5 6.9 5.4 5 7.8 5c1.6 0 3.1.8 4.2 2.3C13.1 5.8 14.6 5 16.2 5c2.4 0 4.3 1.9 4.3 4.4 0 3.8-3.5 7.1-8.5 11.1Z" />
        </svg>
      );
    case "blitz":
      return (
        <svg {...common}>
          <path d="M13 2 5 13h5l-1 9 8-11h-5l1-9Z" />
        </svg>
      );
    case "schild":
      return (
        <svg {...common}>
          <path d="M12 3.5 19 6v5.5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6l7-2.5Z" />
          <path d="m9 11.5 2 2 4-4" />
        </svg>
      );
    case "uhr":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3.5 2" />
        </svg>
      );
    case "diamant":
      return (
        <svg {...common}>
          <path d="M6 3.5h12l3.5 5-9.5 12L2.5 8.5 6 3.5Z" />
          <path d="M2.5 8.5h19M8 3.5 6 8.5l6 12 6-12-2-5" />
        </svg>
      );
  }
};
