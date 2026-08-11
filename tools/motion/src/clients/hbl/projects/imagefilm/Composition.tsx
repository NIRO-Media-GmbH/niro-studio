// ============================================================
// HBL Management — Imagefilm „Wer ist HBL" (Grafik-Paket)
// Master-Overlay (eine Datei, Timings aus Cut02-SRT) + Einzel-Comps
// 16:9 landscape-4k (3840×2160), 25 fps, ProRes 4444 Alpha
//
// CI (Material/CI/guidline.pdf): Kirschrot #FF1438 ·
// Eierschalenweiß #FCF8EC · Dunkles Grau #908385.
// Fonts lt. CI: N27 Regular (große Headlines/Slogans, liegt in
// public/fonts/hbl/n27-regular.otf) + Futura (Fließtext/Sublines,
// Medium+Bold aus macOS-TTC — System-Auflösung hatte defektes „é").
//
// Master-Timings = Davids Cut02 (Material/Cut02-HBL trans.srt),
// Video-Zeit 0:00 = DaVinci-TC 01:00:00.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("hbl", brandJson as any);

const ROT = "#FF1438";
const EIERSCHALE = "#FCF8EC";
const GRAU = "#908385";
const LOGO_ROT = "clients/hbl/logo-rot.png";

const FONT_FACES = [
  { family: "HBL Futura", file: "futura-medium.ttf", weight: 500 },
  { family: "HBL Futura", file: "futura-bold.ttf", weight: 700 },
  { family: "HBL N27", file: "n27-regular.otf", weight: 400 },
];
if (typeof document !== "undefined" && !document.getElementById("hbl-fonts")) {
  const style = document.createElement("style");
  style.id = "hbl-fonts";
  style.textContent = FONT_FACES.map(
    (f) =>
      `@font-face { font-family: "${f.family}"; font-weight: ${f.weight}; font-display: block; src: url("${staticFile(
        `fonts/hbl/${f.file}`
      )}"); }`
  ).join("\n");
  document.head.appendChild(style);
}
const FONT = "'HBL Futura', Futura, 'Trebuchet MS', sans-serif";
// N27 nur für große Headlines/Slogans (CI-Regel); Regular-Schnitt → weight 400.
const FONT_HEAD = "'HBL N27', 'HBL Futura', Futura, sans-serif";

const REVIEW_DEFAULTS = {
  showGuides: false,
  showSafeZone: true,
  showFaceZone: true,
  showGrid: false,
  guideOpacity: 0.35,
} as const;

// --- Anim-Helfer ---

const useStage = () => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const sc = width / 3840; // alle px-Werte sind für 4K gesetzt
  return { frame, fps, sc, durationInFrames };
};

/** Weicher Einstieg ohne Überschwingen (seriöse CI). */
const easeIn = (frame: number, fps: number, delay = 0) =>
  spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 28 });

/** Dezenter Pop (leichtes Überschwingen) für Akzente. */
const popIn = (frame: number, fps: number, delay = 0) =>
  spring({ frame: frame - delay, fps, config: { damping: 16, mass: 0.7 } });

/** Ausblenden am Ende: outAtFrames = Länge der (Sequenz-)Einblendung. */
const outFade = (frame: number, outAtFrames: number, lenFrames = 10) =>
  interpolate(frame, [outAtFrames - lenFrames - 2, outAtFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

/** In Sequenzen ist useVideoConfig().durationInFrames die Gesamtlänge —
 *  Visuals bekommen ihr Out deshalb explizit als outAtSec. */
const useOutAt = (outAtSec?: number) => {
  const { fps, durationInFrames } = useVideoConfig();
  return outAtSec ? Math.round(outAtSec * fps) : durationInFrames;
};

type Vis<T> = React.FC<T & { outAtSec?: number }>;

const Guides: React.FC<{ review?: z.infer<typeof projectPropsSchema>["review"] }> = ({ review }) =>
  review?.showGuides ? (
    <ReviewOverlay
      showSafeZone={review.showSafeZone ?? true}
      showFaceZone={review.showFaceZone ?? true}
      showGrid={review.showGrid ?? false}
      faceZone={review.faceZone}
      guideOpacity={review.guideOpacity ?? 0.35}
    />
  ) : null;

/** Wrapper für die registrierten Einzel-Comps. */
const Standalone = (
  p: { review?: z.infer<typeof projectPropsSchema>["review"] },
  children: React.ReactNode
) => (
  <CIProvider ci={ci}>
    <AbsoluteFill style={{ fontFamily: FONT }}>
      {children}
      <Guides review={p.review} />
    </AbsoluteFill>
  </CIProvider>
);

// ============================================================
// Visuals (werden von Einzel-Comps UND vom Master genutzt)
// ============================================================

// --- 1) Säulen-Grafik „Wer ist HBL" (Vollbild-Karte mit Alpha-Blenden) ---

type SaeulenTexte = {
  klartextzeile: string;
  saeule1Nr: string;
  saeule1Titel: string;
  saeule2Nr: string;
  saeule2Titel: string;
  mitOutro: boolean;
};

const SaeulenVisual: Vis<SaeulenTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const bg = easeIn(frame, fps, 0);
  const logo = easeIn(frame, fps, 4);
  const s1 = easeIn(frame, fps, 10);
  const s2 = easeIn(frame, fps, 15);
  const punkt = popIn(frame, fps, 19);
  const zeile = easeIn(frame, fps, 22);
  const out = p.mitOutro ? outFade(frame, outAt, 12) : 1;

  const saeule = (nr: string, titel: string, drive: number, dir: 1 | -1) => (
    <div
      style={{
        width: 1240 * sc,
        textAlign: "center",
        opacity: drive,
        transform: `translateX(${(1 - drive) * 70 * sc * dir}px)`,
      }}
    >
      <div style={{ fontFamily: FONT_HEAD, fontSize: 210 * sc, fontWeight: 400, color: ROT, lineHeight: 1 }}>
        {nr}
      </div>
      <div
        style={{
          marginTop: 36 * sc,
          fontFamily: FONT_HEAD,
          fontSize: 86 * sc,
          fontWeight: 400,
          color: GRAU,
          textTransform: "uppercase",
          letterSpacing: 8 * sc,
          lineHeight: 1.25,
        }}
      >
        {titel}
      </div>
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: out }}>
      <AbsoluteFill style={{ backgroundColor: EIERSCHALE, opacity: bg }} />
      <AbsoluteFill style={{ alignItems: "center" }}>
        <Img
          src={staticFile(LOGO_ROT)}
          style={{
            width: 620 * sc,
            marginTop: 240 * sc,
            opacity: logo,
            transform: `scale(${0.92 + 0.08 * logo})`,
          }}
        />
        <div
          style={{
            marginTop: 170 * sc,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 130 * sc,
          }}
        >
          {saeule(p.saeule1Nr, p.saeule1Titel, s1, -1)}
          {/* Trenner: Linie + Punkt (Motiv aus dem Logo-„H") */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34 * sc }}>
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
            <div
              style={{
                width: 54 * sc,
                height: 54 * sc,
                borderRadius: "50%",
                background: ROT,
                transform: `scale(${punkt})`,
              }}
            />
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
          </div>
          {saeule(p.saeule2Nr, p.saeule2Titel, s2, 1)}
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 210 * sc,
            fontFamily: FONT_HEAD,
            fontSize: 58 * sc,
            fontWeight: 400,
            color: ROT,
            textTransform: "uppercase",
            letterSpacing: 12 * sc,
            opacity: zeile,
          }}
        >
          {p.klartextzeile}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// --- 1b) Säulen-Fokus: startet wie die Säulen-Grafik (beide sichtbar),
