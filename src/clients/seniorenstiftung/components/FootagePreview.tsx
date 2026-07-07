// ============================================================
// Seniorenstiftung — FootagePreview
// Studio-only sync check: renders the source footage (720p proxy,
// with audio) BEHIND the overlay so timing can be scrubbed against
// picture + sound. Hard-guarded against export: renders nothing
// while Remotion is rendering, regardless of the toggle.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  getRemotionEnvironment,
} from "remotion";

interface FootagePreviewProps {
  /** Path under public/, e.g. "projects/seniorenstiftung-recruiting/proxy/pflegefachkraft.mp4" */
  src: string;
  enabled?: boolean;
}

export const FootagePreview: React.FC<FootagePreviewProps> = ({
  src,
  enabled = false,
}) => {
  if (!enabled || getRemotionEnvironment().isRendering) {
    return null;
  }
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(src)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
  );
};
