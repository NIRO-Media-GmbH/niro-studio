# Protokoll — LohiBW / Recruiting / 2026-07 Erster Dreh

## 2026-08-12 — Untertitel-Animation für die vier Ads

**Gemacht.** Die vier fertig geschnittenen Ads lagen unsortiert in
`projects/`; sie liegen jetzt in `Material/Video/`. Für sie wurde eine
Untertitelspur gebaut, die sich in Farbe, Schrift und Verhalten an die
bereits eingebauten Animationen anlegt.

**CI aus dem Bild gemessen**, nicht von der Website übernommen:

| | |
|---|---|
| Gelb | `#FFD900` — in allen vier Ads identisch. Die Website führt `#FFEE00`, ein anderer Ton. Maßgeblich ist das Video. |
| Schrift | Open Sans ExtraBold (92,1 % Glyphdeckung im Vergleich gegen alle Systemschriften) |
| Kastentext | `#1A1A1A`, ~64 px @4K, Laufweite ~0,01 em |
| Kasten | 964×160 px, Eckradius 16 px, Inset 66 px |

**Belegte Zonen im Bestand.** Keyword-Kästen liegen in allen vier Ads bei
y 49,5–54,0 %; einzige Ausnahme ist Video 2 bei 13,2–15,0 s (75,5–79,8 %).
Video 3 und 4 haben zusätzlich Hook-Text bei ~0,9–3,3 s im selben Band,
Video 1 und 2 nicht. Logo-Badge oben links ab ~3 s.

**Entscheidungen (David).**

- Untertitel stehen im Mittelband, wo auch die Kästen sitzen.
- Kasten **unter 2 s** → Untertitel pausiert. Kasten **ab 2 s** → weicht
  nach unten aus (Bandmitte 58,5 %, Glyphen bei 59–62 %).
- Grund für die Schwelle: reines Pausieren hätte in Video 1 **38 % der
  Wörter** gekostet, darunter den vollständigen CTA unter einem 6,6-s-Kasten.
  Mit der Schwelle sinkt das auf 4–9 %, bei nur **fünf Bewegungen** über
  alle vier Ads.
- Stil weiß mit Schatten, höchstens **ein gelbes Wort pro Seite** (6 je Ad).
- Lieferform: fertig eingebranntes MP4, 2160×3840.

**Geliefert** nach `Ergebnisse/Renders/`, je Ad ein MP4 mit eingebrannten
Untertiteln (2160×3840, H.264 CRF 16, Ton unverändert, 368 MB gesamt).
Alpha-Master (ProRes 4444, 1,3 GB) liegen in `_intern/work/alpha/` — damit
sind Textkorrekturen ohne neuen Remotion-Lauf möglich; wenn der Platz
gebraucht wird, können sie weg.

**Abnahme bestanden.** `_intern/verify_no_overlap.py` misst die Textlage
Frame für Frame aus der Alphaspur des fertigen Renders und hält sie gegen
die gemessenen Kastenfenster: **2 750 Untertitel-Frames geprüft, null
Überschneidungen.** Dauern, Ton und Maße stimmen mit den Quellen überein.

### Nachtrag gleicher Tag — Dopplungen entfernt

David: *„Wenn inhaltlich ein Thema durch die Animation schon abgedeckt ist,
brauchen wir es nicht auch noch im Untertitel."* Alle Kastentexte wurden aus
dem Bild gelesen und den Untertiteln gegenübergestellt; 14 Sinneinheiten
sind entfallen. Entfernt wird immer die **ganze** Sinneinheit — ein Schnitt
mitten im Satz hinterlässt sonst Bruchstücke.

| Ad | Wörter gesamt | im Untertitel | Seiten | Ausweich-Fenster |
|---|---|---|---|---|
| 1 — Der schnellere Weg nach oben | 118 | 69 | 15 | 3 |
| 2 — Raus aus dem Fristen-Hamsterrad | 110 | 49 | 13 | 0 |
| 3 — Wieder mit Menschen arbeiten | 106 | 51 | 12 | 0 |
| 4 — Der Steuerjob… | 116 | 86 | 21 | 0 |

**Nachträge David, 13.08.2026:** In Video 2 die ersten drei Sekunden ganz
ohne Untertitel (der Hook trägt allein); ab 27 s nur noch „Das heißt für
dich" als Anmoderation, dann übernimmt die dunkle Liste, weiter erst bei
„Das heißt nicht, dass Langeweile herrscht." In Video 4 fliegt „Geht das?"
raus, der Untertitel setzt bei „Wenn der Mitarbeiter…" ein.

**Übergabe an die Animation** statt Totalschnitt: Wo eine Animation nur
einen Teil des Satzes trägt, bleibt der Rest als Vor- und Nachlauf stehen.
Sonst startet die Ad ohne Text.

- V1: „In welcher Steuerkanzlei wirst du" → **FÜHRUNGSKRAFT?** → **OHNE EXAMEN**
- V2: „Wie viele Abende" → **HAST DU LETZTES JAHR** → „im Büro verbracht?"

Stellen ganz ohne Text (weder Untertitel noch Kasten noch Hook) bleiben
unter 4,5 s: V1 2,2 s · V2 2,4 s · V3 2,4 s · V4 4,2 s — Letzteres ist eine
echte Sprechpause über B-Roll.

