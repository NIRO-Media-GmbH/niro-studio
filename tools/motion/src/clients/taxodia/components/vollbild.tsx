// ============================================================
// Taxodia — Vollbild-Grafiken (15.09.2026): Flash, Kapitel-Blende, Karte, Taxodia-Weg
// Decken die Pausen des Rohschnitts (keine Schwarzframes) und tragen die Erklär-Momente.
// Vorbild HBL-Imagefilm (Blenden „öffnen in den Take"), Look taxodia.de (Weiß, Schwarz, Grün).
// Karten: Natural Earth 1:10m Admin-1 (gemeinfrei), eigene Äquirektangular-Projektion.
// Nur transform/opacity/clip-path/mask animiert (Doktrin).
// ============================================================

import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import geo from "../geo/deutschland-laender.json";
import {
  CLAMP,
  EASE_IN,
  EASE_OUT,
  Kicker,
  SCHWARZ,
  TAXODIA_BAND,
  TAXODIA_CREME,
  TAXODIA_GRUEN,
  TAXODIA_HELL,
  TAXODIA_TIEF,
  LUDWIG_GRUEN,
  LUDWIG_TIEF,
  Textzeile,
  URBANIST,
  WortKaskade,
  hexA,
  rein,
  setzen,
} from "./grafik-basis";

// ------------------------------------------------------------
// Gemeinsamer weißer Grund (wie Endcard): Wipe rein, Iris öffnet in den Take
// ------------------------------------------------------------

const WeisserGrund: React.FC<{ dauer: number; irisDauer?: number; reinDauer?: number; children: React.ReactNode }> = ({
  dauer,
  irisDauer = 11,
  reinDauer = 7,
  children,
}) => {
  const frame = useCurrentFrame();
  const r = interpolate(frame, [0, reinDauer], [0, 1], { ...CLAMP, easing: EASE_OUT });
  // Iris: transparentes Loch wächst von der Mitte bis über die Bildecken
  const iris = interpolate(frame, [dauer - irisDauer, dauer], [0, 1], { ...CLAMP, easing: EASE_IN });
  const lochPx = iris * 1250;
  const maske = iris > 0 ? `radial-gradient(circle at 50% 50%, transparent ${lochPx}px, black ${lochPx + 2}px)` : undefined;
  return (
    <AbsoluteFill
      style={{
        clipPath: `inset(0 ${(1 - r) * 100}% 0 0)`,
        WebkitMaskImage: maske,
        maskImage: maske,
      }}
    >
      <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }} />
      <AbsoluteFill
        style={{ background: `radial-gradient(60% 72% at 90% 106%, ${hexA(TAXODIA_HELL, 0.9)} 0%, ${hexA(TAXODIA_CREME, 0.55)} 46%, ${hexA("#FFFFFF", 0)} 74%)` }}
      />
      {/* grüne Kante läuft beim Wipe mit */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: `${r * 100}%`,
          width: 14,
          marginLeft: -14,
          background: TAXODIA_GRUEN,
          opacity: r < 1 ? 1 : 0,
        }}
      />
      {children}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------
// Flash (Kaltstart): grünes Vollbild mit einem Wort, trocken und kurz
// ------------------------------------------------------------

export const Flash: React.FC<{ dauer: number; wort: string }> = ({ dauer, wort }) => {
  const frame = useCurrentFrame();
  const auf = interpolate(frame, [0, 3], [0, 1], CLAMP);
  const ab = interpolate(frame, [dauer - 4, dauer], [0, 1], CLAMP);
  const s = interpolate(frame, [0, dauer], [1.06, 1], { ...CLAMP, easing: Easing.out(Easing.quad) });
  return (
    <AbsoluteFill style={{ opacity: auf * (1 - ab) }}>
      <AbsoluteFill style={{ backgroundColor: TAXODIA_BAND }} />
      <AbsoluteFill style={{ background: `radial-gradient(70% 80% at 50% 50%, ${hexA(TAXODIA_GRUEN, 0.55)} 0%, ${hexA(TAXODIA_BAND, 0)} 70%)` }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            fontFamily: URBANIST,
            fontWeight: 800,
            fontSize: 148,
            letterSpacing: -4,
            color: "#FFFFFF",
            transform: `scale(${s})`,
          }}
        >
          {wort}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------
// Kapitel-Blende: Kicker + Titel, grüner Punkt, Iris öffnet in den Take
// ------------------------------------------------------------

export const Blende: React.FC<{ dauer: number; kicker: string; titel: string }> = ({ dauer, kicker, titel }) => {
  const frame = useCurrentFrame();
  const punkt = setzen(frame, 4);
  const textAb = interpolate(frame, [dauer - 14, dauer - 9], [1, 0], CLAMP);
  return (
    <WeisserGrund dauer={dauer}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: URBANIST, color: SCHWARZ, opacity: textAb }}>
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: 22,
              height: 22,
              borderRadius: 11,
              background: TAXODIA_GRUEN,
              margin: "0 auto 28px",
              transform: `scale(${punkt})`,
            }}
          />
          <div style={{ display: "flex", justifyContent: "center" }}>
            <Kicker text={kicker} marke="taxodia" start={5} groesse={22} sperrung={4} />
          </div>
          <WortKaskade zeilen={[titel]} start={8} versatz={2} groesse={98} gewicht={800} sperrung={-2.4} marginTop={12} ausrichtung="center" />
        </div>
      </AbsoluteFill>
    </WeisserGrund>
  );
};

