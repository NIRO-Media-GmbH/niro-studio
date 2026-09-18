// ============================================================
// Schmitt „Neuer Spielstand“ · Game-HUD, Untertitel und Logo-Karte
// Eigene Oberfläche in Schmitt-Farben, keine GTA-Elemente nachgebaut.
// HUD und Untertitel laufen auf der globalen Zeitachse (Sekunden im Video);
// alle Texte liegen in der Reels-Safe-Zone (y 134–1104, x 54–1026).
// ============================================================

import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { asset, ci, clamp, easeIn, easeOut, fontFamily, NAVY, sc } from "./shared";

export const HUD_TOP = 150;
const MAP = 208;

export type IconName = "pin" | "key" | "truck" | "route";
export type MinimapWindow = { from: number; to: number; routeFrom?: number };
export type ToastWindow = { from: number; to: number; kicker: string; text: string; icon: IconName };
export type CueWindow = { from: number; to: number; speaker: string; text: string };

const Icon: React.FC<{ name: IconName; size: number; color: string }> = ({ name, size, color }) => {
  const box = { width: size, height: size, viewBox: "0 0 24 24" };
  if (name === "key") {
    return (
      <svg {...box}>
        <path d="M7.5 16a4.5 4.5 0 1 1 4.24-6H22v3h-2.5v3h-3v-3h-4.76A4.5 4.5 0 0 1 7.5 16zm0-2.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" fill={color} />
      </svg>
    );
  }
  if (name === "truck") {
    return (
      <svg {...box}>
        <path d="M1.5 5.5h12v10h-12zM14.5 9h4.2l3.8 3.8v2.7h-8z" fill={color} />
        <circle cx="6" cy="17.5" r="2.2" fill={color} />
        <circle cx="18" cy="17.5" r="2.2" fill={color} />
      </svg>
    );
  }
  if (name === "route") {
    return (
      <svg {...box}>
        <path d="M6 17h10a3.5 3.5 0 0 0 0-7H8a3.5 3.5 0 0 1 0-7h9" fill="none" stroke={color} strokeWidth={2.6} strokeLinecap="round" />
        <circle cx="5" cy="17" r="2.4" fill={color} />
        <circle cx="19" cy="3" r="2.4" fill={color} />
      </svg>
    );
  }
  return (
    <svg {...box}>
      <path d="M12 2C8.1 2 5 5 5 8.8 5 14 12 22 12 22s7-8 7-13.2C19 5 15.9 2 12 2zm0 9.6a2.8 2.8 0 1 1 0-5.6 2.8 2.8 0 0 1 0 5.6z" fill={color} />
    </svg>
  );
};

