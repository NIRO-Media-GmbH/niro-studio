// Eigener Einstieg für die Dold-Reel-Entwürfe (2026-09-17): rendert nur Dold-ReelOverlay,
// damit die gemeinsame Root.tsx (parallel in Arbeit) unangetastet bleibt.
// Render: npx remotion render src/entry-dold-entwurf.tsx Dold-ReelOverlay <out.mov> --props=<json> --public-dir=public-dold
import React from "react";
import { Composition, registerRoot } from "remotion";
import { DoldReelOverlay, calculateDoldReel, doldReelDefaults, doldReelSchema } from "./clients/dold/projects/reel-overlay/Composition";

const DoldEntwurfRoot: React.FC = () => (
  <Composition
    id="Dold-ReelOverlay"
    component={DoldReelOverlay}
    schema={doldReelSchema}
    defaultProps={doldReelDefaults}
    calculateMetadata={calculateDoldReel}
    width={1080}
    height={1920}
    fps={25}
    durationInFrames={300}
  />
);

registerRoot(DoldEntwurfRoot);
