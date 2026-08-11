// ============================================================
// NIRO — Cutter Ad (9:16) Recruiting-Untertitel
// Transparentes Alpha-Overlay (ProRes 4444) über Davids Schnitt.
// 1080×1920, 25fps, ~77s. Timeline t=0 = SRT 01:00:00,000.
//
// Apple-Look: Meutas SemiBold, Weiß auf Footage (kein Kasten),
// weicher Schatten, Wort-für-Wort-Reveal mit dezentem Spring.
// Einziger Akzent: NIRO-Grün (#A1D334) für Schlüsselwörter.
// Beat-Stile: flow / punch / stack (Branchen) / Name-Insert / CTA.
//
// Alle Wörter einer Page sind immer im Layout (opacity 0 vor dem
// Einsatz) — kein Zeilen-Reflow während des Reveals.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  PAGES,
  STACK,
  STACK_START_SEC,
  STACK_END_SEC,
  NAME_INSERT_START_SEC,
  NAME_INSERT_END_SEC,
  CTA_START_SEC,
  TOTAL_DURATION_SEC,
  type CaptionPage,
} from "./transcript";
import brandJson from "../../brand.json";

const { fontFamily: robotoFamily } = loadRoboto();

const MEUTAS_FACES = [
  { weight: 400, file: "Meutas-Regular.otf" },
  { weight: 500, file: "Meutas-Medium.otf" },
  { weight: 600, file: "Meutas-SemiBold.otf" },
  { weight: 700, file: "Meutas-Bold.otf" },
  { weight: 800, file: "Meutas-ExtraBold.otf" },
  { weight: 900, file: "Meutas-Black.otf" },
] as const;

for (const face of MEUTAS_FACES) {
  const style = document.createElement("style");
  style.textContent = `@font-face { font-family: "Meutas"; font-weight: ${face.weight}; src: url("${staticFile(`fonts/${face.file}`)}") format("opentype"); }`;
  document.head.appendChild(style);
}

const FONT_TITLE = '"Meutas", sans-serif';
const FONT_BODY = `${robotoFamily}, sans-serif`;

const ci = loadBrand("niro", brandJson as any);
const GREEN = ci.colors.primary;
const WHITE = "#FFFFFF";

// Untertitel-Band: unterhalb der Face Zone (45 %), innerhalb der
// Reels-Safe-Zone (endet bei 57,5 % — darunter IG/TikTok-UI).
const BAND_TOP_FRAC = 0.45;
const BAND_BOTTOM_FRAC = 0.575;

const TEXT_SHADOW =
  "0 2px 8px rgba(0,0,0,0.40), 0 10px 32px rgba(0,0,0,0.30)";

const FLOW_SPRING = { damping: 30, stiffness: 260, mass: 0.9 };
const PUNCH_SPRING = { damping: 13, stiffness: 190, mass: 1 };

// --- Schema ---

export const niroCutterAdSchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
  captionShiftY: z
    .number()
    .step(1)
    .describe("Untertitel-Band vertikal verschieben (px)"),
  showNameInsert: z.boolean().describe("Name-Insert bei der Vorstellung"),
  showCtaFinale: z.boolean().describe("CTA-Finale nach dem letzten Wort"),
  jobTitle: z.string().describe("Jobtitel im CTA-Finale"),
  ctaText: z.string().describe("CTA-Zeile im Finale"),
  nameInsertText: z.string().describe("Text des Name-Inserts"),
});

export type NiroCutterAdProps = z.infer<typeof niroCutterAdSchema>;

export const niroCutterAdDefaults: NiroCutterAdProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: TOTAL_DURATION_SEC,
  transparent: true,
  timeOffsetSec: 0,
  captionShiftY: 0,
  showNameInsert: true,
  showCtaFinale: true,
  jobTitle: "Cutter & Videograf (m/w/d)",
  ctaText: "Trag dich unten ein.",
  nameInsertText: "Gründer & Geschäftsführer · NIRO Media",
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