//     dann gleitet die gewählte Säule in die Mitte und wächst — Rest weicht.
//     Bewusst eigene Komponente: die Master-Grafik bleibt eingefroren. ---

type SaeulenFokusTexte = SaeulenTexte & { fokus: "1" | "2"; switchAtSec: number };

const SaeulenFokusVisual: Vis<SaeulenFokusTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const bg = easeIn(frame, fps, 0);
  const logo = easeIn(frame, fps, 4);
  const s1 = easeIn(frame, fps, 10);
  const s2 = easeIn(frame, fps, 15);
  const punkt = popIn(frame, fps, 19);
  const zeile = easeIn(frame, fps, 22);
  const out = p.mitOutro ? outFade(frame, outAt, 12) : 1;

  // Switch: gewählte Säule zur Mitte + größer, alles andere weicht
  const sw = interpolate(
    frame,
    [Math.round(p.switchAtSec * fps), Math.round(p.switchAtSec * fps) + 20],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
  );
  // Abstand Säulen-Mitte ↔ Bild-Mitte im Row-Layout (1240 + 130 + 54 + 130 + 1240)
  const versatz = 777 * sc;

  const saeule = (nr: string, titel: string, drive: number, dir: 1 | -1, imFokus: boolean) => {
    const einflug = (1 - drive) * 70 * sc * dir;
    const fokusX = imFokus ? -dir * versatz * sw : -dir * 160 * sc * sw;
    const fokusY = imFokus ? 60 * sc * sw : 0;
    const scale = imFokus ? 1 + 0.5 * sw : 1;
    const opacity = imFokus ? drive : drive * (1 - sw);
    return (
      <div
        style={{
          width: 1240 * sc,
          textAlign: "center",
          opacity,
          transform: `translate(${einflug + fokusX}px, ${fokusY}px) scale(${scale})`,
          transformOrigin: "center",
        }}
      >
        <div style={{ fontFamily: FONT_HEAD, fontSize: 210 * sc, fontWeight: 400, color: ROT, lineHeight: 1 }}>
          {nr}
        </div>
        <div
          style={{
            marginTop: 36 * sc,
            fontFamily: FONT_HEAD,
            fontSize: 86 * sc,
            fontWeight: 400,
            color: GRAU,
            textTransform: "uppercase",
            letterSpacing: 8 * sc,
            lineHeight: 1.25,
          }}
        >
          {titel}
        </div>
      </div>
    );
  };

  return (
    <AbsoluteFill style={{ opacity: out }}>
      <AbsoluteFill style={{ backgroundColor: EIERSCHALE, opacity: bg }} />
      <AbsoluteFill style={{ alignItems: "center" }}>
        <Img
          src={staticFile(LOGO_ROT)}
          style={{
            width: 620 * sc,
            marginTop: 240 * sc,
            opacity: logo * (1 - sw),
            transform: `scale(${0.92 + 0.08 * logo}) translateY(${-40 * sc * sw}px)`,
          }}
        />
        <div
          style={{
            marginTop: 170 * sc,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 130 * sc,
          }}
        >
          {saeule(p.saeule1Nr, p.saeule1Titel, s1, -1, p.fokus === "1")}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 34 * sc,
              opacity: 1 - sw,
            }}
          >
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
            <div
              style={{
                width: 54 * sc,
                height: 54 * sc,
                borderRadius: "50%",
                background: ROT,
                transform: `scale(${punkt * (1 - sw)})`,
              }}
            />
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
          </div>
          {saeule(p.saeule2Nr, p.saeule2Titel, s2, 1, p.fokus === "2")}
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 210 * sc,
            fontFamily: FONT_HEAD,
            fontSize: 58 * sc,
            fontWeight: 400,
            color: ROT,
            textTransform: "uppercase",
            letterSpacing: 12 * sc,
            opacity: zeile * (1 - sw),
          }}
        >
          {p.klartextzeile}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// --- 1c) Brand-Opener: allgemeiner Einstieg „Wer ist HBL" —
//     Punkt → Logo → „Deine HR-Agentur" + Zeile → Säulen 01|02 → Fokus 01.
//     Ersetzt am Filmanfang die Fokus-01-Karte (Master bleibt eingefroren). ---

type OpenerTexte = SaeulenTexte & {
  headline: string;
  fokus: "1" | "2";
  saeulenAtSec: number;
  fokusAtSec: number;
};

