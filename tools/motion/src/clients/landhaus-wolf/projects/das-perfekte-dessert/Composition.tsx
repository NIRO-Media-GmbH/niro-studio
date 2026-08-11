// ============================================================
// Landhaus Wolf — Das Perfekte Dessert
// Lavendelschnitte mit Schoko-Glacage (~3:10)
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig, OffthreadVideo, staticFile } from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import brandJson from "../../brand.json";
import {
  SectionTitle,
  IngredientList,
  Callout,
  StepBadge,
  BrandSignOff,
  t,
} from "../../components";

const ci = loadBrand("landhaus-wolf", brandJson as any);

export const landhausWolfDasPerfekteDessertSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfDasPerfekteDessertSchema>;

export const LandhausWolfDasPerfekteDessert: React.FC<Props> = ({
  transparent = true,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);
  const GAP = fps; // 1 second gap between scenes

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/landhaus-wolf-kochvideos/das-perfekte-dessert.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:05) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <SectionTitle
            title="Das perfekte Dessert"
            subtitle="Ende vom Degustationsmenü"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <Callout
            text="Finale"
            subtext="Degustationsmenü"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: DER AUFBAU (0:06 - 0:22) ===== */}
        <Sequence from={s(t("00:00:05,540")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Der Aufbau" />
        </Sequence>

        <Sequence from={s(t("00:00:05,540")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Die Schichten"
            subtitle="Von unten nach oben"
          />
        </Sequence>

        <Sequence from={s(t("00:00:05,540")) + GAP} durationInFrames={s(7)}>
          <IngredientList
            items={[
              "Schokolade (Boden)",
              "Biskuit",
              "Schokoladenganache",
              "Lavendelmousse (hell)",
            ]}
            title="Aufbau"
          />
        </Sequence>

        <Sequence from={s(t("00:00:08,540")) + GAP} durationInFrames={s(4)}>
          <SectionTitle
            title="Schichten von unten"
            subtitle="Schoko · Biskuit · Ganache · Mousse"
          />
        </Sequence>

        {/* ===== STEP 2: GLACAGE VORBEREITEN (0:23 - 0:43) ===== */}
        <Sequence from={s(t("00:00:23,059")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="Glacage" />
        </Sequence>

        <Sequence from={s(t("00:00:23,059")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Schoko-Glacage"
            subtitle="Valrhona Napache Nœtre"
          />
        </Sequence>

        <Sequence from={s(t("00:00:23,059")) + GAP * 2} durationInFrames={s(6)}>
          <IngredientList
            items={[
              "Sahne (ca. 190g)",
              "Valrhona Napache Nœtre",
              "Calais (Schokoladen-Stücke)",
            ]}
            title="Glacage"
          />
        </Sequence>

        <Sequence from={s(t("00:00:29,679")) + GAP * 2} durationInFrames={s(5)}>
          <Callout
            text="~190g Sahne"
            subtext="Valrhona Napache Nœtre"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: KOCHEN & MIXEN (0:44 - 1:02) ===== */}
        <Sequence from={s(t("00:00:46,350")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Kochen & Mixen" />
        </Sequence>

        <Sequence from={s(t("00:00:46,350")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Kochen und mixen"
            subtitle="Ganz vorsichtig"
          />
        </Sequence>

        <Sequence from={s(t("00:00:46,350")) + GAP * 3} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Möglichst wenig Luft einarbeiten!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:52,229")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Vorsichtig mixen"
            subtitle="Wenig Luft einarbeiten"
          />
        </Sequence>

        {/* ===== STEP 4: GLASIEREN (1:03 - 1:24) ===== */}
        <Sequence from={s(t("00:01:03,500")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Glasieren" />
        </Sequence>

        <Sequence from={s(t("00:01:03,500")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Lavendelschnitte glasieren"
            subtitle="Ideale Temperatur"
          />
        </Sequence>

        <Sequence from={s(t("00:01:09,480")) + GAP * 4} durationInFrames={s(4)}>
          <SectionTitle
            title="Gleichmäßig glasieren"
            subtitle="Auf einmal drüber"
          />
        </Sequence>

        <Sequence from={s(t("00:01:19,519")) + GAP * 4} durationInFrames={s(4)}>
          <Callout
            text="Spachtel"
            subtext="Vorsichtig auf den Teller"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 5: PÂTE À CIGARETTE (1:25 - 1:53) ===== */}
        <Sequence from={s(t("00:01:24,500")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Hippenteig" />
        </Sequence>

        <Sequence from={s(t("00:01:24,500")) + GAP * 5} durationInFrames={s(3)}>
          <SectionTitle
            title="Pâte à Cigarette"
            subtitle="Hippenteig · Zacken-Teigschaber"
          />
        </Sequence>

        <Sequence from={s(t("00:01:29,640")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Streifen ziehen"
            subtitle="Zacken-Teigschaber"
          />
        </Sequence>

        <Sequence from={s(t("00:01:40,060")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="Gleichmäßig!"
            subtext="Dann ab in den Ofen"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 6: BACKEN & ROLLEN (1:54 - 2:22) ===== */}
        <Sequence from={s(t("00:02:04,180")) + GAP * 6} durationInFrames={s(5)}>
          <StepBadge step={6} label="Backen & Rollen" />
        </Sequence>

        <Sequence from={s(t("00:02:04,180")) + GAP * 6} durationInFrames={s(3)}>
          <SectionTitle
            title="Backen und sofort rollen"
            subtitle="Schnell sein!"
          />
        </Sequence>

        <Sequence from={s(t("00:02:04,180")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="180°C"
            subtext="Vorgeheizt"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:02:11,840")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Schnell!"
            subtext="Bevor der Teig fest wird"
            position="bottom-right"
          />
        </Sequence>

        <Sequence from={s(t("00:02:20,360")) + GAP * 6} durationInFrames={s(5)}>
          <Callout
            text="Timing"
            subtext="Nicht zu wenig gebacken!"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 7: ANRICHTEN (2:23 - 2:58) ===== */}
        <Sequence from={s(t("00:02:31,539")) + GAP * 7} durationInFrames={s(5)}>
          <StepBadge step={7} label="Anrichten" />
        </Sequence>

        <Sequence from={s(t("00:02:31,539")) + GAP * 7} durationInFrames={s(3)}>
          <SectionTitle
            title="Anrichten"
            subtitle="Alle Komponenten zusammen"
          />
        </Sequence>

        <Sequence from={s(t("00:02:31,539")) + GAP * 7} durationInFrames={s(8)}>
          <IngredientList
            items={[
              "Glasierte Lavendelschnitte",
              "Cigarette-Rolle oben drauf",
              "Schokoladeneis (rund geformt)",
              "Restliche Schoko-Glacage",
            ]}
            title="Anrichten"
          />
        </Sequence>

        <Sequence from={s(t("00:02:37,240")) + GAP * 7} durationInFrames={s(4)}>
          <SectionTitle
            title="Zusammensetzen"
            subtitle="Schnitte · Rolle · Eis"
          />
        </Sequence>

        <Sequence from={s(t("00:02:48,259")) + GAP * 7} durationInFrames={s(4)}>
          <Callout
            text="Geometrie"
            subtext="Eis rund geformt"
            position="top-right"
          />
        </Sequence>

        {/* ===== FINALE ===== */}
        <Sequence from={s(t("00:03:00,099")) + GAP * 8} durationInFrames={s(5)}>
          <Callout
            text="Voilà!"
            subtext="Das perfekte Dessert"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:03:00,099")) + GAP * 8 + s(5) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
