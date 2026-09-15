// ============================================================
// Craiss Generation Logistik — "02 Einblick in meinen Arbeitsalltag"
// Hook als LOWER-THIRD (Talking-Head-Opener, Gesicht bis ~45% Höhe)
// + CTA 1:1 aus Video 01 (ab 70,4s über Drohnen-Endshot)
// Transparent overlay (ProRes 4444 mit Alpha)
// 9:16 portrait-4k (2160×3840), 25fps — Stand 2026-09-11: Länge, Footage
// und CTA-Zeit = Kunden-Schnitt V3 ohne Animation (1828 Frames = 73,12s),
// CTA per Differenz gegen den animierten V3 gemessen. Die Angaben unten
// beziehen sich noch auf den alten V2-Schnitt.
//
// Schnittgrenzen vorn: 1,44 / 3,12 / 4,68s; letzter Schnitt 70,28s,
// danach ein durchgehender Drohnen-Landschaftsshot bis zum Ende —
// David stellt ihn im Schnitt unscharf, der CTA liegt darüber.
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

export const craissArbeitsalltagSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Hook"),
  cta: ctaSchema.describe("CTA"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissArbeitsalltagProps = z.infer<typeof craissArbeitsalltagSchema>;

export const craissArbeitsalltagDefaults: CraissArbeitsalltagProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  // Neuexport 11.09. 18:42: Bild bis 73,12s identisch, Drohnen-Endshot 1s länger (1853 Frames)
  durationInSeconds: 74.12,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hook: {
    headline: "MEIN ARBEITSALLTAG",
    chip: "BEI CRAISS",
    startSec: 0.24,
    endSec: 3.12,
    offsetY: 0,
  },
  cta: {
    ...CTA_TEXTS,
    // V3: Drohnen-Endshot ab 61,64s, CTA wie im Kunden-Schnitt ab 62,28s
    startSec: 62.28,
    offsetY: 0,
  },
  footage: {
    showInStudio: true,
    simulateBlur: false, // Blur ist im Kunden-Schnitt schon drin
    renderInExport: false,
  },
};

export const craissArbeitsalltagPreviewDefaults: CraissArbeitsalltagProps = {
  ...craissArbeitsalltagDefaults,
  transparent: false,
  footage: {
    showInStudio: true,
    simulateBlur: false, // Blur ist im Kunden-Schnitt schon drin
    renderInExport: true,
  },
};

const FOOTAGE_SRC =
  "projects/craiss-arbeitsalltag/ohne-Animation/proxy/02_Einblick_in_meinen_Arbeitsalltag_V3_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

export const CraissArbeitsalltag: React.FC<CraissArbeitsalltagProps> = ({
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
            <Hook hook={hook} layout="lower" />
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
