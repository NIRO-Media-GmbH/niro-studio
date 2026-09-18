// ============================================================
// Craiss Generation Logistik — Vorschau-Neu (Stand 2026-09-11)
// Abnahme-Ansicht im Studio: Kunden-Schnitt OHNE Animation (NAS-Export)
// als Unterbau + aktuelle Animationen (Overlay-Kompositionen mit ihren
// Defaults) + Untertitel-Spur. Geliefert werden weiterhin die Overlays
// einzeln (ProRes 4444 Alpha) — diese Kompositionen sind nur zum Prüfen.
// ============================================================

import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, getRemotionEnvironment, staticFile, useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { SUBTITLE_DEFAULTS } from "../../Subtitles";
import { CraissErsterTag, craissErsterTagDefaults } from "../erster-tag/Composition";
import { CraissArbeitsalltag, craissArbeitsalltagDefaults } from "../arbeitsalltag/Composition";
import { CraissVieleJahre, craissVieleJahreDefaults, INTRO_SHIFT_FRAMES, VIELE_JAHRE_SECONDS } from "../viele-jahre/Composition";
import { CraissFunnel, craissFunnelDefaults } from "../funnel/Composition";
import { CraissTestimonial, craissTestimonialDefaults } from "../testimonial/Composition";
import { CraissErsterTagKeywordLayer, CraissErsterTagMixLayer, CraissErsterTagSubtitleLayer } from "../erster-tag/CompositionSubtitled";
import { CraissArbeitsalltagKeywordLayer, CraissArbeitsalltagMixLayer, CraissArbeitsalltagSubtitleLayer } from "../arbeitsalltag/CompositionSubtitled";
import { CraissVieleJahreKeywordLayer, CraissVieleJahreMixLayer, CraissVieleJahreSubtitleLayer } from "../viele-jahre/CompositionSubtitled";
import { CraissFunnelKeywordLayer, CraissFunnelMixLayer, CraissFunnelSubtitleLayer } from "../funnel/CompositionSubtitled";
import { CraissTestimonialKeywordLayer, CraissTestimonialMixLayer, CraissTestimonialSubtitleLayer } from "../testimonial/CompositionSubtitled";

const VIDEO_IDS = ["01", "02", "03", "04", "05"] as const;
type VideoId = (typeof VIDEO_IDS)[number];

export const craissVorschauSchema = projectPropsSchema.extend({
  video: z.enum(VIDEO_IDS).describe("Video"),
  showAnimation: z.boolean().describe("Animationen zeigen"),
  showSubtitles: z.boolean().describe("Untertitel zeigen"),
  subtitleStyle: z
    .enum(["schlagwort", "neu", "alt"])
    .describe("Untertitel-Look (schlagwort = Chips 16.09., neu = Mix 11.09., alt = Leiste 07.09.)"),
});

export type CraissVorschauProps = z.infer<typeof craissVorschauSchema>;

const NO_FOOTAGE = { showInStudio: false, simulateBlur: false, renderInExport: false };

const VIDEOS: Record<
  VideoId,
  { src: string; seconds: number; Overlay: React.FC; Subs: React.FC; MixSubs?: React.FC; KeywordSubs: React.FC }