// --- Einzelnes Wort (Reveal mit Spring + Blur) ---

const CaptionWordView: React.FC<{
  text: string;
  accent?: boolean;
  big?: boolean;
  startFrame: number;
  punch?: boolean;
}> = ({ text, accent, big, startFrame, punch }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - startFrame;

  const enter = spring({
    frame: t,
    fps,
    config: punch ? PUNCH_SPRING : FLOW_SPRING,
  });
  const opacity = interpolate(t, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [punch ? 26 : 16, 0]);
  const scale = interpolate(enter, [0, 1], [punch ? 0.82 : 0.94, 1]);
  const blur = interpolate(t, [0, 6], [punch ? 10 : 6, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "50% 80%",
        filter: blur > 0.1 ? `blur(${blur}px)` : undefined,
        color: accent ? GREEN : WHITE,
        fontSize: big ? "1.14em" : undefined,
        fontWeight: big ? 700 : undefined,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  );
};

// --- Eine Untertitel-Page (flow oder punch) ---

const CaptionPageView: React.FC<{
  page: CaptionPage;
  pageStartSec: number;
  fadeOutAtEnd?: boolean;
  bandTop: number;
  bandHeight: number;
}> = ({ page, pageStartSec, fadeOutAtEnd, bandTop, bandHeight }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const punch = page.style === "punch";
  const fontSize = page.sizePx ?? (punch ? 100 : 64);

  const pageDurF = Math.round((page.endSec - page.startSec) * fps);
  const fadeOut = fadeOutAtEnd
    ? interpolate(frame, [pageDurF - 6, pageDurF - 1], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        transform: "translateX(-50%)",
        top: bandTop,
        height: bandHeight,
        width: 920,
        display: "flex",
        flexDirection: "row",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "baseline",
        alignContent: page.alignTop ? "flex-start" : "center",
        paddingTop: page.alignTop ? 10 : 0,
        columnGap: "0.26em",
        rowGap: "0.06em",
        fontFamily: FONT_TITLE,
        fontWeight: punch ? 700 : 600,
        fontSize,
        lineHeight: 1.16,
        letterSpacing: punch ? "-0.015em" : "-0.01em",
        textAlign: "center",
        textShadow: TEXT_SHADOW,
        opacity: fadeOut,
      }}
    >
      {page.words.map((w, i) => (
        <CaptionWordView
          key={i}
          text={w.text}
          accent={w.accent}
          big={w.big}
          startFrame={Math.round((w.startSec - pageStartSec) * fps)}
          punch={punch}
        />
      ))}
    </div>
  );
};

// --- Kicker-Page: kleine Versalzeile oben, große Hauptzeile darunter ---

const KickerPageView: React.FC<{
  page: CaptionPage;
  pageStartSec: number;
  bandTop: number;
  bandHeight: number;
}> = ({ page, pageStartSec, bandTop, bandHeight }) => {
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        transform: "translateX(-50%)",
        top: bandTop,
        height: bandHeight,
        width: 920,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        rowGap: 10,
      }}
    >
      <div
        style={{
          display: "flex",
          columnGap: "0.55em",
          fontFamily: FONT_BODY,
          fontWeight: 500,
          fontSize: 26,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.88)",
          textShadow: "0 2px 10px rgba(0,0,0,0.45)",
        }}
      >
        {(page.kicker ?? []).map((w, i) => (
          <CaptionWordView
            key={i}
            text={w.text}
            startFrame={Math.round((w.startSec - pageStartSec) * fps)}
          />
        ))}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          columnGap: "0.24em",
          fontFamily: FONT_TITLE,
          fontWeight: 700,
          fontSize: page.sizePx ?? 88,
          lineHeight: 1.1,
          letterSpacing: "-0.015em",
          textShadow: TEXT_SHADOW,
        }}
      >
        {page.words.map((w, i) => (
          <CaptionWordView
            key={i}
            text={w.text}
            accent={w.accent}
            startFrame={Math.round((w.startSec - pageStartSec) * fps)}
            punch
          />
        ))}
      </div>
    </div>
  );
};

