// ============================================================
// Mehrere Standbilder einer Komposition mit EINEM Bundle rendern (Review-Kontaktbögen)
// Aufruf: npx tsx scripts/stills-multi.ts <CompId> <Ausgabeordner> <frame,frame,...> [--scale=0.5] [--public-dir=public-x] [--props='{"review":{...}}']
// Ausgabe: <Ausgabeordner>/<CompId>_<frame>.png (PNG mit Alpha, wenn die Komposition transparent ist)
// ============================================================

import path from "path";
import fs from "fs";
import { bundle } from "@remotion/bundler";
import { getCompositions, renderStill } from "@remotion/renderer";

async function main() {
  const [compId, outDir, frameList, ...rest] = process.argv.slice(2);
  if (!compId || !outDir || !frameList) {
    console.error("Aufruf: npx tsx scripts/stills-multi.ts <CompId> <Ausgabeordner> <frame,frame,...> [--scale=0.5] [--public-dir=public-x] [--props='{...}']");
    process.exit(1);
  }
  const opt = (name: string) => rest.find((a) => a.startsWith(`--${name}=`))?.slice(name.length + 3);
  const scale = Number(opt("scale") ?? "0.5");
  const publicDir = opt("public-dir");
  const extraProps = opt("props") ? JSON.parse(opt("props")!) : {};
  const frames = frameList.split(",").map((f) => Number(f.trim())).filter((f) => Number.isFinite(f));

  const root = path.resolve(__dirname, "..");
  const serveUrl = await bundle({
    entryPoint: path.join(root, "src/index.ts"),
    publicDir: publicDir ? path.join(root, publicDir) : undefined,
  });
  const comps = await getCompositions(serveUrl, { inputProps: extraProps });
  const comp = comps.find((c) => c.id === compId);
  if (!comp) throw new Error(`Komposition ${compId} nicht gefunden`);
  fs.mkdirSync(outDir, { recursive: true });
  for (const frame of frames) {
    const output = path.join(outDir, `${compId}_${frame}.png`);
    await renderStill({
      composition: comp,
      serveUrl,
      output,
      frame,
      scale,
      imageFormat: "png",
      inputProps: { ...comp.defaultProps, ...extraProps },
    });
    console.log("Still:", output);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
