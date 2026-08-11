// ============================================================
// NIRO — "Praktikant Reel" Overlay
// KRANK: Over-the-top animations, clean & hochwertig
// 9:16 portrait, ~36s @ 30fps, transparent overlay on video
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
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("niro-demo", brandJson as any);

// --- Load fonts ---
const { fontFamily: robotoFamily } = loadRoboto();

const MEUTAS_FACES = [
  { weight: 400, file: "Meutas-Regular.otf" },
  { weight: 500, file: "Meutas-Medium.otf" },
  { weight: 600, file: "Meutas-SemiBold.otf" },
  { weight: 700, file: "Meutas-Bold.otf" },
  { weight: 800, file: "Meutas-ExtraBold.otf" },
  { weight: 900, file: "Meutas-Black.otf" },
] as const;

for (const face of MEUTAS_FACES) {
  const style = document.createElement("style");
  style.textContent = `@font-face { font-family: "Meutas"; font-weight: ${face.weight}; src: url("${staticFile(`fonts/${face.file}`)}") format("opentype"); }`;
  document.head.appendChild(style);
}

const FONT_TITLE = '"Meutas", sans-serif';
const FONT_BODY = `${robotoFamily}, sans-serif`;

// =============================================================
// SCHEMA
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
  mainWord: z.string().describe("Hauptwort"),
  subtitle: z.string().describe("Untertitel"),
  wordPos: posSchema.describe("Position: Hauptwort"),
  subtitlePos: posSchema.describe("Position: Untertitel"),
});

const daySchema = timingSchema.extend({
  dayLabel: z.string().describe("Tag-Label"),
  activityIcon: z.string().describe("Aktivitäts-Icon"),
  activityName: z.string().describe("Aktivitäts-Name"),
  activityDesc: z.string().describe("Beschreibung"),
  cardPos: posSchema.describe("Position: Karte"),
});

const outroSchema = timingSchema.extend({
  mainText: z.string().describe("Haupttext"),
  subText: z.string().describe("Untertext"),
  textPos: posSchema.describe("Position: Text"),
});

const ctaSchema = timingSchema.extend({
  brandName: z.string().describe("Markenname"),
  ctaText: z.string().describe("CTA-Text"),
  brandPos: posSchema.describe("Position: Marke"),
});

export const praktikantReelSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Szene 1: Hook"),
  montag: daySchema.describe("Szene 2: Montag — Vertrieb"),
  dienstag: daySchema.describe("Szene 3: Dienstag — Filmdreh"),
  mittwoch: daySchema.describe("Szene 4: Mittwoch — Design"),
  donnerstag: daySchema.describe("Szene 5: Donnerstag — Videoschnitt"),
  freitag: daySchema.describe("Szene 6: Freitag — Marketing & AI"),
  outro: outroSchema.describe("Szene 7: Outro"),
  cta: ctaSchema.describe("Szene 8: CTA"),
});

export type Props = z.infer<typeof praktikantReelSchema>;
type Pos = { x: number; y: number };

// =============================================================
// CONSTANTS
// =============================================================

// NIRO Media Brand Colors
const GREEN = "#A2C73D";
const GREEN_LIGHT = "#C6DA87";
const DARK = "#1A211D";
const BLUE = "#85CFF4";
const LIGHT_BLUE = "#CCEAFC";
const WHITE = "#FFFFFF";

const SAFE = { top: 0.07, bottom: 0.575, left: 0.05, right: 0.95 };
const FACE_BOTTOM = 0.45;

const SLAM_SPRING = { damping: 6, stiffness: 280 };
const PUNCH_SPRING = { damping: 10, stiffness: 200 };
const BOUNCE_SPRING = { damping: 5, stiffness: 300 };
const SMOOTH_SPRING = { damping: 14, stiffness: 120 };

// =============================================================
// HELPERS
// =============================================================

const useExit = (exitFrames = 8) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);
  const exitProg = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitSlide = interpolate(exitProg, [0, 1], [50, 0]);
  const exitScale = interpolate(exitProg, [0, 1], [0.8, 1]);
  return { exitProg, exitSlide, exitScale };
};

