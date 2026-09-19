/**
 * Remocn-Komponenten installieren (Ersatz für `npx shadcn add @remocn/…`)
 *
 * Usage:
 *   npm run remocn:add -- <name> [<name> …]        z. B. npm run remocn:add -- whip-pan number-wheel
 *   npm run remocn:add -- --force <name>           vorhandene Dateien überschreiben
 *   npm run remocn:add -- --list                   installierte Komponenten zeigen
 *
 * Was passiert:
 *   1. Holt https://remocn.dev/r/<name>.json (Katalog: https://remocn.dev/llms-components.txt)
 *   2. Schreibt die Dateien BYTE-GENAU nach src/<target> (src/components/remocn/…, src/lib/remocn/…)
 *   3. Löst registryDependencies (@remocn/…) rekursiv auf
 *   4. Installiert fehlende npm-Abhängigkeiten (npm install <pkg>)
 *
 * Warum nicht die shadcn-CLI: Sie dedupliziert Tokens in ALLEN String-Literalen
 * (nicht nur in className) und macht dabei aus `split("\n")` ein `split("")`,
 * aus `"50% 50%"` ein `"50%"` und aus `rgba(0,0,0,0.5)` ein `rgba(0,0,0.5)` —
 * elf von 35 Dateien kamen beschädigt an (19.09.2026, shadcn 3.x).
 *
 * Lokale Anpassungen: Dateien, die wir bewusst geändert haben, stehen in
 * src/components/remocn/_NIRO-PATCHES.md — nach einem --force dort nachlesen
 * und die Änderungen wieder anwenden.
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const ROOT = path.resolve(__dirname, "..");
const REGISTRY = "https://remocn.dev/r";
const PREFIX = "@remocn/";

interface RegistryFile {
  path: string;
  type: string;
  target?: string;
  content: string;
}
interface RegistryItem {
  name: string;
  type: string;
  dependencies?: string[];
  registryDependencies?: string[];
  files: RegistryFile[];
}

// --- Args ---
const args = process.argv.slice(2);
const force = args.includes("--force");
const names = args.filter((a) => !a.startsWith("--")).map((n) => n.replace(PREFIX, ""));

if (args.includes("--list")) {
  const dir = path.join(ROOT, "src/components/remocn");
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".tsx")) : [];
  console.log(files.map((f) => f.replace(/\.tsx$/, "")).sort().join("\n"));
  process.exit(0);
}

if (names.length === 0) {
  console.log(`
  Remocn-Komponenten installieren:
    npm run remocn:add -- <name> [<name> …]
    npm run remocn:add -- --force <name>      (überschreiben)
    npm run remocn:add -- --list

  Katalog: https://remocn.dev/llms-components.txt
  `);
  process.exit(1);
}

// --- Helfer ---
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));
const installed = new Set<string>([
  ...Object.keys(pkg.dependencies ?? {}),
  ...Object.keys(pkg.devDependencies ?? {}),
]);

async function fetchItem(name: string): Promise<RegistryItem> {
  const res = await fetch(`${REGISTRY}/${name}.json`);
  if (!res.ok) throw new Error(`Registry-Eintrag „${name}“ nicht gefunden (${res.status})`);
  return (await res.json()) as RegistryItem;
}

function targetPath(file: RegistryFile): string {
  // Registry-Ziel ist z. B. "components/remocn/whip-pan.tsx" → bei uns unter src/
  const rel = (file.target ?? file.path.replace(/^registry\/[^/]+\//, "components/remocn/"))
    .replace(/^src\//, "");
  return path.join(ROOT, "src", rel);
}

// --- Auflösen und schreiben ---
const done = new Set<string>();
const toInstall = new Set<string>();
const written: string[] = [];
const skipped: string[] = [];

async function add(name: string): Promise<void> {
  if (done.has(name)) return;
  done.add(name);
  const item = await fetchItem(name);

  for (const dep of item.registryDependencies ?? []) {
    await add(dep.replace(PREFIX, ""));
  }
  for (const dep of item.dependencies ?? []) {
    if (!installed.has(dep)) toInstall.add(dep);
  }
  for (const file of item.files) {
    const out = targetPath(file);
    const rel = path.relative(ROOT, out);
    if (fs.existsSync(out) && !force) {
      skipped.push(rel);
      continue;
    }
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, file.content); // byte-genau, keine Transformation
    written.push(rel);
  }
}

(async () => {
  for (const n of names) await add(n);

  if (toInstall.size > 0) {
    const list = [...toInstall].join(" ");
    console.log(`\n  npm install ${list}\n`);
    execSync(`npm install ${list}`, { cwd: ROOT, stdio: "inherit" });
  }

  if (written.length) console.log(`\n  Geschrieben (${written.length}):\n    ${written.sort().join("\n    ")}`);
  if (skipped.length) console.log(`\n  Übersprungen, schon vorhanden (${skipped.length}; --force überschreibt):\n    ${skipped.sort().join("\n    ")}`);
  console.log(`\n  Fertig. Komponenten unter src/components/remocn/, Doku je Komponente: https://remocn.dev/docs/…/<name>.md\n`);
})().catch((err) => {
  console.error(`\n  Fehler: ${err.message}\n`);
  process.exit(1);
});