const OpenerVisual: Vis<OpenerTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const t = (sec: number) => Math.round(sec * fps);
  const bg = easeIn(frame, fps, 0);
  const logo = easeIn(frame, fps, 10);
  const head = easeIn(frame, fps, 32);
  const zeile = easeIn(frame, fps, 55);
  // Phase 2: Headline/Zeile weichen, Säulen erscheinen
  const wechsel = interpolate(frame, [t(p.saeulenAtSec), t(p.saeulenAtSec) + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const s1 = easeIn(frame, fps, t(p.saeulenAtSec) + 8);
  const s2 = easeIn(frame, fps, t(p.saeulenAtSec) + 13);
  const trenner = popIn(frame, fps, t(p.saeulenAtSec) + 17);
  // Phase 3: Fokus auf eine Säule
  const sw = interpolate(frame, [t(p.fokusAtSec), t(p.fokusAtSec) + 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const out = p.mitOutro ? outFade(frame, outAt, 12) : 1;
  const versatz = 777 * sc;

  const saeule = (nr: string, titel: string, drive: number, dir: 1 | -1, imFokus: boolean) => {
    const einflug = (1 - drive) * 70 * sc * dir;
    const fokusX = imFokus ? -dir * versatz * sw : -dir * 160 * sc * sw;
    const scale = imFokus ? 1 + 0.5 * sw : 1;
    const opacity = imFokus ? drive : drive * (1 - sw);
    return (
      <div
        style={{
          width: 1240 * sc,
          textAlign: "center",
          opacity,
          transform: `translate(${einflug + fokusX}px, ${imFokus ? 60 * sc * sw : 0}px) scale(${scale})`,
          transformOrigin: "center",
        }}
      >
        <div style={{ fontFamily: FONT_HEAD, fontSize: 210 * sc, fontWeight: 400, color: ROT, lineHeight: 1 }}>
          {nr}
        </div>
        <div
          style={{
            marginTop: 36 * sc,
            fontFamily: FONT_HEAD,
            fontSize: 86 * sc,
            fontWeight: 400,
            color: GRAU,
            textTransform: "uppercase",
            letterSpacing: 8 * sc,
            lineHeight: 1.25,
          }}
        >
          {titel}
        </div>
      </div>
    );
  };

  return (
    <AbsoluteFill style={{ opacity: out }}>
      <AbsoluteFill style={{ backgroundColor: EIERSCHALE, opacity: bg }} />
      <AbsoluteFill style={{ alignItems: "center" }}>
        <Img
          src={staticFile(LOGO_ROT)}
          style={{
            width: 620 * sc,
            marginTop: 240 * sc,
            opacity: logo * (1 - sw),
            transform: `scale(${0.92 + 0.08 * logo}) translateY(${-40 * sc * sw}px)`,
          }}
        />
        {/* Phase 1: allgemeine Headline + Zeile */}
        <div
          style={{
            position: "absolute",
            top: 1080 * sc,
            textAlign: "center",
            opacity: 1 - wechsel,
            transform: `translateY(${-40 * sc * wechsel}px)`,
          }}
        >
          <div
            style={{
              fontFamily: FONT_HEAD,
              fontSize: 150 * sc,
              fontWeight: 400,
              color: ROT,
              textTransform: "uppercase",
              letterSpacing: 20 * sc,
              opacity: head,
              transform: `translateY(${(1 - head) * 40 * sc}px)`,
            }}
          >
            {p.headline}
          </div>
          <div
            style={{
              marginTop: 70 * sc,
              fontFamily: FONT,
              fontSize: 58 * sc,
              fontWeight: 500,
              color: GRAU,
              textTransform: "uppercase",
              letterSpacing: 10 * sc,
              opacity: zeile,
            }}
          >
            {p.klartextzeile}
          </div>
        </div>
        {/* Phase 2+3: Säulen mit Fokus */}
        <div
          style={{
            marginTop: 170 * sc,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 130 * sc,
            opacity: wechsel,
          }}
        >
          {saeule(p.saeule1Nr, p.saeule1Titel, s1, -1, p.fokus === "1")}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 34 * sc,
              opacity: 1 - sw,
            }}
          >
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
            <div
              style={{
                width: 54 * sc,
                height: 54 * sc,
                borderRadius: "50%",
                background: ROT,
                transform: `scale(${trenner * (1 - sw)})`,
              }}
            />
            <div style={{ width: 6 * sc, height: 190 * sc, borderRadius: 999, background: GRAU, opacity: 0.45 }} />
          </div>
          {saeule(p.saeule2Nr, p.saeule2Titel, s2, 1, p.fokus === "2")}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// --- 2+3) Säulen-Titel-Badge unten links (optional mit Erklär-Subline) ---

type TitelTexte = { nr: string; titel: string; subline?: string };

const TitelBadgeVisual: Vis<TitelTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const sub = easeIn(frame, fps, 8);
  const out = outFade(frame, outAt, 10);

  return (
    <div
      style={{
        position: "absolute",
        left: 200 * sc,
        bottom: 220 * sc,
        display: "flex",
        alignItems: "stretch",
        gap: 26 * sc,
        opacity: drive * out,
        transform: `translateX(${(drive - 1) * 90 * sc}px)`,
        fontFamily: FONT_HEAD,
      }}
    >
      <div
        style={{
          background: ROT,
          color: EIERSCHALE,
          borderRadius: 999,
          padding: `${26 * sc}px ${54 * sc}px`,
          fontSize: 88 * sc,
          fontWeight: 400,
          display: "flex",
          alignItems: "center",
        }}
      >
        {p.nr}
      </div>
      <div
        style={{
          background: EIERSCHALE,
          borderRadius: 28 * sc,
          padding: `${26 * sc}px ${64 * sc}px`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
        }}
      >
        <div
          style={{
            color: ROT,
            fontSize: 76 * sc,
            fontWeight: 400,
            textTransform: "uppercase",
            letterSpacing: 6 * sc,
          }}
        >
          {p.titel}
        </div>
        {p.subline ? (
          <div
            style={{
              fontFamily: FONT,
              color: GRAU,
              fontSize: 46 * sc,
              fontWeight: 500,
              marginTop: 12 * sc,
              opacity: sub,
            }}
          >
            {p.subline}
          </div>
        ) : null}
      </div>
    </div>
  );
};

// --- Screen-Fenster: Rahmen im HBL-Look mit TRANSPARENTEM Loch —
//     Davids Bildschirmaufnahme liegt in DaVinci in der Spur DARUNTER
//     und erscheint gerahmt; die Themen-Chips laufen darüber. ---

type ScreenFrameTexte = { chips: string[]; fensterRatio?: number };

const ScreenFrameVisual: Vis<ScreenFrameTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const out = outFade(frame, outAt, 12);
  const rand = 22 * sc;
  const breite = 2700 * sc;
  // Seitenverhältnis von Davids Bildschirmaufnahme (Referenzbild 1118×570)
  const ratio = p.fensterRatio ?? 1.96;
  const fensterHoehe = (breite - 2 * rand) / ratio;
  const chromeHoehe = 84 * sc;
  const gesamtHoehe = chromeHoehe + fensterHoehe + rand;
  const radius = 40 * sc;
  const ueberlapp = 4 * sc; // gleichfarbige Balken satt überlappen — nie wieder Haarlinien

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "46%",
        transform: `translate(-50%, -50%) scale(${0.96 + 0.04 * drive})`,
        opacity: drive * out,
      }}
    >
      {/* Rahmen aus 4 überlappenden Eierschale-Balken (KEIN border/overflow —
          deren Clip-Innenkante erzeugte im Alpha eine sichtbare Haarlinie) */}
      <div
        style={{
          position: "relative",
          width: breite,
          height: gesamtHoehe,
          filter: `drop-shadow(0 ${14 * sc}px ${60 * sc}px rgba(0,0,0,0.30))`,
        }}
      >
        {/* Browser-Leiste (= oberer Rahmen) mit Punkt-Motiv */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: chromeHoehe + ueberlapp,
            background: EIERSCHALE,
            borderRadius: `${radius}px ${radius}px 0 0`,
            display: "flex",
            alignItems: "center",
            gap: 22 * sc,
            paddingLeft: 47 * sc,
            paddingBottom: ueberlapp,
            boxSizing: "border-box",
          }}
        >
          <div style={{ width: 26 * sc, height: 26 * sc, borderRadius: "50%", background: ROT }} />
          <div style={{ width: 26 * sc, height: 26 * sc, borderRadius: "50%", background: GRAU }} />
          <div style={{ width: 26 * sc, height: 26 * sc, borderRadius: "50%", background: GRAU, opacity: 0.45 }} />
        </div>
        {/* Seitenränder — überlappen Leiste und Fußleiste */}
        <div
          style={{
            position: "absolute",
            top: chromeHoehe - ueberlapp,
            bottom: rand - ueberlapp,
            left: 0,
            width: rand,
            background: EIERSCHALE,
          }}
        />
        <div
          style={{
            position: "absolute",
            top: chromeHoehe - ueberlapp,
            bottom: rand - ueberlapp,
            right: 0,
            width: rand,
            background: EIERSCHALE,
          }}
        />
        {/* Fußleiste */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: rand,
            background: EIERSCHALE,
            borderRadius: `0 0 ${radius}px ${radius}px`,
          }}
        />
        {/* dazwischen: transparentes Fenster für die Bildschirmaufnahme */}
      </div>
      {/* Themen-Chips — UNTER dem Rahmen (nicht im Bild), kumulativ einfliegend */}
      <div
        style={{
          position: "absolute",
          top: gesamtHoehe + 44 * sc,
          left: "50%",
          transform: "translateX(-50%)",
          width: 2760 * sc,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 26 * sc,
        }}
      >
        {p.chips.map((chip, i) => {
          const c = popIn(frame, fps, 34 + i * 16);
          return (
            <div
              key={chip}
              style={{
                background: EIERSCHALE,
                color: ROT,
                borderRadius: 999,
                padding: `${22 * sc}px ${56 * sc}px`,
                fontFamily: FONT,
                fontSize: 58 * sc,
                fontWeight: 700,
                boxShadow: `0 ${6 * sc}px ${28 * sc}px rgba(0,0,0,0.22)`,
                opacity: Math.min(1, c),
                transform: `scale(${0.7 + 0.3 * c})`,
              }}
            >
              {chip}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// --- 4) Zahl „−40 %" unten rechts ---

type ZahlTexte = { prefix: string; zahl: number; suffix: string };

const Zahl40Visual: Vis<ZahlTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const count = spring({ frame: frame - 6, fps, config: { damping: 60 }, durationInFrames: 40 });
  const wert = Math.round(count * p.zahl);
  const out = outFade(frame, outAt, 10);

  return (
    <div
      style={{
        position: "absolute",
        right: 200 * sc,
        bottom: 220 * sc,
        background: EIERSCHALE,
        borderRadius: 36 * sc,
        padding: `${56 * sc}px ${96 * sc}px`,
        textAlign: "center",
        opacity: drive * out,
        transform: `translateY(${(1 - drive) * 70 * sc}px)`,
        boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
      }}
    >
      <div
        style={{
          fontSize: 56 * sc,
          fontWeight: 500,
          color: GRAU,
          textTransform: "uppercase",
          letterSpacing: 10 * sc,
        }}
      >
        {p.prefix}
      </div>
      <div style={{ fontFamily: FONT_HEAD, fontSize: 310 * sc, fontWeight: 400, color: ROT, lineHeight: 1.05 }}>
        −{wert} %
      </div>
      <div
        style={{
          fontSize: 62 * sc,
          fontWeight: 500,
          color: GRAU,
          textTransform: "uppercase",
          letterSpacing: 10 * sc,
        }}
      >
        {p.suffix}
      </div>
    </div>
  );
};

// --- 4b) Ergebnis-Karte M1: „Weniger Fehler" + „Schnellere Durchlaufzeiten"
//     wortsynchron, dann −40 %-Countdown (kombiniert Checklisten- und
//     Zahl-Style; eigene Komponente, Master bleibt eingefroren) ---

type ErgebnisseM1Texte = {
  punkte: { text: string; atSec: number }[];
  zahlAtSec: number;
  prefix: string;
  zahl: number;
  suffix: string;
};

const ErgebnisseM1Visual: Vis<ErgebnisseM1Texte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const karte = easeIn(frame, fps, 0);
  const out = outFade(frame, outAt, 10);
  const zahlDelay = Math.round(p.zahlAtSec * fps);
  const zahlDrive = easeIn(frame, fps, zahlDelay - 4);
  const count = spring({ frame: frame - zahlDelay, fps, config: { damping: 60 }, durationInFrames: 40 });
  // führende Null + feste Ziffernfächer — Box und Zahl bleiben beim Zählen ruhig
  const ziffern = String(Math.round(count * p.zahl)).padStart(2, "0").split("");

  return (
    <div
      style={{
        position: "absolute",
        right: 200 * sc,
        bottom: 220 * sc,
        width: 1020 * sc, // fixe Breite — Karte darf beim Countdown nicht atmen
        background: EIERSCHALE,
        borderRadius: 36 * sc,
        padding: `${52 * sc}px ${90 * sc}px`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: karte * out,
        transform: `translateY(${(1 - karte) * 70 * sc}px)`,
        boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
      }}
    >
      {/* Punkte linksbündig */}
      <div style={{ alignSelf: "stretch", display: "flex", flexDirection: "column", gap: 30 * sc }}>
        {p.punkte.map((punkt, i) => {
          const t = popIn(frame, fps, Math.round(punkt.atSec * fps));
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 28 * sc,
                opacity: Math.min(1, t),
                transform: `translateX(${(1 - Math.min(1, t)) * 40 * sc}px)`,
              }}
            >
              <div
                style={{
                  width: 32 * sc,
                  height: 32 * sc,
                  borderRadius: "50%",
                  background: ROT,
                  flexShrink: 0,
                  transform: `scale(${t})`,
                }}
              />
              <div style={{ fontFamily: FONT, fontSize: 56 * sc, fontWeight: 500, color: GRAU }}>
                {punkt.text}
              </div>
            </div>
          );
        })}
      </div>
      {/* Trenner zwischen Punkten und Zahl */}
      <div
        style={{
          alignSelf: "stretch",
          height: 5 * sc,
          borderRadius: 999,
          background: GRAU,
          opacity: 0.3 * zahlDrive,
          marginTop: 44 * sc,
        }}
      />
      <div style={{ textAlign: "center", opacity: zahlDrive, marginTop: 36 * sc }}>
        <div
          style={{
            fontSize: 54 * sc,
            fontWeight: 500,
            color: GRAU,
            textTransform: "uppercase",
            letterSpacing: 10 * sc,
          }}
        >
          {p.prefix}
        </div>
        <div style={{ fontFamily: FONT_HEAD, fontSize: 290 * sc, fontWeight: 400, color: ROT, lineHeight: 1.05 }}>
          <span>−</span>
          {ziffern.map((z, i) => (
            <span key={i} style={{ display: "inline-block", width: "0.66em", textAlign: "center" }}>
              {z}
            </span>
          ))}
          <span> %</span>
        </div>
        <div
          style={{
            fontSize: 60 * sc,
            fontWeight: 500,
            color: GRAU,
            textTransform: "uppercase",
            letterSpacing: 10 * sc,
          }}
        >
          {p.suffix}
        </div>
      </div>
    </div>
  );
};

