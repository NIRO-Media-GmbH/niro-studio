// ============================================================
// Dold Holzwerke — Reel-Overlay (Entwürfe Recruiting-Reels, Charge 2026-07 Dreh 27-28.07)
// Eine Komposition für alle Reels: Elemente + Endcard kommen als Props (JSON je Video,
// erzeugt von _intern/entwurf/schnitt.py). 1080×1920 @ 25 fps, transparent (Alpha-Overlay).
//
// Gestaltung aus der Dold-CI: Markengrün #00694D, Weiß, Akzentgelb #F6EA5E, Roboto.
// Schräge Flächen (−14°) wie die Balken im Dold-Logo; Text bleibt aufrecht.
// Motion: Fläche WISCHT rein (0,28 s ease-out), Zeilen SCHIEBEN aus der Maske hoch,
// Ausstieg 0,2 s (Doktrin: Exit schneller als Entry). Alle Texte in der Reels-Safe-Zone
// (Studio-Standard y 7–57,5 %, seitlich ≥ 5 %); Position über Interviews oben (über dem Kopf),
// über B-Roll mittig — setzt schnitt.py je nach Bild darunter.
// ============================================================

import React from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame } from "remotion";
import { z } from "zod";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { projectPropsSchema } from "../../../../core/schemas";
import { DoldEndcard, DoldMark, doldEndcardDefaults } from "../recruiting-endcard/Composition";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";

const { fontFamily: ROBOTO } = loadRoboto("normal", { weights: ["400", "500", "700", "900"], subsets: ["latin", "latin-ext"] });

const GRUEN = "#00694D";
const GRUEN_DUNKEL = "#004F3A";
const WEISS = "#FFFFFF";
const GELB = "#F6EA5E";
const SCHRAEG = -14; // Grad, wie die Logo-Balken

const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const EASE_IN = Easing.bezier(0.5, 0, 0.75, 0);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ─── Schema ───────────────────────────────────────────────
const elementSchema = z.object({
  typ: z.enum(["hook", "keyword", "name", "zahl", "stufen", "liste", "logo", "fullscreen", "flash", "burn", "slam"]),
  start: z.number().int().describe("Startframe"),
  dauer: z.number().int().describe("Dauer in Frames"),
  zeilen: z.array(z.string()).describe("Textzeilen (hook/keyword/liste: Zeilen; name: [Name, Rolle]; zahl: [Zahl, Label]; stufen: Stationen)"),
  y: z.number().min(0).max(1).optional().describe("vertikale Mitte (0–1), Standard je Typ"),
  ausrichtung: z.enum(["links", "mitte", "rechts"]).optional(),
  akzent: z.number().int().optional().describe("Index der Zeile in Gelb (hook/keyword)"),
  schritt: z.number().int().optional().describe("stufen/liste: Frames zwischen den Zeilen"),
  nummer: z.string().optional().describe("liste: Nummer-Badge, z. B. „1/5“"),
  staerke: z.number().optional().describe("flash/burn: 0–1, Standard 0.9 / 0.85"),
  seite: z.enum(["links", "rechts"]).optional().describe("burn: Einfallseite"),
  farbe: z.enum(["gruen", "weiss", "dunkel"]).optional().describe("fullscreen: Hintergrund"),
});
export type ReelElement = z.infer<typeof elementSchema>;

const utWortSchema = z.object({ text: z.string(), start: z.number().int(), ende: z.number().int() });
const utSeiteSchema = z.object({
  start: z.number().int().describe("Startframe der Seite"),
  dauer: z.number().int(),
  zeilen: z.array(z.array(utWortSchema)).describe("Zeilen → Wörter (start/ende relativ zur Seite)"),
});

export const doldReelSchema = projectPropsSchema.extend({
  dauerFrames: z.number().int().min(1),
  elemente: z.array(elementSchema),
  untertitel: z.array(utSeiteSchema).optional(),
  endcard: z
    .object({
      start: z.number().int(),
      jobEyebrow: z.string(),
      jobTitle: z.string(),
      jobSuffix: z.string(),
      ctaText: z.string(),
      website: z.string(),
    })
    .nullable(),
});
export type DoldReelProps = z.infer<typeof doldReelSchema>;