Entfallen sind Hook-Fenster, kurze Kästen und die Dopplungen. Die Liste der
entfernten Sätze steht als `COVERED_BY_BOX` in `_intern/build_captions.py`
— dort je Eintrag mit dem Kasten, der den Inhalt trägt.

Drei Nebenwirkungen, bewusst so gelöst:
- Wo ein Kasten den Satz vollendet („…und hast vom" → **EINKOMMEN AB TAG 1**),
  endet der Untertitel jetzt sauber vorher statt auf einem Wortrest.
- Ein gekapptes Satzende bekommt einen Punkt statt des hängenden Kommas.
- Verdeckt ein Kasten das Satzanfangswort, wird der Seitenanfang
  großgeschrieben („Klick auf den Button" statt „klick…").

Dabei fielen zwei Fehler auf:

1. Das Füllwort „äh" in Video 4 stand trotz Filter noch drin — die
   Vergleichsliste enthielt „äh", der Normalisierer macht daraus aber „ah".
   Behoben.
2. **Der Kastendetektor verschmilzt direkt aufeinanderfolgende Kästen zu
   einem Fenster.** Beim ersten Abgleich wurde deshalb je nur der erste Text
   gelesen — drei Kästen fehlten in der Liste („OHNE EXAMEN",
   „INTERN AUSGESCHRIEBEN", „DIE GANZE FAMILIE"), zwei davon hätten weiter
   gedoppelt. Gefunden erst beim Sichtbeleg am fertigen Render.
   `analyze_overlays.py` warnt jetzt mit `boxCount`, wenn ein Fenster
   mehrere Kästen enthält — **aber nur als Hinweis**: Einblend-Animationen
   treiben die Zahl hoch, gleich breite Kästen nacheinander bleiben
   unentdeckt. Verlässlich ist nur, jedes Fenster im Sekundentakt
   auszuschneiden und die Texte zu lesen.
3. **Video 2 hat doch einen Hook** — „HAST DU LETZTES JAHR" bei 0,8–1,4 s,
   aber bei **23–27 % Bildhöhe** statt im Mittelband. `analyze_hook.py`
   tastete nur 30–75 % ab und hat ihn übersehen; der Untertitel doppelte
   deshalb den ganzen Eröffnungssatz. Suchbereich jetzt 18–85 %.
4. **Zwei Renderläufe liefen parallel** und überschrieben dieselben Dateien
   (ein hängender Lauf sprang verspätet an). `render_all.sh` hat jetzt eine
   `mkdir`-Sperre und bricht ab, statt sich selbst ins Gehege zu kommen.

5. **Es gibt eine dritte Animationsart.** Video 2 zeigt bei 27,2–29,8 s eine
   gestapelte Liste in **dunklen** Kästen („KEINE BUCHHALTUNG / KEINE
   LOHNABRECHNUNG / KEINE UMSATZSTEUER"). Beide Detektoren suchen nach Gelb
   und waren dafür blind — der Untertitel doppelte sie wortwörtlich.
   `scan_all_boxes.py` sucht jetzt zusätzlich dunkle Kästen (viele
   Fehltreffer durch dunkle Kleidung, deshalb einzeln nachsehen). Die Liste
   steht als `EXTRA_ANIMATIONS` in `build_captions.py`, damit sie auch als
   Sperrfläche wirkt.

**Vollständige Animationsliste** (mühsam erarbeitet, bei Änderungen prüfen):
17 gelbe Keyword-Kästen, 3 Hooks (V2/V3/V4 — V1 hat keinen), 1 dunkle Liste.

**Abschlussprüfung.** Alle 21 Animationen wurden im Bild gelesen und
maschinell gegen jede Untertitelseite gehalten, auch gegen benachbarte im
Umkreis von einer Sekunde: keine inhaltliche Berührung. Räumlich ebenfalls
sauber (1 891 Untertitel-Frames, null Überschneidungen).

**Offen / zu prüfen.**

- **Video 3, 19,3–21,4 s:** „der sich immer **den** ganzen Sachverhalt
  gekümmert hat" — grammatisch müsste es „um den" heißen. Entweder
  Scribe-Aussetzer oder echter Versprecher. **Bitte gegenhören**, dann
  entweder so lassen (Versprecher) oder in `_intern/build_captions.py`
  ergänzen.
- Die Ads haben **keinen CTA-Endcard** — nur einen Keyword-Kasten am
  Schluss („WEG NACH OBEN OFFEN"). Für Recruiting-Ads ohne Endcard fehlt
  der Jobtitel mit „(m/w/d)". Eigenes Thema, nicht Teil dieser Lieferung.
- Untertitel reichen zwangsläufig unter die interne Safe-Zone-Kante von
  57,5 %: zwischen Kastenunterkante (54 %) und 57,5 % passen keine zwei
  Zeilen. Der Kunde nutzt den Bereich mit seinem eigenen Kasten bei 77 %
  ohnehin.

**Werkzeuge** in `_intern/`: `analyze_overlays.py` (misst die Kästen),
`analyze_hook.py`, `transcribe_ads.py`, `build_captions.py` (erzeugt
`captions.ts`, bricht bei jeder Überschneidung hart ab), `render_all.sh`.
Remotion-Client `lohi-bw`, Kompositionen `LohiBW-Untertitel-1..4`.
