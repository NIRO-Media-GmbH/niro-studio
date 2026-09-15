// ============================================================
// Aeterna Weddings — Messe-Screen, Grafik-Ebene (Look „Elfenbein“)
// 3840×2160 @ 50 fps, 100 s = ein Info-Durchlauf (8 Kapitel à 12,5 s).
// Gerendert als ProRes 4444 mit Alpha: Elfenbein-Fläche mit ausgespartem
// Videofenster links (1152×648 im 1080er-Raster) – das Showreel liegt in
// Resolve darunter (Zoom 0,6 · Pan −640 px) und der Loop läuft 3× = 5:00.
// Loop-exakt: Kapitel 8 blendet zum Ende aus, Kapitel 1 startet bei Frame 0.
// Spezifikation: projects/AeternaWeddings/Messe-Showreel/2026-09 Hochzeitsmesse/_intern/design-spec.md
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadRedHat } from "@remotion/google-fonts/RedHatText";
import { loadFont as loadGreatVibes } from "@remotion/google-fonts/GreatVibes";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("aeterna-weddings", brandJson as any);

const { fontFamily: PLAYFAIR } = loadPlayfair("normal", { weights: ["400", "500"], subsets: ["latin", "latin-ext"] });
const { fontFamily: REDHAT } = loadRedHat("normal", { weights: ["400", "500"], subsets: ["latin", "latin-ext"] });
const { fontFamily: SCRIPT } = loadGreatVibes("normal", { weights: ["400"], subsets: ["latin", "latin-ext"] });

// --- CI (Logo-SVG + aeterna-weddings.de) ---
const IVORY = "#FCFBF8";
const BROWN = "#3B352F";
const GOLD = "#C1A67A";
const GOLD_DEEP = "#9C8156"; // Schreibschrift/Text in Gold (Kontrast auf Elfenbein)
const LINE_IDLE = "#E6DED1";

// --- Layout im 1920×1080-Raster (Stage skaliert auf die Kompositionsgröße) ---
const BASE_W = 1920;
const BASE_H = 1080;
const WIN = { x: 64, y: 216, w: 1152, h: 648, r: 14 };
const PANEL_X = 1280;
const PANEL_W = 576;
const CHAPTER_Y = 300;
const PROGRESS_Y = 772;
const QR_Y = 812;
const QR_SIZE = 180;

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const EASE_IN = Easing.in(Easing.cubic);

export const messeScreenSchema = projectPropsSchema.extend({
  qrUrl: z.string().describe("QR-Ziel (nur Info – Grafik liegt als SVG in public/clients/aeterna-weddings)"),
  videoVorschau: z.boolean().describe("Nur Studio: dunkle Fläche im Videofenster statt Transparenz"),
});

export const messeScreenDefaults: z.infer<typeof messeScreenSchema> = {
  format: "landscape-4k",
  fps: 50,
  durationInSeconds: 100,
  transparent: true,
  qrUrl: "https://aeterna-weddings.de",
  videoVorschau: false,
  review: { showGuides: false, showSafeZone: true, showFaceZone: false, showGrid: false, guideOpacity: 0.35 },
};

// ------------------------------------------------------------
// Kapitel (Texte laut abgenommenem Kapitelplan)
// ------------------------------------------------------------

type Chapter =
  | { kind: "statement"; lines: string[]; accentFrom: number; size?: number }
  | { kind: "list"; kicker?: string; headline: string; items: string[] }
  | { kind: "numbers"; headline: string; items: { von: number; bis?: number; einheit: string; label: string }[] }
  | { kind: "script"; script: string; lines: string[] }
  | { kind: "team"; lines: string[]; sub: string[] }
  | { kind: "bonus"; kicker: string; headline: string; sub: string[] };

