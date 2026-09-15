// ============================================================
// Taxodia-Erklärvideo „Der Taxodia-Weg" — komplette Grafikebene als EINE Alpha-Spur
// v1 15.09.2026 (Titel, Bauchbinden, Faktenkarten, Endcard) · v2 15.09.2026 (User: „keine Blackframes,
// deutlich mehr Grafiken, auch Vollbild, z. B. Karte bei Ilshofen" — Vorbild HBL-Imagefilm):
// Flashes im Kaltstart, Kapitel-Blenden in den Pausen, zwei Karten, Taxodia-Weg, Endcard deckend ab Schnittende.
// Passt ab 0:00 auf die Feinschnitt-Timeline (gleiche O-Ton-Positionen wie „AutoCut video-1-taxodia-weg
// 2026-09-15 0941 (roh)", 6645 Frames Schnitt + Endcard = 6845 Frames, 25 fps, 3840×2160).
// Alle Zeiten = Timeline-Frames (Quelle: _intern/autocut/timeline.json + Wortzeiten aus dem Scribe-Cache).
//
// Inhalte nur Website-belegt (taxodia.de / lbl-bw.de, gesichert in _intern/website/):
//  Software (DATEV, HANNIBAL, LAND-DATA, nlb) · Bachelor Professional = Qualifikationsniveau Hochschul-Bachelor ·
//  Einstiegskurs 4 Wochen / 32 UStd / 8 UStd pro Woche · Teil I und II je ca. 350 UStd · Kurs startet jeden Monat ·
//  keine Hotel-/Reisekosten, Gesamtkosten mind. 50 % günstiger · Monitoring: Lernfortschritt und Noten ·
//  keine Vorkasse, keine Stornokosten · Musterkurs „Ohne Risiko. Ohne Kosten." · „Die Anmeldung funktioniert nur über
//  den Arbeitgeber." · „Die Online-Steuerfachschule für Quereinsteiger" · „Dem Fachkräftemangel begegnen" ·
//  Standorte: Taxodia GmbH Visselhövede (Impressum), Steuerkanzlei Ludwig Ilshofen, Landwirtschaftliche Buchstelle.
//  Karte Ilshofen: 50-km-Radius aus dem O-Ton (Ludwig), als Kartenmaß.
// Nicht enthalten: Ampel-Grafik (#16) — nur nach Freigabe durch Taxodia (Schnittplan).
// Seiten-System: Ludwig/Flammann-Gesicht rechts bzw. mittig → Karten unten links; Hein-Stellen unten rechts.
// ============================================================