// =============================================================
// SCENE 1: HOOK — "PRAKTIKUM" slam
// =============================================================

const HookScene: React.FC<{
  mainWord: string; subtitle: string;
  wordPos: Pos; subtitlePos: Pos;
}> = ({ mainWord, subtitle, wordPos, subtitlePos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const slamProg = spring({ frame, fps, config: { damping: 7, stiffness: 320 } });
  const scale = interpolate(slamProg, [0, 1], [5, 1]);
  const rotate = interpolate(slamProg, [0, 1], [-15, 0]);

  const shakeX = frame < 10 ? Math.sin(frame * 9) * (10 - frame) * 2 : 0;
  const shakeY = frame < 10 ? Math.cos(frame * 7) * (10 - frame) * 1.5 : 0;

  const flashOpacity = interpolate(frame, [0, 2, 6], [0.7, 0.4, 0], { extrapolateRight: "clamp" });
  const subProg = spring({ frame: frame - 12, fps, config: PUNCH_SPRING });

  const ringProg = spring({ frame: frame - 2, fps, config: { damping: 22, stiffness: 50 } });
  const ringScale = interpolate(ringProg, [0, 1], [0, 4]);
  const ringOpacity = interpolate(ringProg, [0, 0.3, 1], [0.9, 0.4, 0]);

  const lineProg = spring({ frame: frame - 8, fps, config: SMOOTH_SPRING });

  const centerY = ((FACE_BOTTOM + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <AbsoluteFill style={{ backgroundColor: GREEN, opacity: flashOpacity }} />

      <div
        style={{
          position: "absolute", top: centerY + wordPos.y, left: centerX + wordPos.x,
          width: width * 0.3, height: width * 0.3, borderRadius: "50%",
          border: `3px solid ${BLUE}`,
          transform: `translate(-50%, -50%) scale(${ringScale * exitScale})`,
          opacity: ringOpacity * exitProg * 0.7,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: centerY - height * 0.04 + wordPos.y,
          left: centerX + wordPos.x,
          transform: `translate(-50%, -50%) scale(${scale * exitScale}) rotate(${rotate}deg) translate(${shakeX}px, ${shakeY}px)`,
          fontFamily: FONT_TITLE,
          fontSize: height * 0.065,
          fontWeight: 900,
          color: WHITE,
          letterSpacing: 6,
          textShadow: `0 4px 30px rgba(0,0,0,0.9), 0 0 60px ${GREEN}80`,
          opacity: slamProg * exitProg,
        }}
      >
        {mainWord}
      </div>

      <div
        style={{
          position: "absolute",
          top: centerY + height * 0.015 + wordPos.y,
          left: centerX,
          width: interpolate(lineProg, [0, 1], [0, width * 0.35]),
          height: 3,
          background: `linear-gradient(90deg, transparent, ${BLUE}, transparent)`,
          transform: "translateX(-50%)",
          opacity: lineProg * exitProg,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: centerY + height * 0.035 + subtitlePos.y,
          left: centerX + subtitlePos.x,
          transform: `translate(-50%, 0) translateY(${interpolate(subProg, [0, 1], [25, 0])}px) scale(${exitScale})`,
          opacity: subProg * exitProg,
          fontFamily: FONT_BODY,
          fontSize: height * 0.018,
          fontWeight: 500,
          color: GREEN_LIGHT,
          letterSpacing: 4,
          textTransform: "uppercase" as const,
          textShadow: "0 2px 20px rgba(0,0,0,0.9)",
        }}
      >
        {subtitle}
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// DAY CARD SCENE — reusable for each day
// =============================================================

const DayCardScene: React.FC<{
  dayLabel: string;
  activityIcon: string;
  activityName: string;
  activityDesc: string;
  cardPos: Pos;
}> = ({ dayLabel, activityIcon, activityName, activityDesc, cardPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide } = useExit(8);

  const safeLeft = width * SAFE.left;
  const safeWidth = width * (SAFE.right - SAFE.left);

  const badgeProg = spring({ frame: frame - 2, fps, config: SLAM_SPRING });
  const badgeScale = interpolate(badgeProg, [0, 1], [0, 1]);
  const badgeRotate = interpolate(badgeProg, [0, 1], [-20, 0]);

  const cardProg = spring({ frame: frame - 6, fps, config: PUNCH_SPRING });
  const cardWidthAnim = interpolate(cardProg, [0, 1], [0, safeWidth * 0.9]);

  const iconProg = spring({ frame: frame - 8, fps, config: BOUNCE_SPRING });
  const descProg = spring({ frame: frame - 14, fps, config: SMOOTH_SPRING });
  const lineProg = spring({ frame: frame - 4, fps, config: { damping: 14, stiffness: 100 } });

  const badgeY = FACE_BOTTOM * height + height * 0.01;
  const cardY = FACE_BOTTOM * height + height * 0.05;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: badgeY + cardPos.y,
          left: safeLeft + width * 0.03 + cardPos.x,
          transform: `scale(${badgeScale * (exitProg < 1 ? exitProg : 1)}) rotate(${badgeRotate}deg)`,
          opacity: badgeProg * exitProg,
          transformOrigin: "left center",
        }}
      >
        <div
          style={{
            backgroundColor: GREEN,
            borderRadius: 25,
            padding: `${height * 0.007}px ${height * 0.025}px`,
            boxShadow: `0 4px 20px rgba(0,0,0,0.4), 0 0 25px ${GREEN}40`,
            display: "inline-block",
          }}
        >
          <span
            style={{
              fontFamily: FONT_TITLE,
              fontSize: height * 0.017,
              fontWeight: 800,
              color: WHITE,
              letterSpacing: 3,
              textTransform: "uppercase" as const,
            }}
          >
            {dayLabel}
          </span>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: cardY + cardPos.y,
          left: safeLeft + width * 0.02 + cardPos.x,
          width: cardWidthAnim,
          opacity: cardProg * exitProg,
          transform: `translateY(${interpolate(exitProg, [0, 1], [exitSlide, 0])}px)`,
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(26, 33, 29, 0.85)",
            backdropFilter: `blur(${16 * cardProg}px)`,
            borderRadius: 14,
            padding: `${height * 0.016}px ${height * 0.025}px`,
            borderLeft: `4px solid ${BLUE}`,
            boxShadow: `0 4px 30px rgba(0,0,0,0.5), 0 0 20px ${BLUE}15`,
            display: "flex",
            alignItems: "center",
            gap: width * 0.04,
            overflow: "hidden",
            position: "relative" as const,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: `${interpolate(lineProg, [0, 1], [0, 100])}%`,
              height: 2,
              background: `linear-gradient(90deg, ${BLUE}, ${GREEN}, transparent)`,
            }}
          />

          <div
            style={{
              fontSize: height * 0.038,
              transform: `scale(${interpolate(iconProg, [0, 1], [0, 1.1])}) rotate(${interpolate(iconProg, [0, 1], [-180, 0])}deg)`,
              filter: `drop-shadow(0 0 8px ${BLUE}60)`,
              flexShrink: 0,
            }}
          >
            {activityIcon}
          </div>

          <div>
            <div
              style={{
                fontFamily: FONT_TITLE,
                fontSize: height * 0.024,
                fontWeight: 800,
                color: WHITE,
                textShadow: "0 2px 10px rgba(0,0,0,0.5)",
                transform: `translateX(${interpolate(cardProg, [0, 1], [30, 0])}px)`,
              }}
            >
              {activityName}
            </div>
            <div
              style={{
                fontFamily: FONT_BODY,
                fontSize: height * 0.013,
                fontWeight: 500,
                color: BLUE,
                letterSpacing: 1,
                marginTop: 3,
                opacity: descProg,
                transform: `translateX(${interpolate(descProg, [0, 1], [15, 0])}px)`,
              }}
            >
              {activityDesc}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 7: OUTRO — "RICHTIG COOL!"
// =============================================================

const OutroScene: React.FC<{
  mainText: string; subText: string; textPos: Pos;
}> = ({ mainText, subText, textPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(10);

  const centerY = ((FACE_BOTTOM + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  const mainProg = spring({ frame: frame - 2, fps, config: SLAM_SPRING });
  const mainScale = interpolate(mainProg, [0, 1], [4, 1]);
  const subProg = spring({ frame: frame - 12, fps, config: SMOOTH_SPRING });

  const shakeX = frame < 12 ? Math.sin(frame * 8) * (12 - frame) * 1.5 : 0;
  const glowPulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: centerY + textPos.y,
          left: centerX + textPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          textAlign: "center" as const,
        }}
      >
        <div
          style={{
            fontFamily: FONT_TITLE,
            fontSize: height * 0.05,
            fontWeight: 900,
            color: GREEN,
            lineHeight: 1.1,
            transform: `scale(${mainScale}) translateX(${shakeX}px)`,
            opacity: mainProg,
            textShadow: `0 0 ${40 * glowPulse}px ${GREEN}60, 0 4px 20px rgba(0,0,0,0.8)`,
            letterSpacing: 2,
          }}
        >
          {mainText}
        </div>
        <div
          style={{
            fontFamily: FONT_BODY,
            fontSize: height * 0.018,
            fontWeight: 500,
            color: WHITE,
            letterSpacing: 4,
            textTransform: "uppercase" as const,
            marginTop: height * 0.015,
            opacity: subProg,
            transform: `translateY(${interpolate(subProg, [0, 1], [20, 0])}px)`,
            textShadow: "0 2px 15px rgba(0,0,0,0.9)",
          }}
        >
          {subText}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// SCENE 8: CTA — "NeuroMedia"
// =============================================================

const CTAScene: React.FC<{
  brandName: string; ctaText: string; brandPos: Pos;
}> = ({ brandName, ctaText, brandPos }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitScale } = useExit(6);

  const centerY = ((FACE_BOTTOM + SAFE.bottom) / 2) * height;
  const centerX = width / 2;

  const brandProg = spring({ frame: frame - 2, fps, config: SLAM_SPRING });
  const brandScale = interpolate(brandProg, [0, 1], [5, 1]);
  const ctaProg = spring({ frame: frame - 15, fps, config: BOUNCE_SPRING });
  const arrowProg = spring({ frame: frame - 8, fps, config: PUNCH_SPRING });

  const pulseScale = 1 + Math.sin(frame * 0.2) * 0.04;
  const arrowBounce = Math.sin(frame * 0.3) * 5;
  const glowPulse = Math.sin(frame * 0.15) * 0.4 + 0.6;

  return (
    <AbsoluteFill style={{ opacity: exitProg }}>
      <div
        style={{
          position: "absolute",
          top: centerY + brandPos.y,
          left: centerX + brandPos.x,
          transform: `translate(-50%, -50%) scale(${exitScale})`,
          textAlign: "center" as const,
        }}
      >
        <div
          style={{
            fontFamily: FONT_TITLE,
            fontSize: height * 0.035,
            color: BLUE,
            opacity: arrowProg,
            transform: `translateY(${interpolate(arrowProg, [0, 1], [-30, arrowBounce])}px)`,
            filter: `drop-shadow(0 0 10px ${BLUE}80)`,
            marginBottom: height * 0.01,
          }}
        >
          ↓
        </div>

        <div
          style={{
            fontFamily: FONT_TITLE,
            fontSize: height * 0.045,
            fontWeight: 900,
            color: WHITE,
            transform: `scale(${brandScale * pulseScale})`,
            opacity: brandProg,
            textShadow: `0 0 ${30 * glowPulse}px ${GREEN}60, 0 4px 20px rgba(0,0,0,0.8)`,
            letterSpacing: 3,
          }}
        >
          {brandName}
        </div>

        <div
          style={{
            display: "inline-block",
            marginTop: height * 0.015,
            opacity: ctaProg,
            transform: `scale(${interpolate(ctaProg, [0, 1], [0.5, 1]) * pulseScale})`,
          }}
        >
          <div
            style={{
              backgroundColor: GREEN,
              borderRadius: 30,
              padding: `${height * 0.01}px ${height * 0.04}px`,
              boxShadow: `0 4px 25px rgba(0,0,0,0.4), 0 0 ${25 * glowPulse}px ${GREEN}40`,
            }}
          >
            <span
              style={{
                fontFamily: FONT_TITLE,
                fontSize: height * 0.017,
                fontWeight: 700,
                color: WHITE,
                letterSpacing: 2,
                textTransform: "uppercase" as const,
              }}
            >
              {ctaText}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// AMBIENT PARTICLES (Orange + Cyan)
// =============================================================

const AmbientParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { height, width, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const particles = Array.from({ length: 10 }, (_, i) => {
    const seed = i * 137.508;
    const baseX = ((seed * 7.3) % 100) / 100;
    const baseY = ((seed * 3.7) % 100) / 100;
    const speed = 0.3 + ((seed * 1.9) % 1) * 0.7;
    const size = 2 + ((seed * 2.3) % 1) * 3;
    const isBlue = i % 3 === 0;

    const x = baseX * width + Math.sin(frame * 0.02 * speed + seed) * 25;
    const y =
      baseY * height +
      Math.cos(frame * 0.015 * speed + seed) * 20 -
      frame * 0.25 * speed;
    const wrappedY = ((y % height) + height) % height;
    const opacity =
      (Math.sin(frame * 0.05 + seed) * 0.3 + 0.5) * fadeIn * fadeOut;
    const color = isBlue ? BLUE : GREEN;

    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: wrappedY,
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: color,
          opacity: opacity * 0.5,
          boxShadow: `0 0 ${size * 3}px ${color}60`,
          pointerEvents: "none" as const,
        }}
      />
    );
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {particles}
    </AbsoluteFill>
  );
};

// =============================================================
// BRAND WATERMARK — "NeuroMedia"
// =============================================================

const BrandWatermark: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();

  const enterProg = spring({
    frame: frame - 25,
    fps,
    config: { damping: 20, stiffness: 80 },
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 30, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: height * (1 - SAFE.bottom + 0.01),
        right: width * (1 - SAFE.right),
        opacity: enterProg * fadeOut * 0.45,
        display: "flex",
        alignItems: "center",
        gap: 6,
      }}
    >
      <div
        style={{
          width: 6,
          height: 6,
          backgroundColor: BLUE,
          borderRadius: "50%",
          boxShadow: `0 0 8px ${BLUE}60`,
          transform: `scale(${enterProg})`,
        }}
      />
      <span
        style={{
          fontFamily: FONT_BODY,
          fontSize: height * 0.011,
          fontWeight: 500,
          color: BLUE,
          letterSpacing: 2,
          textTransform: "uppercase" as const,
          opacity: enterProg,
          transform: `translateX(${interpolate(enterProg, [0, 1], [8, 0])}px)`,
          textShadow: "0 1px 8px rgba(0,0,0,0.9)",
        }}
      >
        NeuroMedia
      </span>
    </div>
  );
};