// Minimap oben rechts: Karte driftet beim Gehen langsam, beim Fahren schneller;
// ab routeFrom zeichnet sich die gelbe Route zum Ziel.
export const Minimap: React.FC<{ windows: MinimapWindow[] }> = ({ windows }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const w = windows.find((x) => t >= x.from && t < x.to);
  if (!w) return null;
  const vis =
    interpolate(t - w.from, [0, 0.3], [0, 1], { ...clamp, easing: easeOut }) * interpolate(w.to - t, [0, 0.2], [0, 1], clamp);
  const drive = w.routeFrom !== undefined && t >= w.routeFrom ? t - w.routeFrom : -1;
  const shift = Math.min(t - w.from, 6) * 7 + (drive > 0 ? drive * 34 : 0);
  const heading = Math.sin((t - w.from) * 0.7) * 4 - (drive > 0 ? interpolate(drive, [0, 1.2], [0, 18], { ...clamp, easing: easeOut }) : 0);
  const routeLen = 400;
  const routeDraw = drive >= 0 ? interpolate(drive, [0, 0.9], [routeLen, 0], { ...clamp, easing: easeOut }) : routeLen;
  return (
    <div
      style={{
        position: "absolute",
        right: 54,
        top: HUD_TOP,
        width: MAP,
        height: MAP,
        borderRadius: 26,
        overflow: "hidden",
        backgroundColor: "#16203A",
        boxShadow: "inset 0 0 0 3px rgba(255,255,255,0.22), 0 12px 34px rgba(0,0,0,0.45)",
        opacity: vis,
        scale: sc(interpolate(vis, [0, 1], [0.86, 1])),
      }}
    >
      <svg width={MAP} height={MAP} viewBox={`0 0 ${MAP} ${MAP}`}>
        <g transform={`rotate(${heading} 104 128) translate(-196 ${-216 + shift})`}>
          {[
            [120, 380, 140, 70],
            [340, 380, 160, 70],
            [120, 230, 140, 80],
            [340, 230, 120, 80],
            [120, 60, 140, 100],
            [340, 60, 200, 100],
            [30, 490, 100, 90],
            [370, 500, 160, 80],
          ].map(([x, y, bw, bh], i) => (
            <rect key={i} x={x} y={y} width={bw} height={bh} rx={6} fill="#223052" />
          ))}
          <path d="M300 640 L300 -40" stroke="#3B4B6B" strokeWidth={22} />
          <path d="M20 470 L600 470 M20 330 L600 330" stroke="#3B4B6B" strokeWidth={14} />
          <path d="M20 180 L600 180" stroke="#3B4B6B" strokeWidth={18} />
          <path d="M300 180 Q420 120 600 50" fill="none" stroke="#3B4B6B" strokeWidth={12} />
          <path
            d="M300 344 L300 180 L520 180"
            fill="none"
            stroke={ci.colors.accent}
            strokeWidth={8}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={`${routeLen} ${routeLen}`}
            strokeDashoffset={routeDraw}
          />
          <circle cx={520} cy={180} r={10} fill={ci.colors.accent} stroke="#FFFFFF" strokeWidth={3} />
        </g>
        <path d="M104 112 L117 142 L104 134 L91 142 Z" fill="#FFFFFF" stroke={ci.colors.accent} strokeWidth={2.5} strokeLinejoin="round" />
        <circle cx={104} cy={17} r={11} fill="rgba(10,16,28,0.85)" />
        <text x={104} y={21.5} textAnchor="middle" fontFamily={fontFamily} fontWeight={700} fontSize={14} fill="#FFFFFF">
          N
        </text>
      </svg>
    </div>
  );
};

// Hinweis-Karte oben links (Standort, Item, Ziel, Route); bei Überlappung gewinnt die jüngste
export const Toasts: React.FC<{ items: ToastWindow[] }> = ({ items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const active = items.filter((x) => t >= x.from && t < x.to);
  if (active.length === 0) return null;
  const it = active[active.length - 1];
  const inV = interpolate(t - it.from, [0, 0.28], [0, 1], { ...clamp, easing: easeOut });
  const outV = interpolate(it.to - t, [0, 0.22], [0, 1], { ...clamp, easing: easeIn });
  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        top: HUD_TOP + 106, // unter dem Schmitt-Schriftzug an der Fassade in Shot 1 (y 86–227)
        display: "flex",
        alignItems: "center",
        gap: 18,
        padding: "14px 30px 14px 14px",
        borderRadius: 16,
        backgroundColor: "rgba(10,16,28,0.8)",
        boxShadow: "0 12px 34px rgba(0,0,0,0.4)",
        fontFamily,
        opacity: Math.min(inV, outV),
        translate: `${interpolate(inV, [0, 1], [-40, 0]) + interpolate(outV, [0, 1], [-16, 0])}px 0px`,
      }}
    >
      <div
        style={{
          width: 68,
          height: 68,
          borderRadius: 12,
          flexShrink: 0,
          backgroundColor: ci.colors.accent,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          scale: sc(interpolate(inV, [0, 1], [0.7, 1])),
        }}
      >
        <Icon name={it.icon} size={40} color={NAVY} />
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.16em", textTransform: "uppercase", color: ci.colors.accent }}>
          {it.kicker}
        </div>
        <div style={{ marginTop: 2, fontSize: 40, fontWeight: 700, lineHeight: 1.05, whiteSpace: "nowrap", color: ci.colors.text }}>
          {it.text}
        </div>
      </div>
    </div>
  );
};

