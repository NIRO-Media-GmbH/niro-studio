// ============================================================
// Rappold Video 2 — Untertitel „Freie Typo": Grundzeilen weiß (einzelne Wörter blau),
// Heroes versal (weiß/blau). Lage fest je Seite; Wörter erscheinen am Wortanfang.
// ============================================================
import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Abdunklung } from "../../Abdunklung";
import { BASE_W, BLAU, FONT, SCHATTEN, SCHATTEN_BLAU, WEISS } from "../../lib";
import { WORTE } from "./daten-generiert";
import { anzeigeText, HERO_SPERRUNG, seitenBereich, seitenOben, seitenUnterkante, seitenZeilen, wortSchnitt, zeilenHoehe } from "./layout";
import { ausblendFrames, einblendung, HERO_FRAMES, seitenIndex, sichtbareSaetze, wortDeckkraft, type Fenster } from "./timing";
import { SAETZE, type Satz } from "./untertitel-plan";

const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const PLAN = sichtbareSaetze(SAETZE, WORTE, 25);

const SatzBlock: React.FC<{ satz: Satz; fenster: Fenster }> = ({ satz, fenster }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const seite = seitenIndex(satz, WORTE, frame / fps);
  const zeilen = seitenZeilen(satz, seite, WORTE);
  const ersteWort = seitenBereich(satz, seite)[0];
  const oben = seitenOben(zeilen, seitenUnterkante(satz, seite));
  const n = ausblendFrames(satz, WORTE, fenster, fps);
  const aus = n === 0 ? 1 : interpolate(frame, [fenster.bis - n, fenster.bis], [1, 0], CLAMP);
  return (
    <div style={{ position: "absolute", left: 0, top: oben, width: BASE_W, opacity: aus, fontFamily: FONT }}>
      {zeilen.map((z, k) => (
        <div
          key={k}
          style={{ position: "relative", height: zeilenHoehe(z), display: "flex", justifyContent: "center", alignItems: "center", whiteSpace: "nowrap" }}
        >
          {z.worte.map((i, n) => {
            const text = anzeigeText(WORTE, satz, i, z.hero !== null);
            const abstand = n < z.worte.length - 1 ? "0.26em" : 0;
            if (z.hero) {
              const p = wortDeckkraft(WORTE[i].start, i === ersteWort, frame, fps);
              const landung = interpolate(einblendung(WORTE[z.worte[0]].start, frame, fps, HERO_FRAMES), [0, 1], [0.94, 1], {
                ...CLAMP,
                easing: EASE_OUT,
              });
              const blau = z.hero === "blau";
              return (
                <span
                  key={i}
                  style={{
                    position: "relative",
                    display: "inline-block",
                    marginRight: abstand,
                    fontWeight: 800,
                    fontSize: z.px,
                    lineHeight: 1,
                    letterSpacing: `${HERO_SPERRUNG}em`,
                    color: blau ? BLAU : WEISS,
                    textShadow: blau ? SCHATTEN_BLAU : SCHATTEN,
                    opacity: p,
                    transform: `scale(${landung})`,
                  }}
                >
                  {satz.abdunkeln ? <Abdunklung staerke={satz.abdunkeln} randX={18} randY={-4} weich={14} style={{ zIndex: -1 }} /> : null}
                  {text}
                </span>
              );
            }
            const p = interpolate(wortDeckkraft(WORTE[i].start, i === ersteWort, frame, fps), [0, 1], [0, 1], { ...CLAMP, easing: EASE_OUT });
            const blau = wortSchnitt(satz, i) === "800";
            return (
              <span
                key={i}
                style={{
                  position: "relative",
                  display: "inline-block",
                  marginRight: abstand,
                  fontWeight: blau ? 800 : 600,
                  fontSize: z.px,
                  lineHeight: 1,
                  color: blau ? BLAU : WEISS,
                  textShadow: blau ? SCHATTEN_BLAU : SCHATTEN,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 12}px)`,
                }}
              >
                {satz.abdunkeln ? <Abdunklung staerke={satz.abdunkeln} randX={14} randY={2} weich={12} style={{ zIndex: -1 }} /> : null}
                {text}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

export const Untertitel: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {PLAN.filter(({ fenster }) => frame >= fenster.von && frame < fenster.bis).map(({ satz, fenster }) => (
        <SatzBlock key={satz.id} satz={satz} fenster={fenster} />
      ))}
    </>
  );
};
