// ============================================================
// Craiss Generation Logistik — "04 Funnel Video", V4
// NUR Untertitel-Spur. Alle Chips/Transition/Schritte/End-Logo sind bereits
// im Footage eingebrannt (Material/Video/04_Funnel_Video_V4.mp4 ist der
// fertig komponierte Schnitt, kein Rohmaterial) — diese Komposition legt
// nur die Untertitel-Spur obendrauf, sonst nichts. Das Video ist durchgehend
// dicht mit Grafiken belegt — die Untertitel-Spur zeigt entsprechend nur in
// den echten Luecken (s. Sperrzeiten unten).
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
import captionsJson from "../../captions/funnel-v4.json";
import planJson from "../../captions/funnel-v4.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);
const captions = captionsJson as CaptionFile;

export const craissFunnelSubtitledSchema = projectPropsSchema.extend({
  subtitles: subtitlesSchema.describe("Untertitel"),
});

export type CraissFunnelSubtitledProps = z.infer<typeof craissFunnelSubtitledSchema>;

const DURATION_SEC = 59.08;

// Sperrzeiten per lueckenlosem 1s-Kontaktbogen (0-59s) gegen den V4-Proxy
// verifiziert (2026-09-07) — ein erster Durchlauf mit den Root.tsx-Defaults
// (projects/funnel/Composition.tsx) + kleiner Polsterung kollidierte an
// mehreren Stellen (z. B. "KEIN LEBENSLAUF"-Chip real ~1s frueher als
// dokumentiert), deshalb hier komplett gegen echte Frames neu vermessen.
export const BLOCKED: BlockedRange[] = [
  // 2026-09-11 exakt = Sequenzen von Craiss-Funnel (auf V4 ausgerichtet, per
  // Differenz animiert − ohne Animation bestätigt). Dauern als Literale, damit
  // Math.floor in freeWindows nicht an Rundungsresten einen Frame verliert.
  { startSec: 0.64, durationSec: 2.48 }, // Chef-Namenskarte "MICHAEL CRAISS"
  { startSec: 5.24, durationSec: 1.4 }, // Standort-Chip "MUEHLACKER"
  { startSec: 21.0, durationSec: 1.68 }, // Swipe-Transition
  { startSec: 23.76, durationSec: 3.56 }, // Namenskarte "EVA"
  { startSec: 32.48, durationSec: 3.04 }, // "KEIN LEBENSLAUF / KEIN ANSCHREIBEN"
  { startSec: 35.72, durationSec: 1.36 }, // Schritt 1 "TRAG DICH EIN"
  { startSec: 37.08, durationSec: 2.44 }, // Schritt 2 "TELEFONAT"
  { startSec: 39.56, durationSec: 3.96 }, // Phone-Chip "SEI ERREICHBAR"
  { startSec: 46.88, durationSec: 2.44 }, // Schritt 3 "PERSÖNLICHES KENNENLERNEN"
  { startSec: 50.32, durationSec: 2.6 }, // Outro "WORAUF WARTEST DU?"
  { startSec: 54.72, durationSec: DURATION_SEC - 54.72 }, // CTA
];

export const craissFunnelSubtitledDefaults: CraissFunnelSubtitledProps = {
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
const FOOTAGE_SRC = "projects/craiss-funnel/proxy/04_Funnel_Video_V4_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// Untertitel-Buehne: gleiche Position wie Video 01 (knapp unter Bildmitte,
// fuer alle Cues identisch — David-Feedback 2026-09-07).
const STAGE = { top: 1037, height: 230, left: 54, innerWidth: BASE_W - 108 };

// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissFunnelMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={BLOCKED} />
    </div>
  );
};

// Nur die Untertitel-Spur (ohne Footage) — für Craiss → Vorschau-Neu
export const CraissFunnelSubtitleLayer: React.FC<{
  subtitles: CraissFunnelSubtitledProps["subtitles"];
}> = ({ subtitles }) => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <SubtitleTrack pages={captions.pages} blocked={BLOCKED} settings={subtitles} stage={STAGE} />
    </div>
  );
};

export const CraissFunnelSubtitled: React.FC<CraissFunnelSubtitledProps> = ({
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
        {subtitles.enabled ? <CraissFunnelMixLayer /> : null}

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
