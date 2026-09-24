// ============================================================
// akut med Ads (Dreh 11./12.08.2026): viele Standbilder der Akut-Ad-Kompositionen mit EINEM Bundle (public-akut).
// Aufruf: npx tsx scripts/stills-akut.ts <Ausgabeordner> <CompId>:<frame,frame,…> [<CompId>:<frames> …]
//         [--scale=0.5] [--props='{"showSubtitles":false}']
// Ausgabe: <Ausgabeordner>/<CompId>_<frame>.png (Alpha). System-Chrome und eigener Port wie remotion.config.ts
// (Headless-Shell auf diesem Mac kaputt, Port 3000 fremd belegt).
// ============================================================

import path from "path";
import fs from "fs";
import { bundle } from "@remotion/bundler";
import { getCompositions, renderStill } from "@remotion/renderer";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

async function main() {
  const args = process.argv.slice(2);
  const outDir = args[0];
  const opt = (name: string) => args.find((a) => a.startsWith(`--${name}=`))?.slice(name.length + 3);
  const scale = Number(opt("scale") ?? "0.5");
  const extraProps = opt("props") ? JSON.parse(opt("props")!) : {};
  const jobs = args.slice(1).filter((a) => !a.startsWith("--")).map((a) => {
    const [id, frames] = a.split(":");
    return { id, frames: frames.split(",").map(Number).filter((f) => Number.isFinite(f)) };
  });
  const root = path.resolve(__dirname, "..");
  const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts"), publicDir: path.join(root, "public-akut") });
  const browserExecutable = fs.existsSync(CHROME) ? CHROME : undefined;
  const comps = await getCompositions(serveUrl, { inputProps: extraProps, browserExecutable, port: 3217 });
  fs.mkdirSync(outDir, { recursive: true });
  for (const job of jobs) {
    const comp = comps.find((c) => c.id === job.id);
    if (!comp) throw new Error(`Komposition ${job.id} nicht gefunden`);
    for (const frame of job.frames) {
      const output = path.join(outDir, `${job.id}_${frame}.png`);
      await renderStill({ composition: comp, serveUrl, output, frame, scale, imageFormat: "png", browserExecutable, port: 3217,
        inputProps: { ...comp.defaultProps, ...extraProps } });
      console.log("Still:", output);
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
