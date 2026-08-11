// ============================================================
// REM Overlay — Icons
// Flat line icons (24×24 viewBox), stroke = currentColor.
// No internal animation — the container animates them.
// ============================================================

import React from "react";

export type RemIconName =
  | "dach"
  | "farbe"
  | "uhr"
  | "telefon"
  | "dokument"
  | "kalender"
  | "chat"
  | "stern"
  | "geruest"
  | "kran"
  | "check"
  | "cross"
  | "euro"
  | "schild"
  | "daumen"
  | "vergleich"
  | "solar"
  | "glanz";

interface RemIconProps {
  name: RemIconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

const PATHS: Record<RemIconName, React.ReactNode> = {
  dach: (
    <>
      <path d="M2.5 12.5 12 4l9.5 8.5" />
      <path d="M5 10.5V20h14v-9.5" />
    </>
  ),
  farbe: (
    <>
      {/* Farbroller */}
      <rect x="3.5" y="4" width="11" height="5" rx="1" />
      <path d="M14.5 6.5h5v3.5h-8" />
      <path d="M11.5 10v3.5" />
      <rect x="10.3" y="13.5" width="2.4" height="6.5" rx="0.8" />
    </>
  ),
  uhr: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7v5l3.5 2" />
    </>
  ),
  telefon: (
    <path d="M5 4h4l1.5 4.5-2.2 1.6a12 12 0 0 0 5.6 5.6l1.6-2.2L20 15v4a1.5 1.5 0 0 1-1.6 1.5C10.5 20 4 13.5 3.5 5.6A1.5 1.5 0 0 1 5 4z" />
  ),
  dokument: (
    <>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4" />
      <path d="M9 12h6M9 15.5h6" />
    </>
  ),
  kalender: (
    <>
      <rect x="4" y="5.5" width="16" height="14.5" rx="1" />
      <path d="M4 10h16M8.5 3.5v4M15.5 3.5v4" />
    </>
  ),
  chat: (
    <>
      <path d="M4 5h16v11H9l-5 4z" />
      <path d="M8 9h8M8 12h5" />
    </>
  ),
  stern: (
    <path d="m12 3.5 2.5 5.3 5.7.7-4.2 4 1.1 5.7L12 16.4l-5.1 2.8 1.1-5.7-4.2-4 5.7-.7z" />
  ),
  geruest: (
    <>
      <path d="M5.5 3v18M18.5 3v18" />
      <path d="M5.5 7.5h13M5.5 16.5h13" />
      <path d="m5.5 16.5 13-9" />
    </>
  ),
  kran: (
    <>
      {/* Autokran: Fahrzeug + Ausleger + Haken */}
      <path d="M2.5 17.5h11v-3h-11z" />
      <circle cx="5.5" cy="19.5" r="1.6" />
      <circle cx="10.5" cy="19.5" r="1.6" />
      <path d="M6.5 14.5 17 5.5" />
      <path d="M17 5.5v5" />
      <path d="M15.8 10.5h2.4" />
    </>
  ),
  check: <path d="m4.5 12.5 5 5L19.5 7" />,
  cross: <path d="M6 6l12 12M18 6 6 18" />,
  euro: (
    <>
      <path d="M17.5 5.8A7.3 7.3 0 0 0 6.8 12a7.3 7.3 0 0 0 10.7 6.2" />
      <path d="M4 10.3h8.5M4 13.7h7.5" />
    </>
  ),
  schild: (
    <>
      <path d="M12 3 5 5.5v6c0 4.5 3 7.8 7 9.5 4-1.7 7-5 7-9.5v-6z" />
      <path d="m8.8 12 2.3 2.3 4.3-4.3" />
    </>
  ),
  daumen: (
    <>
      <path d="M7 11v9H4v-9z" />
      <path d="M7 19.2c.8.5 1.8.8 3 .8h5.5a2 2 0 0 0 2-1.6l1.3-6A2 2 0 0 0 16.8 10H13l.8-3.8A2 2 0 0 0 11.9 4L7 11" />
    </>
  ),
  vergleich: (
    <>
      <path d="M14 6.5H3.5M6.5 3.5l-3 3 3 3" />
      <path d="M10 17.5h10.5M17.5 14.5l3 3-3 3" />
    </>
  ),
  solar: (
    <>
      {/* PV-Modul, leicht geneigt */}
      <path d="M4 15 7.5 6H20l-3.5 9z" />
      <path d="M9.7 6 6.2 15M14.5 6 11 15M5.7 10.5h12.6" />
      <path d="M11 15v4.5M15 19.5H7" />
    </>
  ),
  glanz: (
    <>
      <path d="M12 4.5 13.6 10l5.4 2-5.4 2L12 19.5 10.4 14 5 12l5.4-2z" />
      <path d="M19 4v3M17.5 5.5h3" />
    </>
  ),
};

export const RemIcon: React.FC<RemIconProps> = ({
  name,
  size = 24,
  color = "currentColor",
  strokeWidth = 2,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {PATHS[name]}
  </svg>
);
