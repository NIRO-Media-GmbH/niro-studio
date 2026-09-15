// ============================================================
// MEK Imagefilm — komplette Grafikebene als EINE Alpha-Spur
// Passt ab 0:00 auf „MEK Test1.mov" (3357 Frames, 25 fps) + 5 s Endcard-Überhang.
// Alle Zeiten = Frames im Testcut 1 (Einstieg jeweils auf einem Schnitt,
// Abgang vor dem nächsten Schnitt; Sandra-Einstieg und Marcel-Peak grafikfrei).
// Seiten-System: Elisabeth rechts, Marienkrankenhaus links, Zusammenschluss mittig —
// hält zugleich alle Karten aus den Gesichtern (Vision-Gesichtskarte des Testcuts, 14.09.).
//
// Inhalte nur Website-belegt: Tabelle „Umgesetzt" in projects/Marien-Elisabeth-
// Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/grafik-fakten-quellen.md.
// Keine Personennamen. Verbund-Marke nur auf der Endcard (Logos der Häuser).
// ============================================================

import React from "react";
import { AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { projectPropsSchema } from "../../../../core/schemas";
import { getCalculateMetadata } from "../../../../core/format-utils";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Akzentlinie,
  BASE_H,
  BASE_W,
  CLAMP,
  EASE_IN,
  GlasKarte,
  Kicker,
  NAVY_ELISABETH,
  NAVY_MARIEN,
  RAMPE_TIEF,
  RAND_UNTEN,
  RAND_X,
  ROBOTO,
  Temperatur,
  Textzeile,
  WortKaskade,
  hexA,
  kartenFarben,
  rein,
  setzen,
  wortAnzahl,
} from "../../components/grafik-basis";
import { REVIEW_AUS, ZertifikatKarte, ci, zertifikatCacDefaults, zertifikatWeaningDefaults } from "./Zertifikate";

// ------------------------------------------------------------
// Ortsmarke (Drohnen): Kicker + Hausname, Wechsel auf dem Schnitt
// ------------------------------------------------------------

type OrtSegment = { kicker: string; titel: string; temperatur: Temperatur; dauer: number; seite: "links" | "rechts" };

