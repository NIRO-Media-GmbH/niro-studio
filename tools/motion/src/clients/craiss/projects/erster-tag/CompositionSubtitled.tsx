// ============================================================
// Craiss Generation Logistik — "01 Dein erster Tag bei uns", V3
// NUR Untertitel-Spur. Hook + CTA sind bereits im Footage eingebrannt
// (Material/Video/01_Dein_erster_Tag_bei_uns_V3.mp4 ist der fertig
// komponierte Schnitt aus Craiss-ErsterTag/-Preview, kein Rohmaterial) —
// diese Komposition legt nur die Untertitel-Spur obendrauf, sonst nichts.
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
import captionsJson from "../../captions/erster-tag-v3.json";
import planJson from "../../captions/erster-tag-v3.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);
const captions = captionsJson as CaptionFile;

export const craissErsterTagSubtitledSchema = projectPropsSchema.extend({
  subtitles: subtitlesSchema.describe("Untertitel"),
});

export type CraissErsterTagSubtitledProps = z.infer<typeof craissErsterTagSubtitledSchema>;

// Hook (0,24–3,6s) und CTA (24,32s–Ende) liegen bereits im Footage —
// Sperrzeiten fuer die Untertitel-Fenster wie in Craiss-ErsterTag.
const HOOK_BLOCK: BlockedRange = { startSec: 0.24, durationSec: 3.6 - 0.24 };
const DURATION_SEC = 29.6;
const CTA_START = 24.32;
const CTA_BLOCK: BlockedRange = { startSec: CTA_START, durationSec: DURATION_SEC - CTA_START };

export const craissErsterTagSubtitledDefaults: CraissErsterTagSubtitledProps = {
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
// (Render/Stills) falsche Frames beim Seeken (Protokoll 2026-08-26).
const FOOTAGE_SRC = "projects/craiss-erster-tag/proxy/01_Dein_erster_Tag_bei_uns_V3_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Untertitel-Buehne: knapp unter der Bildmitte, fuer ALLE Cues identisch
// (David-Feedback 2026-09-07: durchgehend gleiche Hoehe ist fuer Social
// Media wichtiger als die zwei engsten Nahaufnahmen (8,6s/14,06s) komplett
// kinnfrei zu bekommen — dort streift der Text kurz Kinn/Kragen, akzeptiert).
const STAGE = { top: 1037, height: 230, left: 54, innerWidth: BASE_W - 108 };

// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissErsterTagMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={[HOOK_BLOCK, CTA_BLOCK]} />
    </div>
  );
};

// Nur die Untertitel-Spur (ohne Footage) — für Craiss → Vorschau-Neu
export const CraissErsterTagSubtitleLayer: React.FC<{
  subtitles: CraissErsterTagSubtitledProps["subtitles"];
}> = ({ subtitles }) => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <SubtitleTrack pages={captions.pages} blocked={[HOOK_BLOCK, CTA_BLOCK]} settings={subtitles} stage={STAGE} />
    </div>
  );
};

export const CraissErsterTagSubtitled: React.FC<CraissErsterTagSubtitledProps> = ({
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
        {subtitles.enabled ? <CraissErsterTagMixLayer /> : null}

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