export const doldReelDefaults: DoldReelProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 12,
  transparent: true,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  dauerFrames: 300,
  elemente: [
    { typ: "hook", start: 8, dauer: 62, zeilen: ["Jeden Tag", "was anderes"], akzent: 1 },
    { typ: "name", start: 80, dauer: 75, zeilen: ["David Ruch", "Hobelwerk"] },
    { typ: "zahl", start: 165, dauer: 55, zeilen: ["70 t", "mit voller Zange"] },
  ],
  endcard: { start: 230, jobEyebrow: "Wir suchen", jobTitle: "Anlagenführer", jobSuffix: "(m/w/d)", ctaText: "Jetzt in unter 1 Minute bewerben", website: "dold-holzwerke.com" },
};

export const calculateDoldReel = ({ props }: { props: DoldReelProps }) => ({
  width: 1080,
  height: 1920,
  fps: 25,
  durationInFrames: props.dauerFrames,
});

// ─── Bausteine ────────────────────────────────────────────
const zeitkurve = (f: number, dauer: number) => {
  const rein = interpolate(f, [0, 7], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const raus = interpolate(f, [dauer - 5, dauer], [1, 0], { ...CLAMP, easing: EASE_IN });
  return { rein, raus, sichtbar: Math.min(rein, raus) };
};

// Schräge Fläche, die von links aufwischt; Inhalt aufrecht darüber
const SchraegFlaeche: React.FC<{
  breite: number;
  hoehe: number;
  farbe: string;
  wisch: number; // 0..1
  raus: number; // 1..0
  children: React.ReactNode;
  vonRechts?: boolean;
}> = ({ breite, hoehe, farbe, wisch, raus, children, vonRechts }) => (
  <div style={{ position: "relative", width: breite, height: hoehe }}>
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: farbe,
        transform: `skewX(${SCHRAEG}deg) scaleX(${wisch * raus})`,
        transformOrigin: vonRechts ? "right center" : "left center",
        boxShadow: "0 10px 34px rgba(0,0,0,0.28)",
      }}
    />
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      {children}
    </div>
  </div>
);

const MaskenText: React.FC<{ p: number; raus: number; children: React.ReactNode }> = ({ p, raus, children }) => (
  <div style={{ transform: `translateY(${(1 - p) * 105}%)`, opacity: raus }}>{children}</div>
);

// Versalien, aber „(m/w/d)" bleibt klein (Schreibweise laut NIRO-Regel)
const versal = (t: string) => t.toUpperCase().replace(/\(M\/W\/D\)/g, "(m/w/d)");

// Grobe Breitenschätzung (Doktrin: Versalien fett ≈ 0,62 × px je Zeichen, Roboto Black etwas breiter)
const breiteVon = (text: string, px: number, faktor = 0.64) => Math.ceil(text.length * px * faktor);

