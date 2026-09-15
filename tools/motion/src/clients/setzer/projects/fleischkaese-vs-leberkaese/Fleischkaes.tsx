// ============================================================
// Setzer — Fleischkäs als Vektor-Zeichnung, Icon-Stil
//
// Stil nach Kundenvorgabe (Michael, 25.08., Dropbox-Replay + AI-Etikett
// „Backofen Fleischkäse"): **schwarzer Grund, Icon weiß, Highlights rot**.
// Also weiße Line-Art wie die Ofen-/Dampf-Icons auf dem Etikett; die
// rosa Schnittfläche der ersten Fassung ist jetzt das rote Highlight.
//
// Form nach dem echten Laib aus IMG_6933: kastenförmig aus der Form,
// gewölbter Deckel, parallele Einschnitte.
//
// Props:
//   drawP    0..1  Kontur zeichnet sich
//   scoreP   0..1  Einschnitte zeichnen sich nach
//   cutP     0..1  Scheibe löst sich und dreht die Schnittfläche her
//   steamP   0..1  Dampf steigt auf
// ============================================================

import React from "react";

// --- Palette (Icon-Stil) ---
const STROKE = "#FFFFFF";      // Icon weiß
const GROUND = "#0D0802";      // schwarzer Grund (CI-Secondary)
const FILL = GROUND;           // Flächen bleiben Grund-schwarz
const CRUST_TINT = "#241A10";  // hauchfeine Krusten-Andeutung
const HIGHLIGHT = "#E30613";   // Highlights rot (CI-Primary)
const HIGHLIGHT_DARK = "#B9000B";

// Kastenförmiger Laib mit gewölbtem Deckel (viewBox 0 0 640 380)
const LOAF =
  "M 96 298 C 88 258, 86 214, 92 186 C 100 150, 168 128, 320 126 " +
  "C 472 124, 540 150, 548 186 C 554 214, 552 258, 544 298 Z";

// Krusten-Andeutung: Deckelband mit unruhiger Unterkante
const CRUST_CAP =
  "M 56 96 H 584 V 194 C 504 216, 432 198, 356 208 " +
  "C 288 217, 214 197, 142 208 C 112 213, 80 204, 56 196 Z";

// Parallele Einschnitte, wie vor dem Backen gezogen
const SCORES = [
  "M 178 206 L 228 144",
  "M 252 210 L 302 148",
  "M 326 211 L 376 149",
  "M 400 208 L 450 146",
];
const SCORE_LEN = 84;

// Wo der Laib zerteilt wird
const CUT_X = 186;

