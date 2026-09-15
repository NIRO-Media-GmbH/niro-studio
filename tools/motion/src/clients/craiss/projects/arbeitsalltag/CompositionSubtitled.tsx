// ============================================================
// Craiss Generation Logistik — "02 Einblick Arbeitsalltag", V3
// NUR Untertitel-Spur. Hook + CTA sind bereits im Footage eingebrannt
// (Material/Video/02_Einblick_in_meinen_Arbeitsalltag_V3.mp4 ist der fertig
// komponierte Schnitt, kein Rohmaterial) — diese Komposition legt nur die
// Untertitel-Spur obendrauf, sonst nichts.
// 9:16, 25fps. Studio: Proxy-Footage darunter zur Kontrolle. Render mit
// transparent=true (Default): nur die Spur als Alpha-Overlay, 2160×3840.
// ============================================================

import React from "react";
import { AbsoluteFill, OffthreadVideo, getRemotionEnvironment, staticFile, useVideoConfig } from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  SubtitleTrack,
  subtitlesSchema,
  SUBTITLE_DEFAULTS,
  type CaptionFile,
  type BlockedRange,
} from "../../Subtitles";
import brandJson from "../../brand.json";
import captionsJson from "../../captions/arbeitsalltag-v3.json";
import planJson from "../../captions/arbeitsalltag-v3.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);
const captions = captionsJson as CaptionFile;

export const craissArbeitsalltagSubtitledSchema = projectPropsSchema.extend({
  subtitles: subtitlesSchema.describe("Untertitel"),
});

export type CraissArbeitsalltagSubtitledProps = z.infer<typeof craissArbeitsalltagSubtitledSchema>;

const DURATION_SEC = 74.08; // Neuexport 11.09. 18:42: 1853 Frames (Endshot +1s)

// Sperrzeiten per Kontaktbogen gegen den V3-Proxy verifiziert (2026-09-07,
// s. scripts/craiss-captions.ts — die Root.tsx-Defaults sind fuer einen
// aelteren Schnitt und weichen ~9,5s ab).
export const BLOCKED: BlockedRange[] = [
  { startSec: 0, durationSec: 3.0 }, // Hook „MEIN ARBEITSALLTAG / BEI CRAISS"
  { startSec: 61.6, durationSec: DURATION_SEC - 61.6 }, // CTA
];

export const craissArbeitsalltagSubtitledDefaults: CraissArbeitsalltagSubtitledProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: DURATION_SEC,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  subtitles: SUBTITLE_DEFAULTS,
};

// Proxy-Pflicht: das 10-bit-HEVC-Original liefert im Remotion-Frame-Extraktor
// (Render/Stills) falsche Frames beim Seeken.
// Seit Neuexport 11.09.: Schnitt ohne Animation (der alte animierte V3 ist 1s kürzer)
const FOOTAGE_SRC = "projects/craiss-arbeitsalltag/ohne-Animation/proxy/02_Einblick_in_meinen_Arbeitsalltag_V3_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Untertitel-Buehne: gleiche Position wie Video 01 (knapp unter Bildmitte,
// fuer alle Cues identisch — David-Feedback 2026-09-07).
const STAGE = { top: 1037, height: 230, left: 54, innerWidth: BASE_W - 108 };

// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissArbeitsalltagMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={BLOCKED} />
    </div>
  );
};

// Nur die Untertitel-Spur (ohne Footage) — für Craiss → Vorschau-Neu
export const CraissArbeitsalltagSubtitleLayer: React.FC<{
  subtitles: CraissArbeitsalltagSubtitledProps["subtitles"];
}> = ({ subtitles }) => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <SubtitleTrack pages={captions.pages} blocked={BLOCKED} settings={subtitles} stage={STAGE} />
    </div>
  );
};

export const CraissArbeitsalltagSubtitled: React.FC<CraissArbeitsalltagSubtitledProps> = ({
  review,
  subtitles,
  transparent,
}) => {
  // Alpha-Export: Footage nur im Studio zur Kontrolle, nie im Render.
  const { isRendering } = getRemotionEnvironment();
  const showFootage = !transparent || !isRendering;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: showFootage ? "#000" : "transparent" }}>
        {showFootage && (
          <OffthreadVideo src={staticFile(FOOTAGE_SRC)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        )}

        {/* Seit Abnahme 2026-09-11: neuer Untertitel-Look „Mix" (alter Look nur noch in Vorschau-Neu → subtitleStyle „alt") */}
        {subtitles.enabled ? <CraissArbeitsalltagMixLayer /> : null}

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
