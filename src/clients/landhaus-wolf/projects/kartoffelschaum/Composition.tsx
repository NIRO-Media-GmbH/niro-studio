// ============================================================
// Landhaus Wolf — Kartoffelschaum
// Kartoffelschaum mit brûliertem Eigelb & Périgord-Trüffel (~2:30)
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

export const landhausWolfKartoffelschaumSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfKartoffelschaumSchema>;

export const LandhausWolfKartoffelschaum: React.FC<Props> = ({
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
              src={staticFile("projects/landhaus-wolf-kochvideos/kartoffelschaum.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:04) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <SectionTitle
            title="Kartoffelschaum"
            subtitle="Ein Klassiker unserer Gäste"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <Callout
            text="Klassiker"
            subtext="Unsere Gäste lieben es"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: KARTOFFELN SCHÄLEN (0:05 - 0:14) ===== */}
        <Sequence from={s(t("00:00:04,540")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Kartoffeln schälen" />
        </Sequence>

        <Sequence from={s(t("00:00:04,540")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Annabelle schälen"
            subtitle="Keime vorher entfernen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:09,660")) + GAP} durationInFrames={s(4)}>
          <Callout
            text="Annabelle"
            subtext="Keime vorher rausmachen"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 2: BUTTER (0:15 - 0:25) ===== */}
        <Sequence from={s(t("00:00:19,359")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="Butter" />
        </Sequence>

        <Sequence from={s(t("00:00:19,359")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Ordentlich Butter"
            subtitle="Auf keinen Fall sparen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:22,359")) + GAP * 2} durationInFrames={s(4)}>
          <Callout
            text="Butter!"
            subtext="Auf keinen Fall sparen"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: PÜRIEREN (0:26 - 0:42) ===== */}
        <Sequence from={s(t("00:00:25,410")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Pürieren" />
        </Sequence>

        <Sequence from={s(t("00:00:25,410")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Pürieren"
            subtitle="Sämig und gleichmäßig"
          />
        </Sequence>

        <Sequence from={s(t("00:00:28,410")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Schön sämig pürieren"
            subtitle="Gleichmäßige Konsistenz"
          />
        </Sequence>

        <Sequence from={s(t("00:00:31,730")) + GAP * 3} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Kurze Pausen einlegen!"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 4: RINDERKRAFTBRÜHE (0:43 - 0:59) ===== */}
        <Sequence from={s(t("00:00:42,289")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Konsistenz" />
        </Sequence>

        <Sequence from={s(t("00:00:42,289")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Rinderkraftbrühe"
            subtitle="Langsam antasten"
          />
        </Sequence>

        <Sequence from={s(t("00:00:42,289")) + GAP * 4} durationInFrames={s(8)}>
          <IngredientList
            items={[
              "Rinderkraftbrühe",
              "Kartoffelpüree (sämig)",
              "Ordentlich Butter",
            ]}
            title="Für den Siphon"
          />
        </Sequence>

        <Sequence from={s(t("00:00:50,189")) + GAP * 4} durationInFrames={s(5)}>
          <Callout
            text="Wichtig"
            subtext="Nicht zu fest, nicht zu flüssig!"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 5: WÜRZEN (1:00 - 1:13) ===== */}
        <Sequence from={s(t("00:01:04,250")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Würzen" />
        </Sequence>

        <Sequence from={s(t("00:01:04,250")) + GAP * 5} durationInFrames={s(3)}>
          <SectionTitle
            title="Kräftig würzen"
            subtitle="Fast überwürzen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:04,250")) + GAP * 5 + s(3)} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Fast überwürzen — Luft nimmt Geschmack!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:09,129")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Fast überwürzen"
            subtitle="Luft nimmt Geschmack"
          />
        </Sequence>

        {/* ===== STEP 6: SIPHON (1:14 - 1:30) ===== */}
        <Sequence from={s(t("00:01:13,430")) + GAP * 6} durationInFrames={s(5)}>
          <StepBadge step={6} label="Siphon" />
        </Sequence>

        <Sequence from={s(t("00:01:13,430")) + GAP * 6} durationInFrames={s(3)}>
          <SectionTitle
            title="Siphon füllen"
            subtitle="Warm aber nicht zu heiß"
          />
        </Sequence>

        <Sequence from={s(t("00:01:19,230")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Temperatur"
            subtext="Warm, nicht zu heiß!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:26,420")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Schütteln!"
            subtext="Ventil macht dicht"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 7: WASSERBAD (1:31 - 1:55) ===== */}
        <Sequence from={s(t("00:01:31,280")) + GAP * 7} durationInFrames={s(5)}>
          <StepBadge step={7} label="Wasserbad" />
        </Sequence>

        <Sequence from={s(t("00:01:31,280")) + GAP * 7} durationInFrames={s(3)}>
          <SectionTitle
            title="Wasserbad"
            subtitle="Siphon warmhalten"
          />
        </Sequence>

        <Sequence from={s(t("00:01:31,280")) + GAP * 7 + s(3)} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Metalldeckel unter den Siphon!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:36,560")) + GAP * 7} durationInFrames={s(4)}>
          <SectionTitle
            title="Siphon sichern"
            subtitle="Metalldeckel unterlegen"
          />
        </Sequence>

        {/* ===== STEP 8: PÉRIGORD-TRÜFFEL (1:56 - 2:10) ===== */}
        <Sequence from={s(t("00:01:56,599")) + GAP * 8} durationInFrames={s(5)}>
          <StepBadge step={8} label="Périgord-Trüffel" />
        </Sequence>

        <Sequence from={s(t("00:01:56,599")) + GAP * 8} durationInFrames={s(3)}>
          <SectionTitle
            title="Périgord-Trüffel"
            subtitle="Ganz frisch · Voller Reifegrad"
          />
        </Sequence>

        <Sequence from={s(t("00:02:01,769")) + GAP * 8} durationInFrames={s(4)}>
          <Callout
            text="Top-Qualität"
            subtext="Voller Reifegrad"
            position="top-right"
          />
        </Sequence>

        {/* ===== ANRICHTEN (2:11 - 2:22) ===== */}
        <Sequence from={s(t("00:02:11,840")) + GAP * 9} durationInFrames={s(4)}>
          <SectionTitle
            title="Anrichten"
            subtitle="Kartoffelschaum · Eigelb · Trüffel"
          />
        </Sequence>

        <Sequence from={s(t("00:02:17,530")) + GAP * 9} durationInFrames={s(5)}>
          <Callout
            text="Fertig!"
            subtext="Schaum · Eigelb · Trüffel"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:02:17,530")) + GAP * 9 + s(6) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
