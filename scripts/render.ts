// ============================================================
// CLI Script: Render with presets
// Usage: npm run render -- --preset transparent-prores --composition SocialPost
// ============================================================

import { execSync } from "child_process";
import { RENDER_PRESETS, buildRenderArgs } from "../src/core/render-utils";

const args = process.argv.slice(2);
const presetIndex = args.indexOf("--preset");
const compIndex = args.indexOf("--composition");
const outputIndex = args.indexOf("--output");

if (presetIndex === -1 || compIndex === -1) {
  console.log("Usage: npx tsx scripts/render.ts --preset <preset> --composition <id> [--output <path>]");
  console.log("\nAvailable presets:");
  Object.entries(RENDER_PRESETS).forEach(([key, preset]) => {
    console.log(`  ${key.padEnd(22)} ${preset.name}`);
  });
  process.exit(1);
}

const presetName = args[presetIndex + 1];
const compositionId = args[compIndex + 1];

const preset = RENDER_PRESETS[presetName];
if (!preset) {
  console.error(`Unknown preset: "${presetName}"`);
  console.log("Available:", Object.keys(RENDER_PRESETS).join(", "));
  process.exit(1);
}

// Determine output path
const extMap: Record<string, string> = {
  h264: ".mp4",
  prores: ".mov",
  vp8: ".webm",
  vp9: ".webm",
  gif: ".gif",
};
const ext = extMap[preset.codec] ?? ".mp4";
const outputPath =
  outputIndex !== -1 && args[outputIndex + 1]
    ? args[outputIndex + 1]
    : `out/${compositionId}-${presetName}${ext}`;

const renderArgs = buildRenderArgs(preset, compositionId, outputPath);
const command = `npx remotion ${renderArgs.join(" ")}`;

console.log(`\n  Rendering: ${compositionId}`);
console.log(`  Preset:    ${preset.name}`);
console.log(`  Output:    ${outputPath}`);
console.log(`  Command:   ${command}\n`);

try {
  execSync(command, { stdio: "inherit" });
  console.log(`\n  Done! Output: ${outputPath}\n`);
} catch (error) {
  console.error("\n  Render failed!");
  process.exit(1);
}