// --- 5+7) Kleine Captions unten links (karte = Eierschale/rot, pill = rot/Eierschale) ---

type CaptionTexte = { text: string; variante: "karte" | "pill" };

const CaptionVisual: Vis<CaptionTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const punkt = popIn(frame, fps, 6);
  const out = outFade(frame, outAt, 10);
  const istPill = p.variante === "pill";

  return (
    <div
      style={{
        position: "absolute",
        left: 200 * sc,
        bottom: 220 * sc,
        display: "flex",
        alignItems: "center",
        gap: 34 * sc,
        background: istPill ? ROT : EIERSCHALE,
        color: istPill ? EIERSCHALE : ROT,
        borderRadius: istPill ? 999 : 28 * sc,
        padding: `${30 * sc}px ${66 * sc}px`,
        fontFamily: istPill ? FONT_HEAD : FONT,
        fontSize: 68 * sc,
        fontWeight: istPill ? 400 : 500,
        textTransform: istPill ? "uppercase" : "none",
        letterSpacing: istPill ? 8 * sc : 1 * sc,
        opacity: drive * out,
        transform: `translateY(${(1 - drive) * 60 * sc}px)`,
        boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
      }}
    >
      {!istPill && (
        <div
          style={{
            width: 30 * sc,
            height: 30 * sc,
            borderRadius: "50%",
            background: ROT,
            transform: `scale(${punkt})`,
          }}
        />
      )}
      {p.text}
    </div>
  );
};

// --- 5b) Praxisfall-Transition: Vollbild-Karte mit Türen-Split —
//     zwei Flächenhälften schließen sich beim Einstieg und fahren am Ende
//     nach links/rechts auseinander (gibt den A1-Take frei). Kein Kreis. ---

type PraxisTransTexte = { text: string };