const CHAPTERS: Chapter[] = [
  { kind: "statement", lines: ["Liebe, die man sieht.", "Momente, die man fühlt."], accentFrom: 1, size: 50 },
  { kind: "statement", lines: ["Fotos zeigen,", "wie es aussah.", "Filme zeigen,", "wie es sich", "angefühlt hat."], accentFrom: 2 },
  { kind: "list", headline: "Alles aus einer Hand", items: ["Cinematic Film", "Social-Reels inklusive", "Fotos auf Wunsch"] },
  {
    kind: "numbers",
    headline: "Schnell bei euch",
    items: [
      { von: 48, bis: 72, einheit: "h", label: "Sneak Peek" },
      { von: 24, einheit: "h", label: "erste Reels" },
      { von: 100, einheit: "%", label: "pünktliche Lieferung" },
    ],
  },
  {
    kind: "list",
    headline: "Was euch nicht passiert:",
    items: ["Keine gestellten Posen", "Kein Warten ohne Ende", "Keine Überraschungen", "Kein Risiko"],
  },
  { kind: "script", script: "Aeterna Legacy", lines: ["Geführte Interviews", "mit euch und", "euren Liebsten"] },
  { kind: "team", lines: ["Ein eingespieltes Team.", "Ein Ansprechpartner."], sub: ["Deutschlandweit", "2027 noch Termine frei"] },
  { kind: "bonus", kicker: "Messe-Bonus", headline: "Ein Extra-Reel geschenkt", sub: ["bei Buchung bis 14 Tage", "nach der Messe"] },
];

// ------------------------------------------------------------
// Bausteine
// ------------------------------------------------------------

/** Kapitel-Timing relativ zum Kapitelstart: Einblendung, Halten, Ausblendung (0,4 s). */
const useChapterPhase = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const exitStart = durationInFrames - Math.round(0.4 * fps);
  const exit = interpolate(frame, [exitStart, durationInFrames - 1], [1, 0], { ...CLAMP, easing: EASE_IN });
  const exitY = interpolate(frame, [exitStart, durationInFrames - 1], [0, -10], { ...CLAMP, easing: EASE_IN });
  return { frame, fps, exit, exitY };
};

/** Zeile gleitet aus einer Maske nach oben (0,7 s, weicher Auslauf). */
const MaskLine: React.FC<{ delay: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [delay, delay + Math.round(0.7 * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <div style={{ overflow: "hidden", paddingBottom: "0.12em", marginBottom: "-0.12em" }}>
      <div style={{ transform: `translateY(${(1 - p) * 110}%)`, opacity: 0.2 + 0.8 * p, ...style }}>{children}</div>
    </div>
  );
};

/** Goldene Linie, die sich von links zeichnet. */
const GoldRule: React.FC<{ delay: number; width?: number; top?: number }> = ({ delay, width = 72, top = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const w = interpolate(frame, [delay, delay + Math.round(0.8 * fps)], [0, width], { ...CLAMP, easing: EASE_OUT });
  return <div style={{ marginTop: top, width: w, height: 2, background: GOLD }} />;
};

/** Listenpunkt: kleiner Goldpunkt + Text, gleitet sanft ein. */
const ListItem: React.FC<{ delay: number; text: string }> = ({ delay, text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [delay, delay + Math.round(0.6 * fps)], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        marginTop: 20,
        opacity: p,
        transform: `translateX(${(1 - p) * 24}px)`,
      }}
    >
      <div style={{ width: 9, height: 9, borderRadius: 5, background: GOLD, flexShrink: 0 }} />
      <div style={{ fontFamily: REDHAT, fontWeight: 400, fontSize: 38, color: BROWN, letterSpacing: 0.2 }}>{text}</div>
    </div>
  );
};

const HEADLINE: React.CSSProperties = {
  fontFamily: PLAYFAIR,
  fontWeight: 400,
  fontSize: 58,
  lineHeight: 1.14,
  color: BROWN,
  letterSpacing: -0.6,
};

