/**
 * Neuen Kunden anlegen
 *
 * Usage:
 *   npm run new:client -- --name "Kundenname"
 *
 * Was passiert:
 *   1. Erstellt Ordner src/clients/<slug>/
 *   2. Erstellt brand.json mit Platzhalter-Werten
 *   3. Erstellt public/clients/<slug>/ fuer Logo & Brand-Assets
 *
 * Danach (CI-zuerst, siehe WORKFLOW-Motion.md):
 *   → brand.json oeffnen und Farben/Fonts einpflegen
 *   → Logo nach public/clients/<slug>/ legen und Pfad in brand.json eintragen
 */

import fs from "fs";
import path from "path";

// --- Parse Args ---
const args = process.argv.slice(2);
const nameIndex = args.indexOf("--name");

if (nameIndex === -1 || !args[nameIndex + 1]) {
  console.log(`
  Neuen Kunden anlegen:
    npm run new:client -- --name "Kundenname"

  Beispiel:
    npm run new:client -- --name "Acme Corp"
  `);
  process.exit(1);
}

const clientName = args[nameIndex + 1];
const slug = clientName
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/^-|-$/g, "");

const clientDir = path.join(__dirname, "..", "src", "clients", slug);

if (fs.existsSync(clientDir)) {
  console.error(`\n  Kunde "${slug}" existiert bereits!\n`);
  process.exit(1);
}

// --- Ordner erstellen ---
const publicAssetsDir = path.join(__dirname, "..", "public", "clients", slug);
fs.mkdirSync(publicAssetsDir, { recursive: true });
fs.mkdirSync(path.join(clientDir, "projects"), { recursive: true });

// --- brand.json erstellen ---
const brand = {
  name: clientName,
  colors: {
    primary: "#3B82F6",
    secondary: "#1E293B",
    accent: "#F59E0B",
    background: "#FFFFFF",
    text: "#0F172A",
  },
  fonts: {
    heading: "Inter",
    body: "Inter",
  },
  logo: "",
  style: {
    borderRadius: 8,
    animationSpeed: "normal",
  },
};

fs.writeFileSync(
  path.join(clientDir, "brand.json"),
  JSON.stringify(brand, null, 2) + "\n"
);

fs.writeFileSync(path.join(publicAssetsDir, ".gitkeep"), "");
fs.writeFileSync(path.join(clientDir, "projects", ".gitkeep"), "");

console.log(`
  ✓ Kunde "${clientName}" angelegt!

  Ordner: src/clients/${slug}/

  Naechste Schritte:

  1. Oeffne src/clients/${slug}/brand.json
     und passe die Farben und Fonts an:

     {
       "colors": {
         "primary":    "#FF6B00",   ← Hauptfarbe
         "secondary":  "#1A1A2E",   ← Zweitfarbe / Hintergrund
         "accent":     "#00D4FF",   ← Akzentfarbe
         "background": "#FFFFFF",   ← Heller Hintergrund
         "text":       "#0F172A"    ← Textfarbe
       },
       "fonts": {
         "heading": "Montserrat",   ← Google Font Name
         "body":    "Inter"         ← Google Font Name
       }
     }

  2. Logo nach public/clients/${slug}/ legen (SVG bevorzugt) und in
     brand.json eintragen: "logo": "clients/${slug}/logo.svg"
     (CI-zuerst-Regel: brand.json muss VOR der ersten Komposition
     vollstaendig sein — siehe WORKFLOW-Motion.md)

  3. Neues Projekt anlegen:
     npm run new:project -- --client ${slug} --name "mein-projekt"
`);
