// ============================================================
// MEK Imagefilm — Zertifikats-Grafiken (Alpha-Overlay für den Schnitt)
// 3840×2160 @ 25 fps, je Karte 4,6 s (Aufbau ~1,9 s · Stand · Abgang 0,36 s).
// Länge = Testcut-Fenster zwischen zwei Schnitten (Einstieg auf dem Schnitt).
//
// Inhalte nur Website-belegt (Quellen: projects/Marien-Elisabeth-Kliniken/
// Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/grafik-fakten-quellen.md):
//  - Cardiac Arrest Center: offizielles Logo von elisabeth-krankenhaus-kassel.de,
//    zertifiziert vom Deutschen Rat für Wiederbelebung (PM 17.09.2025).
//  - Weaningzentrum: „eines von nur gut 50 von der Deutschen Gesellschaft für
//    Pneumologie zertifizierten Weaningzentren" (marienkrankenhaus-kassel.de).
//    Kein offizielles Siegel verfügbar → eigenes Lungen-Emblem (kein Siegel-Nachbau).
// Keine Personennamen. CI: Verbund-Navy + Bildmarken-Rampe, Roboto (Website-Font).
// Temperatur-Differenzierung: Elisabeth kühl, Marien warm (Animations-Ebene 01.09.).
// Bausteine: ../../components/grafik-basis.tsx (auch für die Komplett-Ebene).
// ============================================================

import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import {
  Akzentlinie,
  BASE_H,
  BASE_W,
  GlasKarte,
  Kicker,
  NAVY_MARIEN,
  RAMPE_TIEF,
  ROBOTO,
  Textzeile,
  WortKaskade,
  hexA,
  kartenFarben,
  rein,
  setzen,
} from "../../components/grafik-basis";

export const ci = loadBrand("mek", brandJson as any);

const KARTE_B = 680;

export const zertifikatSchema = projectPropsSchema.extend({
  variante: z.enum(["cac", "weaning"]).describe("Kachel: offizielles CAC-Logo oder eigenes Lungen-Emblem mit Wortmarke"),
  haus: z.string().describe("Hauszeile (Kicker)"),
  kachelZeilen: z.array(z.string()).max(2).describe("Nur Weaning: Wortmarke in der Kachel (klein, groß)"),
  hauptzeile: z.string().describe("Große Zeile unter der Kachel"),
  belege: z.array(z.string()).max(2).describe("Erklärung + Zertifizierer (Website-belegt)"),
  temperatur: z.enum(["kuehl", "warm"]).describe("Elisabeth kühl, Marien warm"),
  position: z.enum(["unten-rechts", "unten-links"]),
  versatzX: z.number().min(-600).max(600).describe("Feinjustage X im 1920er-Raster"),
  versatzY: z.number().min(-600).max(600).describe("Feinjustage Y im 1920er-Raster"),
  studioDunkel: z.boolean().describe("Nur Studio: dunkler Grund statt Transparenz"),
});

export type ZertifikatProps = z.infer<typeof zertifikatSchema>;

export const REVIEW_AUS = { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 };

export const zertifikatCacDefaults: ZertifikatProps = {
  format: "landscape-4k",
  fps: 25,
  durationInSeconds: 4.6,
  transparent: true,
  variante: "cac",
  haus: "Elisabeth-Krankenhaus Kassel",
  kachelZeilen: [],
  hauptzeile: "Zertifiziert seit 2025",
  belege: ["Versorgung bei Herz-Kreislauf-Stillstand", "Deutscher Rat für Wiederbelebung"],
  temperatur: "kuehl",
  position: "unten-rechts",
  versatzX: 0,
  versatzY: 0,
  studioDunkel: false,
  review: REVIEW_AUS,
};

export const zertifikatWeaningDefaults: ZertifikatProps = {
  ...zertifikatCacDefaults,
  variante: "weaning",
  haus: "Marienkrankenhaus Kassel",
  kachelZeilen: ["Zertifiziertes", "Weaningzentrum"],
  hauptzeile: "Eines von nur gut 50",
  belege: ["Entwöhnung von der Beatmung", "Deutsche Gesellschaft für Pneumologie"],
  temperatur: "warm",
};

// ------------------------------------------------------------
// Embleme
// ------------------------------------------------------------

const CacLogo: React.FC = () => (
  <Img
    src={staticFile("clients/mek/zertifikate/cac-logo.png")}
    style={{ width: 292, height: "auto", display: "block" }}
  />
);

