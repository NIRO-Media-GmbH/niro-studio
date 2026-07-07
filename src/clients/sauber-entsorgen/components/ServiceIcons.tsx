// ============================================================
// Sauber Entsorgen — Service Icons
// Flat line icons (24×24 viewBox), stroke = currentColor.
// No internal animation — the container animates them.
// ============================================================

import React from "react";

export type ServiceIconName =
  // services
  | "haus"
  | "nachlass"
  | "keller"
  | "dachboden"
  | "garage"
  | "firma"
  | "express"
  // objects / situations
  | "wohnung"
  | "gewerbe"
  | "herz"
  | "umzug"
  | "sonne"
  | "schluessel"
  | "frage"
  | "partner"
  | "pin"
  | "karte"
  // status / audience
  | "check"
  | "cross"
  | "person"
  // process / execution
  | "auge"
  | "preis"
  | "kalender"
  | "lkw"
  | "entsorgung"
  | "umwelt"
  | "schild"
  | "schloss"
  | "telefon"
  | "dokument"
  | "glanz";

interface ServiceIconProps {
  name: ServiceIconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

const PATHS: Record<ServiceIconName, React.ReactNode> = {
  // ---- Services ----
  haus: (
    <>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v9h14v-9" />
      <path d="M10 19v-5h4v5" />
    </>
  ),
  nachlass: (
    <>
      <path d="M3 7.5 12 3l9 4.5-9 4.5-9-4.5z" />
      <path d="M3 7.5v9L12 21l9-4.5v-9" />
      <path d="M12 12v9" />
    </>
  ),
  keller: (
    <>
      <path d="M20 5h-4v4h-4v4H8v4H4" />
      <path d="M16 5v4M12 9v4M8 13v4" />
    </>
  ),
  dachboden: (
    <>
      <path d="M3.5 20 12 5l8.5 15z" />
      <circle cx="12" cy="14.5" r="2.2" />
    </>
  ),
  garage: (
    <>
      <path d="M3 20V9l9-4 9 4v11" />
      <path d="M6.5 20v-7h11v7" />
      <path d="M6.5 16h11M6.5 18h11" />
    </>
  ),
  firma: (
    <>
      <path d="M4 21V4h10v17" />
      <path d="M14 21V9h6v12" />
      <path d="M7 8h1.5M11 8h1.5M7 12h1.5M11 12h1.5M7 16h1.5M11 16h1.5" />
      <path d="M17 13h1M17 17h1" />
    </>
  ),
  express: <path d="M13 3 4.5 14H10l-1 7 9.5-11.5H13z" />,

  // ---- Objects / situations ----
  wohnung: (
    <>
      <path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17" />
      <path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2" />
      <path d="M10.5 21v-3h3v3" />
      <path d="M4 21h16" />
    </>
  ),
  gewerbe: (
    <>
      <path d="M3 9l2-4h14l2 4" />
      <path d="M4.5 9v11h15V9" />
      <path d="M8 20v-6h8v6" />
      <path d="M3 9h18" />
    </>
  ),
  herz: (
    <path d="M12 20s-7-4.4-7-9.4A3.5 3.5 0 0 1 12 7a3.5 3.5 0 0 1 7 3.6C19 15.6 12 20 12 20z" />
  ),
  umzug: (
    <>
      <path d="M13 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" />
      <path d="M3 12h10" />
      <path d="M9 8l4 4-4 4" />
    </>
  ),
  sonne: (
    <>
      <path d="M3 18h18" />
      <path d="M7 18a5 5 0 0 1 10 0" />
      <path d="M12 6v2M5.5 9.5l1.4 1.4M18.5 9.5l-1.4 1.4M2.5 13.5h2M19.5 13.5h2" />
    </>
  ),
  schluessel: (
    <>
      <circle cx="8" cy="8" r="4" />
      <path d="M10.8 10.8 20 20M16 16l2-2M18 18l2-2" />
    </>
  ),
  frage: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 0 1 4.6 1.4c0 1.6-2.1 2-2.1 3.1" />
      <path d="M12 17.5h.01" />
    </>
  ),
  partner: (
    <>
      <circle cx="9" cy="8" r="3" />
      <circle cx="16.5" cy="9" r="2.4" />
      <path d="M3.5 19a5.5 5.5 0 0 1 11 0" />
      <path d="M14.5 19a4 4 0 0 1 6 0" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  karte: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </>
  ),

  // ---- Status / audience ----
  check: <path d="M5 13l4 4 10-11" />,
  cross: <path d="M6 6l12 12M18 6 6 18" />,
  person: (
    <>
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </>
  ),

  // ---- Process / execution ----
  auge: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  preis: (
    <>
      <path d="M20.5 13.5 12 22l-9-9V4h9z" />
      <circle cx="7.5" cy="7.5" r="1.3" />
    </>
  ),
  kalender: (
    <>
      <rect x="3.5" y="5" width="17" height="16" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
      <path d="M7.5 13h3M13.5 13h3M7.5 17h3" />
    </>
  ),
  lkw: (
    <>
      <path d="M3 6h11v9H3z" />
      <path d="M14 9h4l3 3v3h-7z" />
      <circle cx="7" cy="18" r="2" />
      <circle cx="17" cy="18" r="2" />
    </>
  ),
  entsorgung: (
    <>
      <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" />
      <path d="M10 11v6M14 11v6" />
    </>
  ),
  umwelt: (
    <>
      <path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14z" />
      <path d="M5 19c4-4 8-7 12-9" />
    </>
  ),
  schild: (
    <>
      <path d="M12 3l7 3v6c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z" />
      <path d="M9 12l2 2 4-4.2" />
    </>
  ),
  schloss: (
    <>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
      <path d="M12 15v2" />
    </>
  ),
  telefon: (
    <path d="M6.5 4h3l1.5 4-2 1.5a12 12 0 0 0 5.5 5.5L16 13l4 1.5v3a2 2 0 0 1-2 2A15 15 0 0 1 4.5 6.5 2 2 0 0 1 6.5 4z" />
  ),
  dokument: (
    <>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4" />
      <path d="M9 12h6M9 15h6M9 18h4" />
    </>
  ),
  glanz: (
    <>
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
      <path d="M18.5 15.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z" />
    </>
  ),
};

export const ServiceIcon: React.FC<ServiceIconProps> = ({
  name,
  size = 48,
  color = "currentColor",
  strokeWidth = 2,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
};
