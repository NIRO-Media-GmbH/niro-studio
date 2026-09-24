// Eigener Einstieg für die akut-Ads (2026-09-21, Studio-Mac): rendert nur Akut-Ad-<Nr>,
// damit die gemeinsame Root.tsx (auf beiden Macs parallel geändert) unangetastet bleibt.
// Render: npx remotion render src/entry-akut.tsx Akut-Ad-<Nr> <out.mov> --props=<json> --public-dir=public-akut
import React from "react";
import { Composition, registerRoot } from "remotion";
import { AkutAd, akutAdSchema, akutAdDefaults, calculateAkutAd, AKUT_NUMMERN } from "./clients/akut/projects/ads-2608/AkutAd";

const AkutRoot: React.FC = () => (
  <>
    {AKUT_NUMMERN.map((nr) => (
      <Composition
        key={nr}
        id={`Akut-Ad-${nr}`}
        component={AkutAd}
        schema={akutAdSchema}
        defaultProps={akutAdDefaults(nr)}
        calculateMetadata={calculateAkutAd}
      />
    ))}
  </>
);

registerRoot(AkutRoot);
