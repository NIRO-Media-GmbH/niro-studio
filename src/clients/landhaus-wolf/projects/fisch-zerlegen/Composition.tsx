// ============================================================
// Landhaus Wolf — Fisch zerlegen
// Wolfsbarsch fachgerecht zerlegen (~2:08)
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useVideoConfig,
  OffthreadVideo,
  staticFile,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import brandJson from "../../brand.json";
import {
  SectionTitle,
  Callout,
  StepBadge,
  BrandSignOff,
  t,
} from "../../components";

const ci = loadBrand("landhaus-wolf", brandJson as any);

export const landhausWolfFischZerlegenSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfFischZerlegenSchema>;

export const LandhausWolfFischZerlegen: React.FC<Props> = ({
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
              src={staticFile("projects/landhaus-wolf-kochvideos/fisch-zerlegen.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:04) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <SectionTitle
            title="Fisch zerlegen"
            subtitle="Wolfsbarsch · 3 Kilo"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <Callout
            text="Wolfsbarsch"
            subtext="Fachgerecht zerlegt"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: AUSNEHMEN (0:04 - 0:26) ===== */}
        <Sequence from={s(t("00:00:04,440")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Ausnehmen" />
        </Sequence>

        <Sequence from={s(t("00:00:04,440")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Bauch aufschneiden"
            subtitle="Bis zur Unterseite vom Kopf"
          />
        </Sequence>

        <Sequence from={s(t("00:00:10,080")) + GAP} durationInFrames={s(4)}>
          <Callout
            text="Vorsicht!"
            subtext="Innereien nicht zerbrechen"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:16,660")) + GAP} durationInFrames={s(4)}>
          <SectionTitle
            title="Innereien entfernen"
            subtitle="Vorsichtig herausnehmen"
          />
        </Sequence>

        {/* ===== STEP 2: ZURICHTEN (0:27 - 0:39) ===== */}
        <Sequence from={s(t("00:00:27,579")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="Zurichten" />
        </Sequence>

        <Sequence from={s(t("00:00:27,579")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Zurück auf dem Brett"
            subtitle="Fisch komplett entledigt"
          />
        </Sequence>

        <Sequence from={s(t("00:00:33,520")) + GAP * 2} durationInFrames={s(4)}>
          <Callout
            text="~1 kg"
            subtext="Gewichtsverlust einplanen!"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 3: STACHELN (0:39 - 1:06) ===== */}
        <Sequence from={s(t("00:00:39,399")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Stacheln" />
        </Sequence>

        <Sequence from={s(t("00:00:39,399")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Flossen & Stacheln"
            subtitle="Unbedingt entfernen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:50,170")) + GAP * 3} durationInFrames={s(5)}>
          <Callout
            text="Achtung!"
            subtext="Stacheln → Blutvergiftung!"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:00,630")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Richtig fest!"
            subtitle="Mit Kraft wegschneiden"
          />
        </Sequence>

        {/* ===== STEP 4: KOPF ABTRENNEN (1:06 - 1:18) ===== */}
        <Sequence from={s(t("00:01:06,120")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Kopf abtrennen" />
        </Sequence>

        <Sequence from={s(t("00:01:06,120")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Hinter den Kiemen"
            subtitle="Kopf sauber abtrennen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:12,040")) + GAP * 4} durationInFrames={s(4)}>
          <Callout
            text="Blutig!"
            subtext="Brett immer säubern"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 5: FILIEREN (1:18 - 1:49) ===== */}
        <Sequence from={s(t("00:01:17,980")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Filieren" />
        </Sequence>

        <Sequence from={s(t("00:01:17,980")) + GAP * 5} durationInFrames={s(3)}>
          <SectionTitle
            title="Vom Rücken filieren"
            subtitle="Leichter Druck zur Mittelgräte"
          />
        </Sequence>

        <Sequence from={s(t("00:01:26,439")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="Tipp"
            subtext="Mittelgräte durchtrennen"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:32,590")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Die Kunst des Filierens"
            subtitle="Fleisch am Fisch, nicht an der Gräte"
          />
        </Sequence>

        <Sequence from={s(t("00:01:39,230")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="Gräte"
            subtext="Langsam vorarbeiten"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 6: BAUCHLAPPEN (1:44 - 1:56) ===== */}
        <Sequence from={s(t("00:01:44,489")) + GAP * 6} durationInFrames={s(5)}>
          <StepBadge step={6} label="Bauchlappen" />
        </Sequence>

        <Sequence from={s(t("00:01:44,489")) + GAP * 6} durationInFrames={s(3)}>
          <SectionTitle
            title="Bauchlappen lösen"
            subtitle="Durchschneiden & rausziehen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:51,200")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Tipp"
            subtext="Nicht zu weit gehen — wird zu dünn"
            position="top-right"
          />
        </Sequence>

        {/* ===== FINALE (2:01 - 2:02) ===== */}
        <Sequence from={s(t("00:02:01,349")) + GAP * 7} durationInFrames={s(5)}>
          <Callout
            text="Fertig!"
            subtext="Wolfsbarsch fachgerecht zerlegt"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:02:01,349")) + GAP * 7 + s(4) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
