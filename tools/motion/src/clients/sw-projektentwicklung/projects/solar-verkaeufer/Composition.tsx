// ============================================================
// SW Projektentwicklung — "Solar Verkäufer" Reel Overlay
// KRANK: Over-the-top animations, clean & hochwertig
// 9:16 portrait, 47s, transparent overlay on video
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  OffthreadVideo,
  staticFile,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("sw-projektentwicklung", brandJson as any);

// =============================================================
// SCHEMA — alles editierbar im Remotion Studio
// =============================================================

const timingSchema = z.object({
  startSec: z.number().step(0.1).describe("Start (Sekunden)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sekunden)"),
});

const posSchema = z.object({
  x: z.number().step(1).describe("X (px)"),
  y: z.number().step(1).describe("Y (px)"),
});

const P0 = { x: 0, y: 0 };

const hookSchema = timingSchema.extend({
  hookWord: z.string().describe("Hauptwort"),
  hookSuffix: z.string().describe("Suffix (z.B. ?)"),
  wordPos: posSchema.describe("Position: Hauptwort"),
  subtitle: z.string().describe("Untertitel"),
  subtitlePos: posSchema.describe("Position: Untertitel"),
});

const problemSchema = timingSchema.extend({
  item1: z.string().describe("Punkt 1"),
  item1Pos: posSchema.describe("Position: Punkt 1"),
  item2: z.string().describe("Punkt 2"),
  item2Pos: posSchema.describe("Position: Punkt 2"),
  item3: z.string().describe("Punkt 3"),
  item3Pos: posSchema.describe("Position: Punkt 3"),
});

const lowerThirdSchema = timingSchema.extend({
  name: z.string().describe("Name"),
  title: z.string().describe("Titel / Position"),
  cardPos: posSchema.describe("Position: Karte"),
});

const statCounterSchema = timingSchema.extend({
  statNumber: z.number().describe("Zahl"),
  statSuffix: z.string().describe("Suffix (z.B. +)"),
  numberPos: posSchema.describe("Position: Zahl"),
  statLabel: z.string().describe("Label"),
  labelPos: posSchema.describe("Position: Label"),
  statSublabel: z.string().describe("Unterlabel"),
  sublabelPos: posSchema.describe("Position: Unterlabel"),
});

const threeComponentsSchema = timingSchema.extend({
  titleNumber: z.string().describe("Zahl-Titel"),
  titleSubtext: z.string().describe("Untertitel"),
  titlePos: posSchema.describe("Position: Titel"),
  comp1Icon: z.string().describe("Icon 1"),
  comp1Label: z.string().describe("Name 1"),
  comp1Desc: z.string().describe("Beschreibung 1"),
  comp1Pos: posSchema.describe("Position: Bauteil 1"),
  comp2Icon: z.string().describe("Icon 2"),
  comp2Label: z.string().describe("Name 2"),
  comp2Desc: z.string().describe("Beschreibung 2"),
  comp2Pos: posSchema.describe("Position: Bauteil 2"),
  comp3Icon: z.string().describe("Icon 3"),
  comp3Label: z.string().describe("Name 3"),
  comp3Desc: z.string().describe("Beschreibung 3"),
  comp3Pos: posSchema.describe("Position: Bauteil 3"),
});

const geldSparenSchema = timingSchema.extend({
  symbol: z.string().describe("Symbol (z.B. €)"),
  symbolPos: posSchema.describe("Position: Symbol"),
  mainText: z.string().describe("Haupttext"),
  mainTextPos: posSchema.describe("Position: Haupttext"),
  subText: z.string().describe("Untertext"),
  subTextPos: posSchema.describe("Position: Untertext"),
});

const fullServiceSchema = timingSchema.extend({
  title: z.string().describe("Titel"),
  titlePos: posSchema.describe("Position: Titel"),
  item1: z.string().describe("Punkt 1"),
  item1Pos: posSchema.describe("Position: Punkt 1"),
  item2: z.string().describe("Punkt 2"),
  item2Pos: posSchema.describe("Position: Punkt 2"),
  item3: z.string().describe("Punkt 3"),
  item3Pos: posSchema.describe("Position: Punkt 3"),
  item4: z.string().describe("Punkt 4"),
  item4Pos: posSchema.describe("Position: Punkt 4"),
});

const ctaSchema = timingSchema.extend({
  introText: z.string().describe("Intro-Text"),
  introPos: posSchema.describe("Position: Intro"),
  bubbleText: z.string().describe("Bubble-Text"),
  bubblePos: posSchema.describe("Position: Bubble"),
  arrowSymbol: z.string().describe("Pfeil-Symbol"),
  arrowPos: posSchema.describe("Position: Pfeil"),
  brandName: z.string().describe("Markenname"),
  brandPos: posSchema.describe("Position: Marke"),
  website: z.string().describe("Website"),
  websitePos: posSchema.describe("Position: Website"),
});

export const swSolarVerkaeuferSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Szene 1: SOLAR? Hook"),
  problem: problemSchema.describe("Szene 2: Problem-Punkte"),
  lowerThird: lowerThirdSchema.describe("Szene 3: Name & Titel"),
  statCounter: statCounterSchema.describe("Szene 4: 180+ Projekte"),
  threeComponents: threeComponentsSchema.describe("Szene 5: 3 Bauteile"),
  geldSparen: geldSparenSchema.describe("Szene 6: Geld sparen"),
  fullService: fullServiceSchema.describe("Szene 7: Full Service"),
  cta: ctaSchema.describe("Szene 8: CTA Solar"),
});