const Hook: React.FC<{ el: ReelElement; klein?: boolean }> = ({ el, klein }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const zeilen = el.zeilen.map((z) => versal(z));
  // Schriftgröße so wählen, dass die längste Zeile (inkl. Fläche) in 940 px passt — für alle Zeilen gleich
  const basis = klein ? 70 : 92;
  const laengste = Math.max(...zeilen.map((z) => z.length));
  const px = Math.min(basis, Math.floor(840 / (laengste * 0.64)));
  const maxB = Math.min(940, Math.max(...zeilen.map((z) => breiteVon(z, px))) + 90);
  const y = el.y ?? (klein ? 0.5 : 0.56);
  const ausr = el.ausrichtung ?? "mitte";
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: `${y * 100}%`,
          left: 70,
          right: 70,
          transform: "translateY(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: ausr === "links" ? "flex-start" : ausr === "rechts" ? "flex-end" : "center",
          gap: 14,
        }}
      >
        {zeilen.map((z, i) => {
          const start = 2 + i * 4;
          const wisch = interpolate(f, [start, start + 7], [0, 1], { ...CLAMP, easing: EASE_OUT });
          const text = interpolate(f, [start + 3, start + 11], [0, 1], { ...CLAMP, easing: EASE_OUT });
          const gelb = el.akzent === i;
          const b = Math.min(maxB, breiteVon(z, px) + 90);
          return (
            <SchraegFlaeche key={i} breite={b} hoehe={px * 1.32} farbe={gelb ? WEISS : GRUEN} wisch={wisch} raus={raus} vonRechts={ausr === "rechts"}>
              <MaskenText p={text} raus={raus}>
                <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: px, lineHeight: 1, letterSpacing: "-0.01em", color: gelb ? GRUEN_DUNKEL : WEISS, whiteSpace: "nowrap" }}>
                  {z}
                </span>
              </MaskenText>
            </SchraegFlaeche>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const NameInsert: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const [name, rolle] = el.zeilen;
  const y = el.y ?? 0.63;
  const namePx = Math.min(74, Math.floor(820 / (name.length * 0.6)));
  const rollePx = Math.min(48, Math.floor(760 / ((rolle ?? "").length * 0.56 || 1)));
  const w1 = interpolate(f, [2, 9], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const t1 = interpolate(f, [5, 13], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const w2 = interpolate(f, [7, 14], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const t2 = interpolate(f, [10, 18], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: `${y * 100}%`, left: 80, transform: "translateY(-50%)", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 10 }}>
        <SchraegFlaeche breite={breiteVon(name, namePx, 0.6) + 80} hoehe={namePx * 1.34} farbe={GRUEN} wisch={w1} raus={raus}>
          <MaskenText p={t1} raus={raus}>
            <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: namePx, color: WEISS, whiteSpace: "nowrap" }}>{name}</span>
          </MaskenText>
        </SchraegFlaeche>
        {rolle ? (
          <div style={{ marginLeft: 26 }}>
            <SchraegFlaeche breite={breiteVon(rolle, rollePx, 0.56) + 64} hoehe={rollePx * 1.4} farbe={WEISS} wisch={w2} raus={raus}>
              <MaskenText p={t2} raus={raus}>
                <span style={{ fontFamily: ROBOTO, fontWeight: 700, fontSize: rollePx, color: GRUEN, whiteSpace: "nowrap" }}>{rolle}</span>
              </MaskenText>
            </SchraegFlaeche>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const Zahl: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const [zahl, label] = el.zeilen;
  const y = el.y ?? 0.58;
  const zahlPx = Math.min(190, Math.floor(900 / (zahl.length * 0.62)));
  const labelPx = Math.min(46, Math.floor(820 / (((label ?? "").length || 1) * 0.64)));
  const p = interpolate(f, [2, 11], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const s = interpolate(p, [0, 1], [0.86, 1]);
  const w = interpolate(f, [8, 15], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const t = interpolate(f, [11, 19], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const ausr = el.ausrichtung ?? "mitte";
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: `${y * 100}%`,
          left: 70,
          right: 70,
          transform: "translateY(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: ausr === "links" ? "flex-start" : ausr === "rechts" ? "flex-end" : "center",
          gap: 6,
        }}
      >
        <div style={{ opacity: p * raus, transform: `scale(${s})` }}>
          <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: zahlPx, lineHeight: 0.95, color: WEISS, letterSpacing: "-0.03em", textShadow: "0 6px 30px rgba(0,0,0,0.55)", whiteSpace: "nowrap" }}>
            {zahl}
          </span>
        </div>
        {label ? (
          <SchraegFlaeche breite={breiteVon(versal(label), labelPx) + 70} hoehe={labelPx * 1.43} farbe={GRUEN} wisch={w} raus={raus}>
            <MaskenText p={t} raus={raus}>
              <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: labelPx, color: WEISS, whiteSpace: "nowrap" }}>{versal(label)}</span>
            </MaskenText>
          </SchraegFlaeche>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const Stufen: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const schritt = el.schritt ?? 18;
  const y = el.y ?? 0.4;
  const n = el.zeilen.length;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: `${y * 100}%`, left: 90, transform: "translateY(-50%)", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 12 }}>
        {el.zeilen.map((z, i) => {
          const st = 2 + i * schritt;
          const w = interpolate(f, [st, st + 7], [0, 1], { ...CLAMP, easing: EASE_OUT });
          const t = interpolate(f, [st + 3, st + 11], [0, 1], { ...CLAMP, easing: EASE_OUT });
          const letzte = i === n - 1;
          const aktiv = f >= st + 3 && (letzte || f < 2 + (i + 1) * schritt + 3);
          const px = Math.min(50, Math.floor(700 / (z.length * 0.64)));
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, marginLeft: i * 22 }}>
              <SchraegFlaeche breite={breiteVon(versal(z), px) + 70} hoehe={74} farbe={aktiv ? WEISS : GRUEN} wisch={w} raus={raus}>
                <MaskenText p={t} raus={raus}>
                  <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: px, color: aktiv ? GRUEN_DUNKEL : WEISS, whiteSpace: "nowrap" }}>{versal(z)}</span>
                </MaskenText>
              </SchraegFlaeche>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Liste: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const y = el.y ?? 0.42;
  const b = interpolate(f, [0, 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const zeilenAnzahl = Math.max(1, el.zeilen.length);
  // Nummer-Badge über dem Textblock; Textblock (Hook klein) darunter, beide um y zentriert
  const badgeY = y - 0.035 - zeilenAnzahl * 0.024;
  const textY = y + 0.045;
  return (
    <AbsoluteFill>
      {el.nummer ? (
        <div
          style={{
            position: "absolute",
            top: `${badgeY * 100}%`,
            left: "50%",
            transform: `translate(-50%, -50%) scale(${interpolate(b, [0, 1], [0.7, 1])})`,
            opacity: b * raus,
            width: 150,
            height: 150,
            borderRadius: 75,
            backgroundColor: GRUEN,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 8px 30px rgba(0,0,0,0.3)",
          }}
        >
          <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: el.nummer.length > 3 ? 48 : 64, color: WEISS }}>{el.nummer}</span>
        </div>
      ) : null}
      <Hook el={{ ...el, y: textY }} klein />
    </AbsoluteFill>
  );
};


