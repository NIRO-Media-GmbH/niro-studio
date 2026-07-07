// ============================================================
// WTN — VoicePreview
// Studio-only sync check: plays the source voiceover (WAV) so the
// overlay timing can be scrubbed against the spoken words. There is
// no footage yet — the VO is the sync reference. Hard-guarded
// against export: renders nothing while Remotion is rendering,
// regardless of the toggle, so the alpha overlay stays silent.
// ============================================================

import React from "react";
import { Audio, staticFile, getRemotionEnvironment } from "remotion";

interface VoicePreviewProps {
  /** Path under public/, e.g. "projects/wtn-5x-ads/erster-tag.wav" */
  src: string;
  enabled?: boolean;
}

export const VoicePreview: React.FC<VoicePreviewProps> = ({
  src,
  enabled = false,
}) => {
  if (!enabled || getRemotionEnvironment().isRendering) {
    return null;
  }
  return <Audio src={staticFile(src)} />;
};