import React from "react";
import { AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { getCalculateMetadata } from "../../../../core/format-utils";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import {
  BASE_H,
  BASE_W,
  CLAMP,
  EASE_OUT,
  HelleKarte,
  Kicker,
  Marke,
  Position,
  SCHWARZ,
  TAXODIA_BAND,
  TAXODIA_CREME,
  TAXODIA_GRUEN,
  TAXODIA_HELL,
  Textzeile,
  URBANIST,
  WortKaskade,
  hexA,
  rein,
  setzen,
  wortAnzahl,
} from "../../components/grafik-basis";
import { Blende, Flash, KarteIlshofen, KarteTaxodia, TaxodiaWeg } from "../../components/vollbild";

export const ci = loadBrand("taxodia", brandJson as any);
export const REVIEW_AUS = { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 };

// ------------------------------------------------------------
// Titel über der Ankunft (B-Roll)
// ------------------------------------------------------------

const Titel: React.FC<{ dauer: number }> = ({ dauer }) => (
  <HelleKarte dauer={dauer} marke="taxodia" padding="36px 56px 40px 60px">
    <Kicker text="Steuerkanzlei Ludwig × Taxodia" marke="taxodia" groesse={19} />
    <WortKaskade zeilen={["Der Taxodia-Weg"]} start={9} groesse={96} gewicht={800} sperrung={-2} marginTop={10} />
    <WortKaskade
      zeilen={["Vom Quereinsteiger zum Bachelor Professional"]}
      start={17}
      groesse={40}
      gewicht={700}
      sperrung={-0.4}
      marginTop={8}
      gruen={["Bachelor", "Professional"]}
      gruenFarbe={TAXODIA_BAND}
    />
  </HelleKarte>
);

// ------------------------------------------------------------
// Bauchbinde: Kicker (Organisation) · Name · Rolle
// ------------------------------------------------------------

const Bauchbinde: React.FC<{ dauer: number; marke: Marke; organisation: string; name: string; rolle: string; position?: Position }> = (p) => (
  <HelleKarte dauer={p.dauer} marke={p.marke} position={p.position} padding="24px 40px 26px 46px">
    <Kicker text={p.organisation} marke={p.marke} groesse={18} sperrung={2.4} />
    <WortKaskade zeilen={[p.name]} start={9} groesse={46} gewicht={800} sperrung={-0.8} marginTop={6} />
    <Textzeile text={p.rolle} start={14} groesse={27} marginTop={4} />
  </HelleKarte>
);

// ------------------------------------------------------------
// Fakten-Karte
// ------------------------------------------------------------

const FaktKarte: React.FC<{ dauer: number; kicker: string; titel: string[]; zeilen?: string[]; position?: Position }> = (p) => {
  const titelStart = 12;
  const zeilenStart = titelStart + wortAnzahl(p.titel) * 3 + 3;
  return (
    <HelleKarte dauer={p.dauer} marke="taxodia" position={p.position} minBreite={460}>
      <Kicker text={p.kicker} marke="taxodia" />
      <WortKaskade zeilen={p.titel} start={titelStart} marginTop={10} />
      {(p.zeilen ?? []).map((z, i) => (
        <Textzeile key={i} text={z} start={zeilenStart + i * 4} marginTop={i === 0 ? 12 : 2} />
      ))}
    </HelleKarte>
  );
};

// ------------------------------------------------------------
// Endcard: weißer Grund wie taxodia.de (Wipe, ab Frame 8 deckend), Logos, Musterkurs, Weg für Quereinsteiger
// ------------------------------------------------------------

const Endcard: React.FC<{ logoTaxodia: string; logoLudwig: string; url: string }> = (p) => {
  const frame = useCurrentFrame();
  const wipe = interpolate(frame, [0, 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const bogen = interpolate(frame, [8, 60], [0, 1], CLAMP);
  const logos = rein(frame, 16, 14);
  const pill = rein(frame, 52, 12);
  return (
    <AbsoluteFill style={{ clipPath: `inset(0 ${(1 - wipe) * 100}% 0 0)` }}>
      <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }} />
      <AbsoluteFill
        style={{
          opacity: bogen,
          background: `radial-gradient(58% 70% at 88% 104%, ${hexA(TAXODIA_HELL, 0.95)} 0%, ${hexA(TAXODIA_CREME, 0.6)} 46%, ${hexA("#FFFFFF", 0)} 74%)`,
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, top: 252, fontFamily: URBANIST, color: SCHWARZ, textAlign: "center" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 54,
            opacity: logos,
            transform: `translateY(${(1 - logos) * 14}px) scale(${setzen(frame, 16)})`,
          }}
        >
          <Img src={staticFile(p.logoTaxodia)} style={{ height: 78, width: "auto", display: "block" }} />
          <div style={{ width: 2, height: 74, background: hexA("#000000", 0.18) }} />
          <Img src={staticFile(p.logoLudwig)} style={{ height: 112, width: "auto", display: "block" }} />
        </div>
        <WortKaskade zeilen={["Taxodia Musterkurs"]} start={30} groesse={92} gewicht={800} sperrung={-2} marginTop={70} ausrichtung="center" />
        <WortKaskade zeilen={["Ohne Risiko. Ohne Kosten."]} start={40} groesse={50} gewicht={700} sperrung={-0.6} marginTop={10} farbe={TAXODIA_BAND} ausrichtung="center" />
        <div style={{ marginTop: 44, display: "flex", justifyContent: "center" }}>
          <div
            style={{
              padding: "14px 42px 16px",
              borderRadius: 60,
              background: TAXODIA_GRUEN,
              color: "#FFFFFF",
              fontWeight: 800,
              fontSize: 44,
              letterSpacing: 0.2,
              opacity: pill,
              transform: `scale(${setzen(frame, 52)})`,
            }}
          >
            {p.url}
          </div>
        </div>
        <Textzeile text="Für Quereinsteiger: Die Anmeldung funktioniert nur über den Arbeitgeber." start={62} groesse={30} marginTop={34} farbe={hexA("#000000", 0.7)} ausrichtung="center" />
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------
// Timeline (Frames der Feinschnitt-Timeline, O-Ton-Positionen der Kurzfassung 15.09.)
// ------------------------------------------------------------

export const SCHNITT_FRAMES = 6645; // letztes O-Ton-Item endet hier
export const GESAMT_FRAMES = 6845; // Endcard bis Dateiende

export const grafikSchema = projectPropsSchema.extend({
  url: z.string().describe("Endcard-URL (Website)"),
  logoTaxodia: z.string().describe("public-Pfad Taxodia-Logo"),
  logoLudwig: z.string().describe("public-Pfad Logo Steuerkanzlei Ludwig"),
  studioDunkel: z.boolean().describe("Nur Studio: dunkler Grund statt Transparenz"),
});

export type GrafikProps = z.infer<typeof grafikSchema>;

export const grafikDefaults: GrafikProps = {
  format: "landscape-4k",
  fps: 25,
  durationInSeconds: GESAMT_FRAMES / 25,
  transparent: true,
  review: REVIEW_AUS,
  url: "taxodia.de",
  logoTaxodia: "clients/taxodia/logos/taxodia-logo.svg",
  logoLudwig: "clients/taxodia/logos/ludwig-logo.svg",
  studioDunkel: false,
};

export const calculateGrafik = ({ props }: { props: GrafikProps }) => ({
  ...getCalculateMetadata(props),
  durationInFrames: GESAMT_FRAMES,
});

type Eintrag = { id: string; from: number; dauer: number; vollbild?: boolean; inhalt: (dauer: number, p: GrafikProps) => React.ReactNode };

export const TIMELINE: Eintrag[] = [
  // Kaltstart: Pause #1→#2 (60–85) und #2→#3 (233–258), weg vor dem nächsten Wort
  { id: "flash-fachkraeftemangel", from: 60, dauer: 28, vollbild: true, inhalt: (d) => <Flash dauer={d} wort="Fachkräftemangel" /> },
  { id: "flash-quereinsteiger", from: 233, dauer: 28, vollbild: true, inhalt: (d) => <Flash dauer={d} wort="Quereinsteiger" /> },
  // #4 Titel über der Ankunft (B-Roll 345–470)
  { id: "titel", from: 372, dauer: 96, inhalt: (d) => <Titel dauer={d} /> },
  // #5 Ludwig: „wir betreuen hier von Ilshofen aus …" (476–578) — Bauchbinde, dann Karte
  {
    id: "bauchbinde-ludwig",
    from: 480,
    dauer: 72,
    inhalt: (d) => <Bauchbinde dauer={d} marke="ludwig" organisation="Steuerkanzlei Ludwig · Landwirtschaftliche Buchstelle" name="Friedrich Ludwig" rolle="Steuerberater" />,
  },
  // Karte Ilshofen: „… mit circa vierzig Mitarbeitern, vor allem landwirtschaftliche Betriebe im Radius von fünfzig Kilometern" (550–660), Radius bei „Radius" (626)
  { id: "karte-ilshofen", from: 552, dauer: 141, vollbild: true, inhalt: (d) => <KarteIlshofen dauer={d} radiusStart={626 - 552} /> },
  // #7 Hein: „Ich hab vorher Landwirtschaft dual studiert …" (1023–1127), Bild ab 1014
  {
    id: "bauchbinde-hein",
    from: 1026,
    dauer: 95,
    inhalt: (d) => <Bauchbinde dauer={d} marke="ludwig" organisation="Steuerkanzlei Ludwig" name="Jan Philipp Hein" rolle="Steuersachbearbeiter" />,
  },
  // Kapitel-Blende vor Taxodia: Pause #8→#9 (1664–1689), Flammanns erste Worte ab 1695 laufen darunter (J-Cut)
  { id: "blende-taxodia", from: 1664, dauer: 48, vollbild: true, inhalt: (d) => <Blende dauer={d} kicker="Taxodia" titel="Die Online-Steuerfachschule" /> },
  {
    id: "bauchbinde-flammann",
    from: 1716,
    dauer: 114,
    inhalt: (d) => <Bauchbinde dauer={d} marke="taxodia" organisation="Taxodia" name="Jörn Flammann" rolle="Gründer und Geschäftsführer" />,
  },
  // #9 „… mit dem Schwerpunkt des landwirtschaftlichen Steuerrechts. Wir haben uns spezialisiert …" (1862–1982)
  { id: "karte-taxodia", from: 1862, dauer: 120, vollbild: true, inhalt: (d) => <KarteTaxodia dauer={d} /> },
  // #10 Hein: „… das tägliche Doing in der Steuerkanzlei …" (2511–2629)
  {
    id: "software",
    from: 2511,
    dauer: 116,
    inhalt: (d) => <FaktKarte dauer={d} position="unten-rechts" kicker="Taxodia" titel={["Gelernt wird in der", "Software der Kanzlei"]} zeilen={["DATEV · HANNIBAL · LAND-DATA · nlb"]} />,
  },
  // #11 Flammann (nach dem B-Roll-Block 2638–2812): „… Das war bisher der sogenannte Fachagrarwirt …"
  {
    id: "bachelor-professional",
    from: 2881,
    dauer: 124,
    inhalt: (d) => <FaktKarte dauer={d} kicker="Bachelor Professional" titel={["Gleiches Qualifikationsniveau", "wie ein Hochschul-Bachelor"]} />,
  },
  // #12 Taxodia-Weg über „geht über vier Wochen … man schafft ein Arbeitsverhältnis … mit der dreiunddreißigsten
  // Unterrichtsstunde … fortfahren" (3222–3536), deckt beide Innenschnitte und die Pause, Ludwigs erste Worte (3575) darunter
  {
    id: "taxodia-weg",
    from: 3222,
    dauer: 368,
    vollbild: true,
    inhalt: (d) => (
      <TaxodiaWeg
        dauer={d}
        stationen={[
          { titel: "Einstiegskurs", zeilen: ["4 Wochen · 32 UStd", "8 UStd pro Woche"], start: 10 },
          { titel: "Teil I", zeilen: ["ca. 350 UStd"], start: 3327 - 3222 },
          { titel: "Teil II", zeilen: ["ca. 350 UStd"], start: 3372 - 3222 },
          { titel: "Prüfung", zeilen: ["Bachelor Professional"], start: 3419 - 3222 },
        ]}
        fortschritt={[3427 - 3222, 3536 - 3222]}
        fussStart={3450 - 3222}
      />
    ),
  },
  // #13 Ludwig: „… nicht teurer als einen einzigen Vermittlungsauftrag hier zu geben." (3648–3831)
  {
    id: "kosten",
    from: 3652,
    dauer: 138,
    inhalt: (d) => <FaktKarte dauer={d} kicker="Kosten" titel={["Keine Hotel- und Reisekosten"]} zeilen={["Gesamtkosten mindestens 50 % günstiger", "als in vergleichbaren Präsenzkursen"]} />,
  },
  // Kapitel-Blende Online-Alltag: Pause #13→#14 (3831–3856), Heins erste Worte ab 3862 darunter
  { id: "blende-online", from: 3831, dauer: 59, vollbild: true, inhalt: (d) => <Blende dauer={d} kicker="Taxodia" titel="Online lernen" /> },
  // #17 Ludwig: „Und wenn was Schlimmes ist, dann bekomme ich ja Nachricht …" (4840–4931)
  { id: "monitoring", from: 4840, dauer: 106, inhalt: (d) => <FaktKarte dauer={d} kicker="Monitoring" titel={["Die Kanzlei sieht", "Lernfortschritt und Noten"]} /> },
  // #18 Ludwig: „jeder Kurs, jeder Abschnitt, der gemacht wird, wird bezahlt. Das ist sehr fair." (4962–5042)
  { id: "abrechnung", from: 4966, dauer: 104, inhalt: (d) => <FaktKarte dauer={d} kicker="Abrechnung pro Modul" titel={["Keine Vorkasse.", "Keine Stornokosten."]} /> },
  // Kapitel-Blende Ergebnis: Pause #19→#20 (5454–5479), Flammanns „Wir haben" ab 5485 darunter
  { id: "blende-ergebnis", from: 5454, dauer: 46, vollbild: true, inhalt: (d) => <Blende dauer={d} kicker="Die Prüfung" titel="Das Ergebnis" /> },
  // CTA-Blenden: Pause #21→#22 (6007–6032) bis zum ersten Innenschnitt (6057); Pause #22→#23 (6349–6374)
  { id: "blende-kanzleien", from: 6007, dauer: 50, vollbild: true, inhalt: (d) => <Blende dauer={d} kicker="Der nächste Schritt" titel="Für Kanzleien" /> },
  { id: "blende-quereinsteiger", from: 6349, dauer: 36, vollbild: true, inhalt: (d) => <Blende dauer={d} kicker="Der nächste Schritt" titel="Für Quereinsteiger" /> },
  // #24 Endcard: Wipe ab 6637, deckend ab 6645 (Ende von Heins CTA) bis Dateiende
  {
    id: "endcard",
    from: 6637,
    dauer: GESAMT_FRAMES - 6637,
    vollbild: true,
    inhalt: (_d, p) => <Endcard logoTaxodia={p.logoTaxodia} logoLudwig={p.logoLudwig} url={p.url} />,
  },
];

/** Deckende Frames der Grafikebene (für die Schwarzframe-Prüfung im Resolve-Bau): Vollbild-Einträge, ohne Wipe/Iris-Ränder. */
export const VOLLBILD_DECKEND = TIMELINE.filter((e) => e.vollbild).map((e) => ({ id: e.id, von: e.from, bis: e.from + e.dauer }));

export const TaxodiaGrafikebene: React.FC<GrafikProps> = (props) => {
  const { width } = useVideoConfig();
  const scale = width / BASE_W;
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: props.studioDunkel ? "#2a2f22" : "transparent" }}>
        <div style={{ position: "absolute", width: BASE_W, height: BASE_H, transform: `scale(${scale})`, transformOrigin: "0 0" }}>
          {TIMELINE.map((e) => (
            <Sequence key={e.id} name={e.id} from={e.from} durationInFrames={e.dauer} layout="none">
              {e.inhalt(e.dauer, props)}
            </Sequence>
          ))}
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