export const FleischkaesLoaf: React.FC<{
  drawP?: number;
  scoreP?: number;
  cutP?: number;
  steamP?: number;
  showTray?: boolean;
  width?: number;
}> = ({ drawP = 1, scoreP = 1, cutP = 0, steamP = 0, showTray = true, width = 640 }) => {
  const d = Math.max(0, Math.min(1, drawP));
  const s = Math.max(0, Math.min(1, scoreP));
  const c = Math.max(0, Math.min(1, cutP));

  // Scheibe rutscht ein Stück weg und kippt zur Kamera — Wege kurz
  // halten, sonst läuft sie aus dem 9:16-Bild.
  const sliceX = -c * 96;
  const sliceRot = -c * 18;
  const faceIn = Math.max(0, Math.min(1, (c - 0.4) / 0.4));

  return (
    <svg viewBox="0 0 640 380" width={width} style={{ overflow: "visible", display: "block" }}>
      <defs>
        <clipPath id="szLoaf">
          <path d={LOAF} />
        </clipPath>
        <clipPath id="szMain">
          <rect x={CUT_X} y="0" width={640 - CUT_X} height="380" />
        </clipPath>
        <clipPath id="szSlice">
          <rect x="0" y="0" width={CUT_X} height="380" />
        </clipPath>
      </defs>

      {showTray && (
        <g opacity={d}>
          <path
            d="M 44 296 H 596 L 620 348 H 20 Z"
            fill={FILL}
            stroke={STROKE}
            strokeWidth="8"
            strokeLinejoin="round"
          />
          {/* Griffkante als weiße Linie statt Grauton */}
          <path d="M 50 312 H 590" stroke={STROKE} strokeWidth="4" opacity="0.5" fill="none" />
        </g>
      )}

      {/* --- Restlaib (rechts vom Schnitt) --- */}
      <g clipPath="url(#szMain)" opacity={d}>
        <g clipPath="url(#szLoaf)">
          <rect x="0" y="0" width="640" height="380" fill={FILL} />
          <path d={CRUST_CAP} fill={CRUST_TINT} />
          {/* Glanzlinie auf dem Deckel — weiß, wie die Etikett-Icons */}
          <path
            d="M 216 148 C 272 132, 386 130, 446 146"
            fill="none"
            stroke={STROKE}
            strokeWidth="7"
            strokeLinecap="round"
            opacity="0.55"
          />
          {/* Anschnittfläche des Restlaibs = rotes Highlight */}
          {c > 0.02 && (
            <g opacity={faceIn}>
              <rect x={CUT_X - 2} y="100" width="30" height="220" fill={HIGHLIGHT} />
              <g fill={HIGHLIGHT_DARK} opacity="0.7">
                <ellipse cx={CUT_X + 9} cy="176" rx="6" ry="4" />
                <ellipse cx={CUT_X + 14} cy="232" rx="5" ry="3.5" />
                <ellipse cx={CUT_X + 7} cy="268" rx="5" ry="3" />
              </g>
            </g>
          )}
        </g>
        <path
          d={LOAF}
          fill="none"
          stroke={STROKE}
          strokeWidth="10"
          strokeLinejoin="round"
          strokeDasharray="1700"
          strokeDashoffset={(1 - d) * 1700}
        />
        <g fill="none" stroke={STROKE} strokeWidth="8" strokeLinecap="round" opacity="0.9">
          {SCORES.map((p, i) => (
            <path
              key={i}
              d={p}
              strokeDasharray={SCORE_LEN}
              strokeDashoffset={
                (1 - Math.max(0, Math.min(1, s * SCORES.length - i))) * SCORE_LEN
              }
            />
          ))}
        </g>
      </g>

      {/* --- Scheibe (links vom Schnitt) --- */}
      <g opacity={d} transform={`translate(${sliceX} 0) rotate(${sliceRot} ${CUT_X} 296)`}>
        <g clipPath="url(#szSlice)">
          <g clipPath="url(#szLoaf)">
            <rect x="0" y="0" width="640" height="380" fill={FILL} />
            <path d={CRUST_CAP} fill={CRUST_TINT} />
            {/* gekippte Scheibe: die rote Schnittfläche kommt zur Kamera */}
            <g opacity={faceIn}>
              <rect x="0" y="0" width="640" height="380" fill={HIGHLIGHT} />
              <g fill={HIGHLIGHT_DARK} opacity="0.65">
                <ellipse cx="112" cy="176" rx="12" ry="7" />
                <ellipse cx="148" cy="228" rx="8" ry="5" />
                <ellipse cx="106" cy="258" rx="9" ry="6" />
                <ellipse cx="150" cy="160" rx="7" ry="4.5" />
                <ellipse cx="128" cy="286" rx="10" ry="6" />
              </g>
              {/* Krustenrand oben bleibt schwarz stehen */}
              <path d="M 56 96 H 584 V 152 C 470 134, 190 132, 56 152 Z" fill={FILL} />
            </g>
          </g>
          <path
            d={LOAF}
            fill="none"
            stroke={STROKE}
            strokeWidth="10"
            strokeLinejoin="round"
            strokeDasharray="1700"
            strokeDashoffset={(1 - d) * 1700}
          />
          {/* Ein Einschnitt auf der Scheibe, solange sie noch flach liegt */}
          <g
            fill="none"
            stroke={STROKE}
            strokeWidth="8"
            strokeLinecap="round"
            opacity={0.9 * (1 - faceIn)}
          >
            <path
              d={SCORES[0]}
              strokeDasharray={SCORE_LEN}
              strokeDashoffset={(1 - Math.max(0, Math.min(1, s * 4))) * SCORE_LEN}
            />
          </g>
        </g>
        {/* Schnittkante der Scheibe */}
        <line
          x1={CUT_X}
          y1="130"
          x2={CUT_X}
          y2="298"
          stroke={STROKE}
          strokeWidth="10"
          strokeLinecap="round"
          opacity={c > 0.02 ? 1 : 0}
        />
      </g>

      {steamP > 0.01 && <Steam p={steamP} />}
    </svg>
  );
};

const Steam: React.FC<{ p: number }> = ({ p }) => {
  const wisps = [
    { x: 262, delay: 0.0, h: 1.0 },
    { x: 344, delay: 0.22, h: 1.18 },
    { x: 424, delay: 0.11, h: 0.9 },
  ];
  return (
    <g fill="none" stroke={STROKE} strokeWidth="11" strokeLinecap="round">
      {wisps.map((wi, i) => {
        const t = Math.max(0, Math.min(1, (p - wi.delay) / Math.max(0.001, 1 - wi.delay)));
        const rise = t * 58;
        const op = Math.sin(Math.PI * t) * 0.8;
        const H = 46 * wi.h;
        return (
          <path
            key={i}
            d={`M ${wi.x} ${120 - rise} c -16 -${H * 0.5} 16 -${H * 0.75} 0 -${H} c -14 -${H * 0.45} 12 -${H * 0.7} 0 -${H}`}
            opacity={op}
          />
        );
      })}
    </g>
  );
};

// Messer für den Schnitt-Moment — weiße Line-Art wie die Etikett-Icons
export const KnifeIcon: React.FC<{ size?: number }> = ({ size = 220 }) => (
  <svg viewBox="0 0 200 340" width={size} style={{ display: "block", overflow: "visible" }}>
    <path
      d="M 96 8 C 128 62, 142 130, 138 196 L 60 196 C 56 130, 66 62, 96 8 Z"
      fill={GROUND}
      stroke={STROKE}
      strokeWidth="10"
      strokeLinejoin="round"
    />
    <path
      d="M 96 30 C 114 78, 122 134, 121 184"
      fill="none"
      stroke={STROKE}
      strokeWidth="6"
      strokeLinecap="round"
      opacity="0.5"
    />
    <rect x="60" y="194" width="78" height="22" fill={GROUND} stroke={STROKE} strokeWidth="10" />
    <rect x="70" y="216" width="58" height="112" rx="14" fill={GROUND} stroke={STROKE} strokeWidth="10" />
    {/* rote Nieten als Highlight */}
    <circle cx="99" cy="248" r="7" fill={HIGHLIGHT} />
    <circle cx="99" cy="292" r="7" fill={HIGHLIGHT} />
  </svg>
);
