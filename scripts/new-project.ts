/**
 * Neues Animations-Projekt fuer einen Kunden anlegen
 *
 * Usage:
 *   npm run new:project -- --client <slug> --name "projektname"
 *
 * Was passiert:
 *   1. Erstellt Projekt-Ordner mit Composition.tsx
 *   2. Fuegt die Composition automatisch in Root.tsx ein
 *   3. Ladet die brand.json des Kunden automatisch
 *
 * Danach:
 *   → npm run studio  (und die neue Composition ist sofort sichtbar)
 */

import fs from "fs";
import path from "path";

// --- Parse Args ---
const args = process.argv.slice(2);
const clientIndex = args.indexOf("--client");
const nameIndex = args.indexOf("--name");

if (
  clientIndex === -1 ||
  !args[clientIndex + 1] ||
  nameIndex === -1 ||
  !args[nameIndex + 1]
) {
  console.log(`
  Neues Projekt anlegen:
    npm run new:project -- --client <client-slug> --name "projektname"

  Beispiel:
    npm run new:project -- --client acme-corp --name "social-ad-01"

  Vorhandene Kunden:`);

  // List existing clients
  const clientsDir = path.join(__dirname, "..", "src", "clients");
  if (fs.existsSync(clientsDir)) {
    const clients = fs
      .readdirSync(clientsDir)
      .filter((d) =>
        fs.existsSync(path.join(clientsDir, d, "brand.json"))
      );
    if (clients.length > 0) {
      clients.forEach((c) => console.log(`    - ${c}`));
    } else {
      console.log(
        "    (keine) — erstelle zuerst einen: npm run new:client -- --name \"Name\""
      );
    }
  }
  console.log("");
  process.exit(1);
}

const clientSlug = args[clientIndex + 1];
const projectName = args[nameIndex + 1];
const projectSlug = projectName
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/^-|-$/g, "");

const clientDir = path.join(__dirname, "..", "src", "clients", clientSlug);
const projectDir = path.join(clientDir, "projects", projectSlug);

// --- Validierung ---
if (!fs.existsSync(clientDir)) {
  console.error(`\n  Kunde "${clientSlug}" nicht gefunden!`);
  console.error(
    `  Erstelle ihn zuerst: npm run new:client -- --name "${clientSlug}"\n`
  );
  process.exit(1);
}

if (!fs.existsSync(path.join(clientDir, "brand.json"))) {
  console.error(`\n  brand.json fehlt fuer "${clientSlug}"!\n`);
  process.exit(1);
}

if (fs.existsSync(projectDir)) {
  console.error(`\n  Projekt "${projectSlug}" existiert bereits!\n`);
  process.exit(1);
}

// --- Helpers ---
function toPascalCase(str: string): string {
  return str
    .split("-")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join("");
}

const pascalClient = toPascalCase(clientSlug);
const pascalProject = toPascalCase(projectSlug);
const componentName = pascalClient + pascalProject;
const schemaName = componentName.charAt(0).toLowerCase() + componentName.slice(1) + "Schema";
const compositionId = pascalClient + "-" + pascalProject;

// --- Projekt-Ordner erstellen ---
fs.mkdirSync(projectDir, { recursive: true });

// --- Composition.tsx generieren ---
const compositionCode = `import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { zTextarea } from "@remotion/zod-types";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { GradientBackground } from "../../../../components/backgrounds/GradientBackground";
import { FadeInText } from "../../../../components/text/FadeInText";
import { LogoReveal } from "../../../../components/effects/LogoReveal";
import brandJson from "../../brand.json";

const ci = loadBrand("${clientSlug}", brandJson as any);

export const ${schemaName} = projectPropsSchema.extend({
  headline: zTextarea(),
  bodyText: zTextarea(),
});

type Props = z.infer<typeof ${schemaName}>;

export const ${componentName}: React.FC<Props> = ({
  headline = "Deine Headline",
  bodyText = "Dein Text hier",
  transparent = false,
}) => {
  const { durationInFrames, height } = useVideoConfig();

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <GradientBackground
            colors={[ci.colors.secondary, ci.colors.primary]}
          />
        )}

        <Sequence from={0} durationInFrames={Math.floor(durationInFrames * 0.6)}>
          <FadeInText
            text={headline}
            mode="word"
            fontSizeRatio={0.06}
            color="#FFFFFF"
            fontWeight="800"
          />
        </Sequence>

        <Sequence
          from={Math.floor(durationInFrames * 0.5)}
          durationInFrames={Math.floor(durationInFrames * 0.3)}
        >
          <FadeInText
            text={bodyText}
            mode="word"
            fontSizeRatio={0.035}
            color="rgba(255,255,255,0.8)"
            fontWeight="400"
          />
        </Sequence>

        <Sequence
          from={Math.floor(durationInFrames * 0.75)}
          durationInFrames={Math.floor(durationInFrames * 0.25)}
        >
          <LogoReveal mode="scale" size={0.2} />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
`;

fs.writeFileSync(path.join(projectDir, "Composition.tsx"), compositionCode);

// --- Root.tsx automatisch updaten ---
const rootPath = path.join(__dirname, "..", "src", "Root.tsx");
let rootContent = fs.readFileSync(rootPath, "utf-8");

// Import hinzufuegen (vor dem letzten bestehenden Import)
const importLine = `import { ${componentName}, ${schemaName} } from "./clients/${clientSlug}/projects/${projectSlug}/Composition";`;

// Finde die letzte Import-Zeile
const importLines = rootContent.split("\n");
let lastImportIndex = 0;
for (let i = 0; i < importLines.length; i++) {
  if (importLines[i].startsWith("import ")) {
    lastImportIndex = i;
  }
}

// Import einfuegen
importLines.splice(lastImportIndex + 1, 0, importLine);
rootContent = importLines.join("\n");

// Composition in den Clients-Folder einfuegen (vor dem schliessenden </Folder> des Clients-Bereichs)
const compositionBlock = `
        <Folder name="${pascalClient}">
          <Composition
            id="${compositionId}"
            component={${componentName}}
            schema={${schemaName}}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 8,
              transparent: false,
              headline: "Deine Headline",
              bodyText: "Dein Text hier",
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>`;

// Vor dem letzten </Folder> im Clients-Bereich einfuegen
const closingClientsFolder = "      </Folder>\n    </>";
rootContent = rootContent.replace(
  closingClientsFolder,
  compositionBlock + "\n      </Folder>\n    </>"
);

fs.writeFileSync(rootPath, rootContent);

console.log(`
  ✓ Projekt "${projectName}" angelegt!

  Dateien:
    src/clients/${clientSlug}/projects/${projectSlug}/Composition.tsx

  Root.tsx wurde automatisch aktualisiert!

  Jetzt starten:
    npm run studio

  Die Composition "${compositionId}" ist sofort im Studio sichtbar.
  Dort kannst du:
    - Format umschalten (portrait / landscape)
    - FPS aendern (24 / 25 / 30 / 60)
    - Texte live bearbeiten
    - Farben anpassen

  Rendern:
    npm run render:web -- ${compositionId}
    npm run render:transparent:prores -- ${compositionId}
`);