// --- Stack: Branchen-Liste (gestaffelte Zeilen) ---

const StackView: React.FC<{ bandTop: number; bandHeight: number }> = ({
  bandTop,
  bandHeight,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        transform: "translateX(-50%)",
        top: bandTop,
        height: bandHeight,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "flex-start",
        rowGap: 8,
      }}
    >
      {STACK.map((item, i) => {
        const t = frame - Math.round((item.startSec - STACK_START_SEC) * fps);
        const enter = spring({ frame: t, fps, config: FLOW_SPRING });
        const opacity = interpolate(t, [0, 4], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const x = interpolate(enter, [0, 1], [-22, 0]);
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              columnGap: 18,
              opacity,
              transform: `translateX(${x}px)`,
            }}
          >
            <div
              style={{
                width: 26,
                height: 5,
                borderRadius: 3,
                backgroundColor: GREEN,
                boxShadow: "0 2px 8px rgba(0,0,0,0.35)",
              }}
            />
            <span
              style={{
                fontFamily: FONT_TITLE,
                fontWeight: 600,
                fontSize: 44,
                lineHeight: 1.1,
                letterSpacing: "-0.01em",
                color: WHITE,
                textShadow: TEXT_SHADOW,
                whiteSpace: "nowrap",
              }}
            >
              {item.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// --- Name-Insert (CI: Subtitles = Roboto Medium Uppercase) ---

const NameInsert: React.FC<{ text: string; bandBottom: number }> = ({
  text,
  bandBottom,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 26, stiffness: 180, mass: 1 } });
  const exit = interpolate(
    frame,
    [durationInFrames - 6, durationInFrames - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: bandBottom - 44,
        transform: `translateX(-50%) translateY(${interpolate(enter, [0, 1], [12, 0])}px)`,
        opacity: Math.min(enter, exit),
        fontFamily: FONT_BODY,
        fontWeight: 500,
        fontSize: 25,
        letterSpacing: "0.13em",
        textTransform: "uppercase",
        color: "rgba(255,255,255,0.85)",
        textShadow: "0 2px 10px rgba(0,0,0,0.45)",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

// --- CTA-Finale (Symbol + Jobtitel m/w/d + CTA + Chevron) ---

const NIRO_SYMBOL_PATH =
  "m2673.08,2926.79h-779.68l-551.12-672.98v-553.48h328.03l124.94,152.46,342.6-418.24.29-.29-.29-.44L1276.64,382.48h-7.36c-427.22,0-900.79,315.52-900.79,860.02v957.15l595.72,727.14H0V0h1623.66c487.66,0,882.98,395.32,882.98,882.98v911.53l-380.57,464.45,547.01,667.83Z";

const CtaFinale: React.FC<{
  jobTitle: string;
  ctaText: string;
  bandTop: number;
  bandHeight: number;
}> = ({ jobTitle, ctaText, bandTop, bandHeight }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const item = (delayFrames: number) => {
    const t = frame - delayFrames;
    const enter = spring({ frame: t, fps, config: { damping: 22, stiffness: 170, mass: 1 } });
    return {
      opacity: interpolate(t, [0, 5], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
      transform: `translateY(${interpolate(enter, [0, 1], [18, 0])}px)`,
    };
  };

  const bounceY = 5 * Math.sin(Math.max(0, frame - 18) * 0.21);

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        transform: "translateX(-50%)",
        top: bandTop,
        height: bandHeight,
        width: 920,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        rowGap: 10,
      }}
    >
      <div style={item(0)}>
        <svg
          width={40}
          height={44}
          viewBox="0 0 2673.08 2926.79"
          style={{ display: "block", filter: "drop-shadow(0 3px 10px rgba(0,0,0,0.35))" }}
        >
          <path d={NIRO_SYMBOL_PATH} fill={GREEN} />
        </svg>
      </div>
      <div
        style={{
          fontFamily: FONT_BODY,
          fontWeight: 500,
          fontSize: 26,
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          color: GREEN,
          textShadow: "0 2px 10px rgba(0,0,0,0.45)",
          whiteSpace: "nowrap",
          ...item(4),
        }}
      >
        {jobTitle}
      </div>
      <div
        style={{
          fontFamily: FONT_TITLE,
          fontWeight: 600,
          fontSize: 56,
          letterSpacing: "-0.01em",
          color: WHITE,
          textShadow: TEXT_SHADOW,
          whiteSpace: "nowrap",
          ...item(8),
        }}
      >
        {ctaText}
      </div>
      <div style={{ opacity: item(12).opacity, transform: `${item(12).transform} translateY(${bounceY}px)` }}>
        <svg
          width={38}
          height={22}
          viewBox="0 0 40 24"
          style={{ display: "block", filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.4))" }}
        >
          <path
            d="M4 4 L20 20 L36 4"
            fill="none"
            stroke={GREEN}
            strokeWidth={5}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};

// --- Hauptkomposition ---

export const NiroCutterAd: React.FC<NiroCutterAdProps> = ({
  timeOffsetSec,
  captionShiftY,
  showNameInsert,
  showCtaFinale,
  jobTitle,
  ctaText,
  nameInsertText,
  review,
}) => {
  const { fps, height } = useVideoConfig();

  const bandTop = Math.round(height * BAND_TOP_FRAC) + captionShiftY;
  const bandBottom = Math.round(height * BAND_BOTTOM_FRAC) + captionShiftY;
  const bandHeight = bandBottom - bandTop;

  const toF = (sec: number) => Math.round((sec + timeOffsetSec) * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {PAGES.map((page, i) => {
          // Fade-out nur, wenn danach eine echte Pause kommt
          // (Stack zählt als Anschluss-Content, kein Gap)
          const nextStart =
            page.endSec === STACK_START_SEC
              ? STACK_START_SEC
              : i + 1 < PAGES.length
                ? PAGES[i + 1].startSec
                : Infinity;
          const gapAfter = nextStart - page.endSec;
          return (
            <Sequence
              key={i}
              from={toF(page.startSec)}
              durationInFrames={Math.max(
                1,
                toF(page.endSec) - toF(page.startSec)
              )}
              name={`Page ${String(i + 1).padStart(2, "0")} (${page.style})`}
            >
              {page.style === "kicker" ? (
                <KickerPageView
                  page={page}
                  pageStartSec={page.startSec}
                  bandTop={bandTop}
                  bandHeight={bandHeight}
                />
              ) : (
                <CaptionPageView
                  page={page}
                  pageStartSec={page.startSec}
                  fadeOutAtEnd={gapAfter > 0.15}
                  bandTop={bandTop}
                  bandHeight={bandHeight}
                />
              )}
            </Sequence>
          );
        })}

        <Sequence
          from={toF(STACK_START_SEC)}
          durationInFrames={toF(STACK_END_SEC) - toF(STACK_START_SEC)}
          name="Stack Branchen"
        >
          <StackView bandTop={bandTop} bandHeight={bandHeight} />
        </Sequence>

        {showNameInsert && (
          <Sequence
            from={toF(NAME_INSERT_START_SEC)}
            durationInFrames={
              toF(NAME_INSERT_END_SEC) - toF(NAME_INSERT_START_SEC)
            }
            name="Name-Insert"
          >
            <NameInsert text={nameInsertText} bandBottom={bandBottom} />
          </Sequence>
        )}

        {showCtaFinale && (
          <Sequence from={toF(CTA_START_SEC)} name="CTA-Finale">
            <CtaFinale
              jobTitle={jobTitle}
              ctaText={ctaText}
              bandTop={bandTop}
              bandHeight={bandHeight}
            />
          </Sequence>
        )}

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