// Untertitel im Game-Stil: Sprechername klein in Gelb, Satz in Weiß, textboxgroße Abdunklung
export const Subtitles: React.FC<{ cues: CueWindow[] }> = ({ cues }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const c = cues.find((x) => t >= x.from && t < x.to);
  if (!c) return null;
  const inV = interpolate(t - c.from, [0, 0.18], [0, 1], { ...clamp, easing: easeOut });
  const outV = interpolate(c.to - t, [0, 0.15], [0, 1], clamp);
  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        right: 54,
        bottom: 1920 - 1092,
        display: "flex",
        justifyContent: "center",
        fontFamily,
        opacity: Math.min(inV, outV),
        translate: `0px ${interpolate(inV, [0, 1], [14, 0])}px`,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          maxWidth: 920,
          padding: "10px 28px 14px",
          borderRadius: 14,
          backgroundColor: "rgba(8,12,22,0.58)",
        }}
      >
        <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: "0.16em", textTransform: "uppercase", color: ci.colors.accent }}>
          {c.speaker}
        </div>
        <div
          style={{
            marginTop: 2,
            fontSize: 50,
            fontWeight: 600,
            lineHeight: 1.12,
            textAlign: "center",
            color: ci.colors.text,
            textShadow: "0 2px 10px rgba(0,0,0,0.55)",
          }}
        >
          {c.text}
        </div>
      </div>
    </div>
  );
};

export type QuestWindow = {
  label: string;
  steps: number[]; // Zeitpunkte der Teilschritte (Zähler 0/2 → 2/2)
  progress?: { from: number; to: number }; // Fortschrittsbalken, solange die Quest aktiv ist
  doneAt: number;
};
export type QuestLogWindow = { title: string; from: number; to: number; quests: QuestWindow[] };

