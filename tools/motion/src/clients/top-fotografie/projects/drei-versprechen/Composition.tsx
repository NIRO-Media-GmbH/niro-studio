// ============================================================
// Top Fotografie — Drei Versprechen
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait (1080×1920), 30fps, 20s
// Expanding list box — items appear one by one
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/OpenSans";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { ITEMS, TOTAL_DURATION_SEC } from "./transcript";
import type { ListItem } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

// --- Brand Colors ---
const PRIMARY = "#104697";
const WHITE = "#FFFFFF";

// --- Spring Configs ---
const ITEM_SPRING = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const EXIT_SPRING = { damping: 12, stiffness: 160, mass: 1 };

const EXIT_LEAD = 15; // frames before end

// --- Schemas ---

const listItemSchema = z.object({
  text: z.string().describe("Text"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
});

export const dreiVersprechenSchema = projectPropsSchema.extend({
  items: z.array(listItemSchema).describe("Listenpunkte"),
});

export type DreiVersprechenProps = z.infer<typeof dreiVersprechenSchema>;

// --- Default Props ---

export const dreiVersprechenDefaults: DreiVersprechenProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: TOTAL_DURATION_SEC,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  items: ITEMS.map((item) => ({ ...item })),
};

// =============================================================
// Expanding List Component
// =============================================================

const ExpandingList: React.FC<{ items: ListItem[] }> = ({ items }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: EXIT_SPRING })
      : 0;
  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.92]);
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  // Box entrance
  const boxEntrance = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 120, mass: 1, overshootClamping: true },
  });
  const boxOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const boxSlideY = interpolate(boxEntrance, [0, 1], [30, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "42%",
      }}
    >
      <div
        style={{
          transform: `translateY(${boxSlideY}px) scale(${exitScale})`,
          opacity: boxOpacity * exitOpacity,
          transformOrigin: "center bottom",
          width: "88%",
        }}
      >
        {/* Box container — auto height, no fixed calculation */}
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(16, 70, 151, 0.92) 0%, rgba(12, 52, 112, 0.95) 100%)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            borderRadius: 20,
            padding: "32px 36px",
            boxShadow:
              "0 12px 48px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          {items.map((item, i) => {
            const itemFrame = s(item.startSec);
            const localFrame = frame - itemFrame;

            // Reveal progress: drives both height and content fade
            // First item is always fully revealed, only animate items 2+
            const revealProgress =
              i === 0
                ? frame >= itemFrame ? 1 : 0
                : frame >= itemFrame
                  ? spring({
                      frame: localFrame,
                      fps,
                      config: ITEM_SPRING,
                    })
                  : 0;

            // Snap to 1 once close enough to prevent sub-pixel jitter
            const snappedProgress = revealProgress > 0.995 ? 1 : revealProgress;

            // Item content fades in
            const itemOpacity = i === 0
              ? interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" })
              : interpolate(
                  snappedProgress,
                  [0, 0.4, 1],
                  [0, 0, 1],
                  { extrapolateRight: "clamp" },
                );
            const itemSlideX = i === 0 ? 0 : interpolate(snappedProgress, [0, 1], [24, 0]);

            // Estimated row height (item + divider + gap)
            const ITEM_ROW_HEIGHT = i === 0 ? 90 : 127;
            const rowHeight = i === 0 ? ITEM_ROW_HEIGHT : Math.round(snappedProgress * ITEM_ROW_HEIGHT);

            return (
              <div
                key={i}
                style={{
                  height: rowHeight,
                  overflow: "hidden",
                }}
              >
                {i > 0 && (
                  <div
                    style={{
                      height: 1,
                      backgroundColor: "rgba(255,255,255,0.15)",
                      margin: "18px 0",
                      opacity: itemOpacity,
                    }}
                  />
                )}
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 20,
                    opacity: itemOpacity,
                    transform: `translateX(${itemSlideX}px)`,
                  }}
                >
                  {/* Number badge */}
                  <div
                    style={{
                      minWidth: 40,
                      height: 40,
                      borderRadius: 10,
                      backgroundColor: "rgba(255,255,255,0.15)",
                      border: "1.5px solid rgba(255,255,255,0.25)",
                      color: WHITE,
                      fontFamily: "Open Sans",
                      fontWeight: 700,
                      fontSize: 20,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      marginTop: 3,
                    }}
                  >
                    {i + 1}
                  </div>

                  {/* Text */}
                  <div
                    style={{
                      fontFamily: "Open Sans",
                      fontWeight: 600,
                      fontSize: 28,
                      color: WHITE,
                      lineHeight: 1.4,
                      paddingTop: 4,
                    }}
                  >
                    {item.text}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// Main Composition
// =============================================================

export const TopFotografieDreiVersprechen: React.FC<DreiVersprechenProps> = ({
  review,
  items,
}) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        <ExpandingList items={items} />

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