export type Props = z.infer<typeof swSolarVerkaeuferSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

const ORANGE = "#FF8022";
const ORANGE_LIGHT = "#FF9A4D";
const WHITE = "#FFFFFF";
const RED_WARN = "#FF3B3B";

const SAFE = { top: 0.09, bottom: 0.60, left: 0.05, right: 0.95 };

const SLAM_SPRING = { damping: 8, stiffness: 220 };
const PUNCH_SPRING = { damping: 10, stiffness: 180 };
const SMOOTH_SPRING = { damping: 14, stiffness: 120 };
const BOUNCE_SPRING = { damping: 6, stiffness: 260 };

// =============================================================
// HELPERS
// =============================================================

const useExit = (exitFrames = 10) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);
  const exitProg = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitSlide = interpolate(exitProg, [0, 1], [40, 0]);
  const exitScale = interpolate(exitProg, [0, 1], [0.85, 1]);
  return { exitProg, exitSlide, exitScale };
};

// =============================================================
// SCENE 1: HOOK — explosive entrance
// =============================================================

const HookScene: React.FC<{
  hookWord: string; hookSuffix: string; wordPos: Pos;
  subtitle: string; subtitlePos: Pos;
}> = ({ hookWord, hookSuffix, wordPos, subtitle, subtitlePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(8);

  const slamProg = spring({ frame, fps, config: { damping: 6, stiffness: 300 } });
  const scale = interpolate(slamProg, [0, 1], [4, 1]);
  const rotate = interpolate(slamProg, [0, 1], [-12, 0]);

  const shakeX = frame < 12 ? Math.sin(frame * 8) * (12 - frame) * 1.5 : 0;
  const shakeY = frame < 12 ? Math.cos(frame * 6) * (12 - frame) * 1.2 : 0;

  const qProg = spring({ frame: frame - 8, fps, config: BOUNCE_SPRING });
  const flashOpacity = interpolate(frame, [0, 3, 8], [0.6, 0.3, 0], { extrapolateRight: "clamp" });
  const subProg = spring({ frame: frame - 15, fps, config: PUNCH_SPRING });

  const ringProg = spring({ frame: frame - 2, fps, config: { damping: 20, stiffness: 60 } });
  const ringScale = interpolate(ringProg, [0, 1], [0, 3.5]);
  const ringOpacity = interpolate(ringProg, [0, 0.3, 1], [0.8, 0.4, 0]);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <AbsoluteFill style={{ backgroundColor: ORANGE, opacity: flashOpacity }} />

      <div
        style={{
          position: "absolute", top: centerY + wordPos.y, left: centerX + wordPos.x,
          width: width * 0.25, height: width * 0.25, borderRadius: "50%",
          border: `4px solid ${ORANGE}`,
          transform: `translate(-50%, -50%) scale(${ringScale * exitScale})`,
          opacity: ringOpacity * exitProg,
        }}
      />

      <div
        style={{
          position: "absolute", top: centerY - height * 0.06 + wordPos.y, left: centerX + wordPos.x,
          transform: `translate(-50%, -50%) scale(${scale * exitScale}) rotate(${rotate}deg) translate(${shakeX}px, ${shakeY}px)`,
          fontFamily: "Montserrat, sans-serif", fontSize: height * 0.08,
          fontWeight: 900, color: WHITE, letterSpacing: -2,
          textShadow: `0 4px 30px rgba(0,0,0,0.9), 0 0 60px ${ORANGE}80`,
          opacity: slamProg * exitProg,
        }}
      >
        {hookWord}
        <span
          style={{
            color: ORANGE, display: "inline-block",
            transform: `scale(${interpolate(qProg, [0, 1], [0, 1.3])}) rotate(${interpolate(qProg, [0, 1], [90, 0])}deg)`,
            transformOrigin: "center bottom", marginLeft: 4,
          }}
        >
          {hookSuffix}
        </span>
      </div>

      <div
        style={{
          position: "absolute", top: centerY + height * 0.04 + subtitlePos.y, left: centerX + subtitlePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(subProg, [0, 1], [30, 0])}px) scale(${exitScale})`,
          opacity: subProg * exitProg,
          fontFamily: "Montserrat, sans-serif", fontSize: height * 0.02,
          fontWeight: 700, color: ORANGE_LIGHT, letterSpacing: 4,
          textTransform: "uppercase", textShadow: "0 2px 20px rgba(0,0,0,0.9)",
        }}
      >
        {subtitle}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 2: PROBLEM — warning X marks
// =============================================================

const ProblemScene: React.FC<{
  item1: string; item1Pos: Pos;
  item2: string; item2Pos: Pos;
  item3: string; item3Pos: Pos;
}> = ({ item1, item1Pos, item2, item2Pos, item3, item3Pos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(8);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const items = [
    { text: item1, pos: item1Pos },
    { text: item2, pos: item2Pos },
    { text: item3, pos: item3Pos },
  ];

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      {items.map(({ text, pos }, i) => {
        const delay = 3 + i * 8;
        const enterProg = spring({ frame: frame - delay, fps, config: SLAM_SPRING });
        const xProg = spring({ frame: frame - delay, fps, config: { damping: 5, stiffness: 300 } });
        const shake = frame >= delay && frame < delay + 6
          ? Math.sin((frame - delay) * 10) * (6 - (frame - delay)) * 2 : 0;

        const yPos = centerY - height * 0.08 + i * (height * 0.07) + pos.y;

        return (
          <div
            key={i}
            style={{
              position: "absolute", top: yPos,
              left: width * SAFE.left + width * 0.03 + pos.x,
              right: width * (1 - SAFE.right),
              display: "flex", alignItems: "center", gap: width * 0.035,
              opacity: enterProg * exitProg,
              transform: `translateX(${interpolate(enterProg, [0, 1], [-80, 0]) + shake}px) scale(${exitScale})`,
            }}
          >
            <div
              style={{
                width: height * 0.04, height: height * 0.04, borderRadius: "50%",
                backgroundColor: `rgba(255, 59, 59, ${0.2 * enterProg})`,
                display: "flex", justifyContent: "center", alignItems: "center",
                flexShrink: 0, border: `2px solid ${RED_WARN}`,
                boxShadow: `0 0 ${15 * xProg}px ${RED_WARN}60`,
                transform: `scale(${interpolate(xProg, [0, 1], [0, 1])}) rotate(${interpolate(xProg, [0, 1], [180, 0])}deg)`,
              }}
            >
              <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.022, fontWeight: 900, color: RED_WARN, lineHeight: 1 }}>
                ✕
              </span>
            </div>
            <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.026, fontWeight: 800, color: WHITE, textShadow: "0 2px 20px rgba(0,0,0,0.95)" }}>
              {text}
            </span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 3: LOWER THIRD — Name + Title
// =============================================================

const LowerThirdScene: React.FC<{
  name: string; title: string; cardPos: Pos;
}> = ({ name, title, cardPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide } = useExit(10);

  const barProg = spring({ frame: frame - 2, fps, config: { damping: 12, stiffness: 160 } });
  const nameProg = spring({ frame: frame - 6, fps, config: PUNCH_SPRING });
  const titleProg = spring({ frame: frame - 12, fps, config: SMOOTH_SPRING });
  const lineProg = spring({ frame: frame - 1, fps, config: { damping: 14, stiffness: 100 } });

  const barWidth = interpolate(barProg, [0, 1], [0, width * 0.85]);
  const lineWidth = interpolate(lineProg, [0, 1], [0, width * 0.5]);

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          bottom: height * (1 - SAFE.bottom) + cardPos.y,
          left: width * SAFE.left + cardPos.x,
          opacity: exitProg, transform: `translateY(${exitSlide}px)`,
        }}
      >
        <div
          style={{
            width: barWidth, backgroundColor: "rgba(0,0,0,0.65)",
            backdropFilter: `blur(${interpolate(barProg, [0, 1], [0, 20])}px)`,
            borderRadius: 12, padding: `${height * 0.015}px ${height * 0.025}px`,
            borderLeft: `4px solid ${ORANGE}`,
            boxShadow: `0 4px 30px rgba(0,0,0,0.5), inset 0 0 30px rgba(255,128,34,0.05)`,
            overflow: "hidden",
          }}
        >
          <div style={{ position: "absolute", top: 0, left: 0, width: lineWidth, height: 2, background: `linear-gradient(90deg, ${ORANGE}, ${ORANGE_LIGHT}, transparent)` }} />
          <div
            style={{
              opacity: nameProg,
              transform: `translateX(${interpolate(nameProg, [0, 1], [40, 0])}px) scale(${interpolate(nameProg, [0, 1], [0.8, 1])})`,
              transformOrigin: "left center",
              fontFamily: "Montserrat, sans-serif", fontSize: height * 0.032,
              fontWeight: 900, color: WHITE, letterSpacing: 0.5,
              textShadow: "0 2px 10px rgba(0,0,0,0.5)",
            }}
          >
            {name}
          </div>
          <div
            style={{
              opacity: titleProg, transform: `translateX(${interpolate(titleProg, [0, 1], [20, 0])}px)`,
              fontFamily: "Montserrat, sans-serif", fontSize: height * 0.016,
              fontWeight: 600, color: ORANGE_LIGHT, letterSpacing: 2,
              textTransform: "uppercase", marginTop: 4,
            }}
          >
            {title}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 4: STAT COUNTER
// =============================================================

const StatCounter: React.FC<{
  statNumber: number; statSuffix: string; numberPos: Pos;
  statLabel: string; labelPos: Pos;
  statSublabel: string; sublabelPos: Pos;
}> = ({ statNumber, statSuffix, numberPos, statLabel, labelPos, statSublabel, sublabelPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  const countProg = spring({ frame: frame - 3, fps, config: { damping: 18, stiffness: 80 } });
  const count = Math.floor(interpolate(countProg, [0, 1], [0, statNumber]));
  const numScale = spring({ frame: frame - 3, fps, config: SLAM_SPRING });
  const labelProg = spring({ frame: frame - 15, fps, config: PUNCH_SPRING });
  const subProg = spring({ frame: frame - 22, fps, config: SMOOTH_SPRING });

  const glowPulse = Math.sin(frame * 0.12) * 0.4 + 0.6;
  const ringProg = spring({ frame: frame - 5, fps, config: { damping: 20, stiffness: 60 } });

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: centerY, left: centerX, transform: `translate(-50%, -50%) scale(${exitScale})`, opacity: exitProg, textAlign: "center" }}>
        <div
          style={{
            position: "absolute", top: "50%", left: "50%",
            width: height * 0.22, height: height * 0.22, borderRadius: "50%",
            border: `2px solid ${ORANGE}30`,
            transform: `translate(-50%, -50%) scale(${interpolate(ringProg, [0, 1], [0, 1])})`,
            opacity: ringProg * 0.5, boxShadow: `0 0 ${30 * glowPulse}px ${ORANGE}30`,
          }}
        />
        <div
          style={{
            fontFamily: "Montserrat, sans-serif", fontSize: height * 0.1,
            fontWeight: 900, color: ORANGE, lineHeight: 1,
            transform: `scale(${interpolate(numScale, [0, 1], [3, 1])}) translate(${numberPos.x}px, ${numberPos.y}px)`,
            opacity: numScale, textShadow: `0 0 ${40 * glowPulse}px ${ORANGE}80, 0 4px 20px rgba(0,0,0,0.8)`,
          }}
        >
          {count}<span style={{ fontSize: height * 0.06, color: ORANGE_LIGHT }}>{statSuffix}</span>
        </div>
        <div style={{ opacity: labelProg, transform: `translateY(${interpolate(labelProg, [0, 1], [20, 0])}px) translate(${labelPos.x}px, ${labelPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.028, fontWeight: 800, color: WHITE, letterSpacing: 6, textTransform: "uppercase", marginTop: height * 0.01, textShadow: "0 2px 20px rgba(0,0,0,0.9)" }}>
          {statLabel}
        </div>
        <div style={{ opacity: subProg, transform: `translateY(${interpolate(subProg, [0, 1], [15, 0])}px) translate(${sublabelPos.x}px, ${sublabelPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.015, fontWeight: 600, color: "rgba(255,255,255,0.7)", letterSpacing: 3, textTransform: "uppercase", marginTop: height * 0.008, textShadow: "0 1px 10px rgba(0,0,0,0.9)" }}>
          {statSublabel}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 5: THREE COMPONENTS
// =============================================================

const ThreeComponents: React.FC<{
  titleNumber: string; titleSubtext: string; titlePos: Pos;
  comp1Icon: string; comp1Label: string; comp1Desc: string; comp1Pos: Pos;
  comp2Icon: string; comp2Label: string; comp2Desc: string; comp2Pos: Pos;
  comp3Icon: string; comp3Label: string; comp3Desc: string; comp3Pos: Pos;
}> = ({
  titleNumber, titleSubtext, titlePos,
  comp1Icon, comp1Label, comp1Desc, comp1Pos,
  comp2Icon, comp2Label, comp2Desc, comp2Pos,
  comp3Icon, comp3Label, comp3Desc, comp3Pos,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const safeLeft = width * SAFE.left;
  const safeRight = width * SAFE.right;
  const safeWidth = safeRight - safeLeft;

  const titleProgVal = spring({ frame: frame - 2, fps, config: PUNCH_SPRING });

  const components = [
    { icon: comp1Icon, label: comp1Label, desc: comp1Desc, pos: comp1Pos },
    { icon: comp2Icon, label: comp2Label, desc: comp2Desc, pos: comp2Pos },
    { icon: comp3Icon, label: comp3Label, desc: comp3Desc, pos: comp3Pos },
  ];

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: height * SAFE.top + height * 0.01 + titlePos.y,
          left: width / 2 + titlePos.x,
          transform: `translate(-50%, 0) scale(${exitScale})`,
          opacity: titleProgVal, textAlign: "center",
        }}
      >
        <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.05, fontWeight: 900, color: ORANGE, textShadow: `0 4px 20px rgba(0,0,0,0.8), 0 0 40px ${ORANGE}50`, transform: `scale(${interpolate(titleProgVal, [0, 1], [2, 1])})` }}>
          {titleNumber}
        </div>
        <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.018, fontWeight: 700, color: WHITE, letterSpacing: 5, textTransform: "uppercase", textShadow: "0 2px 15px rgba(0,0,0,0.9)", transform: `translateY(${interpolate(titleProgVal, [0, 1], [15, 0])}px)` }}>
          {titleSubtext}
        </div>
      </div>

      {components.map((comp, i) => {
        const delay = 10 + i * 10;
        const cardProg = spring({ frame: frame - delay, fps, config: SLAM_SPRING });
        const cardScale = interpolate(cardProg, [0, 1], [0.3, 1]);
        const cardRotate = interpolate(cardProg, [0, 1], [15 - i * 8, 0]);
        const cardX = interpolate(cardProg, [0, 1], [i % 2 === 0 ? -120 : 120, 0]);
        const iconProg = spring({ frame: frame - delay - 2, fps, config: BOUNCE_SPRING });
        const glowPulse = Math.sin((frame + i * 10) * 0.1) * 0.3 + 0.7;
        const cardWidth = safeWidth * 0.88;
        const cardY = centerY - height * 0.1 + i * (height * 0.1) + comp.pos.y;

        return (
          <div
            key={i}
            style={{
              position: "absolute", top: cardY, left: width / 2 + comp.pos.x,
              width: cardWidth,
              transform: `translate(-50%, -50%) scale(${cardScale * exitScale}) rotate(${cardRotate}deg) translateX(${cardX}px)`,
              opacity: cardProg * exitProg,
            }}
          >
            <div
              style={{
                display: "flex", alignItems: "center", gap: width * 0.04,
                backgroundColor: "rgba(0,0,0,0.7)",
                backdropFilter: `blur(${14 * cardProg}px)`, borderRadius: 14,
                padding: `${height * 0.016}px ${height * 0.025}px`,
                border: `2px solid ${ORANGE}${Math.round(40 + glowPulse * 30).toString(16)}`,
                boxShadow: `0 4px 30px rgba(0,0,0,0.5), 0 0 ${20 * glowPulse}px ${ORANGE}25`,
              }}
            >
              <div style={{ fontSize: height * 0.04, transform: `scale(${interpolate(iconProg, [0, 1], [0, 1.1])}) rotate(${interpolate(iconProg, [0, 1], [-180, 0])}deg)`, filter: `drop-shadow(0 0 ${10 * glowPulse}px ${ORANGE}80)` }}>
                {comp.icon}
              </div>
              <div>
                <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.024, fontWeight: 800, color: WHITE, textShadow: "0 2px 10px rgba(0,0,0,0.7)" }}>{comp.label}</div>
                <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.014, fontWeight: 600, color: ORANGE_LIGHT, letterSpacing: 1, marginTop: 2 }}>{comp.desc}</div>
              </div>
              <div style={{ marginLeft: "auto", width: height * 0.035, height: height * 0.035, borderRadius: "50%", backgroundColor: ORANGE, display: "flex", justifyContent: "center", alignItems: "center", fontFamily: "Montserrat, sans-serif", fontSize: height * 0.018, fontWeight: 900, color: WHITE, boxShadow: `0 0 ${15 * glowPulse}px ${ORANGE}60`, transform: `scale(${interpolate(cardProg, [0, 1], [0, 1])})` }}>
                {i + 1}
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 6: GELD SPAREN — Euro badge
// =============================================================

const GeldSparen: React.FC<{
  symbol: string; symbolPos: Pos;
  mainText: string; mainTextPos: Pos;
  subText: string; subTextPos: Pos;
}> = ({ symbol, symbolPos, mainText, mainTextPos, subText, subTextPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  const euroProg = spring({ frame: frame - 2, fps, config: { damping: 5, stiffness: 250 } });
  const textProg = spring({ frame: frame - 10, fps, config: PUNCH_SPRING });
  const subProg = spring({ frame: frame - 18, fps, config: SMOOTH_SPRING });

  const glowPulse = Math.sin(frame * 0.1) * 0.4 + 0.6;
  const floatY = Math.sin(frame * 0.08) * 5;
  const ringRotate = frame * 1.5;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div style={{ position: "absolute", top: centerY, left: centerX, transform: `translate(-50%, -50%) scale(${exitScale}) translateY(${floatY}px)`, textAlign: "center" }}>
        <div style={{ position: "absolute", top: "50%", left: "50%", width: height * 0.18, height: height * 0.18, borderRadius: "50%", border: `2px dashed ${ORANGE}40`, transform: `translate(-50%, -65%) rotate(${ringRotate}deg) scale(${interpolate(euroProg, [0, 1], [0, 1])})` }} />
        <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.12, fontWeight: 900, color: ORANGE, lineHeight: 1, transform: `scale(${interpolate(euroProg, [0, 1], [5, 1])}) rotate(${interpolate(euroProg, [0, 1], [-30, 0])}deg) translate(${symbolPos.x}px, ${symbolPos.y}px)`, opacity: euroProg, textShadow: `0 0 ${50 * glowPulse}px ${ORANGE}80, 0 4px 20px rgba(0,0,0,0.8)` }}>
          {symbol}
        </div>
        <div style={{ opacity: textProg, transform: `translateY(${interpolate(textProg, [0, 1], [30, 0])}px) translate(${mainTextPos.x}px, ${mainTextPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.028, fontWeight: 900, color: WHITE, letterSpacing: 1, marginTop: height * 0.015, textShadow: "0 2px 20px rgba(0,0,0,0.95)" }}>
          {mainText}
        </div>
        <div style={{ opacity: subProg, transform: `translateY(${interpolate(subProg, [0, 1], [15, 0])}px) translate(${subTextPos.x}px, ${subTextPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.015, fontWeight: 600, color: ORANGE_LIGHT, letterSpacing: 3, textTransform: "uppercase", marginTop: height * 0.006, textShadow: "0 1px 10px rgba(0,0,0,0.9)" }}>
          {subText}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 7: FULL SERVICE — Checklist
// =============================================================

const FullService: React.FC<{
  title: string; titlePos: Pos;
  item1: string; item1Pos: Pos;
  item2: string; item2Pos: Pos;
  item3: string; item3Pos: Pos;
  item4: string; item4Pos: Pos;
}> = ({ title, titlePos, item1, item1Pos, item2, item2Pos, item3, item3Pos, item4, item4Pos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide, exitScale } = useExit(10);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const titleProgVal = spring({ frame: frame - 2, fps, config: PUNCH_SPRING });

  const items = [
    { text: item1, pos: item1Pos },
    { text: item2, pos: item2Pos },
    { text: item3, pos: item3Pos },
    { text: item4, pos: item4Pos },
  ];

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: height * SAFE.top + height * 0.01 + titlePos.y,
          left: width * SAFE.left + width * 0.03 + titlePos.x,
          opacity: titleProgVal, transform: `translateX(${interpolate(titleProgVal, [0, 1], [-50, 0])}px) scale(${exitScale})`,
        }}
      >
        <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.032, fontWeight: 900, color: ORANGE, textShadow: `0 2px 20px rgba(0,0,0,0.8), 0 0 30px ${ORANGE}40`, letterSpacing: 1 }}>
          {title}
        </div>
        <div style={{ width: interpolate(titleProgVal, [0, 1], [0, width * 0.25]), height: 3, background: `linear-gradient(90deg, ${ORANGE}, transparent)`, borderRadius: 2, marginTop: 4 }} />
      </div>

      {items.map(({ text, pos }, i) => {
        const delay = 8 + i * 8;
        const itemProg = spring({ frame: frame - delay, fps, config: PUNCH_SPRING });
        const checkProg = spring({ frame: frame - delay - 3, fps, config: BOUNCE_SPRING });
        const yPos = centerY - height * 0.06 + i * (height * 0.068) + pos.y;

        return (
          <div
            key={i}
            style={{
              position: "absolute", top: yPos,
              left: width * SAFE.left + width * 0.03 + pos.x,
              right: width * (1 - SAFE.right),
              display: "flex", alignItems: "center", gap: width * 0.035,
              opacity: itemProg * exitProg,
              transform: `translateX(${interpolate(itemProg, [0, 1], [60, 0])}px) translateY(${exitSlide * 0.3}px) scale(${exitScale})`,
            }}
          >
            <div
              style={{
                width: height * 0.036, height: height * 0.036, borderRadius: "50%",
                backgroundColor: `${ORANGE}${Math.round(checkProg * 255).toString(16).padStart(2, '0')}`,
                display: "flex", justifyContent: "center", alignItems: "center", flexShrink: 0,
                transform: `scale(${interpolate(checkProg, [0, 1], [0, 1])}) rotate(${interpolate(checkProg, [0, 1], [-180, 0])}deg)`,
                boxShadow: `0 0 ${15 * checkProg}px ${ORANGE}50`,
              }}
            >
              <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.02, fontWeight: 900, color: WHITE, opacity: checkProg, transform: `scale(${interpolate(checkProg, [0, 1], [0, 1.2])})` }}>
                ✓
              </span>
            </div>
            <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.023, fontWeight: 700, color: WHITE, textShadow: "0 2px 15px rgba(0,0,0,0.95)" }}>
              {text}
            </span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 8: CTA — "Schreib uns SOLAR"
// =============================================================

const CTAScene: React.FC<{
  introText: string; introPos: Pos;
  bubbleText: string; bubblePos: Pos;
  arrowSymbol: string; arrowPos: Pos;
  brandName: string; brandPos: Pos;
  website: string; websitePos: Pos;
}> = ({ introText, introPos, bubbleText, bubblePos, arrowSymbol, arrowPos, brandName, brandPos, website, websitePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const centerY = ((SAFE.top + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  const bubbleProg = spring({ frame: frame - 3, fps, config: SLAM_SPRING });
  const solarProg = spring({ frame: frame - 10, fps, config: BOUNCE_SPRING });
  const arrowProg = spring({ frame: frame - 16, fps, config: PUNCH_SPRING });
  const brandProg = spring({ frame: frame - 22, fps, config: SMOOTH_SPRING });
  const webProg = spring({ frame: frame - 28, fps, config: SMOOTH_SPRING });

  const glowPulse = Math.sin(frame * 0.15) * 0.4 + 0.6;
  const pulseScale = 1 + Math.sin(frame * 0.2) * 0.03;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div style={{ position: "absolute", top: centerY, left: centerX, transform: `translate(-50%, -50%) scale(${exitScale})`, textAlign: "center" }}>
        <div style={{ opacity: bubbleProg, transform: `translateY(${interpolate(bubbleProg, [0, 1], [20, 0])}px) translate(${introPos.x}px, ${introPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.02, fontWeight: 700, color: "rgba(255,255,255,0.8)", letterSpacing: 2, textTransform: "uppercase", marginBottom: height * 0.015, textShadow: "0 2px 15px rgba(0,0,0,0.9)" }}>
          {introText}
        </div>

        <div style={{ display: "inline-block", transform: `scale(${interpolate(bubbleProg, [0, 1], [0, 1]) * pulseScale}) translate(${bubblePos.x}px, ${bubblePos.y}px)`, opacity: bubbleProg }}>
          <div style={{ backgroundColor: ORANGE, borderRadius: 20, borderBottomLeftRadius: 5, padding: `${height * 0.02}px ${height * 0.06}px`, boxShadow: `0 4px 30px rgba(0,0,0,0.5), 0 0 ${40 * glowPulse}px ${ORANGE}50`, position: "relative" }}>
            <div style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.055, fontWeight: 900, color: WHITE, letterSpacing: 4, transform: `scale(${interpolate(solarProg, [0, 1], [0.5, 1])})`, opacity: solarProg, textShadow: "0 2px 10px rgba(0,0,0,0.3)" }}>
              {bubbleText}
            </div>
          </div>
          <div style={{ position: "absolute", bottom: -10, left: 20, width: 0, height: 0, borderLeft: "12px solid transparent", borderRight: "12px solid transparent", borderTop: `14px solid ${ORANGE}`, transform: "rotate(-10deg)" }} />
        </div>

        <div style={{ opacity: arrowProg, transform: `translateY(${interpolate(arrowProg, [0, 1], [20, 0])}px) translate(${arrowPos.x}px, ${arrowPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.035, marginTop: height * 0.025, color: ORANGE, filter: `drop-shadow(0 0 10px ${ORANGE}80)` }}>
          {arrowSymbol}
        </div>
        <div style={{ opacity: brandProg, transform: `translateY(${interpolate(brandProg, [0, 1], [10, 0])}px) translate(${brandPos.x}px, ${brandPos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.024, fontWeight: 900, color: WHITE, letterSpacing: 2, marginTop: height * 0.008, textShadow: "0 2px 20px rgba(0,0,0,0.95)" }}>
          {brandName}
        </div>
        <div style={{ opacity: webProg, transform: `translateY(${interpolate(webProg, [0, 1], [10, 0])}px) translate(${websitePos.x}px, ${websitePos.y}px)`, fontFamily: "Montserrat, sans-serif", fontSize: height * 0.014, fontWeight: 600, color: ORANGE_LIGHT, letterSpacing: 2, marginTop: height * 0.006, textShadow: "0 1px 10px rgba(0,0,0,0.9)" }}>
          {website}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// PERSISTENT: Orange energy particles
// =============================================================

const EnergyParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { height, width, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const particles = Array.from({ length: 12 }, (_, i) => {
    const seed = i * 137.508;
    const baseX = ((seed * 7.3) % 100) / 100;
    const baseY = ((seed * 3.7) % 100) / 100;
    const speed = 0.3 + ((seed * 1.9) % 1) * 0.7;
    const size = 2 + ((seed * 2.3) % 1) * 4;

    const x = baseX * width + Math.sin(frame * 0.02 * speed + seed) * 30;
    const y = baseY * height + Math.cos(frame * 0.015 * speed + seed) * 25 - frame * 0.3 * speed;
    const wrappedY = ((y % height) + height) % height;
    const opacity = (Math.sin(frame * 0.05 + seed) * 0.3 + 0.5) * fadeIn * fadeOut;

    return (
      <div
        key={i}
        style={{
          position: "absolute", left: x, top: wrappedY,
          width: size, height: size, borderRadius: "50%",
          backgroundColor: ORANGE, opacity: opacity * 0.6,
          boxShadow: `0 0 ${size * 3}px ${ORANGE}80`,
          pointerEvents: "none" as const,
        }}
      />
    );
  });

  return <AbsoluteFill style={{ pointerEvents: "none" }}>{particles}</AbsoluteFill>;
};

// =============================================================
// PERSISTENT: Brand watermark
// =============================================================

const BrandWatermark: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();

  const enterProg = spring({ frame: frame - 20, fps, config: { damping: 20, stiffness: 80 } });
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div
      style={{
        position: "absolute",
        bottom: height * (1 - SAFE.bottom + 0.01),
        right: width * (1 - SAFE.right),
        opacity: enterProg * fadeOut * 0.5,
        display: "flex", alignItems: "center", gap: 6,
      }}
    >
      <div style={{ width: 6, height: 6, backgroundColor: ORANGE, borderRadius: "50%", boxShadow: `0 0 8px ${ORANGE}60`, transform: `scale(${enterProg})` }} />
      <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: height * 0.011, fontWeight: 600, color: ORANGE_LIGHT, letterSpacing: 2, textTransform: "uppercase", opacity: enterProg, transform: `translateX(${interpolate(enterProg, [0, 1], [8, 0])}px)`, textShadow: "0 1px 8px rgba(0,0,0,0.9)" }}>
        SW Projektentwicklung
      </span>
    </div>
  );
};

// =============================================================
// MAIN COMPOSITION
// =============================================================

export const SWSolarVerkaeufer: React.FC<Props> = ({
  transparent = false,
  review,
  hook = { startSec: 0, durationSec: 5, hookWord: "SOLAR", hookSuffix: "?", wordPos: P0, subtitle: "Jeder will dir was verkaufen", subtitlePos: P0 },
  problem = { startSec: 5, durationSec: 4, item1: "Falsche Berater", item1Pos: P0, item2: "Keine Erfahrung", item2Pos: P0, item3: "Keine Transparenz", item3Pos: P0 },
  lowerThird = { startSec: 9, durationSec: 3.9, name: "Fabrice Stradinger", title: "Gründer & Geschäftsführer · SW Projektentwicklung", cardPos: P0 },
  statCounter = { startSec: 12.9, durationSec: 5, statNumber: 180, statSuffix: "+", numberPos: P0, statLabel: "Projekte", labelPos: P0, statSublabel: "erfolgreich in der Region", sublabelPos: P0 },
  threeComponents = { startSec: 20, durationSec: 9, titleNumber: "3", titleSubtext: "Bauteile — mehr nicht.", titlePos: P0, comp1Icon: "☀️", comp1Label: "Solarmodul", comp1Desc: "Strom erzeugen", comp1Pos: P0, comp2Icon: "🔋", comp2Label: "Stromspeicher", comp2Desc: "Energie speichern", comp2Pos: P0, comp3Icon: "⚡", comp3Label: "Wechselrichter", comp3Desc: "Strom umwandeln", comp3Pos: P0 },
  geldSparen = { startSec: 29, durationSec: 5.5, symbol: "€", symbolPos: P0, mainText: "Jeden Monat sparen", mainTextPos: P0, subText: "Bares Geld mit Solar", subTextPos: P0 },
  fullService = { startSec: 34.5, durationSec: 6.2, title: "Full Service", titlePos: P0, item1: "Alles aus einer Hand", item1Pos: P0, item2: "Keine Subunternehmer", item2Pos: P0, item3: "Persönliche Beratung", item3Pos: P0, item4: "Volle Betreuung nach Montage", item4Pos: P0 },
  cta = { startSec: 40.7, durationSec: 6.3, introText: "Schreib uns einfach", introPos: P0, bubbleText: "SOLAR", bubblePos: P0, arrowSymbol: "↓", arrowPos: P0, brandName: "SW Projektentwicklung", brandPos: P0, website: "sw-projektentwicklung.com", websitePos: P0 },
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/sw-projektentwicklung-solar-verkaeufer/solar-verkaeufer.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.15)" }} />
          </AbsoluteFill>
        )}

        <EnergyParticles />
        <BrandWatermark />

        <Sequence from={s(hook.startSec)} durationInFrames={s(hook.durationSec)}>
          <HookScene hookWord={hook.hookWord} hookSuffix={hook.hookSuffix} wordPos={hook.wordPos} subtitle={hook.subtitle} subtitlePos={hook.subtitlePos} />
        </Sequence>

        <Sequence from={s(problem.startSec)} durationInFrames={s(problem.durationSec)}>
          <ProblemScene item1={problem.item1} item1Pos={problem.item1Pos} item2={problem.item2} item2Pos={problem.item2Pos} item3={problem.item3} item3Pos={problem.item3Pos} />
        </Sequence>

        <Sequence from={s(lowerThird.startSec)} durationInFrames={s(lowerThird.durationSec)}>
          <LowerThirdScene name={lowerThird.name} title={lowerThird.title} cardPos={lowerThird.cardPos} />
        </Sequence>

        <Sequence from={s(statCounter.startSec)} durationInFrames={s(statCounter.durationSec)}>
          <StatCounter statNumber={statCounter.statNumber} statSuffix={statCounter.statSuffix} numberPos={statCounter.numberPos} statLabel={statCounter.statLabel} labelPos={statCounter.labelPos} statSublabel={statCounter.statSublabel} sublabelPos={statCounter.sublabelPos} />
        </Sequence>

        <Sequence from={s(threeComponents.startSec)} durationInFrames={s(threeComponents.durationSec)}>
          <ThreeComponents
            titleNumber={threeComponents.titleNumber} titleSubtext={threeComponents.titleSubtext} titlePos={threeComponents.titlePos}
            comp1Icon={threeComponents.comp1Icon} comp1Label={threeComponents.comp1Label} comp1Desc={threeComponents.comp1Desc} comp1Pos={threeComponents.comp1Pos}
            comp2Icon={threeComponents.comp2Icon} comp2Label={threeComponents.comp2Label} comp2Desc={threeComponents.comp2Desc} comp2Pos={threeComponents.comp2Pos}
            comp3Icon={threeComponents.comp3Icon} comp3Label={threeComponents.comp3Label} comp3Desc={threeComponents.comp3Desc} comp3Pos={threeComponents.comp3Pos}
          />
        </Sequence>

        <Sequence from={s(geldSparen.startSec)} durationInFrames={s(geldSparen.durationSec)}>
          <GeldSparen symbol={geldSparen.symbol} symbolPos={geldSparen.symbolPos} mainText={geldSparen.mainText} mainTextPos={geldSparen.mainTextPos} subText={geldSparen.subText} subTextPos={geldSparen.subTextPos} />
        </Sequence>

        <Sequence from={s(fullService.startSec)} durationInFrames={s(fullService.durationSec)}>
          <FullService title={fullService.title} titlePos={fullService.titlePos} item1={fullService.item1} item1Pos={fullService.item1Pos} item2={fullService.item2} item2Pos={fullService.item2Pos} item3={fullService.item3} item3Pos={fullService.item3Pos} item4={fullService.item4} item4Pos={fullService.item4Pos} />
        </Sequence>

        <Sequence from={s(cta.startSec)} durationInFrames={s(cta.durationSec)}>
          <CTAScene introText={cta.introText} introPos={cta.introPos} bubbleText={cta.bubbleText} bubblePos={cta.bubblePos} arrowSymbol={cta.arrowSymbol} arrowPos={cta.arrowPos} brandName={cta.brandName} brandPos={cta.brandPos} website={cta.website} websitePos={cta.websitePos} />
        </Sequence>

        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            showFaceZone={review.showFaceZone ?? true}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