const ChapterView: React.FC<{ chapter: Chapter }> = ({ chapter }) => {
  const { frame, fps, exit, exitY } = useChapterPhase();
  const s = (sec: number) => Math.round(sec * fps);

  let body: React.ReactNode = null;
  if (chapter.kind === "statement") {
    body = (
      <>
        {chapter.lines.map((l, i) => (
          <MaskLine key={i} delay={s(0.2) + i * s(0.12) + (i >= chapter.accentFrom ? s(0.5) : 0)}>
            <div
              style={{ ...HEADLINE, fontSize: chapter.size ?? HEADLINE.fontSize, color: i >= chapter.accentFrom ? GOLD_DEEP : BROWN }}
            >
              {l}
            </div>
          </MaskLine>
        ))}
        <GoldRule delay={s(1.4)} top={34} />
      </>
    );
  } else if (chapter.kind === "list") {
    body = (
      <>
        <MaskLine delay={s(0.2)}>
          <div style={HEADLINE}>{chapter.headline}</div>
        </MaskLine>
        <GoldRule delay={s(0.9)} top={26} />
        <div style={{ marginTop: 18 }}>
          {chapter.items.map((t, i) => (
            <ListItem key={i} delay={s(1.4) + i * s(0.9)} text={t} />
          ))}
        </div>
      </>
    );
  } else if (chapter.kind === "numbers") {
    body = (
      <>
        <MaskLine delay={s(0.2)}>
          <div style={HEADLINE}>{chapter.headline}</div>
        </MaskLine>
        <GoldRule delay={s(0.9)} top={26} />
        <div style={{ marginTop: 26 }}>
          {chapter.items.map((it, i) => {
            const d = s(1.3) + i * s(1.0);
            const p = interpolate(frame, [d, d + s(0.6)], [0, 1], { ...CLAMP, easing: EASE_OUT });
            const count = interpolate(frame, [d, d + s(1.2)], [0, 1], { ...CLAMP, easing: EASE_OUT });
            const zahl = it.bis
              ? `${Math.round(it.von * count)}–${Math.round(it.bis * count)}`
              : `${Math.round(it.von * count)}`;
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: 20,
                  marginTop: i ? 16 : 0,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 16}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily: PLAYFAIR,
                    fontSize: 64,
                    color: GOLD_DEEP,
                    minWidth: 214,
                    fontVariantNumeric: "tabular-nums",
                    letterSpacing: -1,
                  }}
                >
                  {zahl}
                  <span style={{ fontSize: 40, marginLeft: 8 }}>{it.einheit}</span>
                </div>
                <div style={{ fontFamily: REDHAT, fontSize: 31, color: BROWN, whiteSpace: "nowrap" }}>{it.label}</div>
              </div>
            );
          })}
        </div>
      </>
    );
  } else if (chapter.kind === "script") {
    const p = interpolate(frame, [s(0.2), s(1.1)], [0, 1], { ...CLAMP, easing: EASE_OUT });
    body = (
      <>
        <div
          style={{
            fontFamily: SCRIPT,
            fontSize: 104,
            lineHeight: 1,
            color: GOLD_DEEP,
            opacity: p,
            transform: `translateY(${(1 - p) * 20}px)`,
          }}
        >
          {chapter.script}
        </div>
        <GoldRule delay={s(1.0)} top={18} />
        <div style={{ marginTop: 22 }}>
          {chapter.lines.map((l, i) => (
            <MaskLine key={i} delay={s(1.5) + i * s(0.14)}>
              <div style={{ ...HEADLINE, fontSize: 50 }}>{l}</div>
            </MaskLine>
          ))}
        </div>
      </>
    );
  } else if (chapter.kind === "team") {
    const p = interpolate(frame, [s(1.8), s(2.5)], [0, 1], { ...CLAMP, easing: EASE_OUT });
    body = (
      <>
        {chapter.lines.map((l, i) => (
          <MaskLine key={i} delay={s(0.2) + i * s(0.5)}>
            <div style={{ ...HEADLINE, fontSize: 54 }}>{l}</div>
          </MaskLine>
        ))}
        <GoldRule delay={s(1.4)} top={30} />
        <div
          style={{
            marginTop: 26,
            fontFamily: REDHAT,
            fontSize: 34,
            lineHeight: 1.35,
            color: GOLD_DEEP,
            opacity: p,
            transform: `translateY(${(1 - p) * 14}px)`,
          }}
        >
          {chapter.sub.map((t, i) => (
            <div key={i}>{t}</div>
          ))}
        </div>
      </>
    );
  } else if (chapter.kind === "bonus") {
    const k = interpolate(frame, [s(0.2), s(0.8)], [0, 1], { ...CLAMP, easing: EASE_OUT });
    const sub = interpolate(frame, [s(2.0), s(2.7)], [0, 1], { ...CLAMP, easing: EASE_OUT });
    body = (
      <>
        <div
          style={{
            display: "inline-block",
            fontFamily: REDHAT,
            fontWeight: 500,
            fontSize: 24,
            letterSpacing: 6,
            textTransform: "uppercase",
            color: IVORY,
            background: GOLD_DEEP,
            padding: "10px 18px 9px",
            opacity: k,
          }}
        >
          {chapter.kicker}
        </div>
        <div style={{ marginTop: 26 }}>
          <MaskLine delay={s(0.7)}>
            <div style={HEADLINE}>{chapter.headline}</div>
          </MaskLine>
        </div>
        <GoldRule delay={s(1.6)} top={26} />
        <div
          style={{
            marginTop: 24,
            fontFamily: REDHAT,
            fontSize: 34,
            lineHeight: 1.3,
            color: BROWN,
            opacity: sub,
            transform: `translateY(${(1 - sub) * 14}px)`,
          }}
        >
          {chapter.sub.map((t, i) => (
            <div key={i}>{t}</div>
          ))}
        </div>
      </>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        left: PANEL_X,
        top: CHAPTER_Y,
        width: PANEL_W,
        opacity: exit,
        transform: `translateY(${exitY}px)`,
      }}
    >
      {body}
    </div>
  );
};