// ─── v3 (19.09.2026): Logo, Fullscreen-Karte, Flash, Film Burn, Slam ───────
const Logo: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const { raus } = zeitkurve(f, el.dauer);
  const p = interpolate(f, [0, 10], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const s = interpolate(p, [0, 1], [0.82, 1]);
  const y = el.y ?? 0.5;
  const sub = el.zeilen?.[0];
  const subPx = sub ? Math.min(46, Math.floor(820 / (sub.length * 0.64))) : 0;
  const w2 = interpolate(f, [8, 15], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const t2 = interpolate(f, [11, 19], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: `${y * 100}%`, left: 0, right: 0, transform: "translateY(-50%)", display: "flex", flexDirection: "column", alignItems: "center", gap: 26 }}>
        <div style={{ opacity: p * raus, transform: `scale(${s})`, filter: "drop-shadow(0 10px 34px rgba(0,0,0,0.45))" }}>
          <DoldMark width={620} color={WEISS} progress={1} />
        </div>
        {sub ? (
          <SchraegFlaeche breite={breiteVon(versal(sub), subPx) + 70} hoehe={subPx * 1.43} farbe={GRUEN} wisch={w2} raus={raus}>
            <MaskenText p={t2} raus={raus}>
              <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: subPx, color: WEISS, whiteSpace: "nowrap" }}>{versal(sub)}</span>
            </MaskenText>
          </SchraegFlaeche>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// Opake Vollbild-Karte: schräge Fläche wischt in 6 F über das ganze Bild, Zeilen schieben hoch, Ausstieg 5 F (wischt nach rechts raus)
const Fullscreen: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const hg = el.farbe === "weiss" ? WEISS : el.farbe === "dunkel" ? "#0E2B22" : GRUEN;
  const fg = el.farbe === "weiss" ? GRUEN_DUNKEL : WEISS;
  const rein = interpolate(f, [0, 6], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const raus = interpolate(f, [el.dauer - 5, el.dauer], [0, 1], { ...CLAMP, easing: EASE_IN });
  // Wischfläche: Parallelogramm, das von links über das Bild zieht (rein) und nach rechts verlässt (raus)
  const x0 = -1.3 + rein * 1.3 + raus * 1.3; // in Bildbreiten
  const zeilen = el.zeilen.map((z) => versal(z));
  const laengste = Math.max(1, ...zeilen.map((z) => z.length));
  const px = Math.min(118, Math.floor(920 / (laengste * 0.62)));
  const y = el.y ?? 0.46;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: -200,
          bottom: -200,
          left: `${x0 * 100}%`,
          width: "160%",
          backgroundColor: hg,
          transform: `skewX(${SCHRAEG}deg)`,
        }}
      />
      <div style={{ position: "absolute", top: `${y * 100}%`, left: 70, right: 70, transform: "translateY(-50%)", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, opacity: 1 - raus }}>
        {zeilen.map((z, i) => {
          const st = 4 + i * 3;
          const t = interpolate(f, [st, st + 9], [0, 1], { ...CLAMP, easing: EASE_OUT });
          const akz = el.akzent === i;
          return (
            <div key={i} style={{ overflow: "hidden", padding: "0 10px" }}>
              <div style={{ transform: `translateY(${(1 - t) * 110}%)` }}>
                <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: px, lineHeight: 1.08, letterSpacing: "-0.015em", color: akz ? (el.farbe === "weiss" ? "#111" : "#BFEFD8") : fg, whiteSpace: "nowrap" }}>{z}</span>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Flash: warmweißer Blitz über den Schnitt (Start = Schnitt − 3 F): 3 F hoch, danach Abklingen
const Flash: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const st = el.staerke ?? 0.9;
  const a = f < 3 ? interpolate(f, [0, 3], [0, st], CLAMP) : interpolate(f, [3, el.dauer], [st, 0], { ...CLAMP, easing: EASE_IN });
  return <AbsoluteFill style={{ backgroundColor: "#FFF4E0", opacity: a }} />;
};

// Film Burn: warmer Lichteinfall zieht über das Bild (Start = Schnitt − 6 F), mit kurzem Überstrahlen in der Mitte
const Burn: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const st = el.staerke ?? 0.85;
  const p = interpolate(f, [0, el.dauer], [0, 1], CLAMP);
  const vonRechts = el.seite === "rechts";
  const x = (vonRechts ? 1.25 - p * 1.6 : -0.35 + p * 1.6) * 100; // Mittelpunkt in %
  const huell = Math.sin(Math.PI * p); // 0 → 1 → 0
  const spitze = Math.exp(-((p - 0.5) ** 2) / 0.012); // kurzes Überstrahlen am Schnitt
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: st * huell,
          background: `radial-gradient(ellipse 70% 120% at ${x}% 50%, rgba(255,214,120,0.95) 0%, rgba(255,120,30,0.7) 28%, rgba(200,40,10,0.35) 55%, rgba(0,0,0,0) 75%)`,
        }}
      />
      <div style={{ position: "absolute", inset: 0, opacity: st * 0.9 * spitze, backgroundColor: "#FFE9C4" }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: st * 0.45 * huell,
          background: `linear-gradient(${vonRechts ? 270 : 90}deg, rgba(255,90,20,0.0) ${Math.max(0, x - 45)}%, rgba(255,150,40,0.8) ${x}%, rgba(255,90,20,0.0) ${Math.min(100, x + 45)}%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// Slam: ein Wort/zwei Wörter knallen rein (Scale 1,45 → 1 in 3 F), kurz halten, schneller Ausstieg
const Slam: React.FC<{ el: ReelElement }> = ({ el }) => {
  const f = useCurrentFrame();
  const text = versal(el.zeilen.join(" "));
  const px = Math.min(150, Math.floor(960 / (text.length * 0.62)));
  const s = interpolate(f, [0, 3], [1.45, 1], { ...CLAMP, easing: EASE_OUT });
  const a = interpolate(f, [0, 2], [0, 1], CLAMP) * interpolate(f, [el.dauer - 3, el.dauer], [1, 0], CLAMP);
  const y = el.y ?? 0.5;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: `${y * 100}%`, left: 40, right: 40, transform: `translateY(-50%) scale(${s})`, opacity: a, display: "flex", justifyContent: "center" }}>
        <span style={{ fontFamily: ROBOTO, fontWeight: 900, fontSize: px, lineHeight: 1, letterSpacing: "-0.02em", color: WEISS, textShadow: "0 8px 34px rgba(0,0,0,0.6), 0 2px 6px rgba(0,0,0,0.5)", whiteSpace: "nowrap" }}>{text}</span>
      </div>
    </AbsoluteFill>
  );
};

// ─── Untertitel: wörtlich, Unterkante 1460 px (Studio-Standard, darunter Plattform-UI) ───
const UT_PX = 60;
const UT_UNTERKANTE = 1460;
const UT_SCHATTEN = "0 2px 8px rgba(0,0,0,0.55), 0 1px 2px rgba(0,0,0,0.6)";
type UtSeite = z.infer<typeof utSeiteSchema>;

const UntertitelSeite: React.FC<{ seite: UtSeite }> = ({ seite }) => {
  const f = useCurrentFrame();
  const ein = interpolate(f, [0, 3], [0, 1], CLAMP);
  const aus = interpolate(f, [seite.dauer - 3, seite.dauer], [1, 0], CLAMP);
  const zeilenH = UT_PX * 1.22;
  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        top: UT_UNTERKANTE - seite.zeilen.length * zeilenH,
        opacity: Math.min(ein, aus),
        transform: `translateY(${(1 - ein) * 10}px)`,
      }}
    >
      {seite.zeilen.map((zeile, zi) => (
        <div key={zi} style={{ height: zeilenH, display: "flex", justifyContent: "center", alignItems: "center", whiteSpace: "nowrap" }}>
          {zeile.map((w, wi) => {
            const aktiv = f >= w.start && f < Math.max(w.ende, w.start + 3);
            const gesagt = f >= w.start;
            return (
              <span
                key={wi}
                style={{
                  display: "inline-block",
                  marginRight: wi < zeile.length - 1 ? "0.26em" : 0,
                  fontFamily: ROBOTO,
                  fontWeight: 900,
                  fontSize: UT_PX,
                  lineHeight: 1,
                  color: WEISS,
                  opacity: gesagt ? 1 : 0.62,
                  textShadow: UT_SCHATTEN,
                }}
              >
                {w.text}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// ─── Hauptkomposition ─────────────────────────────────────
export const DoldReelOverlay: React.FC<DoldReelProps> = ({ elemente, endcard, dauerFrames, review, untertitel }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "transparent" }}>
      {(untertitel ?? []).map((seite, i) => (
        <Sequence key={`ut${i}`} from={seite.start} durationInFrames={Math.max(1, seite.dauer)} name={`UT: ${seite.zeilen.map((z) => z.map((w) => w.text).join(" ")).join(" / ")}`}>
          <UntertitelSeite seite={seite} />
        </Sequence>
      ))}
      {elemente.map((el, i) => (
        <Sequence key={i} from={el.start} durationInFrames={Math.max(1, el.dauer)} name={`${el.typ}: ${el.zeilen.join(" / ")}`}>
          {el.typ === "hook" ? <Hook el={el} /> : null}
          {el.typ === "keyword" ? <Hook el={el} klein /> : null}
          {el.typ === "name" ? <NameInsert el={el} /> : null}
          {el.typ === "zahl" ? <Zahl el={el} /> : null}
          {el.typ === "stufen" ? <Stufen el={el} /> : null}
          {el.typ === "liste" ? <Liste el={el} /> : null}
          {el.typ === "logo" ? <Logo el={el} /> : null}
          {el.typ === "fullscreen" ? <Fullscreen el={el} /> : null}
          {el.typ === "flash" ? <Flash el={el} /> : null}
          {el.typ === "burn" ? <Burn el={el} /> : null}
          {el.typ === "slam" ? <Slam el={el} /> : null}
        </Sequence>
      ))}
      {endcard ? (
        <Sequence from={endcard.start} durationInFrames={Math.max(1, dauerFrames - endcard.start)} name="Endcard">
          <DoldEndcard
            {...doldEndcardDefaults}
            fps={25}
            transparent
            review={{ showGuides: false, showSafeZone: false, showFaceZone: false, showGrid: false, guideOpacity: 0.35 }}
            jobEyebrow={endcard.jobEyebrow}
            jobTitle={endcard.jobTitle}
            jobSuffix={endcard.jobSuffix}
            jobTitlePx={Math.min(52, Math.floor(860 / Math.max(1, endcard.jobTitle.length * 0.66 + endcard.jobSuffix.length * 0.32)))}
            ctaText={endcard.ctaText}
            website={endcard.website}
          />
        </Sequence>
      ) : null}
      {review?.showGuides ? (
        <ReviewOverlay
          showSafeZone={review.showSafeZone ?? true}
          showFaceZone={review.showFaceZone ?? true}
          showGrid={review.showGrid ?? false}
          faceZone={review.faceZone}
          guideOpacity={review.guideOpacity ?? 0.35}
        />
      ) : null}
    </AbsoluteFill>
  );
};