const PraxisfallTransitionVisual: Vis<PraxisTransTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const { width } = useVideoConfig();
  const outAt = useOutAt(p.outAtSec);
  const halb = width / 2 + 3 * sc; // 3 px Mitten-Überlappung gegen Haarlinie

  // IN: Hälften schließen sich aus links/rechts (~0,5 s)
  const tIn = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 13 });
  // OUT: erst Inhalt ausblenden, dann Türen auf (~0,75 s)
  const inhaltOut = interpolate(frame, [outAt - 26, outAt - 18], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tOut = interpolate(frame, [outAt - 19, outAt - 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const shift = halb * (1 - tIn) + halb * 1.02 * tOut;

  const punkt = popIn(frame, fps, 11);
  const text = easeIn(frame, fps, 13);

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: halb,
          height: "100%",
          background: EIERSCHALE,
          transform: `translateX(${-shift}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: halb,
          height: "100%",
          background: EIERSCHALE,
          transform: `translateX(${shift}px)`,
        }}
      />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", opacity: tIn * inhaltOut }}
      >
        <div
          style={{
            width: 64 * sc,
            height: 64 * sc,
            borderRadius: "50%",
            background: ROT,
            marginBottom: 70 * sc,
            transform: `scale(${punkt})`,
          }}
        />
        <div
          style={{
            fontFamily: FONT_HEAD,
            fontSize: 120 * sc,
            fontWeight: 400,
            color: ROT,
            textTransform: "uppercase",
            letterSpacing: 16 * sc,
            textAlign: "center",
            transform: `translateY(${(1 - text) * 40 * sc}px)`,
          }}
        >
          {p.text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// --- 5c) Split-Blende: schnelle Vollbild-Transition ohne Text —
//     Türen zu (kaschiert den Schnitt), Punkt-Akzent, Türen auf. ---

const SplitBlendeVisual: React.FC<{ outAtSec?: number }> = (p) => {
  const { frame, fps, sc } = useStage();
  const { width } = useVideoConfig();
  const outAt = useOutAt(p.outAtSec);
  const halb = width / 2 + 3 * sc;

  const tZu = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 13 });
  const tAuf = interpolate(frame, [outAt - 19, outAt - 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const shift = halb * (1 - tZu) + halb * 1.02 * tAuf;
  // Punkt muss weg sein, bevor die Türen halb offen sind
  const punkt = popIn(frame, fps, 8) * Math.max(0, 1 - tAuf * 2);

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: halb,
          height: "100%",
          background: EIERSCHALE,
          transform: `translateX(${-shift}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: halb,
          height: "100%",
          background: EIERSCHALE,
          transform: `translateX(${shift}px)`,
        }}
      />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: tZu }}>
        <div
          style={{
            width: 74 * sc,
            height: 74 * sc,
            borderRadius: "50%",
            background: ROT,
            transform: `scale(${punkt})`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// --- 5d) Ergebnis-Checkliste (S3-Part): Karte rechts, Punkte erscheinen
//     wortsynchron zum O-Ton (Timings aus Cut02-SRT) ---

type ChecklisteTexte = { items: { text: string; atSec: number }[] };

const ChecklisteVisual: Vis<ChecklisteTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const karte = easeIn(frame, fps, 0);
  const out = outFade(frame, outAt, 10);

  return (
    <div
      style={{
        position: "absolute",
        right: 170 * sc,
        bottom: 220 * sc,
        width: 1150 * sc,
        background: EIERSCHALE,
        borderRadius: 32 * sc,
        padding: `${52 * sc}px ${60 * sc}px`,
        display: "flex",
        flexDirection: "column",
        gap: 40 * sc,
        opacity: karte * out,
        transform: `translateX(${(1 - karte) * 80 * sc}px)`,
        boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
      }}
    >
      {p.items.map((item, i) => {
        const t = popIn(frame, fps, Math.round(item.atSec * fps));
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 30 * sc,
              opacity: Math.min(1, t),
              transform: `translateX(${(1 - Math.min(1, t)) * 40 * sc}px)`,
            }}
          >
            <div
              style={{
                width: 34 * sc,
                height: 34 * sc,
                borderRadius: "50%",
                background: ROT,
                flexShrink: 0,
                transform: `scale(${t})`,
              }}
            />
            <div
              style={{
                fontFamily: FONT,
                fontSize: 54 * sc,
                fontWeight: 500,
                color: GRAU,
                lineHeight: 1.25,
              }}
            >
              {item.text}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// --- 6) Sub „…läuft MIT UNS fehlerfrei…" unten mittig ---

type SubTexte = { textVor: string; highlight: string; textNach: string };

const SubMitUnsVisual: Vis<SubTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const out = outFade(frame, outAt, 8);

  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          bottom: 180 * sc,
          maxWidth: 3200 * sc,
          background: EIERSCHALE,
          borderRadius: 24 * sc,
          padding: `${28 * sc}px ${70 * sc}px`,
          fontSize: 62 * sc,
          fontWeight: 500,
          color: GRAU,
          textAlign: "center",
          lineHeight: 1.4,
          opacity: drive * out,
          transform: `translateY(${(1 - drive) * 50 * sc}px)`,
          boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
        }}
      >
        {p.textVor} <span style={{ color: ROT, fontWeight: 700 }}>{p.highlight}</span> {p.textNach}
      </div>
    </AbsoluteFill>
  );
};

// --- 8+9) Bauchbinde (Lower Third) ---

type BindeTexte = { name: string; rolle: string };

const BauchbindeVisual: Vis<BindeTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const outAt = useOutAt(p.outAtSec);
  const drive = easeIn(frame, fps, 0);
  const balken = easeIn(frame, fps, 5);
  const out = outFade(frame, outAt, 10);

  return (
    <div
      style={{
        position: "absolute",
        left: 200 * sc,
        bottom: 220 * sc,
        display: "flex",
        alignItems: "stretch",
        gap: 30 * sc,
        opacity: drive * out,
        transform: `translateX(${(drive - 1) * 90 * sc}px)`,
      }}
    >
      <div
        style={{
          width: 14 * sc,
          borderRadius: 999,
          background: ROT,
          transform: `scaleY(${balken})`,
          transformOrigin: "bottom",
        }}
      />
      <div
        style={{
          background: EIERSCHALE,
          borderRadius: 28 * sc,
          padding: `${30 * sc}px ${64 * sc}px`,
          boxShadow: `0 ${8 * sc}px ${40 * sc}px rgba(0,0,0,0.18)`,
        }}
      >
        <div style={{ fontSize: 74 * sc, fontWeight: 700, color: ROT, lineHeight: 1.15 }}>{p.name}</div>
        <div
          style={{
            fontSize: 50 * sc,
            fontWeight: 500,
            color: GRAU,
            letterSpacing: 2 * sc,
            marginTop: 8 * sc,
          }}
        >
          {p.rolle}
        </div>
      </div>
    </div>
  );
};

// --- 10) Endcard: Logo + beide Säulen + Website (kein Job-CTA, kein Out) ---

type EndcardTexte = {
  saeule1Nr: string;
  saeule1Titel: string;
  saeule2Nr: string;
  saeule2Titel: string;
  website: string;
};

