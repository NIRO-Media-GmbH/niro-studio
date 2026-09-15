// ============================================================
// Craiss Generation Logistik — "05 Testimonial Video", V2
// NUR Untertitel-Spur. Hook + Zitat-Chips + Laender-Flaggen + CTA sind
// bereits im Footage eingebrannt (Material/Video/05_Testimonial_Video_V2.mp4
// ist der fertig komponierte Schnitt, kein Rohmaterial) — diese Komposition
// legt nur die Untertitel-Spur obendrauf, sonst nichts.
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
import captionsJson from "../../captions/testimonial-v2.json";
import planJson from "../../captions/testimonial-v2.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
import { CraissTestimonial, craissTestimonialDefaults } from "./Composition";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);
const captions = captionsJson as CaptionFile;

export const craissTestimonialSubtitledSchema = projectPropsSchema.extend({
  subtitles: subtitlesSchema.describe("Untertitel"),
});

export type CraissTestimonialSubtitledProps = z.infer<typeof craissTestimonialSubtitledSchema>;

const DURATION_SEC = 52.56; // Neuexport 11.09. 18:46: 1315 Frames

// Sperrzeiten per lueckenlosem 1s-Kontaktbogen (0-52s) gegen den V2-Proxy
// verifiziert (2026-09-07) — die Root.tsx-Defaults (projects/testimonial/
// Composition.tsx) trafen den tatsaechlichen Schnitt oft nicht (z. B. Zitat
// „JEDEN TAG ZU HAUSE." blendet real ~1,8s frueher ein als dokumentiert und
// kollidierte im ersten Durchlauf sichtbar mit dem Untertitel).
export const BLOCKED: BlockedRange[] = [
  // 2026-09-11: Mix-Look zeigt nur ganze Sätze → Sperren exakt = Sequenzen von
  // Craiss-Testimonial v3 (Hook, Chips, Flaggen, CTA; Dauern als Literale).
  { startSec: 0, durationSec: 2.28 }, // Hook „ICH MAG MEINE ARBEIT / LKW-FAHRER BEI CRAISS"
  { startSec: 3.32, durationSec: 2.48 }, // Zitat „JEDER TAG IST EIN GUTER TAG."
  { startSec: 6.88, durationSec: 1.92 }, // Zitat „DIE FREIHEIT. DIE RUHE."
  // „KEIN STRESS." entfaellt ab Overlay v3 (Kundenfeedback) — kein Sperrfenster;
  // die Phrase ist auch aus den Untertiteln gestrichen (scripts/craiss-captions.ts).
  // ab 16,96s −0,52s (Neuexport 18:46 ohne „Kein Stress")
  { startSec: 28.44, durationSec: 1.88 }, // Zitat „JEDEN TAG ZU HAUSE."
  { startSec: 34.88, durationSec: 1.72 }, // Zitat „BEI CRAISS PASST'S."
  { startSec: 39.64, durationSec: 3.88 }, // Laender-Flaggen (HU/CZ/RO/LT)
  { startSec: 46.12, durationSec: DURATION_SEC - 46.12 }, // CTA auf dem Drohnen-Endshot
];

export const craissTestimonialSubtitledDefaults: CraissTestimonialSubtitledProps = {
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
// Seit Overlay v3: Schnitt OHNE Animation + neues Overlay (CraissTestimonial)
// darunter, damit die Vorschau den Stand nach dem Kundenfeedback zeigt.
const FOOTAGE_SRC = "projects/craiss-testimonial/ohne-Animation/proxy/05_Testimonial_Video_V2_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Untertitel-Buehne: gleiche Position wie Video 01 (knapp unter Bildmitte,
// fuer alle Cues identisch — David-Feedback 2026-09-07).
const STAGE = { top: 1037, height: 230, left: 54, innerWidth: BASE_W - 108 };

// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissTestimonialMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={BLOCKED} />
    </div>
  );
};

// Nur die Untertitel-Spur (ohne Footage) — für Craiss → Vorschau-Neu
export const CraissTestimonialSubtitleLayer: React.FC<{
  subtitles: CraissTestimonialSubtitledProps["subtitles"];
}> = ({ subtitles }) => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <SubtitleTrack pages={captions.pages} blocked={BLOCKED} settings={subtitles} stage={STAGE} />
    </div>
  );
};

export const CraissTestimonialSubtitled: React.FC<CraissTestimonialSubtitledProps> = ({
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
          <>
            <OffthreadVideo src={staticFile(FOOTAGE_SRC)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <CraissTestimonial
              {...craissTestimonialDefaults}
              footage={{ showInStudio: false, simulateBlur: false, renderInExport: false }}
            />
          </>
        )}

        {/* Seit Abnahme 2026-09-11: neuer Untertitel-Look „Mix" (alter Look nur noch in Vorschau-Neu → subtitleStyle „alt") */}
        {subtitles.enabled ? <CraissTestimonialMixLayer /> : null}

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
