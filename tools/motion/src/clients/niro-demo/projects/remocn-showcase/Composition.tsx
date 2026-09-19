// ============================================================
// Client: NIRO Demo — Project: Remocn Showcase
// Lebender Nachweis für die Remocn-Komponenten (src/components/remocn):
// Shader-Hintergründe, Signature-Transitions, Text-Reveals, Odometer,
// Marker, Handschrift, Konfetti — alles in Hausfarben und Meutas.
// Vier Szenen à 4 s, Transitions liegen zwischen den Szenen.
// ============================================================

import React from "react";
import { AbsoluteFill, staticFile, useVideoConfig, Sequence } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { z } from "zod";
import { zTextarea } from "@remotion/zod-types";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

// --- Remocn ---
import { ShaderMeshGradient } from "@/components/remocn/shader-mesh-gradient";
import { ShaderGodRays } from "@/components/remocn/shader-god-rays";
import { SoftBlurIn } from "@/components/remocn/soft-blur-in";
import { MaskRevealUp } from "@/components/remocn/mask-reveal-up";
import { NumberWheel } from "@/components/remocn/number-wheel";
import { MarkerHighlight } from "@/components/remocn/marker-highlight";
import { Handwrite, handwriteDuration } from "@/components/remocn/handwrite";
import { InkUnderline } from "@/components/remocn/ink-underline";
import { Confetti } from "@/components/remocn/confetti";
import { Drift } from "@/components/remocn/drift";
import { whipPan } from "@/components/remocn/whip-pan";
import { grainDissolve } from "@/components/remocn/grain-dissolve";
import { zoomBlur } from "@/components/remocn/zoom-blur";

const ci = loadBrand("niro-demo", brandJson as any);

// --- Fonts: Meutas lokal (wie praktikant-reel) ---
const MEUTAS_FACES = [
  { weight: 400, file: "Meutas-Regular.otf" },
  { weight: 500, file: "Meutas-Medium.otf" },
  { weight: 600, file: "Meutas-SemiBold.otf" },
  { weight: 700, file: "Meutas-Bold.otf" },
  { weight: 800, file: "Meutas-ExtraBold.otf" },
] as const;

for (const face of MEUTAS_FACES) {
  const style = document.createElement("style");
  style.textContent = `@font-face { font-family: "Meutas"; font-weight: ${face.weight}; src: url("${staticFile(`fonts/${face.file}`)}") format("opentype"); }`;
  document.head.appendChild(style);
}

const FONT_TITLE = '"Meutas", sans-serif';

// Remocn-Textkomponenten lesen ihre Schrift aus var(--font-geist-sans);
// die Variable wird am Root gesetzt → alle Reveals laufen in Meutas.
const ROOT_STYLE = { "--font-geist-sans": FONT_TITLE } as React.CSSProperties;

// =============================================================
// SCHEMA
// =============================================================

export const remocnShowcaseSchema = projectPropsSchema.extend({
  headline: z.string().describe("Szene 1: Headline (Soft-Blur-In)"),
  statValue: z.number().int().min(0).max(99999).describe("Szene 2: Zahl (Odometer)"),
  statLabel: z.string().describe("Szene 2: Bezeichnung unter der Zahl"),
  listText: zTextarea().describe("Szene 3: Zeilen (Mask-Reveal, eine je Zeile)"),
  markerBefore: z.string().describe("Szene 3: Satz vor dem Marker (Leerzeichen am Ende mitgeben)"),
  markerWord: z.string().describe("Szene 3: markiertes Wort"),
  markerAfter: z.string().describe("Szene 3: Satz nach dem Marker (Leerzeichen am Anfang mitgeben)"),
  handwriting: z.string().describe("Szene 4: Handschrift-Zeile"),
});

type RemocnShowcaseProps = z.infer<typeof remocnShowcaseSchema>;

export const remocnShowcaseDefaults: RemocnShowcaseProps = {
  format: "landscape",
  fps: 30,
  durationInSeconds: 16,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: false,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.3,
  },
  headline: "Motion Graphics, neu gedacht.",
  statValue: 247,
  statLabel: "Bewerbungen in 30 Tagen",
  listText: "Jede Animation ist Code.\nJede Zahl ist ein Prop.\nJeder Render ist reproduzierbar.",
  markerBefore: "Einmal gebaut, ",
  markerWord: "für jeden Kunden",
  markerAfter: " in Sekunden angepasst.",
  handwriting: "Danke fürs Zuschauen",
};

// =============================================================
// SZENEN
// =============================================================

const SCENE_FRAMES = 120; // 4 s bei 30 fps

const SzeneHeadline: React.FC<{ headline: string; transparent: boolean }> = ({ headline, transparent }) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill>
      {!transparent && (
        <ShaderMeshGradient
          colors={[ci.colors.secondary, "#2E3D2A", ci.colors.primary, "#0F1411"]}
          distortion={0.7}
          swirl={0.15}
          speed={0.6}
        />
      )}
      <SoftBlurIn text={headline} fontSize={Math.round(width * 0.052)} color="#FFFFFF" fontWeight={700} />
    </AbsoluteFill>
  );
};