/** Elfenbein-Fläche mit ausgespartem, abgerundetem Videofenster (evenodd – keine Border-Haarlinie im Alpha). */
const Grund: React.FC<{ vorschau: boolean }> = ({ vorschau }) => {
  const { x, y, w, h, r } = WIN;
  const hole = `M ${x + r} ${y} H ${x + w - r} A ${r} ${r} 0 0 1 ${x + w} ${y + r} V ${y + h - r} A ${r} ${r} 0 0 1 ${x + w - r} ${y + h} H ${x + r} A ${r} ${r} 0 0 1 ${x} ${y + h - r} V ${y + r} A ${r} ${r} 0 0 1 ${x + r} ${y} Z`;
  return (
    <svg width={BASE_W} height={BASE_H} style={{ position: "absolute", left: 0, top: 0 }}>
      {vorschau && <rect x={x} y={y} width={w} height={h} rx={r} fill="#2B2724" />}
      <path d={`M 0 0 H ${BASE_W} V ${BASE_H} H 0 Z ${hole}`} fill={IVORY} fillRule="evenodd" />
      {/* Passepartout-Linie in Gold */}
      <rect x={x - 12} y={y - 12} width={w + 24} height={h + 24} rx={r + 12} fill="none" stroke={GOLD} strokeWidth={1.5} />
    </svg>
  );
};

const Fortschritt: React.FC<{ kapitel: number; anteil: number }> = ({ kapitel, anteil }) => {
  const n = CHAPTERS.length;
  const gap = 8;
  const segW = (PANEL_W - gap * (n - 1)) / n;
  return (
    <div style={{ position: "absolute", left: PANEL_X, top: PROGRESS_Y, display: "flex", gap }}>
      {Array.from({ length: n }, (_, i) => (
        <div key={i} style={{ width: segW, height: 3, background: LINE_IDLE, position: "relative", overflow: "hidden" }}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: GOLD,
              transformOrigin: "left center",
              transform: `scaleX(${i < kapitel ? 1 : i === kapitel ? anteil : 0})`,
            }}
          />
        </div>
      ))}
    </div>
  );
};

