// ============================================================
// Taxodia-Erklärvideo „Der Taxodia-Weg" — Grafikebene v3/v4, MESSE-Fassung (17.09.2026 Kundenfeedback; 18.09. v4 nach Replay-Kommentaren:
// Zitat-Blenden Ludwig/Flammann/Hein, Ampel-Grafik, Karte Visselhövede–Ilshofen am Innenschnitt)
// Eine Alpha-Spur über der Messe-Timeline („Taxodia-Weg Messe V1", 9602 Frames, 25 fps, 3840×2160).
// Alle Zeiten kommen aus messe-timing.json (erzeugt von projects/…/_intern/messe/messe_plan.py): die Element-Positionen
// sind die vom User gesetzten Positionen der v2-Clips, per Ripple auf die neue Timeline übertragen; Banner länger.
//
// Änderungen gegenüber v2 (Grafikebene.tsx):
//  · Bauchbinden 6–8 s statt 3–4,5 s, Faktenkarten länger (Kunde: „Banner zu kurz eingeblendet")
//  · Taxodia-Weg: Einstiegskurs nur „32 Unterrichtsstunden", neue Pause-Station „Entscheidung" (Teilnehmer · Taxodia · Kanzlei),
//    Teil I/II ohne Stundenzahlen (Ziele von taxodia.de/kurse), Prüfung
//  · Software-Karte ohne HANNIBAL (Kunde): DATEV · LAND-DATA · nlb
//  · neue Karten: Kostenbremse (Flammann), Support (Hein), Prüfungsvorbereitung (Hein) — Website-belegt (taxodia.de:
//    Überblick/FAQ „Gebuchte Kurse können jederzeit ohne Stornokosten beendet werden", „Der Teilnehmer kann in Absprache mit
//    dem Arbeitgeber als deaktiviert geführt werden", „Wir beantworten diese fachlich fundiert nach Rücksprache mit den
//    Dozenten", Kanzleiratgeber „telefonischer Beratung"; bachelor-professional: Live-Online-Wiederholungsunterricht,
//    „Vor der mündlichen Prüfung … Live-Online Unterrichtseinheit … über 90 Minuten")
//  · Abrechnungs-Karte: „Keine Vorkasse." + „Rechnung kommt monatlich" (FAQ), damit Flammanns „keine Stornokosten" nicht doppelt
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { getCalculateMetadata } from "../../../../core/format-utils";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { BASE_H, BASE_W, HelleKarte, Kicker, Marke, Position, Textzeile, WortKaskade, wortAnzahl } from "../../components/grafik-basis";
import { AmpelGrafik, Blende, Flash, KarteIlshofen, KarteTaxodia, StationMesse, TaxodiaWegMesse, ZitatBlende } from "../../components/vollbild";
import { ci, grafikDefaults, grafikSchema, GrafikProps } from "./Grafikebene";
import timing from "./messe-timing.json";

export { grafikSchema as grafikMesseSchema };
export const GESAMT_FRAMES_MESSE: number = timing.gesamtFrames;

export const grafikMesseDefaults: GrafikProps = { ...grafikDefaults, durationInSeconds: GESAMT_FRAMES_MESSE / 25 };

export const calculateGrafikMesse = ({ props }: { props: GrafikProps }) => ({
  ...getCalculateMetadata(props),
  durationInFrames: GESAMT_FRAMES_MESSE,
});

// --- Bausteine (wie v2) ---------------------------------------------------------------------------------------------

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
      gruenFarbe="#7B9636"
    />
  </HelleKarte>
);

const Bauchbinde: React.FC<{ dauer: number; marke: Marke; organisation: string; name: string; rolle: string; position?: Position }> = (p) => (
  <HelleKarte dauer={p.dauer} marke={p.marke} position={p.position} padding="24px 40px 26px 46px">
    <Kicker text={p.organisation} marke={p.marke} groesse={18} sperrung={2.4} />
    <WortKaskade zeilen={[p.name]} start={9} groesse={46} gewicht={800} sperrung={-0.8} marginTop={6} />
    <Textzeile text={p.rolle} start={14} groesse={27} marginTop={4} />
  </HelleKarte>
);

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

// Endcard aus v2 wiederverwenden (gleicher Inhalt)
import { TIMELINE as TIMELINE_V2 } from "./Grafikebene";
const endcardV2 = TIMELINE_V2.find((e) => e.id === "endcard")!;

// --- Inhalt je Element-Id --------------------------------------------------------------------------------------------

type El = { id: string; from: number; dauer: number; vollbild?: boolean; [k: string]: unknown };

