// ============================================================
// Landhaus Wolf — Petrischale
// Hamachi-Präsentation im Gourmet-Restaurant (~1:28)
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

export const landhausWolfPetrischaleSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfPetrischaleSchema>;

export const LandhausWolfPetrischale: React.FC<Props> = ({
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
              src={staticFile("projects/landhaus-wolf-kochvideos/petrischale.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:06) ===== */}
        <Sequence from={s(t("00:00:00,820"))} durationInFrames={s(5)}>
          <SectionTitle
            title="Petrischale"
            subtitle="Hamachi im Gourmet"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,820"))} durationInFrames={s(5)}>
          <Callout
            text="Hamachi"
            subtext="Gebeizt & angerichtet"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: HAMACHI SCHNEIDEN (0:07 - 0:17) ===== */}
        <Sequence from={s(t("00:00:06,139")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Hamachi schneiden" />
        </Sequence>

        <Sequence from={s(t("00:00:06,139")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Tartar schneiden"
            subtitle="Tiefgefroren vorgeformt"
          />
        </Sequence>

        <Sequence from={s(t("00:00:10,039")) + GAP} durationInFrames={s(4)}>
          <SectionTitle
            title="Tiefgefroren formen"
            subtitle="Als Tartar geschnitten"
          />
        </Sequence>

        {/* ===== STEP 2: WÜRZEN (0:18 - 0:23) ===== */}
        <Sequence from={s(t("00:00:17,640")) + GAP * 2} durationInFrames={s(2)}>
          <StepBadge step={2} label="Würzen" />
        </Sequence>

        <Sequence from={s(t("00:00:17,640")) + GAP * 2} durationInFrames={s(2)}>
          <SectionTitle
            title="Salz & Pfeffer"
            subtitle="Einfach würzen"
          />
        </Sequence>

        {/* ===== STEP 3: CHAMPAGNER-VINAIGRETTE (0:24 - 0:33) ===== */}
        <Sequence from={s(t("00:00:19,350")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Vinaigrette" />
        </Sequence>

        <Sequence from={s(t("00:00:19,350")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Champagner-Vinaigrette"
            subtitle="Champagner-Essig + Limette"
          />
        </Sequence>

        <Sequence from={s(t("00:00:23,570")) + GAP * 3} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Champagner-Essig, kein Champagner!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:23,570")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Essig & Zeste"
            subtitle="Bio-Limette"
          />
        </Sequence>

        {/* ===== STEP 4: NOCKE (0:34 - 0:47) ===== */}
        <Sequence from={s(t("00:00:33,259")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Nocke formen" />
        </Sequence>

        <Sequence from={s(t("00:00:33,259")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Nocke formen"
            subtitle="Schwarzer Rettich Püree"
          />
        </Sequence>

        <Sequence from={s(t("00:00:38,899")) + GAP * 4} durationInFrames={s(4)}>
          <Callout
            text="3 Punkte"
            subtext="Rettich-Püree Nocke"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 5: GARNITUR (0:48 - 1:05) ===== */}
        <Sequence from={s(t("00:00:47,920")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Garnitur" />
        </Sequence>

        <Sequence from={s(t("00:00:47,920")) + GAP * 5} durationInFrames={s(3)}>
          <SectionTitle
            title="Garnitur"
            subtitle="Die feinen Details"
          />
        </Sequence>

        <Sequence from={s(t("00:00:53,500")) + GAP * 5} durationInFrames={s(12)}>
          <IngredientList
            items={[
              "Schwarzer Rettich (gegarter)",
              "Schwarzer Rettich (Formen)",
              "Crème fraîche",
              "Kaviar (Aquakultur)",
              "Vinaigrette Pünktchen",
            ]}
            title="Garnitur"
          />
        </Sequence>

        <Sequence from={s(t("00:00:53,500")) + GAP * 5} durationInFrames={s(5)}>
          <SectionTitle
            title="Feine Details"
            subtitle="Rettich · Crème fraîche · Kaviar"
          />
        </Sequence>

        {/* ===== FINALE (1:06 - 1:22) ===== */}
        <Sequence from={s(t("00:01:17,409")) + GAP * 6} durationInFrames={s(5)}>
          <Callout
            text="Deckel drauf!"
            subtext="Gang servierbereit"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:01:17,409")) + GAP * 6 + s(5) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
