// ============================================================
// Landhaus Wolf — Die perfekte Beilage
// Schupfnudeln zum Wild (~1:34)
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

export const landhausWolfDiePerfekteBeilageSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfDiePerfekteBeilageSchema>;

export const LandhausWolfDiePerfekteBeilage: React.FC<Props> = ({
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
              src={staticFile("die-perfekte-beilage.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:05) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <SectionTitle
            title="Die perfekte Beilage"
            subtitle="Schupfnudeln zum Wild"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <Callout
            text="Beilage"
            subtext="Die beste zum Wild"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: KARTOFFELN PRESSEN (0:06 - 0:15) ===== */}
        <Sequence from={s(t("00:00:05,320")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Kartoffeln pressen" />
        </Sequence>

        <Sequence from={s(t("00:00:05,320")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Durch das Haarsieb"
            subtitle="Für perfekten Teig"
          />
        </Sequence>

        <Sequence from={s(t("00:00:08,320")) + GAP} durationInFrames={s(4)}>
          <Callout
            text="Haarsieb"
            subtext="Fein durchstreichen"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 2: TEIG MISCHEN (0:16 - 0:25) ===== */}
        <Sequence from={s(t("00:00:10,539")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="Teig mischen" />
        </Sequence>

        <Sequence from={s(t("00:00:10,539")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Teig vermengen"
            subtitle="Fluffig, nicht zu fest"
          />
        </Sequence>

        <Sequence from={s(t("00:00:10,539")) + GAP * 2} durationInFrames={s(5)}>
          <IngredientList
            items={[
              "Kartoffeln (500g max)",
              "Mehl (250g max)",
              "Eigelb",
              "Salz",
              "Muskat",
            ]}
          />
        </Sequence>

        <Sequence from={s(t("00:00:15,500")) + GAP * 2} durationInFrames={s(4)}>
          <Callout
            text="Vermengen"
            subtext="Alles zusammen kneten"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: KONSISTENZ (0:26 - 0:33) ===== */}
        <Sequence from={s(t("00:00:19,839")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Konsistenz" />
        </Sequence>

        <Sequence from={s(t("00:00:19,839")) + GAP * 3} durationInFrames={s(6)}>
          <Callout
            text="Tipp"
            subtext="Max 500g Kartoffeln + 250g Mehl"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:19,839")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Fluffig bleiben"
            subtitle="Trockene Hände!"
          />
        </Sequence>

        {/* ===== STEP 4: ROLLEN & SCHNEIDEN (0:34 - 0:48) ===== */}
        <Sequence from={s(t("00:00:33,549")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Rollen" />
        </Sequence>

        <Sequence from={s(t("00:00:33,549")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Dünn ausrollen"
            subtitle="Gleichmäßig portionieren"
          />
        </Sequence>

        <Sequence from={s(t("00:00:38,070")) + GAP * 4} durationInFrames={s(4)}>
          <SectionTitle
            title="Dünn portionieren"
            subtitle="Arbeitsfläche melieren"
          />
        </Sequence>

        {/* ===== STEP 5: FORMEN (0:49 - 0:58) ===== */}
        <Sequence from={s(t("00:00:48,469")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Formen" />
        </Sequence>

        <Sequence from={s(t("00:00:48,469")) + GAP * 5} durationInFrames={s(6)}>
          <Callout
            text="Form"
            subtext="Vorne und hinten spitz!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:48,469")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Spitz zulaufen lassen"
            subtitle="Vorne und hinten"
          />
        </Sequence>

        {/* ===== STEP 6: KOCHEN (0:59 - 1:13) ===== */}
        <Sequence from={s(t("00:00:58,170")) + GAP * 6} durationInFrames={s(5)}>
          <StepBadge step={6} label="Kochen" />
        </Sequence>

        <Sequence from={s(t("00:00:58,170")) + GAP * 6} durationInFrames={s(3)}>
          <SectionTitle
            title="In Salzwasser kochen"
            subtitle="Gut salzen, in einem Schwung"
          />
        </Sequence>

        <Sequence from={s(t("00:01:03,679")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Auf einmal!"
            subtext="Alle rein & aufkochen"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 7: EISBAD (1:14 - 1:28) ===== */}
        <Sequence from={s(t("00:01:13,209")) + GAP * 7} durationInFrames={s(5)}>
          <StepBadge step={7} label="Abkühlen" />
        </Sequence>

        <Sequence from={s(t("00:01:13,209")) + GAP * 7} durationInFrames={s(3)}>
          <SectionTitle
            title="Eisbad & aufbewahren"
            subtitle="Garprozess unterbrechen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:16,629")) + GAP * 7} durationInFrames={s(4)}>
          <Callout
            text="Eisbad"
            subtext="Garprozess unterbrechen"
            position="top-right"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:01:16,629")) + GAP * 7 + s(6) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
