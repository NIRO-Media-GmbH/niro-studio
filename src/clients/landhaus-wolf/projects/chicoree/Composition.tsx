// ============================================================
// Landhaus Wolf — Chicorée
// Karamellisierter Chicorée fürs Gourmet-Restaurant (~1:15)
// ============================================================

import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import brandJson from "../../brand.json";
import { TimelineRenderer } from "../../timeline";
import { SRT } from "./srt-data";
import { TIMELINE } from "./timeline-config";

const ci = loadBrand("landhaus-wolf", brandJson as any);

export const landhausWolfChicoreeSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfChicoreeSchema>;

export const LandhausWolfChicoree: React.FC<Props> = ({
  transparent = true,
}) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/landhaus-wolf-kochvideos/chicoree.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        <TimelineRenderer srt={SRT} timeline={TIMELINE} />
      </AbsoluteFill>
    </CIProvider>
  );
};
