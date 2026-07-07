// ============================================================
// Landhaus Wolf — Kartoffelgratin
// Part 1: Art 1 · Klassisch (~1:18)
// Part 2: Art 2 · Gourmet / Restaurant-Methode (~1:19)
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
  IngredientList,
  Callout,
  StepBadge,
  BrandSignOff,
  t,
} from "../../components";

const ci = loadBrand("landhaus-wolf", brandJson as any);

// --- Schemas ---
export const landhausWolfKartoffelgratinPart1Schema = projectPropsSchema.extend({});
export const landhausWolfKartoffelgratinPart2Schema = projectPropsSchema.extend({});
type Props = z.infer<typeof landhausWolfKartoffelgratinPart1Schema>;

// =============================================================
// PART 1 — Art 1 · Klassisch
// =============================================================

export const LandhausWolfKartoffelgratinPart1: React.FC<Props> = ({
  transparent = false,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);
  const GAP = fps;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/landhaus-wolf-kochvideos/kartoffelgratin-part1.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:08) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(3)}>
          <SectionTitle
            title="Kartoffelgratin"
            subtitle="Art 1 · Klassisch"
          />
        </Sequence>

        <Sequence from={s(t("00:00:03,000"))} durationInFrames={s(5)}>
          <Callout
            text="2 Arten"
            subtext="Klassisch vs. Restaurant"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: FORM VORBEREITEN (0:08 - 0:20) ===== */}
        <Sequence from={s(t("00:00:08,259")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Form vorbereiten" />
        </Sequence>

        <Sequence from={s(t("00:00:08,259")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Knoblauch einreiben & buttern"
            subtitle="Pfännchen vorbereiten"
          />
        </Sequence>

        <Sequence from={s(t("00:00:11,500")) + GAP + s(2)} durationInFrames={s(4)}>
          <Callout
            text="Butter!"
            subtext="Ordentlich einreiben"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 2: KARTOFFELN SCHNEIDEN (0:20 - 0:30) ===== */}
        <Sequence from={s(t("00:00:19,929")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="Kartoffeln" />
        </Sequence>

        <Sequence from={s(t("00:00:19,929")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Vorwiegend festkochend"
            subtitle="Fein in Scheiben schneiden"
          />
        </Sequence>

        <Sequence from={s(t("00:00:23,000")) + GAP * 2} durationInFrames={s(4)}>
          <Callout
            text="Festkochend"
            subtext="Fein aufschneiden"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: GRATIN-SAHNE (0:30 - 0:52) ===== */}
        <Sequence from={s(t("00:00:30,660")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Gratin-Sahne" />
        </Sequence>

        <Sequence from={s(t("00:00:30,660")) + GAP * 3} durationInFrames={s(4)}>
          <SectionTitle
            title="Gratin-Sahne ansetzen"
            subtitle="Sahne + Milch halb-halb"
          />
        </Sequence>

        <Sequence from={s(t("00:00:36,210")) + GAP * 3} durationInFrames={s(15)}>
          <IngredientList
            items={[
              "Sahne",
              "Milch (ca. halb-halb)",
              "Knoblauch",
              "Thymian",
              "Rosmarin",
              "Salz",
              "Pfeffer",
              "Muskat",
            ]}
            title="Gratin-Sahne"
          />
        </Sequence>

        {/* ===== STEP 4: AUFKOCHEN + WÜRZEN (0:52 - 1:09) ===== */}
        <Sequence from={s(t("00:00:52,270")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Aufkochen" />
        </Sequence>

        <Sequence from={s(t("00:00:52,270")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Kräftig nachwürzen"
            subtitle="Kartoffeln geben viel Wasser ab"
          />
        </Sequence>

        <Sequence from={s(t("00:00:55,500")) + GAP * 4} durationInFrames={s(4)}>
          <Callout
            text="Würzen!"
            subtext="Kartoffeln geben Wasser ab"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 5: IN DEN OFEN (1:09 - 1:18) ===== */}
        <Sequence from={s(t("00:01:06,430")) + GAP * 5} durationInFrames={s(4)}>
          <SectionTitle
            title="Ab in den Ofen!"
            subtitle="Zwei Temperaturstufen"
          />
        </Sequence>

        <Sequence from={s(t("00:01:06,430")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="180°C"
            subtext="Anfangs · nur kurz"
            position="top-right"
          />
        </Sequence>

        <Sequence from={s(t("00:01:11,000")) + GAP * 5} durationInFrames={s(4)}>
          <Callout
            text="140°C"
            subtext="Dann runterschalten"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:01:14,879")) + GAP * 5 + s(4) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};

// =============================================================
// PART 2 — Art 2 · Gourmet / Restaurant-Methode
// =============================================================

export const LandhausWolfKartoffelgratinPart2: React.FC<Props> = ({
  transparent = false,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);
  const GAP = fps;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && (
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile("projects/landhaus-wolf-kochvideos/kartoffelgratin-part2.mov")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* ===== INTRO (0:00 - 0:05) ===== */}
        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <SectionTitle
            title="Kartoffelgratin"
            subtitle="Art 2 · Restaurant-Methode"
          />
        </Sequence>

        <Sequence from={s(t("00:00:00,000"))} durationInFrames={s(5)}>
          <Callout
            text="Art 2"
            subtext="Restaurant-Methode"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 1: MASCHINENSCHNITT (0:05 - 0:15) ===== */}
        <Sequence from={s(t("00:00:05,240")) + GAP} durationInFrames={s(5)}>
          <StepBadge step={1} label="Maschinenschnitt" />
        </Sequence>

        <Sequence from={s(t("00:00:05,240")) + GAP} durationInFrames={s(3)}>
          <SectionTitle
            title="Hauchdünn geschnitten"
            subtitle="Mit der Maschine"
          />
        </Sequence>

        <Sequence from={s(t("00:00:08,500")) + GAP} durationInFrames={s(4)}>
          <Callout
            text="Hauchdünn"
            subtext="Maschinenschnitt"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 2: IN SAHNE KOCHEN (0:15 - 0:33) ===== */}
        <Sequence from={s(t("00:00:14,839")) + GAP * 2} durationInFrames={s(5)}>
          <StepBadge step={2} label="In Sahne kochen" />
        </Sequence>

        <Sequence from={s(t("00:00:14,839")) + GAP * 2} durationInFrames={s(3)}>
          <SectionTitle
            title="Kartoffeln in Gratin-Sahne"
            subtitle="Stärke bindet automatisch"
          />
        </Sequence>

        <Sequence from={s(t("00:00:19,920")) + GAP * 2} durationInFrames={s(4)}>
          <SectionTitle
            title="Stärke bindet"
            subtitle="Sahne wird automatisch sämig"
          />
        </Sequence>

        <Sequence from={s(t("00:00:24,440")) + GAP * 2} durationInFrames={s(5)}>
          <Callout
            text="Tipp"
            subtext="Die Stärke bindet automatisch"
            position="bottom-right"
          />
        </Sequence>

        <Sequence from={s(t("00:00:29,739")) + GAP * 2} durationInFrames={s(4)}>
          <Callout
            text="Ergebnis"
            subtext="Flüssigkeit verändert sich"
            position="top-right"
          />
        </Sequence>

        {/* ===== STEP 3: ABSCHMECKEN (0:35 - 0:48) ===== */}
        <Sequence from={s(t("00:00:35,310")) + GAP * 3} durationInFrames={s(5)}>
          <StepBadge step={3} label="Abschmecken" />
        </Sequence>

        <Sequence from={s(t("00:00:35,310")) + GAP * 3} durationInFrames={s(3)}>
          <SectionTitle
            title="Final abschmecken"
            subtitle="So schmeckt das fertige Gratin"
          />
        </Sequence>

        <Sequence from={s(t("00:00:38,579")) + GAP * 3} durationInFrames={s(4)}>
          <Callout
            text="Abschmecken!"
            subtext="So schmeckt das fertige Gratin"
            position="bottom-right"
          />
        </Sequence>

        {/* ===== STEP 4: ABFÜLLEN (0:48 - 1:01) ===== */}
        <Sequence from={s(t("00:00:47,659")) + GAP * 4} durationInFrames={s(5)}>
          <StepBadge step={4} label="Abfüllen" />
        </Sequence>

        <Sequence from={s(t("00:00:47,659")) + GAP * 4} durationInFrames={s(3)}>
          <SectionTitle
            title="Kräuter raus, abfüllen"
            subtitle="Glatt streichen · ab in den Ofen"
          />
        </Sequence>

        <Sequence from={s(t("00:00:55,090")) + GAP * 4} durationInFrames={s(4)}>
          <SectionTitle
            title="Abfüllen"
            subtitle="Kräuter raus · glatt streichen"
          />
        </Sequence>

        {/* ===== FAZIT (1:01 - 1:19) ===== */}
        <Sequence from={s(t("00:01:01,310")) + GAP * 5} durationInFrames={s(5)}>
          <SectionTitle
            title="Kartoffelgratin — fertig!"
            subtitle="Kein Käse bei uns im Betrieb"
          />
        </Sequence>

        <Sequence from={s(t("00:01:07,840")) + GAP * 5} durationInFrames={s(5)}>
          <Callout
            text="Kein Käse!"
            subtext="Bei uns im Betrieb"
            position="center"
          />
        </Sequence>

        {/* ===== SIGN-OFF ===== */}
        <Sequence from={s(t("00:01:13,040")) + GAP * 5 + s(7) + GAP} durationInFrames={s(6)}>
          <BrandSignOff />
        </Sequence>
      </AbsoluteFill>
    </CIProvider>
  );
};