// ------------------------------------------------------------
// Komposition
// ------------------------------------------------------------

export const AeternaMesseScreen: React.FC<z.infer<typeof messeScreenSchema>> = ({ videoVorschau, review }) => {
  const frame = useCurrentFrame();
  const { width, durationInFrames } = useVideoConfig();
  const chapterLen = durationInFrames / CHAPTERS.length;
  const kapitel = Math.min(CHAPTERS.length - 1, Math.floor(frame / chapterLen));
  const anteil = (frame - kapitel * chapterLen) / chapterLen;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <div
          style={{
            position: "absolute",
            width: BASE_W,
            height: BASE_H,
            transform: `scale(${width / BASE_W})`,
            transformOrigin: "0 0",
          }}
        >
          <Grund vorschau={videoVorschau} />

          {/* Leistungs-Zeile über dem Video */}
          <div
            style={{
              position: "absolute",
              left: WIN.x,
              width: WIN.w,
              top: 140,
              textAlign: "center",
              fontFamily: REDHAT,
              fontWeight: 500,
              fontSize: 22,
              letterSpacing: 7,
              textTransform: "uppercase",
              color: GOLD_DEEP,
            }}
          >
            Hochzeitsfilm · Social-Reels · Fotografie
          </div>

          {/* Claim unter dem Video */}
          <div
            style={{
              position: "absolute",
              left: WIN.x,
              width: WIN.w,
              top: WIN.y + WIN.h + 42,
              textAlign: "center",
              fontFamily: SCRIPT,
              fontSize: 54,
              lineHeight: 1.1,
              color: GOLD_DEEP,
            }}
          >
            Euer Tag. Eure Erinnerungen. Für immer spürbar.
          </div>

          {/* Logo + Linie */}
          <Img
            src={staticFile("clients/aeterna-weddings/aeterna-logo.svg")}
            style={{ position: "absolute", left: PANEL_X - 6, top: 92, width: 300 }}
          />
          <div style={{ position: "absolute", left: PANEL_X, top: 232, width: 44, height: 2, background: GOLD }} />

          {/* Kapitel */}
          {CHAPTERS.map((c, i) => (
            <Sequence
              key={i}
              name={`Kapitel ${i + 1}`}
              from={Math.round(i * chapterLen)}
              durationInFrames={Math.round((i + 1) * chapterLen) - Math.round(i * chapterLen)}
            >
              <ChapterView chapter={c} />
            </Sequence>
          ))}

          <Fortschritt kapitel={kapitel} anteil={anteil} />

          {/* QR + CTA (statisch – Scanbarkeit) */}
          <Img
            src={staticFile("clients/aeterna-weddings/qr-aeterna-weddings.svg")}
            style={{ position: "absolute", left: PANEL_X - 8, top: QR_Y, width: QR_SIZE, height: QR_SIZE }}
          />
          <div style={{ position: "absolute", left: PANEL_X + QR_SIZE + 18, top: QR_Y + 30, width: PANEL_W - QR_SIZE - 18 }}>
            <div style={{ fontFamily: REDHAT, fontWeight: 500, fontSize: 20, letterSpacing: 5, color: GOLD_DEEP, textTransform: "uppercase" }}>
              Jetzt scannen
            </div>
            <div style={{ marginTop: 10, fontFamily: PLAYFAIR, fontSize: 36, lineHeight: 1.15, color: BROWN }}>
              Kostenfreies Kennenlernen
            </div>
            <div style={{ marginTop: 10, fontFamily: REDHAT, fontSize: 24, color: GOLD_DEEP }}>aeterna-weddings.de</div>
          </div>
        </div>

        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            showFaceZone={review.showFaceZone ?? false}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
