# Video 5 — Gesamtvideo „Das ist der MAN Vertrieb" (Langfassung / intern)

**Zweck:** Eigenständiges Gesamtvideo ohne Themen-Fokus, Auftrag Jan, 01.09.2026.
Dopplung zu V1–V4 ausdrücklich erlaubt (V5 steht für sich); Exklusiv-Sperren
zwischen V1–V4 binden V5 nicht. Primärer Einsatz: Probecutter-Assessment
(1 Tag, Premiere), Ergebnis soll kundenverwendbar sein. Cutter-Fassung =
Erklär-PDF in `Ergebnisse/O-Ton-Pläne/Probecutter/` (Einmal-Format, kein
neuer Standard).

**Konzept A (gewählt aus 3 Vorschlägen):** Team-Portrait in 5 Kapiteln,
alle drei Stimmen gleichberechtigt. Hook = stärkste Einzelaussage des Drehs
(Roman 100.000-€-Verantwortung, David-Regel „stärkste Aussage zuerst",
Vorstellung erst als Beat 2). Ziellänge 2:00–2:30 (Länge lt. David egal,
Story schlägt Länge).

**Quellen-Basis:** Alle 22 Zeilen stammen aus den am 15.08. verifizierten
Plänen V1–V4; komplette Neu-Verifikation gegen `_intern/utterances.json`
am 01.09. via `_intern/probecutter/verify_v5.py` — 22/22 OK (Füllwort-
tolerante Prüfung, „äh"-Glättungen dokumentiert). Technik am 01.09. gegen
NAS-Material verifiziert: beide Cams UHD 2160×3840 vertikal (rotation=90),
25p, H.264 10-Bit 4:2:2 ~140 Mbit/s, PCM 48 kHz; XML-Sidecars bestätigen
s-log3-cine / s-gamut3-cine.

## Dramaturgie & Zeilen (Sprecherfolge geprüft: nie 3× dieselbe Person in Folge)

Sprecherfolge gesamt: R | R,V,E | R,V,R | V,V,R,V,E | E,V,E | E,R,E,R | V,E | R

| Block | Ziel | Zeilen |
|---|---|---|
| Hook | ~8 s | 1 (Roman 0547 · 03:57–04:36 Anfang, In nach „…nervös, ne.") |
| K1 Wer wir sind | ~15 s | 2a Roman 0546 · 00:31–00:38 · 2b Victoria 0543 · 01:03–01:06 (Take 2!) · 2c Esther 0545 · 01:11–01:22 (zweiter Anlauf) |
| K2 Was wir verkaufen | ~25 s | 3 Roman „schönste" 0546 · 04:25–04:38 (Wdh.-Take nennt alle 3 Sparten) · 4 Victoria Palette 0544 · 16:29–16:35 · 5 Roman Feuerwehr 0546 · 02:13–02:42 (T-Shirt-Verweis am Anfang beachten) |
| K3 So sieht der Job aus | ~40 s | 6 Victoria Tagesablauf 0543 · 16:25–17:20 (nur Anfang; Rest der Passage = Hook-Material V3) · 7 Victoria Büro/Kunde 0544 · 10:00–10:45 · 8 Roman Kommunal-Zyklus 0546 · 10:05–11:40 (letztes Drittel) · 9 Victoria „beißt keiner" 0544 · 04:39–05:59 (2. Hälfte) · 10 Esther Lösungen 0545 · 21:31–22:06 (Ende) |
| K4 Team & Haltung | ~25 s | 11 Esther Teamsport 0545 · 07:15–08:17 (2. Hälfte) · 12 Victoria „Vicky" 0543 · 12:03–12:34 (Ende) · 13 Esther Marke 0545 · 14:22–15:04 (Mitte) |
| K5 Dein Einstieg | ~40 s | 14 Esther Programm 0545 · 02:45–03:16 · 15 Roman Tag 1 0547 · 00:41–01:04 („Lou-- Laptop"-Versprecher schneidbar) · 16 Esther „für jeden" 0545 · 03:33–04:00 · 17 Roman Milchsammler 0547 · 06:14–06:50 (Musik-Peak, „erster RoMAN") |
| Schluss | ~12 s | 18a Victoria „Sei mutig"/„Glaub an dich" 0544 · 21:15–21:17 + 21:21–21:33 · 18b Esther „mutig sein" 0545 · 24:02–24:24 (Scherz-Anfang der Passage sperren) |
| CTA | ~10 s | 19 Roman „Team der Löwen" 0546 · 24:06–24:17 (Nachdreh; Take ~22:10 sagt „Bisse" — nicht nehmen) + Endcard (Jan, „(m/w/d)") |

## Entscheidungen

- **Milchsammler in V5 erlaubt** (Dopplung V4 ok per Ansage Jan, 01.09.) — bleibt der
  emotionale Peak; Caption-Wortspiel „erster RoMAN" gehört Jan (Grafik).
- **Roman-Aufstiegs-Take (0547 · 08:15–08:43) bewusst NICHT in V5** — Master-
  Frage beim Kunden offen; V5 soll ohne Klärungs-Abhängigkeit schneidbar sein.
- **Vergütung/Mallorca/IAA komplett draußen** (nicht mal als ⚠️-Alternative):
  Probecutter soll keine Compliance-Fallen handhaben müssen.
- **Kein Voice-Over** (Jan-Anfrage 01.09., Empfehlung dagegen angenommen):
  Serie ist O-Ton-pur, VO-Text wäre nicht O-Ton-belegt → Freigabe-Schleife.
- **Grafiken/Inserts/Endcard nicht Cutter-Aufgabe** — läuft über Jan
  (Ansage 01.09.); Musik sucht Cutter selbst auf Artlist (Zugang via Jan).

## Alternativen (für Kürzung/Verlängerung, alle aus verifizierten Plänen)

- Kürzen zuerst: Zeile 7 (Büro/Kunde), dann 13 (Marke), dann 16 (für jeden).
  Nie kürzen: Hook, Vorstellungen, Milchsammler, Mut-Schluss, CTA.
- Verlängern: Roman Aufgaben-Vielfalt 0546 · 14:48–15:22 (sauberer Neustart) ·
  Roman „Hunger" 0546 · 12:08–12:46 Anfang (Out VOR 40-Stunden-Teil!) ·
  Victoria Verkäuferbesprechung 0543 · 19:18–19:39 + Kaffee-Satz 20:17–20:22 ·
  Roman „Rohdiamant" 0547 · 02:47–03:12 · Victoria Stolz/zurückgewonnene
  Kunden 0544 · 14:38–15:49 (Anfang+Ende).
- CTA-Alternativen: Roman kurz „starte jetzt deine Trainee-Ausbildung…"
  0547 · 10:27–10:32 · Victoria Social 0544 · 22:59–23:01 + 24:01–24:02 ·
  Slogan „Bewege Großes…" Victoria 0544 · 23:38–23:43 / Esther 0545 · 27:21–27:24.

## Sperren-Erbe (gilt unverändert, Details Probecutter-PDF Kap. „Sperren")

Vergütung alle drei (Esther 0545 · 18:35–19:21 · Roman 0547 · 08:55–09:21 ·
Victoria 0544 · 07:14–07:23 + Mallorca 11:04–11:09) · Ford-Passage 0544-Anfang ·
Kranwagen · „8–17 Uhr" 0544 · 06:11 · Übergabe „nicht vorgesehen" 0543 · 17:40 ·
Einarbeitung „war 'n Tag da" · Esther-Scherze + „Weiterbildung lange nix" ·
40-Stunden-Teil 0546 · 12:08ff · „Statistisch…Abischnitte" 0546 ·
IAA 0544 · 20:25–20:46 · Aufstiegs-Take 0547 · 08:15–08:43 (Master offen) ·
ASR-Verhörer „blidd"/„Mensch Oma"/„Bisse" (V5 nutzt keinen davon; CTA =
sauberer Nachdreh 24:06).
