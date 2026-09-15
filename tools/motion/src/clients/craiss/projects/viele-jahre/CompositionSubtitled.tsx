// ============================================================
// Craiss Generation Logistik — "03 Viele Jahre Viele Geschichten", V3
// NUR Untertitel-Spur. Hook + Laender-Flaggen + CTA sind bereits im Footage
// eingebrannt (Material/Video/03_Viele_Jahre_Viele_Geschichten_V3.mp4 ist
// der fertig komponierte Schnitt, kein Rohmaterial) — diese Komposition legt
// nur die Untertitel-Spur obendrauf, sonst nichts.
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
import captionsJson from "../../captions/viele-jahre-v3.json";
import planJson from "../../captions/viele-jahre-v3.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);
const captions = captionsJson as CaptionFile;

export const craissVieleJahreSubtitledSchema = projectPropsSchema.extend({
  subtitles: subtitlesSchema.describe("Untertitel"),
});

export type CraissVieleJahreSubtitledProps = z.infer<typeof craissVieleJahreSubtitledSchema>;

const DURATION_SEC = 51.6;

// Sperrzeiten per Kontaktbogen gegen den V3-Proxy verifiziert (2026-09-07,
// s. scripts/craiss-captions.ts — die Root.tsx-Defaults sind fuer einen
// aelteren/kuerzeren Schnitt und weichen ~5,7s ab).
export const BLOCKED: BlockedRange[] = [
  // 2026-09-11 exakt auf die Overlay-Sequenzen gesetzt (Differenz animiert −
  // ohne Animation bestätigt); nötig, weil der Mix-Look nur ganze Sätze zeigt.
  { startSec: 0, durationSec: 2.72 }, // Hook „VIELE JAHRE / VIELE GESCHICHTEN" (Overlay 0,24–2,72)
  { startSec: 7.84, durationSec: 3.76 }, // Laender-Flaggen (Overlay 7,84–11,6)
  { startSec: 46.64, durationSec: DURATION_SEC - 46.64 }, // CTA (Overlay ab 46,64)
];

export const craissVieleJahreSubtitledDefaults: CraissVieleJahreSubtitledProps = {
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
const FOOTAGE_SRC = "projects/craiss-viele-jahre/proxy/03_Viele_Jahre_Viele_Geschichten_V3_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Untertitel-Buehne: gleiche Position wie Video 01 (knapp unter Bildmitte,
// fuer alle Cues identisch — David-Feedback 2026-09-07).
const STAGE = { top: 1037, height: 230, left: 54, innerWidth: BASE_W - 108 };

// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissVieleJahreMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={BLOCKED} />
    </div>
  );
};

// Nur die Untertitel-Spur (ohne Footage) — für Craiss → Vorschau-Neu
export const CraissVieleJahreSubtitleLayer: React.FC<{
  subtitles: CraissVieleJahreSubtitledProps["subtitles"];
}> = ({ subtitles }) => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <SubtitleTrack pages={captions.pages} blocked={BLOCKED} settings={subtitles} stage={STAGE} />
    </div>
  );
};

export const CraissVieleJahreSubtitled: React.FC<CraissVieleJahreSubtitledProps> = ({
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
        {subtitles.enabled ? <CraissVieleJahreMixLayer /> : null}

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