const SzeneZahl: React.FC<{ value: number; label: string; transparent: boolean }> = ({ value, label, transparent }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill>
      {!transparent && (
        <ShaderGodRays
          colorBack="#0F1411"
          colorBloom={ci.colors.primary}
          colors={[ci.colors.primary, ci.colors.accent, "#FFFFFF"]}
          intensity={0.7}
          density={0.28}
          bloom={0.35}
          speed={0.5}
        />
      )}
      <Drift grow={0.03}>
        {/* NumberWheel füllt seinen Container (AbsoluteFill) — deshalb eigene Box, Label darunter */}
        <div style={{ position: "absolute", left: 0, right: 0, top: height * 0.28, height: height * 0.3 }}>
          <NumberWheel from={0} to={value} fontSize={Math.round(width * 0.11)} color="#FFFFFF" />
        </div>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: height * 0.62,
            textAlign: "center",
            fontFamily: FONT_TITLE,
            fontWeight: 500,
            fontSize: Math.round(width * 0.024),
            color: ci.colors.primary,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>
      </Drift>
    </AbsoluteFill>
  );
};

const SzeneListe: React.FC<{
  listText: string;
  before: string;
  word: string;
  after: string;
  transparent: boolean;
}> = ({ listText, before, word, after, transparent }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: transparent ? "transparent" : ci.colors.secondary }}>
      {/* obere Hälfte: Mask-Reveal der Zeilen */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: height * 0.58 }}>
        <MaskRevealUp text={listText} fontSize={Math.round(width * 0.036)} color="#FFFFFF" fontWeight={700} />
      </div>
      {/* untere Hälfte: Marker läuft nach den Zeilen an */}
      <Sequence from={40} layout="none">
        <div style={{ position: "absolute", left: 0, right: 0, top: height * 0.58, height: height * 0.3 }}>
          <MarkerHighlight
            before={before}
            highlight={word}
            after={after}
            markerColor={ci.colors.primary}
            baseColor="rgba(255,255,255,0.72)"
            highlightedTextColor={ci.colors.secondary}
            fontSize={Math.round(width * 0.024)}
            fontWeight={500}
          />
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};

const SzeneHandschrift: React.FC<{ text: string; transparent: boolean }> = ({ text, transparent }) => {
  const { width, height, fps } = useVideoConfig();
  const fontSize = Math.round(width * 0.05);
  const writeFrames = handwriteDuration(text);
  const underlineWidth = Math.round(text.length * fontSize * 0.42);
  return (
    <AbsoluteFill style={{ backgroundColor: transparent ? "transparent" : "#F4F1E8" }}>
      <Handwrite text={text} fontSize={fontSize} color={ci.colors.secondary} weight={600} />
      <div
        style={{
          position: "absolute",
          left: (width - underlineWidth) / 2,
          top: height / 2 + fontSize * 0.55,
        }}
      >
        <InkUnderline width={underlineWidth} color={ci.colors.primary} thickness={Math.round(fontSize * 0.14)} delay={writeFrames} />
      </div>
      <Confetti
        startFrame={writeFrames + Math.round(fps * 0.4)}
        originX={0.5}
        originY={0.45}
        colors={[ci.colors.primary, ci.colors.accent, ci.colors.secondary, "#FFFFFF"]}
        particleCount={160}
        lifetime={80}
        seed={7}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// KOMPOSITION
// =============================================================

export const RemocnShowcase: React.FC<RemocnShowcaseProps> = ({
  headline,
  statValue,
  statLabel,
  listText,
  markerBefore,
  markerWord,
  markerAfter,
  handwriting,
  transparent = false,
  review,
}) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={ROOT_STYLE}>
        <TransitionSeries>
          <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES}>
            <SzeneHeadline headline={headline} transparent={transparent} />
          </TransitionSeries.Sequence>

          <TransitionSeries.Transition presentation={whipPan({ direction: "left" })} timing={linearTiming({ durationInFrames: 26 })} />

          <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES}>
            <SzeneZahl value={statValue} label={statLabel} transparent={transparent} />
          </TransitionSeries.Sequence>

          <TransitionSeries.Transition
            presentation={grainDissolve({ colors: [ci.colors.secondary, ci.colors.primary, "#0F1411"], colorBack: "#0F1411" })}
            timing={linearTiming({ durationInFrames: 45 })}
          />

          <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES}>
            <SzeneListe listText={listText} before={markerBefore} word={markerWord} after={markerAfter} transparent={transparent} />
          </TransitionSeries.Sequence>

          <TransitionSeries.Transition presentation={zoomBlur()} timing={linearTiming({ durationInFrames: 18 })} />

          <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES + 89}>
            <SzeneHandschrift text={handwriting} transparent={transparent} />
          </TransitionSeries.Sequence>
        </TransitionSeries>
        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            showFaceZone={review.showFaceZone ?? true}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
