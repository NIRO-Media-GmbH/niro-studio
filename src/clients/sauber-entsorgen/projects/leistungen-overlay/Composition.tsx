// ============================================================
// Sauber Entsorgen — Leistungen-Overlay
// Transparent alpha overlay (ProRes 4444) over the GF footage.
// 16:9 landscape (1920×1080), 25fps, 12s.
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { KeywordLowerThird, ServiceChips } from "../../components";
import type { Align, ServiceIconName } from "../../components";
import { KEYWORDS, CHIP_GROUPS } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("sauber-entsorgen", brandJson as any);

const ICON_ENUM = z.enum([
  "haus",
  "nachlass",
  "keller",
  "dachboden",
  "garage",
  "firma",
  "express",
]);

// --- Schemas ---

const keywordSchema = z.object({
  word: z.string().describe("Schlagwort"),
  icon: ICON_ENUM.describe("Icon"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
  align: z.enum(["left", "center"]).optional().describe("Ausrichtung"),
  offsetX: z.number().step(1).optional().describe("X-Offset (px)"),
  offsetY: z.number().step(1).optional().describe("Y-Offset (px)"),
});

const chipSchema = z.object({
  label: z.string().describe("Label"),
  icon: ICON_ENUM.describe("Icon"),
});

const chipGroupSchema = z.object({
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
  chips: z.array(chipSchema).describe("Chips"),
  offsetX: z.number().step(1).optional().describe("X-Offset (px)"),
  offsetY: z.number().step(1).optional().describe("Y-Offset (px)"),
});

export const leistungenOverlaySchema = projectPropsSchema.extend({
  keywords: z.array(keywordSchema).describe("Lower-Third-Keywords"),
  chipGroups: z.array(chipGroupSchema).describe("Chip-Gruppen"),
});

export type LeistungenOverlayProps = z.infer<typeof leistungenOverlaySchema>;

// --- Default Props ---

export const leistungenOverlayDefaults: LeistungenOverlayProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 12,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // Centered talking-head (16:9) — adjust per actual footage if needed.
    faceZone: { top: 0.04, bottom: 0.74, left: 0.28, right: 0.72 },
    guideOpacity: 0.35,
  },
  keywords: KEYWORDS.map((kw) => ({
    word: kw.word,
    icon: kw.icon as any,
    startSec: kw.startSec,
    durationSec: kw.durationSec,
    align: kw.align ?? "left",
    offsetX: kw.offsetX,
    offsetY: kw.offsetY,
  })),
  chipGroups: CHIP_GROUPS.map((g) => ({
    startSec: g.startSec,
    durationSec: g.durationSec,
    chips: g.chips as any,
    offsetX: g.offsetX,
    offsetY: g.offsetY,
  })),
};

// --- Composition ---

export const SauberEntsorgenLeistungen: React.FC<LeistungenOverlayProps> = ({
  review,
  keywords,
  chipGroups,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {keywords.map((kw, i) => (
          <Sequence
            key={`kw-${i}`}
            from={s(kw.startSec)}
            durationInFrames={s(kw.durationSec)}
            name={`Keyword: ${kw.word}`}
          >
            <KeywordLowerThird
              word={kw.word}
              icon={kw.icon as ServiceIconName}
              align={(kw.align ?? "left") as Align}
              offsetX={kw.offsetX}
              offsetY={kw.offsetY}
            />
          </Sequence>
        ))}

        {chipGroups.map((group, i) => (
          <Sequence
            key={`chips-${i}`}
            from={s(group.startSec)}
            durationInFrames={s(group.durationSec)}
            name={`Chips: ${group.chips.map((c) => c.label).join(" · ")}`}
          >
            <ServiceChips
              chips={group.chips.map((c) => ({
                label: c.label,
                icon: c.icon as ServiceIconName,
              }))}
              offsetX={group.offsetX}
              offsetY={group.offsetY}
            />
          </Sequence>
        ))}

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