const EndcardVisual: React.FC<EndcardTexte> = (p) => {
  const { frame, fps, sc } = useStage();
  const bg = easeIn(frame, fps, 0);
  const logo = easeIn(frame, fps, 5);
  const s1 = easeIn(frame, fps, 16);
  const punkt = popIn(frame, fps, 20);
  const s2 = easeIn(frame, fps, 22);
  const web = popIn(frame, fps, 32);

  const saeule = (nr: string, titel: string, drive: number, dir: 1 | -1) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 28 * sc,
        opacity: drive,
        transform: `translateX(${(1 - drive) * 50 * sc * dir}px)`,
        fontFamily: FONT_HEAD,
      }}
    >
      <span style={{ fontSize: 84 * sc, fontWeight: 400, color: ROT }}>{nr}</span>
      <span
        style={{
          fontSize: 60 * sc,
          fontWeight: 400,
          color: GRAU,
          textTransform: "uppercase",
          letterSpacing: 7 * sc,
        }}
      >
        {titel}
      </span>
    </div>
  );

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: EIERSCHALE, opacity: bg }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <Img
          src={staticFile(LOGO_ROT)}
          style={{ width: 860 * sc, opacity: logo, transform: `scale(${0.92 + 0.08 * logo})` }}
        />
        <div style={{ marginTop: 160 * sc, display: "flex", alignItems: "center", gap: 90 * sc }}>
          {saeule(p.saeule1Nr, p.saeule1Titel, s1, -1)}
          <div
            style={{
              width: 40 * sc,
              height: 40 * sc,
              borderRadius: "50%",
              background: ROT,
              transform: `scale(${punkt})`,
            }}
          />
          {saeule(p.saeule2Nr, p.saeule2Titel, s2, 1)}
        </div>
        <div
          style={{
            marginTop: 150 * sc,
            background: ROT,
            color: EIERSCHALE,
            borderRadius: 999,
            padding: `${34 * sc}px ${110 * sc}px`,
            fontSize: 72 * sc,
            fontWeight: 700,
            letterSpacing: 3 * sc,
            opacity: Math.min(1, web),
            transform: `scale(${0.85 + 0.15 * web})`,
          }}
        >
          {p.website}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ============================================================
// Einzel-Kompositionen (registriert; Texte als Props)
// ============================================================

export const saeulenGrafikSchema = projectPropsSchema.extend({
  klartextzeile: z.string().describe("Klartextzeile unter den Säulen"),
  saeule1Nr: z.string().describe("Nummer Säule 1"),
  saeule1Titel: z.string().describe("Titel Säule 1"),
  saeule2Nr: z.string().describe("Nummer Säule 2"),
  saeule2Titel: z.string().describe("Titel Säule 2"),
  mitOutro: z.boolean().describe("Am Ende ausblenden"),
});
export type SaeulenGrafikProps = z.infer<typeof saeulenGrafikSchema>;
export const saeulenGrafikDefaults: SaeulenGrafikProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 6,
  transparent: true,
  review: REVIEW_DEFAULTS,
  klartextzeile: "Dein Partner für Lohnabrechnung & HR-Digitalisierung",
  saeule1Nr: "01",
  saeule1Titel: "Dein externes Lohnbüro",
  saeule2Nr: "02",
  saeule2Titel: "HR-Software & Prozesse",
  mitOutro: true,
};
export const HblSaeulenGrafik: React.FC<SaeulenGrafikProps> = (p) =>
  Standalone(p, <SaeulenVisual {...p} />);

export const saeulenFokusSchema = saeulenGrafikSchema.extend({
  fokus: z.enum(["1", "2"]).describe("Welche Säule in den Fokus gleitet"),
  switchAtSec: z.number().step(0.1).describe("Zeitpunkt des Switch (Sek)"),
});
export type SaeulenFokusProps = z.infer<typeof saeulenFokusSchema>;
const saeulenFokusBase = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 6.5,
  transparent: true,
  review: REVIEW_DEFAULTS,
  klartextzeile: "Dein Partner für Lohnabrechnung & HR-Digitalisierung",
  saeule1Nr: "01",
  saeule1Titel: "Dein externes Lohnbüro",
  saeule2Nr: "02",
  saeule2Titel: "HR-Software & Prozesse",
  mitOutro: true,
  switchAtSec: 3,
};
export const saeulenFokus01Defaults: SaeulenFokusProps = { ...saeulenFokusBase, fokus: "1" };
export const saeulenFokus02Defaults: SaeulenFokusProps = { ...saeulenFokusBase, fokus: "2" };
export const HblSaeulenFokus: React.FC<SaeulenFokusProps> = (p) =>
  Standalone(p, <SaeulenFokusVisual {...p} />);

export const openerSchema = saeulenGrafikSchema.extend({
  headline: z.string().describe("Allgemeine Headline (Website-Wording)"),
  fokus: z.enum(["1", "2"]).describe("Säule im Schluss-Fokus"),
  saeulenAtSec: z.number().step(0.1).describe("Säulen erscheinen bei (Sek)"),
  fokusAtSec: z.number().step(0.1).describe("Fokus startet bei (Sek)"),
});
export type OpenerProps = z.infer<typeof openerSchema>;
export const openerDefaults: OpenerProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 9.5,
  transparent: true,
  review: REVIEW_DEFAULTS,
  headline: "Deine HR-Agentur",
  klartextzeile: "Dein Partner für Lohnabrechnung & HR-Digitalisierung",
  saeule1Nr: "01",
  saeule1Titel: "Dein externes Lohnbüro",
  saeule2Nr: "02",
  saeule2Titel: "HR-Software & Prozesse",
  mitOutro: true,
  fokus: "1",
  saeulenAtSec: 3.6,
  fokusAtSec: 6.4,
};
export const HblOpener: React.FC<OpenerProps> = (p) => Standalone(p, <OpenerVisual {...p} />);

export const titelBadgeSchema = projectPropsSchema.extend({
  nr: z.string().describe("Säulen-Nummer"),
  titel: z.string().describe("Säulen-Titel"),
  subline: z.string().optional().describe("Erklär-Zeile (optional)"),
});
export type TitelBadgeProps = z.infer<typeof titelBadgeSchema>;
const titelBadgeBase = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 3,
  transparent: true,
  review: REVIEW_DEFAULTS,
};
export const titel01Defaults: TitelBadgeProps = {
  ...titelBadgeBase,
  nr: "01",
  titel: "Dein externes Lohnbüro",
};
export const titel02Defaults: TitelBadgeProps = {
  ...titelBadgeBase,
  durationInSeconds: 3.6,
  nr: "02",
  titel: "HR-Software & Prozesse",
  subline: "Die passende Software finden, einführen & Prozesse digitalisieren",
};
export const HblTitelBadge: React.FC<TitelBadgeProps> = (p) =>
  Standalone(p, <TitelBadgeVisual {...p} />);

export const screenFensterSchema = projectPropsSchema.extend({
  chips: z.array(z.string()).describe("Themen-Chips (alle O-Ton-belegt)"),
  fensterRatio: z.number().step(0.01).optional().describe("Seitenverhältnis der Aufnahme (Breite/Höhe)"),
});
export type ScreenFensterProps = z.infer<typeof screenFensterSchema>;
export const screenFensterDefaults: ScreenFensterProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 14,
  transparent: true,
  review: REVIEW_DEFAULTS,
  chips: [
    "Bewerbermanagement",
    "Onboarding",
    "Zeiterfassung",
    "Urlaub & Abwesenheiten",
    "Digitale Personalakte",
    "Lohn-Schnittstelle",
  ],
  fensterRatio: 1.96,
};
export const HblScreenFenster: React.FC<ScreenFensterProps> = (p) =>
  Standalone(p, <ScreenFrameVisual {...p} />);

export const zahl40Schema = projectPropsSchema.extend({
  prefix: z.string().describe("Zeile über der Zahl"),
  zahl: z.number().describe("Zielwert (Prozent)"),
  suffix: z.string().describe("Zeile unter der Zahl"),
});
export type Zahl40Props = z.infer<typeof zahl40Schema>;
export const zahl40Defaults: Zahl40Props = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 7,
  transparent: true,
  review: REVIEW_DEFAULTS,
  prefix: "bis zu",
  zahl: 40,
  suffix: "Zeit & Kosten",
};
export const HblZahl40: React.FC<Zahl40Props> = (p) => Standalone(p, <Zahl40Visual {...p} />);