// ------------------------------------------------------------
// Karten
// ------------------------------------------------------------

type Land = { name: string; iso: string; ringe: number[][][] };
const LAENDER = (geo as { laender: Land[] }).laender;
const LAT0 = 51.2;
const COS0 = Math.cos((LAT0 * Math.PI) / 180);
const K = 100; // px je Breitengrad im 1920er-Raster (Deutschland ≈ 575 × 780 px)
const LON_MIN = 5.85;
const LAT_MAX = 55.07;

export const projiziere = (lon: number, lat: number): [number, number] => [(lon - LON_MIN) * COS0 * K, (LAT_MAX - lat) * K];

const pfad = (ringe: number[][][]) =>
  ringe.map((r) => "M" + r.map(([lon, lat]) => projiziere(lon, lat).map((v) => v.toFixed(1)).join(",")).join("L") + "Z").join("");

const PFADE = LAENDER.map((l) => ({ name: l.name, d: pfad(l.ringe) }));
const MAP_W = (15.03 - LON_MIN) * COS0 * K;
const MAP_H = (LAT_MAX - 47.27) * K;

export const ORTE = {
  ilshofen: { lon: 9.9181, lat: 49.1703 },
  visselhoevede: { lon: 9.5822, lat: 52.9853 },
};

const Pin: React.FC<{ x: number; y: number; farbe: string; start: number; skala: number }> = ({ x, y, farbe, start, skala }) => {
  const frame = useCurrentFrame();
  const p = setzen(frame, start);
  const sichtbar = frame >= start ? 1 : 0;
  const puls = interpolate((frame - start) % 40, [0, 40], [0, 1], CLAMP);
  return (
    <g transform={`translate(${x} ${y}) scale(${1 / skala})`} opacity={sichtbar}>
      <circle r={26 + puls * 26} fill={farbe} opacity={0.28 * (1 - puls)} />
      <circle r={13 * p} fill={farbe} stroke="#FFFFFF" strokeWidth={4} />
    </g>
  );
};

/** Ortsschild neben dem Pin (HTML über dem SVG, Position aus der Projektion). */
const Ortsschild: React.FC<{ x: number; y: number; kicker: string; name: string; farbeTief: string; start: number; seite?: "rechts" | "links" }> = ({
  x,
  y,
  kicker,
  name,
  farbeTief,
  start,
  seite = "rechts",
}) => {
  const frame = useCurrentFrame();
  const k = rein(frame, start, 12);
  const rechts = seite === "rechts";
  return (
    <div
      style={{
        position: "absolute",
        left: rechts ? x + 34 : undefined,
        right: rechts ? undefined : 1920 - x + 34,
        top: y - 40,
        padding: "12px 20px 14px",
        borderRadius: 14,
        background: hexA("#FFFFFF", 0.97),
        boxShadow: `0 12px 34px ${hexA("#141A08", 0.18)}`,
        fontFamily: URBANIST,
        opacity: k,
        transform: `translateX(${(1 - k) * (rechts ? -14 : 14)}px)`,
        whiteSpace: "nowrap",
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: 2.2, textTransform: "uppercase", color: farbeTief }}>{kicker}</div>
      <div style={{ fontSize: 34, fontWeight: 800, color: SCHWARZ, marginTop: 2 }}>{name}</div>
    </div>
  );
};

