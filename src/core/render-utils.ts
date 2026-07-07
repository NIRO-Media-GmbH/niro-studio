// ============================================================
// NIRO Motion Graphics — Render Presets & Utilities
// ============================================================

export interface RenderPreset {
  name: string;
  codec: string;
  imageFormat?: string;
  pixelFormat?: string;
  proresProfile?: string;
  crf?: number;
  scale?: number;
  everyNthFrame?: number;
}

export const RENDER_PRESETS: Record<string, RenderPreset> = {
  "transparent-prores": {
    name: "ProRes 4444 Transparent",
    codec: "prores",
    imageFormat: "png",
    pixelFormat: "yuva444p10le",
    proresProfile: "4444",
  },
  "transparent-webm": {
    name: "WebM VP8 Transparent",
    codec: "vp8",
    imageFormat: "png",
    pixelFormat: "yuva420p",
  },
  "web-h264": {
    name: "H.264 Web",
    codec: "h264",
    crf: 18,
  },
  social: {
    name: "Social Media H.264",
    codec: "h264",
    crf: 18,
  },
  draft: {
    name: "Draft Preview",
    codec: "h264",
    crf: 28,
    scale: 0.5,
  },
  gif: {
    name: "GIF Export",
    codec: "gif",
    everyNthFrame: 2,
  },
};

export function buildRenderArgs(
  preset: RenderPreset,
  compositionId: string,
  outputPath: string
): string[] {
  const args = ["render", "src/index.ts", compositionId, outputPath];
  if (preset.codec) args.push(`--codec=${preset.codec}`);
  if (preset.imageFormat) args.push(`--image-format=${preset.imageFormat}`);
  if (preset.pixelFormat) args.push(`--pixel-format=${preset.pixelFormat}`);
  if (preset.proresProfile)
    args.push(`--prores-profile=${preset.proresProfile}`);
  if (preset.crf !== undefined) args.push(`--crf=${preset.crf}`);
  if (preset.scale !== undefined) args.push(`--scale=${preset.scale}`);
  if (preset.everyNthFrame)
    args.push(`--every-nth-frame=${preset.everyNthFrame}`);
  return args;
}