export const ergebnisseM1Schema = projectPropsSchema.extend({
  punkte: z
    .array(z.object({
      text: z.string().describe("Ergebnis-Punkt"),
      atSec: z.number().step(0.1).describe("Erscheint bei (Sek ab Clip-Start)"),
    }))
    .describe("Punkte vor der Zahl (wortsynchron)"),
  zahlAtSec: z.number().step(0.1).describe("Countdown startet bei (Sek)"),
  prefix: z.string().describe("Zeile über der Zahl"),
  zahl: z.number().describe("Zielwert (Prozent)"),
  suffix: z.string().describe("Zeile unter der Zahl"),
});
export type ErgebnisseM1Props = z.infer<typeof ergebnisseM1Schema>;
// Timings = Cut02-SRT, Clip liegt ab TC 01:01:44,8 (M1-Satz)
export const ergebnisseM1Defaults: ErgebnisseM1Props = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 7,
  transparent: true,
  review: REVIEW_DEFAULTS,
  punkte: [
    { text: "Weniger Fehler", atSec: 1.1 },
    { text: "Schnellere Durchlaufzeiten", atSec: 2.3 },
  ],
  zahlAtSec: 4.1,
  prefix: "bis zu",
  zahl: 40,
  suffix: "Zeit & Kosten",
};
export const HblErgebnisseM1: React.FC<ErgebnisseM1Props> = (p) =>
  Standalone(p, <ErgebnisseM1Visual {...p} />);

export const captionSchema = projectPropsSchema.extend({
  text: z.string().describe("Caption-Text"),
  variante: z.enum(["karte", "pill"]).describe("karte = Eierschale/rot, pill = rot/Eierschale"),
});
export type CaptionProps = z.infer<typeof captionSchema>;
export const captionOhneHblDefaults: CaptionProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 6,
  transparent: true,
  review: REVIEW_DEFAULTS,
  text: "Ohne HBL:",
  variante: "pill",
};
export const HblCaption: React.FC<CaptionProps> = (p) => Standalone(p, <CaptionVisual {...p} />);

export const praxisfallTransitionSchema = projectPropsSchema.extend({
  text: z.string().describe("Titel der Transition"),
});
export type PraxisfallTransitionProps = z.infer<typeof praxisfallTransitionSchema>;
export const praxisfallTransitionDefaults: PraxisfallTransitionProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 3.4,
  transparent: true,
  review: REVIEW_DEFAULTS,
  text: "Ein Fall aus der Praxis",
};
export const HblPraxisfallTransition: React.FC<PraxisfallTransitionProps> = (p) =>
  Standalone(p, <PraxisfallTransitionVisual {...p} />);

export const splitBlendeSchema = projectPropsSchema.extend({});
export type SplitBlendeProps = z.infer<typeof splitBlendeSchema>;
export const splitBlendeDefaults: SplitBlendeProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 1.8,
  transparent: true,
  review: REVIEW_DEFAULTS,
};
export const HblSplitBlende: React.FC<SplitBlendeProps> = (p) =>
  Standalone(p, <SplitBlendeVisual />);

export const checklisteSchema = projectPropsSchema.extend({
  items: z
    .array(z.object({
      text: z.string().describe("Listenpunkt"),
      atSec: z.number().step(0.1).describe("Erscheint bei (Sek ab Clip-Start)"),
    }))
    .describe("Checkpunkte, wortsynchron zum O-Ton"),
});
export type ChecklisteProps = z.infer<typeof checklisteSchema>;
// S3-Part ab „Umsetzung und laufende Betreuung" (Kundenmarke!) —
// Timings = Cut02-SRT, Clip liegt ab TC 01:00:47,0
export const checklisteS3Defaults: ChecklisteProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 14.4,
  transparent: true,
  review: REVIEW_DEFAULTS,
  items: [
    { text: "Umsetzung & laufende Betreuung", atSec: 0.4 },
    { text: "Mit Lohnabrechnung nichts mehr zu tun", atSec: 3.7 },
    { text: "Fehlerfreie, pünktliche Auszahlung", atSec: 7.0 },
    { text: "Ohne Nachläufe & Korrekturschleifen", atSec: 9.2 },
    { text: "Zeit für dein Kerngeschäft", atSec: 11.7 },
  ],
};
export const HblCheckliste: React.FC<ChecklisteProps> = (p) =>
  Standalone(p, <ChecklisteVisual {...p} />);

export const subMitUnsSchema = projectPropsSchema.extend({
  textVor: z.string().describe("Text vor der Hervorhebung"),
  highlight: z.string().describe("Hervorgehobene Wörter"),
  textNach: z.string().describe("Text nach der Hervorhebung"),
});
export type SubMitUnsProps = z.infer<typeof subMitUnsSchema>;
export const subMitUnsDefaults: SubMitUnsProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 3.5,
  transparent: true,
  review: REVIEW_DEFAULTS,
  textVor: "Das Ergebnis: Deine Abrechnung läuft",
  highlight: "mit uns",
  textNach: "fehlerfrei und pünktlich.",
};
export const HblSubMitUns: React.FC<SubMitUnsProps> = (p) =>
  Standalone(p, <SubMitUnsVisual {...p} />);

export const bauchbindeSchema = projectPropsSchema.extend({
  name: z.string().describe("Name"),
  rolle: z.string().describe("Rolle/Firma"),
});
export type BauchbindeProps = z.infer<typeof bauchbindeSchema>;
const bauchbindeBase = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 5,
  transparent: true,
  review: REVIEW_DEFAULTS,
};
// Nachname via LinkedIn/RocketReach verifiziert (Head of Recruitment &
// Training, HiSERV GmbH, Schönefeld) — bei Freigabe final bestätigen lassen.
export const bauchbindeAndreDefaults: BauchbindeProps = {
  ...bauchbindeBase,
  name: "André Schwalm",
  rolle: "HR & Digitalisierung · HiSERV",
};
export const bauchbindeBreitenfeldDefaults: BauchbindeProps = {
  ...bauchbindeBase,
  name: "Philipp Eric Breitenfeld",
  rolle: "Gründer & CEO · Humanus Gruppe",
};
// HBL-Team lt. Website /wir (alle „Geschäftsführende Gesellschafterin"):
// Melanie Lang · Susan Hanselmann · Anne Christine Berner.
// Zuordnung Gesicht ↔ Name macht David; Varianten via --props rendern.
export const bauchbindeHblTeamDefaults: BauchbindeProps = {
  ...bauchbindeBase,
  name: "Melanie Lang",
  rolle: "Geschäftsführende Gesellschafterin · HBL Management",
};
export const HblBauchbinde: React.FC<BauchbindeProps> = (p) =>
  Standalone(p, <BauchbindeVisual {...p} />);

export const endcardSchema = projectPropsSchema.extend({
  saeule1Nr: z.string().describe("Nummer Säule 1"),
  saeule1Titel: z.string().describe("Titel Säule 1"),
  saeule2Nr: z.string().describe("Nummer Säule 2"),
  saeule2Titel: z.string().describe("Titel Säule 2"),
  website: z.string().describe("Website"),
});
export type EndcardProps = z.infer<typeof endcardSchema>;
export const endcardDefaults: EndcardProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 8,
  transparent: true,
  review: REVIEW_DEFAULTS,
  saeule1Nr: "01",
  saeule1Titel: "Dein externes Lohnbüro",
  saeule2Nr: "02",
  saeule2Titel: "HR-Software & Prozesse",
  website: "www.hbl-management.com",
};
export const HblEndcard: React.FC<EndcardProps> = (p) => Standalone(p, <EndcardVisual {...p} />);

