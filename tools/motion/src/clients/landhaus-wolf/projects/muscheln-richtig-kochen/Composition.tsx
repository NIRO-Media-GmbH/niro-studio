// ============================================================
// Landhaus Wolf — Muscheln richtig Kochen
// Drei Arten von Muscheln und ihre Zubereitung (~2:14)
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
  Callout,
  StepBadge,
  BrandSignOff,
  t,
} from "../../components";

const ci = loadBrand("landhaus-wolf", brandJson as any);

export const landhausWolfMuschelnRichtigKochenSchema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfMuschelnRichtigKochenSchema>;

export const LandhausWolfMuschelnRichtigKochen: React.FC<Props> = ({
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
              src={staticFile("projects/landhaus-wolf-kochvideos/muscheln-richtig-kochen.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:04) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <SectionTitle
            title="Muscheln richtig Kochen"
            subtitle="Drei Arten von Muscheln"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(4)}>
          <Callout
            text="3 Arten"
            subtext="Und ihre Zubereitung"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: PFAHLMUSCHEL (0:05 - 0:13) ===== */}
        <Sequence from={s(t("00:00:04,440")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Pfahlmuschel" />
        </Sequence>

        <Sequence from={s(t("00:00:04,440")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Pfahlmuschel"
            subtitle="Noch lebendig"
          />
        </Sequence>

        <Sequence from={s(t("00:00:07,440")) + GAP} durationInFrames={s(4)}>
          <Callout
            text="Lebendig!"
            subtext="Noch ganz frisch"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 2: MIESMUSCHEL (0:14 - 0:21) ===== */}
        <Sequence from={s(t("00:00:09,519")) + GAP * 2} durationInFrames={s(4)}>
          <StepBadge step={2} label="Miesmuschel" />
        </Sequence>

        <Sequence from={s(t("00:00:09,519")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Miesmuschel"
            subtitle="Der Klassiker"
          />
        </Sequence>

        <Sequence from={s(t("00:00:09,519")) + GAP * 2 + s(3)} durationInFrames={s(4)}>
          <Callout
            text="Klassiker"
            subtext="So kennt man sie"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: JAKOBSMUSCHEL (0:22 - 0:37) ===== */}
        <Sequence from={s(t("00:00:13,580")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Jakobsmuschel" />
        </Sequence>

        <Sequence from={s(t("00:00:13,580")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Jakobsmuschel"
            subtitle="Von der Schale bis zum Fleisch"
          />
        </Sequence>

        <Sequence from={s(t("00:00:16,580")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Muskelfleisch freilegen"
            subtitle="Von der Schale zum Fleisch"
          />
        </Sequence>

        <Sequence from={s(t("00:00:21,000")) + GAP * 3} durationInFrames={s(5)}>
          <Callout
            text="TK vs Frisch"
            subtext="TK oft frischer als Frischware!"
            position="top-right"
          />
        </Sequence>


        {/* ===== STEP 4: MUSCHELN KOCHEN (0:38 - 0:54) ===== */}
        <Sequence from={s(t("00:00:20,500")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Kochen" />
        </Sequence>

        <Sequence from={s(t("00:00:20,500")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Muscheln kochen"
            subtitle="Zwiebeln · Weißwein"
          />
        </Sequence>

        <Sequence from={s(t("00:00:23,500")) + GAP * 4} durationInFrames={s(4)}>
          <SectionTitle
            title="Ablöschen"
            subtitle="Weißwein · Zwiebeln"
          />
        </Sequence>

        <Sequence from={s(t("00:00:27,620")) + GAP * 4} durationInFrames={s(4)}>
          <Callout
            text="Geduld"
            subtext="Kurz aufziehen lassen"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 5: JAKOBSMUSCHEL ÖFFNEN (0:55 - 1:14) ===== */}
        <Sequence from={s(t("00:00:37,960")) + GAP * 5} durationInFrames={s(5)}>
          <StepBadge step={5} label="Jakobsmuschel öffnen" />
        </Sequence>

        <Sequence from={s(t("00:00:37,960")) + GAP * 5} durationInFrames={s(3)}>
          <SectionTitle
            title="Jakobsmuschel öffnen"
            subtitle="Messer · Löffel · Innereien entfernen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:41,170")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Aufknacken & rausholen"
            subtitle="Muskelfleisch freilegen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:49,840")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="Sorgfalt"
            subtext="Innereien entfernen"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 6: SUD & PUTZEN (1:15 - 1:43) ===== */}
        <Sequence from={s(t("00:00:55,060")) + GAP * 6} durationInFrames={s(5)}>
          <StepBadge step={6} label="Sud & Putzen" />
        </Sequence>

        <Sequence from={s(t("00:00:55,060")) + GAP * 6} durationInFrames={s(3)}>
          <SectionTitle
            title="Muschelsud passieren"
            subtitle="Bart entfernen · Innereien weg"
          />
        </Sequence>

        <Sequence from={s(t("00:01:00,000")) + GAP * 6} durationInFrames={s(4)}>
          <SectionTitle
            title="Sud abkippen"
            subtitle="Muscheln putzen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:07,069")) + GAP * 6} durationInFrames={s(4)}>
          <Callout
            text="Unterschied"
            subtext="Innereien vs. Bart entfernen"
            position="top-right"
          />
        </Sequence>

        {/* ===== FINALE (1:44 - 2:08) ===== */}
        <Sequence from={s(t("00:01:11,810")) + GAP * 7} durationInFrames={s(4)}>
          <Callout
            text="Hauptgang"
            subtext="Auf dem Teller wieder dabei"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:01:11,810")) + GAP * 7 + s(4) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