/** Karte Ilshofen: Deutschland → Zoom Baden-Württemberg, Pin, 50-km-Radius zeichnet sich. */
export const KarteIlshofen: React.FC<{ dauer: number; radiusStart: number }> = ({ dauer, radiusStart }) => {
  const frame = useCurrentFrame();
  const [px, py] = projiziere(ORTE.ilshofen.lon, ORTE.ilshofen.lat);
  const zoom = interpolate(frame, [18, 62], [1, 2.7], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  // Kartenausschnitt: Deutschland rechts im Bild, beim Zoom wandert Ilshofen in die Bildmitte der Kartenfläche
  const feldX = 1180;
  const feldY = 540;
  const mitteX = interpolate(zoom, [1, 2.7], [MAP_W / 2, px]);
  const mitteY = interpolate(zoom, [1, 2.7], [MAP_H / 2, py]);
  const kmLat = 50 / 111.32;
  const rPx = kmLat * K; // gleiche Skala in x (Projektion mit COS0 ≈ lokal winkeltreu genug)
  const kreis = interpolate(frame, [radiusStart, radiusStart + 22], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const umfang = 2 * Math.PI * rPx;
  const labelK = rein(frame, radiusStart + 14, 10);
  return (
    <WeisserGrund dauer={dauer}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <g transform={`translate(${feldX} ${feldY}) scale(${zoom}) translate(${-mitteX} ${-mitteY})`}>
          {PFADE.map((p) => (
            <path
              key={p.name}
              d={p.d}
              fill={p.name === "Baden-Württemberg" ? hexA(LUDWIG_GRUEN, 0.22) : "#E9EBE4"}
              stroke="#FFFFFF"
              strokeWidth={2.2}
              vectorEffect="non-scaling-stroke"
            />
          ))}
          {/* Strich ohne non-scaling-stroke: Dash-Länge bleibt in Karteneinheiten (sonst zeichnet sich der Kreis zu früh) */}
          <circle
            cx={px}
            cy={py}
            r={rPx}
            fill={hexA(LUDWIG_GRUEN, 0.12 * kreis)}
            stroke={LUDWIG_TIEF}
            strokeWidth={3 / zoom}
            strokeDasharray={`${umfang} ${umfang}`}
            strokeDashoffset={umfang * (1 - kreis)}
            opacity={kreis > 0 ? 1 : 0}
          />
          <line x1={px} y1={py} x2={px + rPx} y2={py} stroke={LUDWIG_TIEF} strokeWidth={2 / zoom} opacity={labelK} />
          <Pin x={px} y={py} farbe={LUDWIG_GRUEN} start={10} skala={zoom} />
        </g>
      </svg>
      {/* Radius-Beschriftung (Bildschirmkoordinaten aus der Transformation) */}
      <div
        style={{
          position: "absolute",
          left: feldX + (px + rPx / 2 - mitteX) * zoom - 40,
          top: feldY + (py - mitteY) * zoom + 10,
          width: 80,
          textAlign: "center",
          fontFamily: URBANIST,
          fontWeight: 800,
          fontSize: 26,
          color: LUDWIG_TIEF,
          opacity: labelK,
        }}
      >
        50 km
      </div>
      <Ortsschild
        x={feldX + (px - mitteX) * zoom}
        y={feldY + (py - mitteY) * zoom - 70}
        kicker="Steuerkanzlei Ludwig"
        name="Ilshofen"
        farbeTief={LUDWIG_TIEF}
        start={30}
      />
      {/* weiße Fläche hinter dem Text, damit die gezoomte Karte nicht durchläuft */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 900,
          background: `linear-gradient(90deg, ${hexA("#FFFFFF", 0.97)} 0%, ${hexA("#FFFFFF", 0.92)} 62%, ${hexA("#FFFFFF", 0)} 100%)`,
          opacity: interpolate(frame, [20, 50], [0, 1], CLAMP),
        }}
      />
      <div style={{ position: "absolute", left: 150, top: 400, fontFamily: URBANIST, color: SCHWARZ }}>
        <Kicker text="Landwirtschaftliche Buchstelle" marke="ludwig" start={8} groesse={20} />
        <WortKaskade zeilen={["Steuerkanzlei", "Ludwig"]} start={12} groesse={84} gewicht={800} sperrung={-2} marginTop={12} />
      </div>
    </WeisserGrund>
  );
};

/** Karte Taxodia ↔ Kanzlei: Visselhövede und Ilshofen, gestrichelte Verbindung zeichnet sich, Chip „online". */
export const KarteTaxodia: React.FC<{ dauer: number }> = ({ dauer }) => {
  const frame = useCurrentFrame();
  const [ax, ay] = projiziere(ORTE.visselhoevede.lon, ORTE.visselhoevede.lat);
  const [bx, by] = projiziere(ORTE.ilshofen.lon, ORTE.ilshofen.lat);
  const feldX = 1180 - MAP_W / 2;
  const feldY = 540 - MAP_H / 2;
  const s = interpolate(frame, [0, dauer], [1, 1.04], CLAMP); // dezente Fahrt
  // Bogen (quadratische Bézier-Kurve) nach rechts ausgewölbt
  const cx = (ax + bx) / 2 + 170;
  const cy = (ay + by) / 2;
  const d = `M${ax},${ay} Q${cx},${cy} ${bx},${by}`;
  const laenge = 440; // Näherung der Bogenlänge im Raster
  const zieh = interpolate(frame, [26, 60], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const chip = setzen(frame, 56);
  const chipX = feldX + 0.25 * ax + 0.5 * cx + 0.25 * bx;
  const chipY = feldY + 0.25 * ay + 0.5 * cy + 0.25 * by;
  return (
    <WeisserGrund dauer={dauer}>
      <AbsoluteFill style={{ transform: `scale(${s})`, transformOrigin: "1180px 540px" }}>
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
          <g transform={`translate(${feldX} ${feldY})`}>
            {PFADE.map((p) => (
              <path
                key={p.name}
                d={p.d}
                fill={p.name === "Niedersachsen" ? hexA(TAXODIA_GRUEN, 0.26) : p.name === "Baden-Württemberg" ? hexA(LUDWIG_GRUEN, 0.22) : "#E9EBE4"}
                stroke="#FFFFFF"
                strokeWidth={2.2}
              />
            ))}
            <path
              d={d}
              fill="none"
              stroke={TAXODIA_BAND}
              strokeWidth={4}
              strokeLinecap="round"
              strokeDasharray={`${laenge} ${laenge}`}
              strokeDashoffset={laenge * (1 - zieh)}
            />
            <Pin x={ax} y={ay} farbe={TAXODIA_GRUEN} start={8} skala={1} />
            <Pin x={bx} y={by} farbe={LUDWIG_GRUEN} start={18} skala={1} />
          </g>
        </svg>
        <Ortsschild x={feldX + ax} y={feldY + ay} kicker="Taxodia" name="Visselhövede" farbeTief={TAXODIA_TIEF} start={12} seite="links" />
        <Ortsschild x={feldX + bx} y={feldY + by} kicker="Steuerkanzlei Ludwig" name="Ilshofen" farbeTief={LUDWIG_TIEF} start={22} seite="links" />
        <div
          style={{
            position: "absolute",
            left: chipX - 70,
            top: chipY - 26,
            width: 140,
            height: 52,
            borderRadius: 26,
            background: TAXODIA_GRUEN,
            color: "#FFFFFF",
            fontFamily: URBANIST,
            fontWeight: 800,
            fontSize: 30,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${chip})`,
            opacity: frame >= 56 ? 1 : 0,
          }}
        >
          online
        </div>
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 150, top: 420, fontFamily: URBANIST, color: SCHWARZ }}>
        <Kicker text="Taxodia" marke="taxodia" start={6} groesse={20} />
        <WortKaskade zeilen={["Die Online-", "Steuerfachschule"]} start={10} groesse={78} gewicht={800} sperrung={-2} marginTop={12} />
        <WortKaskade zeilen={["für Quereinsteiger"]} start={18} groesse={48} gewicht={700} sperrung={-0.8} marginTop={10} farbe={TAXODIA_BAND} />
      </div>
    </WeisserGrund>
  );
};

// ------------------------------------------------------------
// Der Taxodia-Weg: vier Stationen auf einer Linie, Reveal auf den Wortzeiten, Fortschrittspunkt
// Werte Website-belegt (taxodia.de/kurse): Einstiegskurs 4 Wochen · 32 UStd · 8 UStd pro Woche;
// Bachelor Professional Teil I ca. 350 UStd, Teil II ca. 350 UStd; Kurs startet jeden Monat.
// ------------------------------------------------------------

type Station = { titel: string; zeilen: string[]; start: number };

export const TaxodiaWeg: React.FC<{ dauer: number; stationen: Station[]; fortschritt: [number, number]; fussStart: number }> = ({
  dauer,
  stationen,
  fortschritt,
  fussStart,
}) => {
  const frame = useCurrentFrame();
  const x0 = 270;
  const x1 = 1650;
  const yLinie = 610;
  const n = stationen.length;
  const xs = stationen.map((_, i) => x0 + (i * (x1 - x0)) / (n - 1));
  const letzterStart = stationen[n - 1].start;
  const linie = interpolate(frame, [stationen[0].start, letzterStart + 10], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const prog = interpolate(frame, fortschritt, [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const punktX = xs[0] + prog * (xs[1] - xs[0]);
  const punktSichtbar = frame >= fortschritt[0] - 4 ? rein(frame, fortschritt[0] - 4, 6) : 0;
  const fuss = rein(frame, fussStart, 12);
  return (
    <WeisserGrund dauer={dauer}>
      <div style={{ position: "absolute", left: 150, top: 150, fontFamily: URBANIST, color: SCHWARZ }}>
        <Kicker text="Steuerkanzlei Ludwig × Taxodia" marke="taxodia" start={4} groesse={20} />
        <WortKaskade zeilen={["Der Taxodia-Weg"]} start={7} groesse={84} gewicht={800} sperrung={-2} marginTop={10} />
      </div>
      {/* Linie: grauer Grund + grüne Füllung */}
      <div style={{ position: "absolute", left: x0, top: yLinie - 3, width: x1 - x0, height: 6, borderRadius: 3, background: "#E4E7DD" }} />
      <div
        style={{
          position: "absolute",
          left: x0,
          top: yLinie - 3,
          width: x1 - x0,
          height: 6,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${TAXODIA_GRUEN}, ${TAXODIA_BAND})`,
          transform: `scaleX(${linie})`,
          transformOrigin: "0 50%",
        }}
      />
      {stationen.map((s, i) => {
        const k = setzen(frame, s.start);
        const t = rein(frame, s.start + 4, 12);
        const oben = i % 2 === 1;
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: "absolute",
                left: xs[i] - 22,
                top: yLinie - 22,
                width: 44,
                height: 44,
                borderRadius: 22,
                background: "#FFFFFF",
                boxShadow: `inset 0 0 0 7px ${TAXODIA_GRUEN}, 0 8px 22px ${hexA("#141A08", 0.16)}`,
                transform: `scale(${frame >= s.start ? k : 0})`,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: xs[i] - 210,
                width: 420,
                top: oben ? yLinie - 196 : yLinie + 48,
                textAlign: "center",
                fontFamily: URBANIST,
                color: SCHWARZ,
                opacity: t,
                transform: `translateY(${(1 - t) * (oben ? 12 : -12)}px)`,
              }}
            >
              <div style={{ fontSize: 19, fontWeight: 800, letterSpacing: 2.6, color: TAXODIA_TIEF, textTransform: "uppercase" }}>Schritt {i + 1}</div>
              <div style={{ fontSize: 52, fontWeight: 800, letterSpacing: -1, marginTop: 6, lineHeight: 1.05 }}>{s.titel}</div>
              {s.zeilen.map((z, zi) => (
                <div key={zi} style={{ fontSize: 31, fontWeight: 500, color: hexA("#000000", 0.72), marginTop: zi === 0 ? 8 : 2 }}>
                  {z}
                </div>
              ))}
            </div>
          </React.Fragment>
        );
      })}
      {/* Fortschrittspunkt: der Quereinsteiger geht weiter in die Kanzlei-Ausbildung */}
      <div
        style={{
          position: "absolute",
          left: punktX - 13,
          top: yLinie - 13,
          width: 26,
          height: 26,
          borderRadius: 13,
          background: TAXODIA_BAND,
          boxShadow: `0 0 0 8px ${hexA(TAXODIA_GRUEN, 0.25)}`,
          opacity: punktSichtbar,
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 150, textAlign: "center", fontFamily: URBANIST, opacity: fuss }}>
        <Textzeile text="Einstieg jederzeit möglich · Hauptkurs startet jeden Monat" start={fussStart} groesse={32} gewicht={700} farbe={TAXODIA_TIEF} ausrichtung="center" />
      </div>
    </WeisserGrund>
  );
};