// ============================================================
// MASTER: komplettes Overlay in einer Datei (Timings = Cut02)
// Video-Zeit 0:00 = DaVinci 01:00:00 · Gesamt 170 s (2:50)
// ============================================================

const timing = <T extends z.ZodRawShape>(extra: T) =>
  z.object({
    startSec: z.number().step(0.1).describe("Start (Sek, ab 01:00:00)"),
    durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
    ...extra,
  });

export const imagefilmMasterSchema = projectPropsSchema.extend({
  saeulen: timing({
    klartextzeile: z.string(),
    saeule1Nr: z.string(),
    saeule1Titel: z.string(),
    saeule2Nr: z.string(),
    saeule2Titel: z.string(),
  }).describe("Säulen-Grafik (Lücke nach Hook)"),
  titel01: timing({ nr: z.string(), titel: z.string() }).describe("Titel 01 (über S1)"),
  subMitUns: timing({
    textVor: z.string(),
    highlight: z.string(),
    textNach: z.string(),
  }).describe("mit-uns-Sub (S1-Ende)"),
  praxisfall: timing({ text: z.string() }).describe("Praxisfall-Transition (Lücke S1→A1, öffnet in den Take)"),
  titel02: timing({ nr: z.string(), titel: z.string(), subline: z.string() }).describe("Titel 02 (Lücke S3→M2)"),
  screenFenster: timing({ chips: z.array(z.string()) }).describe("Screen-Fenster + Chips (über M2; Aufnahme in Spur darunter)"),
  bindeAndre: timing({ name: z.string(), rolle: z.string() }).describe("Bauchbinde André (TA14)"),
  bindeBreitenfeld: timing({ name: z.string(), rolle: z.string() }).describe("Bauchbinde Breitenfeld (TP5)"),
  zahl40: timing({ prefix: z.string(), zahl: z.number(), suffix: z.string() }).describe("−40 % (M1-Satz)"),
  endcard: timing({
    saeule1Nr: z.string(),
    saeule1Titel: z.string(),
    saeule2Nr: z.string(),
    saeule2Titel: z.string(),
    website: z.string(),
  }).describe("Endcard (nach A5, ohne Out)"),
});
export type ImagefilmMasterProps = z.infer<typeof imagefilmMasterSchema>;

export const imagefilmMasterDefaults: ImagefilmMasterProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 170,
  transparent: true,
  review: REVIEW_DEFAULTS,
  // Timings aus Material/Cut02-HBL trans.srt (Wort-Ebene):
  saeulen: {
    startSec: 3.9, // Hook-Out 0:04,0 · S1 startet 0:06,6 — Karte überlappt S1-Anfang bewusst
    durationSec: 4.5,
    klartextzeile: "Dein Partner für Lohnabrechnung & HR-Digitalisierung",
    saeule1Nr: "01",
    saeule1Titel: "Dein externes Lohnbüro",
    saeule2Nr: "02",
    saeule2Titel: "HR-Software & Prozesse",
  },
  titel01: { startSec: 8.6, durationSec: 3, nr: "01", titel: "Dein externes Lohnbüro" },
  subMitUns: {
    startSec: 17.5, // S1-Ergebnis-Satz 17,7–21,1
    durationSec: 3.7,
    textVor: "Das Ergebnis: Deine Abrechnung läuft",
    highlight: "mit uns",
    textNach: "fehlerfrei und pünktlich.",
  },
  praxisfall: {
    startSec: 21.3, // Lücke S1→A1 (21,1–24,2); Kreis öffnet ab 23,9, A1-Wort 1 bei 24,2
    durationSec: 3.4,
    text: "Ein Fall aus der Praxis",
  },
  titel02: {
    startSec: 61.3, // Lücke 61,2–64,4
    durationSec: 3.6,
    nr: "02",
    titel: "HR-Software & Prozesse",
    subline: "Die passende Software finden, einführen & Prozesse digitalisieren",
  },
  screenFenster: {
    startSec: 67.5, // M2 64,4–82,8: erst 3 s Sprecherin, dann Fenster bis kurz vor TA14
    durationSec: 14,
    chips: [
      "Bewerbermanagement",
      "Onboarding",
      "Zeiterfassung",
      "Urlaub & Abwesenheiten",
      "Digitale Personalakte",
      "Lohn-Schnittstelle",
    ],
  },
  bindeAndre: {
    startSec: 84, // TA14 83,7–88,9 (Erstnennung André)
    durationSec: 5,
    name: "André Schwalm",
    rolle: "HR & Digitalisierung · HiSERV",
  },
  bindeBreitenfeld: {
    startSec: 89.8, // TP5 89,6–103,9 (Erstnennung Breitenfeld)
    durationSec: 5,
    name: "Philipp Eric Breitenfeld",
    rolle: "Gründer & CEO · Humanus Gruppe",
  },
  zahl40: { startSec: 104.8, durationSec: 7, prefix: "bis zu", zahl: 40, suffix: "Zeit & Kosten" }, // M1 105,0–111,6
  endcard: {
    startSec: 162, // A5 endet 161,2
    durationSec: 8,
    saeule1Nr: "01",
    saeule1Titel: "Dein externes Lohnbüro",
    saeule2Nr: "02",
    saeule2Titel: "HR-Software & Prozesse",
    website: "www.hbl-management.com",
  },
};

export const HblImagefilmMaster: React.FC<ImagefilmMasterProps> = (p) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const seq = (
    name: string,
    t: { startSec: number; durationSec: number },
    node: React.ReactNode
  ) => (
    <Sequence from={s(t.startSec)} durationInFrames={s(t.durationSec)} name={name}>
      {node}
    </Sequence>
  );

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ fontFamily: FONT }}>
        {seq("Säulen-Grafik", p.saeulen, (
          <SaeulenVisual {...p.saeulen} mitOutro outAtSec={p.saeulen.durationSec} />
        ))}
        {seq("Titel 01", p.titel01, (
          <TitelBadgeVisual {...p.titel01} outAtSec={p.titel01.durationSec} />
        ))}
        {seq("Sub mit uns", p.subMitUns, (
          <SubMitUnsVisual {...p.subMitUns} outAtSec={p.subMitUns.durationSec} />
        ))}
        {seq("Praxisfall-Transition", p.praxisfall, (
          <PraxisfallTransitionVisual text={p.praxisfall.text} outAtSec={p.praxisfall.durationSec} />
        ))}
        {seq("Titel 02", p.titel02, (
          <TitelBadgeVisual {...p.titel02} outAtSec={p.titel02.durationSec} />
        ))}
        {seq("Screen-Fenster + Chips", p.screenFenster, (
          <ScreenFrameVisual chips={p.screenFenster.chips} outAtSec={p.screenFenster.durationSec} />
        ))}
        {seq("Bauchbinde André", p.bindeAndre, (
          <BauchbindeVisual {...p.bindeAndre} outAtSec={p.bindeAndre.durationSec} />
        ))}
        {seq("Bauchbinde Breitenfeld", p.bindeBreitenfeld, (
          <BauchbindeVisual {...p.bindeBreitenfeld} outAtSec={p.bindeBreitenfeld.durationSec} />
        ))}
        {seq("Zahl -40%", p.zahl40, (
          <Zahl40Visual {...p.zahl40} outAtSec={p.zahl40.durationSec} />
        ))}
        {seq("Endcard", p.endcard, <EndcardVisual {...p.endcard} />)}
        <Guides review={p.review} />
      </AbsoluteFill>
    </CIProvider>
  );
};