// =============================================================
// MAIN COMPOSITION
// =============================================================

export const PraktikantReel: React.FC<Props> = ({
  transparent = false,
  review,
  hook = {
    startSec: 0,
    durationSec: 4.5,
    mainWord: "PRAKTIKUM",
    subtitle: "Eine Woche Marketingagentur",
    wordPos: P0,
    subtitlePos: P0,
  },
  montag = {
    startSec: 4.5,
    durationSec: 3.5,
    dayLabel: "MONTAG",
    activityIcon: "\u{1F4DE}",
    activityName: "Cold Calling",
    activityDesc: "Vertrieb wie Jordan Belfort",
    cardPos: P0,
  },
  dienstag = {
    startSec: 8,
    durationSec: 4.5,
    dayLabel: "DIENSTAG",
    activityIcon: "\u{1F3AC}",
    activityName: "Filmdreh",
    activityDesc: "Kfz-Werkstatt \u00b7 Selber filmen",
    cardPos: P0,
  },
  mittwoch = {
    startSec: 12.5,
    durationSec: 4.3,
    dayLabel: "MITTWOCH",
    activityIcon: "\u{1F3A8}",
    activityName: "Canva Design",
    activityDesc: "Behind-the-Scenes Post",
    cardPos: P0,
  },
  donnerstag = {
    startSec: 16.8,
    durationSec: 5.2,
    dayLabel: "DONNERSTAG",
    activityIcon: "\u2702\uFE0F",
    activityName: "Video schneiden",
    activityDesc: "Kreativer Freiraum",
    cardPos: P0,
  },
  freitag = {
    startSec: 22,
    durationSec: 7,
    dayLabel: "FREITAG",
    activityIcon: "\u{1F916}",
    activityName: "Marketing & AI",
    activityDesc: "KI-Nutzen im Marketing gelernt",
    cardPos: P0,
  },
  outro = {
    startSec: 29,
    durationSec: 4,
    mainText: "RICHTIG COOL!",
    subText: "Danke ans Team",
    textPos: P0,
  },
  cta = {
    startSec: 33,
    durationSec: 2.8,
    brandName: "NeuroMedia",
    ctaText: "Jetzt bewerben",
    brandPos: P0,
  },
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/niro-demos/praktikant-reel.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.1)" }} />
          </AbsoluteFill>
        )}

        <AmbientParticles />

        <Sequence from={s(hook.startSec)} durationInFrames={s(hook.durationSec)}>
          <HookScene
            mainWord={hook.mainWord}
            subtitle={hook.subtitle}
            wordPos={hook.wordPos}
            subtitlePos={hook.subtitlePos}
          />
        </Sequence>

        <Sequence from={s(montag.startSec)} durationInFrames={s(montag.durationSec)}>
          <DayCardScene
            dayLabel={montag.dayLabel}
            activityIcon={montag.activityIcon}
            activityName={montag.activityName}
            activityDesc={montag.activityDesc}
            cardPos={montag.cardPos}
          />
        </Sequence>

        <Sequence from={s(dienstag.startSec)} durationInFrames={s(dienstag.durationSec)}>
          <DayCardScene
            dayLabel={dienstag.dayLabel}
            activityIcon={dienstag.activityIcon}
            activityName={dienstag.activityName}
            activityDesc={dienstag.activityDesc}
            cardPos={dienstag.cardPos}
          />
        </Sequence>

        <Sequence from={s(mittwoch.startSec)} durationInFrames={s(mittwoch.durationSec)}>
          <DayCardScene
            dayLabel={mittwoch.dayLabel}
            activityIcon={mittwoch.activityIcon}
            activityName={mittwoch.activityName}
            activityDesc={mittwoch.activityDesc}
            cardPos={mittwoch.cardPos}
          />
        </Sequence>

        <Sequence from={s(donnerstag.startSec)} durationInFrames={s(donnerstag.durationSec)}>
          <DayCardScene
            dayLabel={donnerstag.dayLabel}
            activityIcon={donnerstag.activityIcon}
            activityName={donnerstag.activityName}
            activityDesc={donnerstag.activityDesc}
            cardPos={donnerstag.cardPos}
          />
        </Sequence>

        <Sequence from={s(freitag.startSec)} durationInFrames={s(freitag.durationSec)}>
          <DayCardScene
            dayLabel={freitag.dayLabel}
            activityIcon={freitag.activityIcon}
            activityName={freitag.activityName}
            activityDesc={freitag.activityDesc}
            cardPos={freitag.cardPos}
          />
        </Sequence>

        <Sequence from={s(outro.startSec)} durationInFrames={s(outro.durationSec)}>
          <OutroScene
            mainText={outro.mainText}
            subText={outro.subText}
            textPos={outro.textPos}
          />
        </Sequence>

        <Sequence from={s(cta.startSec)} durationInFrames={s(cta.durationSec)}>
          <CTAScene
            brandName={cta.brandName}
            ctaText={cta.ctaText}
            brandPos={cta.brandPos}
          />
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
