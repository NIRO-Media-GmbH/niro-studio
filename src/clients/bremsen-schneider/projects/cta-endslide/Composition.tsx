// ============================================================
// Bremsen Schneider — CTA End Slide
// Recruiting KFZ Mechatroniker: Azubi, Fachkraft, Meister
// 9:16 portrait, 10s @ 30fps, standalone (not transparent)
// Pipeline line: centered logo → 90° left → trunk → branches → 90° right → CTA
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
} from "remotion";
import { z } from "zod";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("bremsen-schneider", brandJson as any);
const { fontFamily: robotoFamily } = loadRoboto();

// --- Colors ---
const BLUE = "#006BBB";
const DARK_BLUE = "#004A82";
const YELLOW = "#F9D600";
const WHITE = "#FFFFFF";

// --- Spring configs ---
const SMOOTH_SPRING = { damping: 18, stiffness: 120, mass: 1 };
const GENTLE_SPRING = { damping: 22, stiffness: 100, mass: 1 };
const SNAPPY_SPRING = { damping: 14, stiffness: 160, mass: 1 };

// --- Schema ---
const posSchema = z.object({ x: z.number(), y: z.number() });

export const bremsenSchneiderCtaSchema = projectPropsSchema.extend({
  logoPos: posSchema,
  headerText: z.string(),
  headerPos: posSchema,
  job1: z.string(),
  job2: z.string(),
  job3: z.string(),
  jobsPos: posSchema,
  ctaText: z.string(),
  ctaPos: posSchema,
  website: z.string(),
  websitePos: posSchema,
  phone: z.string(),
  phonePos: posSchema,
});

export type Props = z.infer<typeof bremsenSchneiderCtaSchema>;

// --- Layout constants (px in 1080×1920) ---
const CENTER_X = 540;
const TRUNK_X = 155;
const BRANCH_LEN = 140;
const JOB_TEXT_X = TRUNK_X + BRANCH_LEN + 25;

// Connector: logo center → trunk (two 90° segments)
const CONN_V_START = 350; // just below logo
const CONN_Y = 420; // horizontal connector y

// Jobs — even 170px spacing
const JOB_ROWS = [{ y: 590 }, { y: 760 }, { y: 930 }];

const TRUNK_END_Y = 1100; // 930 + 170 = equal spacing
const CONVERGE_STOP_Y = 1210;
const DOT_RADIUS = 7;

// ============================================================
// Animated SVG line segment
// ============================================================
const AnimatedPath: React.FC<{
  d: string;
  progress: number;
  length: number;
  strokeWidth?: number;
  color?: string;
}> = ({ d, progress, length, strokeWidth = 3, color = YELLOW }) => (
  <path
    d={d}
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="square"
    strokeLinejoin="miter"
    strokeDasharray={length}
    strokeDashoffset={length * (1 - progress)}
  />
);

// ============================================================
// Junction dot with glow ring
// ============================================================
const JunctionDot: React.FC<{
  cx: number;
  cy: number;
  progress: number;
}> = ({ cx, cy, progress }) => (
  <>
    <circle
      cx={cx}
      cy={cy}
      r={DOT_RADIUS * progress}
      fill={YELLOW}
      opacity={progress}
    />
    <circle
      cx={cx}
      cy={cy}
      r={DOT_RADIUS * 2 * progress}
      fill="none"
      stroke={YELLOW}
      strokeWidth={1.5}
      opacity={progress * 0.3}
    />
  </>
);

