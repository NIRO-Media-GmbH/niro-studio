// ============================================================
// Seniorenstiftung — Chip Icons
// Small inline stroke icons for ChipRow badges. 24×24 viewBox,
// stroke-based, color/size via props (same pattern as other clients).
// ============================================================

import React from "react";

export type ChipIconName =
  | "herz"
  | "haende"
  | "team"
  | "sprechblase"
  | "check"
  | "buch"
  | "uhr"
  | "kalender"
  | "glanz"
  | "puls"
  | "stufen"
  | "schild"
  | "tropfen"
  | "teller";

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
    case "herz":
      return (
        <svg {...common}>
          <path d="M12 20.5C7 16.5 3.5 13.2 3.5 9.4 3.5 6.9 5.4 5 7.8 5c1.6 0 3.1.8 4.2 2.3C13.1 5.8 14.6 5 16.2 5c2.4 0 4.3 1.9 4.3 4.4 0 3.8-3.5 7.1-8.5 11.1Z" />
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
    case "sprechblase":
      return (
        <svg {...common}>
          <path d="M21 11.5c0 4-4 7-9 7-1 0-2-.1-2.9-.4L4 20l1.2-3.6C3.8 15.1 3 13.4 3 11.5c0-4 4-7 9-7s9 3 9 7Z" />
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
    case "uhr":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3.5 2" />
        </svg>
      );
    case "kalender":
      return (
        <svg {...common}>
          <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" />
          <path d="M3.5 9.5h17M8 3v3.5M16 3v3.5" />
        </svg>
      );
    case "glanz":
      return (
        <svg {...common}>
          <path d="M12 3.5 13.8 9l5.7 1.8-5.7 1.8L12 18.3l-1.8-5.7L4.5 10.8 10.2 9 12 3.5Z" />
          <path d="M19 16.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2Z" />
        </svg>
      );
    case "puls":
      return (
        <svg {...common}>
          <path d="M3 12h3.5l2-5 3.5 10 2.5-6.5 1.5 1.5H21" />
        </svg>
      );
    case "stufen":
      return (
        <svg {...common}>
          <path d="M4 19h4v-4h4v-4h4V7h4" />
        </svg>
      );
    case "schild":
      return (
        <svg {...common}>
          <path d="M12 3.5 19 6v5.5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6l7-2.5Z" />
        </svg>
      );
    case "tropfen":
      return (
        <svg {...common}>
          <path d="M12 3.5C15.5 8 18 11 18 14a6 6 0 0 1-12 0c0-3 2.5-6 6-10.5Z" />
        </svg>
      );
    case "teller":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="4.5" />
        </svg>
      );
  }
};