> = {
  "01": {
    src: "projects/craiss-erster-tag/ohne-Animation/proxy/01_Dein_erster_Tag_bei_uns_V3_ohneAnim_proxy.mp4",
    seconds: 30.04,
    Overlay: () => <CraissErsterTag {...craissErsterTagDefaults} footage={NO_FOOTAGE} />,
    Subs: () => <CraissErsterTagSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />,
    MixSubs: CraissErsterTagMixLayer,
    KeywordSubs: CraissErsterTagKeywordLayer,
  },
  "02": {
    src: "projects/craiss-arbeitsalltag/ohne-Animation/proxy/02_Einblick_in_meinen_Arbeitsalltag_V3_ohneAnim_proxy.mp4",
    seconds: 74.12, // Neuexport 11.09. 18:42
    Overlay: () => <CraissArbeitsalltag {...craissArbeitsalltagDefaults} footage={NO_FOOTAGE} />,
    Subs: () => <CraissArbeitsalltagSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />,
    MixSubs: CraissArbeitsalltagMixLayer,
    KeywordSubs: CraissArbeitsalltagKeywordLayer,
  },
  "03": {
    // Seit 16.09.: Schnitt der Resolve-Kopie „Claude 03 Begrüßung" (Begrüßungs-Montage + D Frames)
    src: "projects/craiss-viele-jahre/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4",
    seconds: VIELE_JAHRE_SECONDS,
    Overlay: () => <CraissVieleJahre {...craissVieleJahreDefaults} footage={NO_FOOTAGE} />,
    // Satz-Untertitel sind auf den V3-Schnitt getimt → um die Verlängerung D versetzt zeigen
    Subs: () => (
      <Sequence from={INTRO_SHIFT_FRAMES} layout="none">
        <CraissVieleJahreSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />
      </Sequence>
    ),
    MixSubs: () => (
      <Sequence from={INTRO_SHIFT_FRAMES} layout="none">
        <CraissVieleJahreMixLayer />
      </Sequence>
    ),
    KeywordSubs: CraissVieleJahreKeywordLayer,
  },
  "04": {
    src: "projects/craiss-funnel/ohne-Animation/proxy/04_Funnel_Video_V3_ohneAnim_proxy.mp4",
    seconds: 59.12,
    Overlay: () => <CraissFunnel {...craissFunnelDefaults} footage={NO_FOOTAGE} />,
    Subs: () => <CraissFunnelSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />,
    MixSubs: CraissFunnelMixLayer,
    KeywordSubs: CraissFunnelKeywordLayer,
  },
  "05": {
    src: "projects/craiss-testimonial/ohne-Animation/proxy/05_Testimonial_Video_V2_ohneAnim_proxy.mp4",
    seconds: 52.6, // Neuexport 11.09. 18:46
    Overlay: () => <CraissTestimonial {...craissTestimonialDefaults} footage={NO_FOOTAGE} />,
    Subs: () => <CraissTestimonialSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />,
    MixSubs: CraissTestimonialMixLayer,
    KeywordSubs: CraissTestimonialKeywordLayer,
  },
};

export const craissVorschauDefaults = (video: VideoId): CraissVorschauProps => ({
  // 1080×1920 reicht für die Abnahme und spielt im Studio flüssiger
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: VIDEOS[video].seconds,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  video,
  showAnimation: true,
  showSubtitles: true,
  subtitleStyle: "schlagwort" as const,
});

// Lieferung (User 11.09.): pro Video EINE Alpha-Datei mit allen Animationen
// + Untertiteln. Gleiche Komposition wie die Vorschau, nur 2160×3840 und
// transparent — der Schnitt darunter erscheint dann nur im Studio.
export const craissAlphaDefaults = (video: VideoId): CraissVorschauProps => ({
  ...craissVorschauDefaults(video),
  format: "portrait-4k" as const,
  transparent: true,
});

export const CraissVorschau: React.FC<CraissVorschauProps> = ({
  video,
  showAnimation,
  showSubtitles,
  subtitleStyle,
  review,
  transparent,
}) => {
  const v = VIDEOS[video];
  const { fps } = useVideoConfig();
  const { isRendering } = getRemotionEnvironment();
  const showFootage = !transparent || !isRendering;

  return (
    <AbsoluteFill style={{ backgroundColor: showFootage ? "#000" : "transparent" }}>
      {showFootage && (
        <Sequence durationInFrames={Math.round(v.seconds * fps)} name="Schnitt ohne Animation">
          <OffthreadVideo src={staticFile(v.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Sequence>
      )}

      {showAnimation && <v.Overlay />}
      {showSubtitles &&
        (subtitleStyle === "schlagwort" ? (
          <v.KeywordSubs />
        ) : subtitleStyle === "neu" && v.MixSubs ? (
          <v.MixSubs />
        ) : (
          <v.Subs />
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
  );
};