// ============================================================
// Background
// ============================================================
const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const gradAngle = interpolate(frame, [0, durationInFrames], [145, 155]);
  const circleProg = spring({ frame, fps, config: GENTLE_SPRING, delay: 10 });

  return (
    <AbsoluteFill>
      <div
        style={{
          width: "100%",
          height: "100%",
          background: `linear-gradient(${gradAngle}deg, ${DARK_BLUE} 0%, ${BLUE} 50%, ${DARK_BLUE} 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
          `,
          backgroundSize: "80px 80px",
        }}
      />
      {/* Decorative circle top-right */}
      <div
        style={{
          position: "absolute",
          top: -120,
          right: -100,
          width: 400,
          height: 400,
          borderRadius: "50%",
          border: `2px solid rgba(249,214,0,${0.08 * circleProg})`,
          transform: `scale(${interpolate(circleProg, [0, 1], [0.6, 1])})`,
        }}
      />
    </AbsoluteFill>
  );
};

// ============================================================
// Main Composition
// ============================================================
export const BremsenSchneiderCta: React.FC<Props> = ({
  review,
  transparent,
  logoPos,
  job1,
  job2,
  job3,
  jobsPos,
  ctaText,
  ctaPos,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const jobs = [job1, job2, job3];

  // --- Animation delays (30% faster) ---
  const LOGO_DELAY = 3;
  const CONN_V_DELAY = 7;
  const CONN_H_DELAY = 11;
  const TRUNK_DELAY = 15;
  const BRANCH_BASE = 21;
  const BRANCH_STAGGER = 10;
  const CONVERGE_DELAY = BRANCH_BASE + 3 * BRANCH_STAGGER + 3;
  const MWD_DELAY = CONVERGE_DELAY + 6;
  const CTA_DELAY = MWD_DELAY + 3;
  const CTA_PILL_DELAY = CTA_DELAY + 3;

  // --- Logo ---
  const logoProg = spring({ frame, fps, config: SMOOTH_SPRING, delay: LOGO_DELAY });
  const logoOpacity = interpolate(logoProg, [0, 1], [0, 1]);
  const logoScale = interpolate(logoProg, [0, 1], [0.9, 1]);

  // --- Connector: single path with 90° corner (logo → trunk) ---
  const connProg = spring({ frame, fps, config: GENTLE_SPRING, delay: CONN_V_DELAY });

  // --- Trunk: connector → first branch ---
  const trunkProg1 = spring({ frame, fps, config: GENTLE_SPRING, delay: TRUNK_DELAY });

  // --- Branch progress per job ---
  const branchProgs = JOB_ROWS.map((_, i) =>
    spring({ frame, fps, config: SMOOTH_SPRING, delay: BRANCH_BASE + i * BRANCH_STAGGER })
  );
  const dotProgs = JOB_ROWS.map((_, i) =>
    spring({ frame, fps, config: SNAPPY_SPRING, delay: BRANCH_BASE + i * BRANCH_STAGGER - 3 })
  );

  // Trunk segments between branches
  const trunkSegProgs = JOB_ROWS.map((_, i) =>
    i === 0
      ? trunkProg1
      : spring({ frame, fps, config: GENTLE_SPRING, delay: BRANCH_BASE + (i - 1) * BRANCH_STAGGER + 5 })
  );

  // --- Trunk bottom + converge (single path with 90° corner) ---
  const trunkBottomProg = spring({ frame, fps, config: GENTLE_SPRING, delay: BRANCH_BASE + 2 * BRANCH_STAGGER + 5 });
  const convergeProg = spring({ frame, fps, config: SMOOTH_SPRING, delay: CONVERGE_DELAY });

  // --- (m/w/d) ---
  const mwdProg = spring({ frame, fps, config: GENTLE_SPRING, delay: MWD_DELAY });
  const mwdOpacity = interpolate(mwdProg, [0, 1], [0, 1]);

  // --- CTA ---
  const ctaProg = spring({ frame, fps, config: SNAPPY_SPRING, delay: CTA_DELAY });
  const ctaOpacity = interpolate(ctaProg, [0, 1], [0, 1]);
  const ctaScale = interpolate(ctaProg, [0, 1], [0.85, 1]);
  const pillProg = spring({ frame, fps, config: SMOOTH_SPRING, delay: CTA_PILL_DELAY });
  const pillScaleX = interpolate(pillProg, [0, 1], [0, 1]);
  const ctaDotProg = spring({ frame, fps, config: SNAPPY_SPRING, delay: CTA_DELAY - 2 });

  // --- SVG path definitions ---
  const OV = 10; // overlap to prevent gaps at junctions

  // Connector: single L-shaped path (logo center → 90° corner → trunk)
  const connPath = `M ${CENTER_X} ${CONN_V_START} L ${CENTER_X} ${CONN_Y} L ${TRUNK_X} ${CONN_Y}`;
  const connLen = (CONN_Y - CONN_V_START) + (CENTER_X - TRUNK_X);

  // Trunk: connector → first branch (overlap at both ends)
  const trunk1 = `M ${TRUNK_X} ${CONN_Y - OV} L ${TRUNK_X} ${JOB_ROWS[0].y + OV}`;
  const trunk1Len = JOB_ROWS[0].y - CONN_Y + OV * 2;

  // Trunk segments between branches (overlap at both ends)
  const trunkSegs = JOB_ROWS.slice(1).map((row, i) => {
    const prevY = JOB_ROWS[i].y;
    return {
      d: `M ${TRUNK_X} ${prevY - OV} L ${TRUNK_X} ${row.y + OV}`,
      len: row.y - prevY + OV * 2,
    };
  });

  // Trunk bottom: last branch → converge (overlap at both ends)
  const trunkBottom = `M ${TRUNK_X} ${JOB_ROWS[2].y - OV} L ${TRUNK_X} ${TRUNK_END_Y + OV}`;
  const trunkBottomLen = TRUNK_END_Y - JOB_ROWS[2].y + OV * 2;

  // Converge: L-shaped path with overlap into trunk
  const convergePath = `M ${TRUNK_X} ${TRUNK_END_Y - OV} L ${TRUNK_X} ${TRUNK_END_Y} L ${CENTER_X} ${TRUNK_END_Y} L ${CENTER_X} ${CONVERGE_STOP_Y}`;
  const convergeLen = OV + (CENTER_X - TRUNK_X) + (CONVERGE_STOP_Y - TRUNK_END_Y);

  // Branches: overlap into trunk
  const branches = JOB_ROWS.map((row) => ({
    d: `M ${TRUNK_X - OV} ${row.y} L ${TRUNK_X + BRANCH_LEN} ${row.y}`,
    len: BRANCH_LEN + OV,
  }));

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && <Background />}

        {/* ===== SVG Line System ===== */}
        <svg
          viewBox="0 0 1080 1920"
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        >
          {/* Connector: vertical from logo */}
          {/* Connector: L-shaped path (logo → 90° → trunk), no gap */}
          <AnimatedPath d={connPath} progress={connProg} length={connLen} />

          {/* Dot at connector corner */}
          <JunctionDot cx={CENTER_X} cy={CONN_Y} progress={connProg} />

          {/* Dot at trunk start */}
          <JunctionDot cx={TRUNK_X} cy={CONN_Y} progress={trunkProg1} />

          {/* Trunk: connector → first branch (overlapping) */}
          <AnimatedPath d={trunk1} progress={trunkProg1} length={trunk1Len} />

          {/* Trunk segments between branches (overlapping) */}
          {trunkSegs.map((seg, i) => (
            <AnimatedPath key={`trunk-${i}`} d={seg.d} progress={trunkSegProgs[i + 1]} length={seg.len} />
          ))}

          {/* Trunk bottom → converge (overlapping) */}
          <AnimatedPath d={trunkBottom} progress={trunkBottomProg} length={trunkBottomLen} />

          {/* Converge: L-shaped path (trunk → 90° → CTA), no gap */}
          <AnimatedPath d={convergePath} progress={convergeProg} length={convergeLen} />

          {/* Branch lines (overlapping into trunk) */}
          {branches.map((br, i) => (
            <AnimatedPath key={`branch-${i}`} d={br.d} progress={branchProgs[i]} length={br.len} />
          ))}

          {/* Junction dots at branches */}
          {JOB_ROWS.map((row, i) => (
            <JunctionDot key={`dot-${i}`} cx={TRUNK_X} cy={row.y} progress={dotProgs[i]} />
          ))}

          {/* Dots at converge corners */}
          <JunctionDot cx={TRUNK_X} cy={TRUNK_END_Y} progress={convergeProg} />
          <JunctionDot cx={CENTER_X} cy={TRUNK_END_Y} progress={convergeProg} />
          <JunctionDot cx={CENTER_X} cy={CONVERGE_STOP_Y} progress={ctaDotProg} />
        </svg>

        {/* ===== Logo — centered ===== */}
        <div
          style={{
            position: "absolute",
            top: `calc(11% + ${logoPos.y}px)`,
            left: "50%",
            transform: `translateX(calc(-50% + ${logoPos.x}px)) scale(${logoScale})`,
            opacity: logoOpacity,
          }}
        >
          <Img
            src={staticFile("clients/bremsen-schneider/logo.png")}
            style={{
              width: 340,
              height: "auto",
              filter: "drop-shadow(0 4px 20px rgba(0,0,0,0.3))",
            }}
          />
        </div>

        {/* ===== Job labels — all left-aligned ===== */}
        {jobs.map((job, i) => {
          const row = JOB_ROWS[i];
          const delay = BRANCH_BASE + i * BRANCH_STAGGER + 3;
          const textProg = spring({ frame, fps, config: SNAPPY_SPRING, delay });
          const textOpacity = interpolate(textProg, [0, 1], [0, 1]);
          const textSlide = interpolate(textProg, [0, 1], [25, 0]);

          return (
            <div
              key={job}
              style={{
                position: "absolute",
                top: row.y / 1920 * 100 + "%",
                left: JOB_TEXT_X / 1080 * 100 + "%",
                transform: `translateY(-50%) translateX(${textSlide}px) translateX(${jobsPos.x}px) translateY(${jobsPos.y}px)`,
                opacity: textOpacity,
                fontFamily: robotoFamily,
                fontSize: 60,
                fontWeight: 700,
                color: WHITE,
                letterSpacing: 5,
                textTransform: "uppercase",
                textShadow: "0 2px 15px rgba(0,0,0,0.2)",
              }}
            >
              {job}
            </div>
          );
        })}

        {/* ===== (m/w/d) — above CTA ===== */}
        <div
          style={{
            position: "absolute",
            top: `calc(66% + ${ctaPos.y}px)`,
            left: "50%",
            transform: "translateX(-50%)",
            fontFamily: robotoFamily,
            fontSize: 22,
            fontWeight: 300,
            color: `${WHITE}AA`,
            letterSpacing: 5,
            textTransform: "uppercase",
            opacity: mwdOpacity,
          }}
        >
          (m/w/d)
        </div>

        {/* ===== CTA pill ===== */}
        <div
          style={{
            position: "absolute",
            top: `calc(70% + ${ctaPos.y}px)`,
            left: "50%",
            transform: `translateX(calc(-50% + ${ctaPos.x}px)) scale(${ctaScale})`,
            opacity: ctaOpacity,
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: "-16px -40px",
              backgroundColor: YELLOW,
              borderRadius: 50,
              transform: `scaleX(${pillScaleX})`,
              boxShadow: "0 4px 30px rgba(249,214,0,0.3)",
            }}
          />
          <div
            style={{
              position: "relative",
              fontFamily: robotoFamily,
              fontSize: 52,
              fontWeight: 900,
              color: DARK_BLUE,
              letterSpacing: 3,
              textTransform: "uppercase",
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {ctaText}
          </div>
        </div>

        {/* Review overlay */}
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
