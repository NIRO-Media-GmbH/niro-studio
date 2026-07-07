// ============================================================
// Bremsen Schneider — Fachkraft KFZ-Mechatroniker Overlay
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait-4k (2160×3840), 25fps, 66.84s
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { KeywordReveal, InfoPanel, EndCard } from "../../components";
import type { OverlayPosition } from "../../components";
import { KEYWORDS, PANELS, END_CARD } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("bremsen-schneider", brandJson as any);

// --- Schemas ---

const keywordSchema = z.object({
  word: z.string().describe("Keyword"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
  position: z.enum(["top", "bottom", "center"]).describe("Position"),
  offsetY: z.number().step(1).optional().describe("Y-Offset (px)"),
});

const panelSchema = z.object({
  title: z.string().describe("Titel"),
  items: z.array(z.string()).optional().describe("Listenpunkte"),
  body: z.string().optional().describe("Fließtext"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
  position: z.enum(["top", "bottom", "center"]).describe("Position"),
  accentSide: z.enum(["left", "top"]).optional().describe("Akzentlinie"),
});

const endCardSchema = z.object({
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
  ctaText: z.string().describe("CTA Text"),
  website: z.string().describe("Website"),
  phone: z.string().optional().describe("Telefon"),
});

export const fachkraftOverlaySchema = projectPropsSchema.extend({
  keywords: z.array(keywordSchema).describe("Keywords"),
  infoPanels: z.array(panelSchema).describe("Info-Panels"),
  endCard: endCardSchema.describe("End-Card"),
});

export type FachkraftOverlayProps = z.infer<typeof fachkraftOverlaySchema>;

// --- Default Props ---

export const fachkraftOverlayDefaults: FachkraftOverlayProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 66.84,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  keywords: KEYWORDS.map((kw) => ({
    word: kw.word,
    startSec: kw.startSec,
    durationSec: kw.durationSec,
    position: kw.position,
    offsetY: kw.offsetY,
  })),
  infoPanels: PANELS.map((p) => ({
    title: p.title,
    items: p.items,
    body: p.body,
    startSec: p.startSec,
    durationSec: p.durationSec,
    position: p.position,
    accentSide: p.accentSide,
  })),
  endCard: {
    startSec: END_CARD.startSec,
    durationSec: END_CARD.durationSec,
    ctaText: END_CARD.ctaText,
    website: END_CARD.website,
    phone: END_CARD.phone,
  },
};

// --- Composition ---

export const BremsenSchneiderFachkraft: React.FC<FachkraftOverlayProps> = ({
  review,
  keywords,
  infoPanels,
  endCard,
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
            <KeywordReveal
              word={kw.word}
              position={kw.position as OverlayPosition}
              offsetY={kw.offsetY}
            />
          </Sequence>
        ))}

        {infoPanels.map((panel, i) => (
          <Sequence
            key={`panel-${i}`}
            from={s(panel.startSec)}
            durationInFrames={s(panel.durationSec)}
            name={`Panel: ${panel.title}`}
          >
            <InfoPanel
              title={panel.title}
              items={panel.items}
              body={panel.body}
              position={panel.position as OverlayPosition}
              accentSide={panel.accentSide}
            />
          </Sequence>
        ))}

        <Sequence
          from={s(endCard.startSec)}
          durationInFrames={s(endCard.durationSec)}
          name="End Card"
        >
          <EndCard
            ctaText={endCard.ctaText}
            website={endCard.website}
            phone={endCard.phone}
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