const OrtsmarkeText: React.FC<OrtSegment & { erstes: boolean; letztes: boolean }> = (s) => {
  const frame = useCurrentFrame();
  const { linie } = kartenFarben(s.temperatur);
  const rechts = s.seite === "rechts";
  const abDauer = s.letztes ? 9 : 6;
  const ab = interpolate(frame, [s.dauer - abDauer, s.dauer], [0, 1], { ...CLAMP, easing: EASE_IN });
  const scrimRein = interpolate(frame, [0, s.erstes ? 10 : 6], [0, 1], CLAMP);
  const v = s.erstes ? 0 : -3;
  const ecke = rechts ? "100% 100%" : "0% 100%";
  return (
    <>
      {/* textbox-großer Scrim in der Ecke (Doktrin: nie framebreit) */}
      <div
        style={{
          position: "absolute",
          [rechts ? "right" : "left"]: 0,
          bottom: 0,
          width: 1180,
          height: 470,
          opacity: scrimRein * (1 - ab),
          background: `radial-gradient(80% 100% at ${ecke}, ${hexA("#000A1E", 0.5)} 0%, ${hexA("#000A1E", 0.24)} 45%, ${hexA("#000A1E", 0)} 78%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          [rechts ? "right" : "left"]: RAND_X,
          bottom: RAND_UNTEN,
          fontFamily: ROBOTO,
          color: "#FFFFFF",
          textAlign: rechts ? "right" : "left",
          textShadow: `0 2px 22px ${hexA("#000A1E", 0.55)}`,
          opacity: 1 - ab,
          transform: `translateY(${-ab * 12}px)`,
        }}
      >
        <Kicker text={s.kicker} start={5 + v} />
        <Akzentlinie linie={linie} start={8 + v} rechts={rechts} />
        <WortKaskade
          zeilen={[s.titel]}
          start={10 + v}
          groesse={60}
          sperrung={-1.2}
          marginTop={18}
          ausrichtung={rechts ? "right" : "left"}
        />
      </div>
    </>
  );
};

/** Wechsel auf dem Schnitt: Elisabeth rechts, Marien links (Haus-Seiten wie bei den Karten). */
const Ortsmarke: React.FC<{ segmente: OrtSegment[] }> = ({ segmente }) => {
  let from = 0;
  return (
    <>
      {segmente.map((s, i) => {
        const start = from;
        from += s.dauer;
        return (
          <Sequence key={i} from={start} durationInFrames={s.dauer} layout="none">
            <OrtsmarkeText {...s} erstes={i === 0} letztes={i === segmente.length - 1} />
          </Sequence>
        );
      })}
    </>
  );
};

// ------------------------------------------------------------
// Fakten-Karte (gleiche Glas-Karte wie die Zertifikate, ohne Kachel)
// ------------------------------------------------------------

const FaktKarte: React.FC<{
  dauer: number;
  temperatur: Temperatur;
  kicker: string;
  titel: string[];
  zeilen: string[];
  position?: "unten-rechts" | "unten-links" | "unten-mitte";
}> = (p) => {
  const { linie } = kartenFarben(p.temperatur);
  const titelStart = 15;
  const zeilenStart = titelStart + wortAnzahl(p.titel) * 3 + 4;
  return (
    <GlasKarte dauer={p.dauer} temperatur={p.temperatur} minBreite={500} position={p.position}>
      <Kicker text={p.kicker} />
      <Akzentlinie linie={linie} />
      <WortKaskade zeilen={p.titel} start={titelStart} marginTop={22} />
      {p.zeilen.map((z, i) => (
        <Textzeile key={i} text={z} start={zeilenStart + i * 4} marginTop={i === 0 ? 14 : 4} />
      ))}
    </GlasKarte>
  );
};

// ------------------------------------------------------------
// Endcard: Verbund-Marke, CTA aus dem Konzept, beide Stellenseiten
// ------------------------------------------------------------

const HausSpalte: React.FC<{ logo: string; url: string; start: number }> = ({ logo, url, start }) => {
  const frame = useCurrentFrame();
  const k = rein(frame, start, 12);
  return (
    <div style={{ width: 680, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div
        style={{
          height: 160,
          display: "flex",
          alignItems: "center",
          background: "#FFFFFF",
          borderRadius: 16,
          padding: "0 36px",
          boxShadow: `0 16px 44px ${hexA("#000A1E", 0.3)}`,
          opacity: k,
          transform: `scale(${setzen(frame, start)})`,
        }}
      >
        <Img src={staticFile(logo)} style={{ width: 450, height: "auto", display: "block" }} />
      </div>
      <Textzeile text={url} start={start + 10} groesse={26} deckkraft={0.88} sperrung={0.2} marginTop={22} ausrichtung="center" />
    </div>
  );
};

const Endcard: React.FC<{ cta: string; urlElisabeth: string; urlMarien: string }> = (p) => {
  const frame = useCurrentFrame();
  const grund = interpolate(frame, [0, 30], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  // einmaliger Soft Bloom hinter der CTA
  const bloom = interpolate(frame, [26, 54, 120], [0, 1, 0.55], CLAMP);
  const { linie } = kartenFarben("beide");
  const komma = p.cta.indexOf(", ");
  const ctaZeilen = komma > 0 ? [p.cta.slice(0, komma + 1), p.cta.slice(komma + 2)] : [p.cta];

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: NAVY_ELISABETH, opacity: grund }} />
      <AbsoluteFill
        style={{
          opacity: grund * bloom,
          background: `radial-gradient(52% 58% at 50% 40%, ${hexA(RAMPE_TIEF, 0.3)} 0%, ${hexA(NAVY_MARIEN, 0)} 72%)`,
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, top: 244, fontFamily: ROBOTO, color: "#FFFFFF", textAlign: "center" }}>
        <Kicker text="Marien-Elisabeth-Kliniken Kassel" start={16} groesse={22} sperrung={5.5} />
        <Akzentlinie linie={linie} start={20} breite={96} zentriert />
        <WortKaskade zeilen={ctaZeilen} start={26} groesse={84} zeilenhoehe={1.08} sperrung={-1.6} marginTop={34} ausrichtung="center" />
        <div style={{ marginTop: 74, display: "flex", justifyContent: "center", gap: 60 }}>
          <HausSpalte logo="clients/mek/logos/mek_elisabeth_logo.svg" url={p.urlElisabeth} start={50} />
          <HausSpalte logo="clients/mek/logos/mek_marien_logo.svg" url={p.urlMarien} start={55} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------
// Timeline (Frames im Testcut 1)
// ------------------------------------------------------------

export const TESTCUT_FRAMES = 3357; // MEK Test1.mov
export const GESAMT_FRAMES = 3482; // + 5 s Endcard-Überhang

export const grafikKomplettSchema = projectPropsSchema.extend({
  cta: z.string().describe("Endcard-CTA (Konzept)"),
  urlElisabeth: z.string().describe("Endcard: Stellenseite Elisabeth (Linkziel mit Kunde klären)"),
  urlMarien: z.string().describe("Endcard: Stellenseite Marien (Linkziel mit Kunde klären)"),
  studioDunkel: z.boolean().describe("Nur Studio: dunkler Grund statt Transparenz"),
});

export type GrafikKomplettProps = z.infer<typeof grafikKomplettSchema>;

export const grafikKomplettDefaults: GrafikKomplettProps = {
  format: "landscape-4k",
  fps: 25,
  durationInSeconds: GESAMT_FRAMES / 25,
  transparent: true,
  review: REVIEW_AUS,
  cta: "Lern uns kennen, bevor du uns googelst.",
  urlElisabeth: "elisabeth-krankenhaus-kassel.de/karriere-mitarbeit",
  urlMarien: "marienkrankenhaus-kassel.de/karriere-mitarbeit",
  studioDunkel: false,
};

export const calculateGrafikKomplett = ({ props }: { props: GrafikKomplettProps }) => ({
  ...getCalculateMetadata(props),
  durationInFrames: GESAMT_FRAMES,
});

type Eintrag = { id: string; from: number; dauer: number; inhalt: (dauer: number, p: GrafikKomplettProps) => React.ReactNode };

export const TIMELINE: Eintrag[] = [
  {
    // 0:16,56–0:20,96 · Drohne Elisabeth (Schnitt 0:18,52) → Drohne Marien, weg vor Sandra (0:21,20)
    id: "ortsmarke",
    from: 414,
    dauer: 110,
    inhalt: () => (
      <Ortsmarke
        segmente={[
          { kicker: "Notfallkrankenhaus", titel: "Elisabeth-Krankenhaus Kassel", temperatur: "kuehl", dauer: 49, seite: "rechts" },
          { kicker: "Seit 1913", titel: "Marienkrankenhaus Kassel", temperatur: "warm", dauer: 61, seite: "links" },
        ]}
      />
    ),
  },
  {
    // 0:37,68–0:42,28 · Beatmungszimmer Marien (Ramona), weg vor Jessi
    id: "weaning",
    from: 942,
    dauer: 115,
    inhalt: (d) => <ZertifikatKarte {...zertifikatWeaningDefaults} position="unten-links" dauerFrames={d} />,
  },
  {
    // 0:48,20–0:52,00 · Marina „Man lernt super schnell" → Gips-B-Roll, weg vor der Außenaufnahme (0:52,04)
    id: "weiterbildung",
    from: 1205,
    dauer: 95,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="kuehl"
        kicker="Elisabeth-Krankenhaus Kassel"
        titel={["Weiterbildung Pflege"]}
        zeilen={["Intensiv und Anästhesie · Notfallpflege", "Praxisanleitung"]}
      />
    ),
  },
  {
    // 0:56,48–0:60,48 · Flur Elisabeth, Martina „spannend … Wir haben Action hier"
    id: "notaufnahme",
    from: 1412,
    dauer: 100,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="kuehl"
        kicker="Elisabeth-Krankenhaus Kassel"
        titel={["Zentrale Notaufnahme"]}
        zeilen={["Rund um die Uhr", "Lokales Traumazentrum"]}
      />
    ),
  },
  {
    // 1:03,48–1:08,08 · Medikamentenraum Elisabeth
    id: "cac",
    from: 1587,
    dauer: 115,
    inhalt: (d) => <ZertifikatKarte {...zertifikatCacDefaults} dauerFrames={d} />,
  },
  {
    // 1:14,40–1:17,80 · Drohnen Elisabeth → Marien (Musikwechsel), weg vor Alina (1:17,88)
    id: "zusammenschluss",
    from: 1860,
    dauer: 85,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="beide"
        kicker="Zusammenschluss 2025"
        titel={["Zweitgrößter", "Krankenhausbetreiber"]}
        zeilen={["für Kassel und Nordhessen"]}
        position="unten-mitte"
      />
    ),
  },
  {
    // 1:24,20–1:27,24 · Beatmungszimmer Marien (Alina), weg vor dem Schnitt auf die Pflegekraft links (1:27,24)
    id: "intensiv-marien",
    from: 2105,
    dauer: 76,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="warm"
        kicker="Marienkrankenhaus Kassel"
        titel={["15 Intensivbetten"]}
        zeilen={["Alle mit Beatmungsgeräten"]}
        position="unten-links"
      />
    ),
  },
  {
    // 1:41,32–1:45,00 · nach Ramonas Weiterbildungs-Satz, Maus/CT-B-Roll, weg vor Johanna (1:45,04)
    id: "lehrkrankenhaus",
    from: 2533,
    dauer: 92,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="warm"
        kicker="Marienkrankenhaus Kassel"
        titel={["Akademisches", "Lehrkrankenhaus"]}
        zeilen={["der Universitätsmedizin Göttingen"]}
        position="unten-links"
      />
    ),
  },
  {
    // 2:03,88–2:07,88 · Eingangshalle Elisabeth → Katja „seit 24 Jahren hier"
    id: "intensiv-elisabeth",
    from: 3097,
    dauer: 100,
    inhalt: (d) => (
      <FaktKarte
        dauer={d}
        temperatur="kuehl"
        kicker="Elisabeth-Krankenhaus Kassel"
        titel={["Intensivstation", "seit 1978"]}
        zeilen={[]}
      />
    ),
  },
  {
    // ab 2:12,00 (nach dem letzten O-Ton 2:10,50) · deckend ab 2:13,20 · bis Dateiende 2:19,28
    id: "endcard",
    from: 3300,
    dauer: GESAMT_FRAMES - 3300,
    inhalt: (_d, p) => <Endcard cta={p.cta} urlElisabeth={p.urlElisabeth} urlMarien={p.urlMarien} />,
  },
];

export const MekImagefilmGrafikKomplett: React.FC<GrafikKomplettProps> = (props) => {
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
