// ============================================================
// Craiss Generation Logistik — "01 Dein erster Tag bei uns"
// Hook (Video-Anfang, oben) + CTA (ab 24,32s über Drohnen-Endshot)
// Transparent overlay (ProRes 4444 mit Alpha)
// 9:16 portrait-4k (2160×3840), 25fps, 30,04s — Stand 2026-09-11: Länge
// und Footage = Kunden-Schnitt V3 ohne Animation (751 Frames); Hook/CTA-
// Zeiten per Differenz gegen den animierten V3 bestätigt (unverändert).
//
// Schnittgrenzen im Footage: 1,76 / 2,72 / 3,72 / … / 24,2s.
// Der Endshot (24,2s bis Ende) wird von David im Schnitt
// unscharf gestellt — der CTA liegt darüber.
// Gemeinsame Bausteine (Hook/CTA/FootageCompare): ../../lib
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Hook,
  Cta,
  FootageCompare,
  hookSchema,
  ctaSchema,
  footageSchema,
  CTA_TEXTS,
} from "../../lib";
import brandJson from "../../brand.json";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);

export const craissErsterTagSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Hook"),
  cta: ctaSchema.describe("CTA"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissErsterTagProps = z.infer<typeof craissErsterTagSchema>;

export const craissErsterTagDefaults: CraissErsterTagProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 30.04,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hook: {
    headline: "DEIN ERSTER TAG",
    chip: "BEI UNS",
    startSec: 0.24,
    endSec: 3.6,
    offsetY: 0,
  },
  cta: {
    ...CTA_TEXTS,
    lineBig: CTA_TEXTS.lineBig,
    startSec: 24.32,
    offsetY: 0,
  },
  footage: {
    showInStudio: true,
    simulateBlur: false, // Blur ist im Kunden-Schnitt schon drin
    renderInExport: false,
  },
};

export const craissErsterTagPreviewDefaults: CraissErsterTagProps = {
  ...craissErsterTagDefaults,
  transparent: false,
  footage: {
    showInStudio: true,
    simulateBlur: false, // Blur ist im Kunden-Schnitt schon drin
    renderInExport: true,
  },
};

const FOOTAGE_SRC = "projects/craiss-erster-tag/ohne-Animation/proxy/01_Dein_erster_Tag_bei_uns_V3_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

export const CraissErsterTag: React.FC<CraissErsterTagProps> = ({
  review,
  hook,
  cta,
  footage,
}) => {
  const { fps, width, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const S = width / BASE_W;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <FootageCompare src={FOOTAGE_SRC} footage={footage} ctaStartSec={cta.startSec} />

        {/* Layout-Bühne 1080×1920 → uniform skaliert */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: BASE_W,
            height: BASE_H,
            transform: `scale(${S})`,
            transformOrigin: "top left",
          }}
        >
          <Sequence
            from={s(hook.startSec)}
            durationInFrames={s(hook.endSec) - s(hook.startSec)}
            name="Hook"
          >
            <Hook hook={hook} layout="top" />
          </Sequence>

          <Sequence
            from={s(cta.startSec)}
            durationInFrames={durationInFrames - s(cta.startSec)}
            name="CTA"
          >
            <Cta cta={cta} />
          </Sequence>
        </div>

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