// ------------------------------------------------------------
// Der Taxodia-Weg, Messe-Fassung (17.09.2026, Kundenfeedback): fünf Stationen, davon eine „Pause"-Station
// (Entscheidung nach 32 UStd: Teilnehmer · Taxodia · Kanzlei — die Chips leuchten auf, wenn Flammann sie nennt).
// Nur 32 UStd als Stundenzahl (Kunde: „Einstiegskurs-Grafik nur 32 h"). Teil I/II-Ziele von taxodia.de/kurse.
// ------------------------------------------------------------

export type ZeileT = { text: string; start: number };
export type StationMesse = { titel: string; zeilen: ZeileT[]; start: number; kicker?: string; pause?: boolean; fuss?: ZeileT };

export const TaxodiaWegMesse: React.FC<{ dauer: number; stationen: StationMesse[]; fortschritt: [number, number]; fussStart: number }> = ({
  dauer,
  stationen,
  fortschritt,
  fussStart,
}) => {
  const frame = useCurrentFrame();
  const x0 = 250;
  const x1 = 1620;
  const yLinie = 600;
  const n = stationen.length;
  const xs = stationen.map((_, i) => x0 + (i * (x1 - x0)) / (n - 1));
  const pauseIdx = stationen.findIndex((s) => s.pause);
  const letzterStart = stationen[n - 1].start;
  // Linie wächst bis zur Pause-Station, wartet dort (der Break), und läuft erst mit dem Fortschritt weiter
  const linie1 = interpolate(frame, [stationen[0].start, stationen[pauseIdx].start + 10], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const linie2 = interpolate(frame, [fortschritt[0], letzterStart + 10], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const xPause = xs[pauseIdx];
  const prog = interpolate(frame, fortschritt, [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const punktX = xPause + prog * (xs[pauseIdx + 1] - xPause);
  const punktSichtbar = frame >= fortschritt[0] - 4 ? rein(frame, fortschritt[0] - 4, 6) : 0;
  const fuss = rein(frame, fussStart, 12);
  const pausePuls = interpolate((frame - stationen[pauseIdx].start) % 40, [0, 20, 40], [0.18, 0.34, 0.18], CLAMP);
  return (
    <WeisserGrund dauer={dauer}>
      <div style={{ position: "absolute", left: 150, top: 140, fontFamily: URBANIST, color: SCHWARZ }}>
        <Kicker text="Steuerkanzlei Ludwig × Taxodia" marke="taxodia" start={4} groesse={20} />
        <WortKaskade zeilen={["Der Taxodia-Weg"]} start={7} groesse={84} gewicht={800} sperrung={-2} marginTop={10} />
      </div>
      {/* Linie: grauer Grund + grüne Füllung in zwei Etappen (Break an der Pause-Station) */}
      <div style={{ position: "absolute", left: x0, top: yLinie - 3, width: x1 - x0, height: 6, borderRadius: 3, background: "#E4E7DD" }} />
      <div
        style={{
          position: "absolute",
          left: x0,
          top: yLinie - 3,
          width: xPause - x0,
          height: 6,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${TAXODIA_GRUEN}, ${TAXODIA_BAND})`,
          transform: `scaleX(${linie1})`,
          transformOrigin: "0 50%",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: xPause,
          top: yLinie - 3,
          width: x1 - xPause,
          height: 6,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${TAXODIA_BAND}, ${TAXODIA_GRUEN})`,
          transform: `scaleX(${linie2})`,
          transformOrigin: "0 50%",
        }}
      />
      {stationen.map((s, i) => {
        const k = setzen(frame, s.start);
        const t = rein(frame, s.start + 4, 12);
        const oben = i % 2 === 1;
        const breit = s.pause ? 760 : 400;
        return (
          <React.Fragment key={i}>
            {s.pause ? (
              // Pause-Knoten: Pillen-Ring mit Pausezeichen, pulsierender Hof
              <>
                <div
                  style={{
                    position: "absolute",
                    left: xs[i] - 46,
                    top: yLinie - 46,
                    width: 92,
                    height: 92,
                    borderRadius: 46,
                    background: hexA(TAXODIA_GRUEN, pausePuls),
                    transform: `scale(${frame >= s.start ? k : 0})`,
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: xs[i] - 30,
                    top: yLinie - 30,
                    width: 60,
                    height: 60,
                    borderRadius: 30,
                    background: "#FFFFFF",
                    boxShadow: `inset 0 0 0 7px ${TAXODIA_BAND}, 0 8px 22px ${hexA("#141A08", 0.16)}`,
                    transform: `scale(${frame >= s.start ? k : 0})`,
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <div style={{ width: 7, height: 24, borderRadius: 2, background: TAXODIA_BAND }} />
                  <div style={{ width: 7, height: 24, borderRadius: 2, background: TAXODIA_BAND }} />
                </div>
              </>
            ) : (
              <div
                style={{
                  position: "absolute",
                  left: xs[i] - 22,
                  top: yLinie - 22,
                  width: 44,
                  height: 44,
                  borderRadius: 22,
                  background: "#FFFFFF",
                  boxShadow: `inset 0 0 0 7px ${TAXODIA_GRUEN}, 0 8px 22px ${hexA("#141A08", 0.16)}`,
                  transform: `scale(${frame >= s.start ? k : 0})`,
                }}
              />
            )}
            <div
              style={{
                position: "absolute",
                left: xs[i] - breit / 2,
                width: breit,
                top: oben ? yLinie - (s.pause ? 300 : 186) : yLinie + (s.pause ? 70 : 48),
                textAlign: "center",
                fontFamily: URBANIST,
                color: SCHWARZ,
                opacity: t,
                transform: `translateY(${(1 - t) * (oben ? 12 : -12)}px)`,
              }}
            >
              <div style={{ fontSize: 19, fontWeight: 800, letterSpacing: 2.6, color: TAXODIA_TIEF, textTransform: "uppercase" }}>
                {s.kicker ?? `Schritt ${i + 1 - (pauseIdx >= 0 && i > pauseIdx ? 1 : 0)}`}
              </div>
              <div style={{ fontSize: s.pause ? 56 : 50, fontWeight: 800, letterSpacing: -1, marginTop: 6, lineHeight: 1.05 }}>{s.titel}</div>
              {s.pause ? (
                <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
                  {s.zeilen.map((z, zi) => {
                    const an = rein(frame, z.start, 8);
                    return (
                      <div
                        key={zi}
                        style={{
                          padding: "8px 22px 10px",
                          borderRadius: 40,
                          fontSize: 30,
                          fontWeight: 700,
                          color: an > 0.5 ? "#FFFFFF" : hexA("#000000", 0.55),
                          background: an > 0.5 ? TAXODIA_BAND : hexA(TAXODIA_HELL, 0.9),
                          transform: `scale(${0.92 + 0.08 * setzen(frame, z.start)})`,
                          opacity: 0.55 + 0.45 * an,
                        }}
                      >
                        {z.text}
                      </div>
                    );
                  })}
                </div>
              ) : (
                s.zeilen.map((z, zi) => (
                  <div
                    key={zi}
                    style={{
                      fontSize: 31,
                      fontWeight: 500,
                      color: hexA("#000000", 0.72),
                      marginTop: zi === 0 ? 8 : 2,
                      opacity: rein(frame, z.start, 10),
                    }}
                  >
                    {z.text}
                  </div>
                ))
              )}
              {s.fuss && (
                <div style={{ marginTop: 14, fontSize: 28, fontWeight: 700, color: TAXODIA_TIEF, whiteSpace: "nowrap", opacity: rein(frame, s.fuss.start, 12) }}>
                  {s.fuss.text}
                </div>
              )}
            </div>
          </React.Fragment>
        );
      })}
      {/* Fortschrittspunkt: nach der Entscheidung geht der Quereinsteiger weiter (ab der 33. Unterrichtsstunde in der Kanzlei) */}
      <div
        style={{
          position: "absolute",
          left: punktX - 13,
          top: yLinie - 13,
          width: 26,
          height: 26,
          borderRadius: 13,
          background: TAXODIA_BAND,
          boxShadow: `0 0 0 8px ${hexA(TAXODIA_GRUEN, 0.25)}`,
          opacity: punktSichtbar,
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 120, textAlign: "center", fontFamily: URBANIST, opacity: fuss }}>
        <Textzeile text="Einstieg jederzeit möglich · Hauptkurs startet jeden Monat" start={fussStart} groesse={32} gewicht={700} farbe={TAXODIA_TIEF} ausrichtung="center" />
      </div>
    </WeisserGrund>
  );
};

// ------------------------------------------------------------
// Zitat-Blende (18.09.2026, User-Feedback K14/K15/K26): Vollbild-Übergang mit dem Zitat des gerade Gehörten —
// Kicker Name · Rolle, großes Zitat, Iris öffnet in den nächsten Take (dessen Ton beginnt schon darunter).
// ------------------------------------------------------------

export const ZitatBlende: React.FC<{ dauer: number; zitat: string[]; name?: string; rolle?: string; marke: "taxodia" | "ludwig" }> = ({
  dauer,
  zitat,
  name,
  rolle,
  marke,
}) => {
  // User 18.09.: keine Quellenzeile (Name · Kanzlei) — der Sprecher war gerade im Bild; name/rolle nur, wenn ausdrücklich gesetzt
  const frame = useCurrentFrame();
  const textAb = interpolate(frame, [dauer - 14, dauer - 9], [1, 0], CLAMP);
  const strich = setzen(frame, 5);
  const akzent = marke === "ludwig" ? LUDWIG_GRUEN : TAXODIA_GRUEN;
  const tief = marke === "ludwig" ? LUDWIG_TIEF : TAXODIA_TIEF;
  return (
    <WeisserGrund dauer={dauer}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: URBANIST, color: SCHWARZ, opacity: textAb }}>
        <div style={{ textAlign: "center", maxWidth: 1500 }}>
          <div style={{ width: 64, height: 8, borderRadius: 4, background: akzent, margin: "0 auto 30px", transform: `scaleX(${strich})` }} />
          <WortKaskade zeilen={zitat} start={7} versatz={2} groesse={78} gewicht={800} sperrung={-1.8} marginTop={0} ausrichtung="center" />
          {name && (
            <div style={{ marginTop: 34, display: "flex", justifyContent: "center", gap: 14, alignItems: "baseline" }}>
              <Textzeile text={name} start={22} groesse={34} gewicht={800} farbe={SCHWARZ} sperrung={-0.4} marginTop={0} ausrichtung="center" />
              {rolle && <Textzeile text={"· " + rolle} start={26} groesse={28} gewicht={600} farbe={tief} marginTop={0} ausrichtung="center" />}
            </div>
          )}
        </div>
      </AbsoluteFill>
    </WeisserGrund>
  );
};

// ------------------------------------------------------------
// Ampel-Grafik (18.09.2026, User-Feedback K21/K22): Controlling nach dem Ampelprinzip — drei Lampen, Grün leuchtet ab
// Start, Gelb und Rot schalten auf Flammanns Wort; Texte aus seinem O-Ton (A8 Grün, #16 Gelb/Rot). Iris öffnet auf ihn.
// ⚠️ Ampel-Grafik laut Schnittplan erst nach Freigabe durch Taxodia (Website nennt „Monitoring"); der User hat sie bestellt.
// ------------------------------------------------------------

export const AmpelGrafik: React.FC<{ dauer: number; titelStart: number; gelb: number; gelbText: number; rot: number; rotText: number }> = ({
  dauer,
  titelStart,
  gelb,
  gelbText,
  rot,
  rotText,
}) => {
  const frame = useCurrentFrame();
  const textAb = interpolate(frame, [dauer - 14, dauer - 9], [1, 0], CLAMP);
  const lampen = [
    { farbe: "#D64545", dunkel: "#5A1F1F", an: frame >= rot, start: rot, label: "Über 1 Woche im Rückstand", text: "Gespräch mit Teilnehmer und Kanzlei", textStart: rotText },
    { farbe: "#F2B705", dunkel: "#5C4A0E", an: frame >= gelb && frame < rot, start: gelb, label: "Bis 1 Woche im Rückstand", text: "Anruf von Taxodia", textStart: gelbText },
    { farbe: TAXODIA_GRUEN, dunkel: "#2E3A18", an: frame < gelb, start: titelStart + 14, label: "Wochenpensum erreicht", text: "Alles läuft", textStart: titelStart + 20 },
  ];
  const gehaeuse = setzen(frame, titelStart + 6);
  return (
    <WeisserGrund dauer={dauer}>
      <AbsoluteFill style={{ fontFamily: URBANIST, color: SCHWARZ, opacity: textAb }}>
        <div style={{ position: "absolute", left: 150, top: 140 }}>
          <Kicker text="Taxodia" marke="taxodia" start={titelStart} groesse={20} />
          <WortKaskade zeilen={["Controlling nach", "dem Ampelprinzip"]} start={titelStart + 3} groesse={80} gewicht={800} sperrung={-2} marginTop={10} />
        </div>
        {/* Ampelgehäuse */}
        <div
          style={{
            position: "absolute",
            left: 1180,
            top: 250,
            width: 200,
            height: 600,
            borderRadius: 100,
            background: "#1F2419",
            boxShadow: `0 30px 70px ${hexA("#141A08", 0.35)}`,
            transform: `scale(${gehaeuse})`,
            transformOrigin: "50% 50%",
          }}
        />
        {lampen.map((l, i) => {
          const cy = 250 + 100 + i * 200;
          const glow = l.an ? 1 : 0;
          const puls = interpolate((frame + i * 13) % 50, [0, 25, 50], [0.75, 1, 0.75], CLAMP);
          const ein = setzen(frame, l.start);
          return (
            <React.Fragment key={i}>
              <div
                style={{
                  position: "absolute",
                  left: 1280 - 70,
                  top: cy - 70,
                  width: 140,
                  height: 140,
                  borderRadius: 70,
                  background: l.an ? l.farbe : l.dunkel,
                  boxShadow: l.an ? `0 0 ${60 * puls}px ${hexA(l.farbe, 0.85)}, inset 0 -10px 24px ${hexA("#000000", 0.25)}` : `inset 0 -10px 24px ${hexA("#000000", 0.45)}`,
                  transform: `scale(${gehaeuse})`,
                  opacity: gehaeuse,
                }}
              />
              <div
                style={{
                  position: "absolute",
                  left: 1400,
                  top: cy - 44,
                  width: 500,
                  opacity: ein,
                  transform: `translateX(${(1 - ein) * -16}px)`,
                }}
              >
                <div style={{ fontSize: 36, fontWeight: 800, letterSpacing: -0.6, color: l.an ? SCHWARZ : hexA("#000000", 0.45) }}>{l.label}</div>
                <div style={{ fontSize: 28, fontWeight: 500, color: hexA("#000000", 0.7), marginTop: 6, opacity: rein(frame, l.textStart, 10) }}>{l.text}</div>
              </div>
              <div style={{ position: "absolute", left: 1200 - 40, top: cy - 44, width: 0, opacity: glow }} />
            </React.Fragment>
          );
        })}
        <div style={{ position: "absolute", left: 150, top: 560, width: 900, opacity: rein(frame, titelStart + 30, 12) }}>
          <Textzeile text="Jedes Wochenende ein Reporting:" start={titelStart + 30} groesse={30} gewicht={600} farbe={TAXODIA_TIEF} marginTop={0} />
          <Textzeile text="Sind die gebuchten Unterrichtsstunden erreicht?" start={titelStart + 34} groesse={30} gewicht={600} farbe={TAXODIA_TIEF} marginTop={6} />
        </div>
      </AbsoluteFill>
    </WeisserGrund>
  );
};