// Quest-Log oben links: Kästchen haken sich mit kurzem Pop ab, die aktive Quest ist hervorgehoben,
// Teilschritte zählen hoch, Beladen zeigt einen Fortschrittsbalken.
export const QuestLog: React.FC<{ log: QuestLogWindow }> = ({ log }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < log.from || t >= log.to) return null;
  const inV = interpolate(t - log.from, [0, 0.3], [0, 1], { ...clamp, easing: easeOut });
  const outV = interpolate(log.to - t, [0, 0.25], [0, 1], { ...clamp, easing: easeIn });
  const activeIdx = log.quests.findIndex((q) => t < q.doneAt);
  const doneCount = log.quests.filter((q) => t >= q.doneAt).length;
  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        top: HUD_TOP,
        width: 560,
        padding: "14px 22px 18px",
        borderRadius: 16,
        backgroundColor: "rgba(10,16,28,0.78)",
        boxShadow: "0 12px 34px rgba(0,0,0,0.4)",
        fontFamily,
        opacity: Math.min(inV, outV),
        translate: `${interpolate(inV, [0, 1], [-40, 0])}px 0px`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.16em", textTransform: "uppercase", color: ci.colors.accent }}>
          {log.title}
        </div>
        <div style={{ fontSize: 24, fontWeight: 700, color: "rgba(255,255,255,0.7)", fontVariantNumeric: "tabular-nums" }}>
          {doneCount}/{log.quests.length}
        </div>
      </div>
      <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 10 }}>
        {log.quests.map((q, i) => {
          const done = t >= q.doneAt;
          const pop = interpolate(t - q.doneAt, [0, 0.12, 0.3], [1, 1.28, 1], clamp);
          const fill = interpolate(t - q.doneAt, [0, 0.12], [0, 1], clamp);
          const active = i === activeIdx;
          const stepsDone = q.steps.filter((s) => t >= s).length;
          const stepPop = q.steps.reduce((m, s) => Math.max(m, interpolate(t - s, [0, 0.1, 0.28], [0, 1, 0], clamp)), 0);
          const prog = q.progress ? interpolate(t, [q.progress.from, q.progress.to], [0, 1], clamp) : 0;
          return (
            <div key={q.label} style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  flexShrink: 0,
                  boxShadow: `inset 0 0 0 3px ${done ? ci.colors.accent : "rgba(255,255,255,0.65)"}`,
                  backgroundColor: `rgba(242,178,51,${fill.toFixed(3)})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  scale: sc(pop),
                }}
              >
                {done && (
                  <svg width={24} height={24} viewBox="0 0 24 24">
                    <path d="M4 12.5l5 5L20 6.5" fill="none" stroke={NAVY} strokeWidth={3.6} strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: active ? 700 : 600,
                      lineHeight: 1.1,
                      whiteSpace: "nowrap",
                      color: done ? "rgba(255,255,255,0.55)" : ci.colors.text,
                    }}
                  >
                    {q.label}
                  </span>
                  {q.steps.length > 0 && !done && (
                    <span
                      style={{
                        fontSize: 28,
                        fontWeight: 700,
                        color: ci.colors.accent,
                        fontVariantNumeric: "tabular-nums",
                        scale: sc(1 + 0.25 * stepPop),
                      }}
                    >
                      {stepsDone}/{q.steps.length}
                    </span>
                  )}
                </div>
                {q.progress && active && t >= q.progress.from - 0.2 && (
                  <div style={{ marginTop: 6, height: 6, borderRadius: 3, overflow: "hidden", backgroundColor: "rgba(255,255,255,0.2)" }}>
                    <div style={{ width: `${prog * 100}%`, height: "100%", backgroundColor: ci.colors.accent }} />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Logo-Karte am Ende: Marine-Grund mit blauem Schimmer, Logo skaliert ein, Adresse darunter.
// Ohne Logodatei steht ein Wortmarken-Platzhalter.
export const LogoCard: React.FC<{ src: string; url?: string; frames: number }> = ({ src, url, frames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const total = frames / fps;
  const bgIn = 1; // der CTA davor klingt schon in den Marine-Grund aus
  const logoIn = interpolate(t, [0.12, 0.6], [0, 1], { ...clamp, easing: easeOut });
  const urlIn = interpolate(t, [0.6, 0.95], [0, 1], { ...clamp, easing: easeOut });
  const out = interpolate(t, [total - 0.3, total], [1, 0], { ...clamp, easing: easeIn });
  const glow = interpolate(t, [0.3, 0.9, 1.8], [0, 1, 0.55], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <AbsoluteFill
        style={{
          opacity: bgIn * out,
          background: `radial-gradient(ellipse 70% 38% at 50% 32%, rgba(37,84,165,${(0.42 * glow).toFixed(3)}) 0%, rgba(14,20,34,0) 70%), ${ci.colors.background}`,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 90,
            right: 90,
            top: 500, // Logo 760 × 173 → Unterkante 673, Adresse bei 740 (Block mittig in der Safe Zone)
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: logoIn,
            scale: sc(interpolate(logoIn, [0, 1], [0.9, 1])),
            translate: `0px ${interpolate(logoIn, [0, 1], [24, 0])}px`,
          }}
        >
          {src ? (
            <Img src={asset(src)} style={{ width: 760, height: "auto" }} />
          ) : (
            <div style={{ fontFamily, textAlign: "center", color: ci.colors.text }}>
              <div style={{ fontSize: 170, fontWeight: 800, lineHeight: 0.9, letterSpacing: "-0.01em", textTransform: "uppercase" }}>
                Schmitt
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 52,
                  fontWeight: 600,
                  letterSpacing: "0.5em",
                  textTransform: "uppercase",
                  color: ci.colors.accent,
                }}
              >
                Gruppe
              </div>
            </div>
          )}
        </div>
        {url && (
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 740,
              textAlign: "center",
              fontFamily,
              fontSize: 40,
              fontWeight: 600,
              letterSpacing: "0.08em",
              color: "rgba(255,255,255,0.75)",
              opacity: urlIn,
            }}
          >
            {url}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