function inhalt(e: El, p: GrafikProps): React.ReactNode {
  const d = e.dauer;
  switch (e.id) {
    case "flash-fachkraeftemangel":
      return <Flash dauer={d} wort="Fachkräftemangel" />;
    case "flash-quereinsteiger":
      return <Flash dauer={d} wort="Quereinsteiger" />;
    case "titel":
      return <Titel dauer={d} />;
    case "karte-ilshofen":
      return <KarteIlshofen dauer={d} radiusStart={e.radiusStart as number} />;
    case "bauchbinde-ludwig":
      return <Bauchbinde dauer={d} marke="ludwig" organisation="Steuerkanzlei Ludwig · Landwirtschaftliche Buchstelle" name="Friedrich Ludwig" rolle="Steuerberater" />;
    case "bauchbinde-hein":
      return <Bauchbinde dauer={d} marke="ludwig" organisation="Steuerkanzlei Ludwig" name="Jan Philipp Hein" rolle="Steuersachbearbeiter" position="unten-rechts" />;
    case "blende-taxodia":
      return <Blende dauer={d} kicker="Taxodia" titel="Die Online-Steuerfachschule" />;
    case "bauchbinde-flammann":
      return <Bauchbinde dauer={d} marke="taxodia" organisation="Taxodia" name="Jörn Flammann" rolle="Gründer und Geschäftsführer" />;
    case "karte-taxodia":
      return <KarteTaxodia dauer={d} />;
    case "software":
      return <FaktKarte dauer={d} position="unten-rechts" kicker="Taxodia" titel={["Gelernt wird in der", "Software der Kanzlei"]} zeilen={["DATEV · LAND-DATA · nlb"]} />;
    case "bachelor-professional":
      return <FaktKarte dauer={d} kicker="Bachelor Professional" titel={["Gleiches Qualifikationsniveau", "wie ein Hochschul-Bachelor"]} />;
    case "taxodia-weg":
      return (
        <TaxodiaWegMesse
          dauer={d}
          stationen={e.stationen as StationMesse[]}
          fortschritt={e.fortschritt as [number, number]}
          fussStart={e.fussStart as number}
        />
      );
    case "kostenbremse":
      return <FaktKarte dauer={d} kicker="Kostenbremse" titel={["Stopp jederzeit möglich –", "auch vor Kursbeginn"]} zeilen={["Teilnehmer wird in Absprache mit der Kanzlei deaktiviert"]} />;
    case "kosten":
      return <FaktKarte dauer={d} kicker="Kosten" titel={["Keine Hotel- und Reisekosten"]} zeilen={["Gesamtkosten mindestens 50 % günstiger", "als in vergleichbaren Präsenzkursen"]} />;
    case "blende-online":
      return <Blende dauer={d} kicker="Taxodia" titel="Online lernen" />;
    case "support":
      return <FaktKarte dauer={d} position="unten-rechts" kicker="Support" titel={["Antwort von den Dozenten"]} zeilen={["fachlich fundiert, auch telefonisch"]} />;
    case "monitoring":
      return <FaktKarte dauer={d} kicker="Monitoring" titel={["Die Kanzlei sieht", "Lernfortschritt und Noten"]} />;
    case "abrechnung":
      return <FaktKarte dauer={d} kicker="Abrechnung pro Modul" titel={["Keine Vorkasse."]} zeilen={["Rechnung kommt monatlich"]} />;
    case "pruefung":
      return <FaktKarte dauer={d} position="unten-rechts" kicker="Prüfungsvorbereitung" titel={["Live-Online-Wiederholungsunterricht", "vor der schriftlichen Prüfung"]} zeilen={["+ 90 Minuten Live-Einheit vor der mündlichen Prüfung"]} />;
    case "blende-ergebnis":
      return <Blende dauer={d} kicker="Die Prüfung" titel="Das Ergebnis" />;
    case "blende-kanzleien":
      return <Blende dauer={d} kicker="Der nächste Schritt" titel="Für Kanzleien" />;
    case "blende-quereinsteiger":
      return <Blende dauer={d} kicker="Der nächste Schritt" titel="Für Quereinsteiger" />;
    case "zitat-ludwig":
    case "zitat-flammann":
    case "zitat-hein":
      return <ZitatBlende dauer={d} zitat={e.zitat as string[]} name={e.name as string | undefined} rolle={e.rolle as string | undefined} marke={e.marke as "taxodia" | "ludwig"} />;
    case "ampel":
      return (
        <AmpelGrafik
          dauer={d}
          titelStart={e.titelStart as number}
          gelb={e.gelb as number}
          gelbText={e.gelbText as number}
          rot={e.rot as number}
          rotText={e.rotText as number}
        />
      );
    case "endcard":
      return endcardV2.inhalt(d, p);
    default:
      throw new Error(`Grafik-Element ohne Inhalt: ${e.id}`);
  }
}

export const TIMELINE_MESSE: El[] = timing.elemente as El[];

export const TaxodiaGrafikebeneMesse: React.FC<GrafikProps> = (props) => {
  const { width } = useVideoConfig();
  const scale = width / BASE_W;
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: props.studioDunkel ? "#2a2f22" : "transparent" }}>
        <div style={{ position: "absolute", width: BASE_W, height: BASE_H, transform: `scale(${scale})`, transformOrigin: "0 0" }}>
          {TIMELINE_MESSE.map((e) => (
            <Sequence key={e.id} name={e.id} from={e.from} durationInFrames={e.dauer} layout="none">
              {inhalt(e, props)}
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
