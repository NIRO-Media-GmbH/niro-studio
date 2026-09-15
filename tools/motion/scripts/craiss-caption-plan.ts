// ============================================================
// Craiss Untertitel-Mix — Plan erzeugen / prüfen
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3          (neu, falls nicht vorhanden)
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --force  (überschreiben)
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --check  (Prüfregeln + Anteile)
//   npx tsx scripts/craiss-caption-plan.ts funnel-v4 --split=cc-08:10,cc-11:6  (Satz an Wortindex teilen)
// Quelle: src/clients/craiss/captions/<id>.json (scripts/craiss-captions.ts)
// ============================================================
import fs from "node:fs";
import path from "node:path";
import { buildPlanFromPages, splitCueAt } from "../src/clients/craiss/captionMix/buildPlan";
import { captionPlanSchema, validatePlan } from "../src/clients/craiss/captionMix/plan";

const DIR = path.resolve(__dirname, "../src/clients/craiss/captions");
const args = process.argv.slice(2);
const force = args.includes("--force");
const check = args.includes("--check");
const splitArg = args.find((a) => a.startsWith("--split="));
const ids = args.filter((a) => !a.startsWith("--"));

for (const id of ids) {
  const planPath = path.join(DIR, `${id}.plan.json`);

  if (splitArg) {
    let plan = captionPlanSchema.parse(JSON.parse(fs.readFileSync(planPath, "utf8")));
    for (const spec of splitArg.slice("--split=".length).split(",")) {
      const [cueId, at] = spec.split(":");
      plan = splitCueAt(plan, cueId, Number(at));
      console.log(`${id}: ${cueId} bei Wort ${at} geteilt`);
    }
    fs.writeFileSync(planPath, JSON.stringify(plan, null, 1) + "\n");
    continue;
  }

  if (check) {
    const plan = captionPlanSchema.parse(JSON.parse(fs.readFileSync(planPath, "utf8")));
    const errors = validatePlan(plan);
    const counts: Record<string, number> = {};
    for (const c of plan.cues) counts[c.treatment] = (counts[c.treatment] ?? 0) + 1;
    const glass = plan.cues.filter((c) => c.glass).length;
    console.log(`${id}: ${plan.cues.length} Sätze — ${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(", ")}, Glas ${glass}`);
    for (const e of errors) console.log(`  ✗ ${e}`);
    if (errors.length === 0) console.log("  ✓ keine Fehler");
    else process.exitCode = 1;
    continue;
  }

  if (fs.existsSync(planPath) && !force) {
    console.log(`${id}: Plan existiert schon — mit --force überschreiben`);
    continue;
  }
  const pages = JSON.parse(fs.readFileSync(path.join(DIR, `${id}.json`), "utf8")).pages;
  const plan = buildPlanFromPages(id, pages);
  fs.writeFileSync(planPath, JSON.stringify(plan, null, 1) + "\n");
  console.log(`${id}: ${plan.cues.length} Sätze → ${planPath}`);
  for (const c of plan.cues) {
    console.log(`  ${c.id} ${c.start.toFixed(2)}–${c.end.toFixed(2)}  ${c.tokens.map((t, i) => `${i}:${t.text}`).join(" ")}`);
  }
}