/** Eigenes Emblem (kein Siegel): Luftröhre + Lungenflügel als Linienzeichnung. */
const LungenEmblem: React.FC<{ farbe: string; akzent: string; groesse?: number }> = ({ farbe, akzent, groesse = 96 }) => (
  <svg width={groesse} height={groesse} viewBox="0 0 100 100" style={{ display: "block" }}>
    <defs>
      <linearGradient id="mek-lunge-fuellung" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor={akzent} stopOpacity={0.22} />
        <stop offset="1" stopColor={akzent} stopOpacity={0.5} />
      </linearGradient>
    </defs>
    <path
      d="M41 30 C 31 30 19 44 17 61 C 15 77 19 89 29 89 C 37 89 43 83 43 73 L 43 37 C 43 33 42.5 30 41 30 Z"
      fill="url(#mek-lunge-fuellung)"
      stroke={farbe}
      strokeWidth={4.2}
      strokeLinejoin="round"
    />
    <path
      d="M59 30 C 69 30 81 44 83 61 C 85 77 81 89 71 89 C 63 89 57 83 57 73 L 57 37 C 57 33 57.5 30 59 30 Z"
      fill="url(#mek-lunge-fuellung)"
      stroke={farbe}
      strokeWidth={4.2}
      strokeLinejoin="round"
    />
    <path d="M50 9 L 50 40" stroke={farbe} strokeWidth={4.6} strokeLinecap="round" fill="none" />
    <path
      d="M50 40 C 50 46 46 49 43 52 M50 40 C 50 46 54 49 57 52"
      stroke={farbe}
      strokeWidth={4.2}
      strokeLinecap="round"
      fill="none"
    />
  </svg>
);

// ------------------------------------------------------------
// Karte (auch in der Komplett-Ebene genutzt: dauerFrames = Sequenzlänge)
// ------------------------------------------------------------

export const ZertifikatKarte: React.FC<ZertifikatProps & { dauerFrames?: number }> = (p) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const dauer = p.dauerFrames ?? durationInFrames;
  const { linie } = kartenFarben(p.temperatur);
  const kachel = rein(frame, 13, 10);

  return (
    <GlasKarte
      dauer={dauer}
      temperatur={p.temperatur}
      position={p.position}
      versatzX={p.versatzX}
      versatzY={p.versatzY}
      breite={KARTE_B}
    >
      <Kicker text={p.haus} />
      <Akzentlinie linie={linie} />

      {/* Kachel: offizielles Logo (CAC) bzw. eigenes Emblem + Wortmarke (Weaning) */}
      <div
        style={{
          marginTop: 26,
          height: 140,
          display: "inline-flex",
          alignItems: "center",
          background: "#FFFFFF",
          borderRadius: 16,
          padding: p.variante === "cac" ? "0 24px" : "0 30px 0 20px",
          boxShadow: `0 10px 30px ${hexA("#000A1E", 0.22)}`,
          opacity: kachel,
          transform: `scale(${setzen(frame, 13)})`,
          transformOrigin: "0 50%",
        }}
      >
        {p.variante === "cac" ? (
          <CacLogo />
        ) : (
          <>
            <LungenEmblem farbe={NAVY_MARIEN} akzent={RAMPE_TIEF} groesse={104} />
            <div style={{ marginLeft: 16, color: NAVY_MARIEN, fontFamily: ROBOTO }}>
              {p.kachelZeilen[0] && (
                <div style={{ fontWeight: 300, fontSize: 25, lineHeight: 1.1, letterSpacing: 0.2 }}>{p.kachelZeilen[0]}</div>
              )}
              {p.kachelZeilen[1] && (
                <div style={{ fontWeight: 700, fontSize: 38, lineHeight: 1.05, letterSpacing: -0.4 }}>{p.kachelZeilen[1]}</div>
              )}
            </div>
          </>
        )}
      </div>

      <WortKaskade zeilen={[p.hauptzeile]} start={21} />

      {p.belege.map((zeile, i) => (
        <Textzeile
          key={i}
          text={zeile}
          start={31 + i * 4}
          groesse={i === 0 ? 29 : 24}
          deckkraft={i === 0 ? 0.94 : 0.8}
          sperrung={i === 0 ? 0.3 : 0.25}
          marginTop={i === 0 ? 12 : 6}
        />
      ))}
    </GlasKarte>
  );
};

// ------------------------------------------------------------
// Komposition
// ------------------------------------------------------------

export const MekZertifikat: React.FC<ZertifikatProps> = (props) => {
  const { width } = useVideoConfig();
  const scale = width / BASE_W;
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: props.studioDunkel ? "#1b2230" : "transparent" }}>
        <div
          style={{
            position: "absolute",
            width: BASE_W,
            height: BASE_H,
            transform: `scale(${scale})`,
            transformOrigin: "0 0",
          }}
        >
          <ZertifikatKarte {...props} />
        </div>
        {props.review?.showGuides && (
          <ReviewOverlay
            showSafeZone={props.review.showSafeZone}
            showFaceZone={props.review.showFaceZone}
            showGrid={props.review.showGrid}
            faceZone={props.review.faceZone}
            guideOpacity={props.review.guideOpacity}
            format="landscape"
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
