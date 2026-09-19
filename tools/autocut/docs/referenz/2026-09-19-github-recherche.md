# GitHub-Recherche für AutoCut (19.09.2026)

Rund 160 Suchanfragen (`gh search repos`, nach Sternen sortiert) und ~70 Repos einzeln geprüft (Sterne, letzter
Push, Lizenz, README). Befund: **Nichts ersetzt AutoCut** — die ähnlichsten Projekte (`mwarf/plotline`,
`theLodgeBots/davinci-resolve-openclaw`, `wassermanproductions/unofficial-davinci-mcp`, `mli/autocut`) sind Skelette.
Brauchbar sind Bausteine für konkrete Lücken. Sterne/Stand: 19.09.2026.

## Reihenfolge (Nutzen ÷ Aufwand)

| # | Baustein | Lücke bei uns | Aufwand |
|---|---|---|---|
| 1 | telemetry-parser (Gyro/Beschleunigung aus FX3, a7 IV, Avata) | `ruhe.py` misst Ruhe-Fenster optisch; `lage_messen.py` parst rtmd selbst | 1 Session |
| 2 | beat_this + PyMusicLooper (+ all-in-one-mlx) | `musik_analyse.py` handgerollt (numpy/scipy), Downbeats und Schleifen wacklig | 1–2 |
| 3 | OmniShotCut statt `ffmpeg gt(scene,0.30)` | Stufe 2: Fehlschnitte bei Schwenks/Lichtwechsel | 1 |
| 4 | CLAP-Index über SFX-Bins und Musikordner | 6g: SFX-Suche über Metriken + Spektrogramm-Bögen | 1 |
| 5 | WhisperX-Alignment / CrisperWhisper | Wortkanten driften (`wort_toleranz_ms 60`), Füllwörter ungesehen | 1–2 |
| 6 | Apple-Vision-Yaw → `SEITE`, L2CS für „Blick in Kamera" | 6i: `SEITE` von Hand; Mangel nur per Claude Vision | 0,5–1 |
| 7 | SigLIP-Embeddings je B-Roll-Keyframe | `setup_hash` (dHash) → semantische Dubletten, Textsuche; Grundlage für Stufe 3 | 2 |
| 8 | mlx-vlm (Qwen-VL lokal) als Vorindex | Stufe 2/2b: Kosten je Anfrage | 1–2 |
| 9 | DeepFilterNet + pedalboard in der Mischsimulation | 6c: Voice Isolation fehlt in der Simulation | 1 |
| 10 | Kanten: ffmpeg `freezedetect`/`signalstats`, SyncNet | Standbild, Broadcast-Pegel, Lippen-Versatz ungeprüft | 1 |
| 11 | Gyroflow (CLI, Horizont-Lock) | 6d: `Stabilize()` ohne Gyro-Daten | 1–2 |
| 12 | colour-checker-detection | 6h: Angleich per Haut/Wand-Stichproben statt Chart | Set-Workflow + 1 |
| 13 | OCR (Apple Vision) für Stand-Banner | „Jeder Stand kommt vor" → `aussteller.md` von Hand | 0,5 |

## A. Sprache und Wortkanten (Stufe 1, Kanten)

| Repo | ★ / Stand / Lizenz | Was es kann | Einsatz |
|---|---|---|---|
| `nyrahealth/CrisperWhisper` | 1,4k · 09/2026 · MIT (Code; Gewichte auf HF prüfen) | Verbatim mit typisierten Füllwörtern, Wiederholungen, Abbrüchen, Pausen; Wortzeiten per Cross-Attention; Deutsch menschlich gelabelt | Füllwörter je Beat im Cutlist-Bericht; präzisere Wortkanten für `align.py`/`kanten.py` |
| `m-bain/whisperX` | 24k · 08/2026 · BSD-2 | wav2vec2-Forced-Alignment je Sprache (deutsches Modell Apache) | Scribe-Text behalten, Zeiten neu ausrichten |
| `MahmoudAshraf97/ctc-forced-aligner` | 563 · 09/2026 · BSD-2 | CTC-Alignment | Standardgewichte (MMS) CC-BY-NC |
| `snakers4/silero-vad` | 10k · 09/2026 · MIT | Sprach-/Stille-Grenzen, ONNX | Schnittpunkt im „Tal" (`wort_tal_db`), Handles datenbasiert |
| `microsoft/DNS-Challenge` (DNSMOS), `fcumlin/DNSMOSPro` | 1,5k CC-BY-4 / 108 MIT | Sprachqualitäts-Score ohne Referenz | Take-Wahl, Kanten-Befund „rauschig" |
| `veritus-git/BadWords` | 35 · 09/2026 · MIT | Text-Editing-Plugin für Resolve, Verbatim-Prompting mit faster-whisper | nur Referenz |

## B. Kamera-Metadaten und Stabilisierung (3a, 6d, 6i, Aftermovie)

| Repo | ★ / Stand / Lizenz | Was es kann | Einsatz |
|---|---|---|---|
| `AdrianEddy/telemetry-parser` | 304 · 09/2026 · Apache-2 · PyPI `telemetry-parser` | Gyro + Beschleunigung je Sample aus FX3, a7 IV, DJI Avata (Mavic nicht), BRAW, Canon | `ruhe.py`/`ruhe_fenster.py` aus dem Gyro; rtmd-Parser für `lage_messen.py`; Wackel-Score für den Sichtungs-Katalog |
| `gyroflow/gyroflow` (+ `gyroflow-plugins`) | 9,5k · 09/2026 · GPL-3 | Gyro-Stabilisierung inkl. Sony-IBIS/OIS, Horizont-Lock, CLI, OFX in Resolve getestet | B-Roll offline vorstabilisieren (externer Prozess) |
| `georgmartius/vid.stab` | 958 · 08/2026 | ffmpeg-Stabilisierung | Rückfall ohne Gyro (Mavic) |

## C. Szenen, Einstellungen, Personen, Bildqualität (2/2b/3, 6e, 6i, Aftermovie)

| Repo | ★ / Stand / Lizenz | Was es kann | Einsatz |
|---|---|---|---|
| `UVA-Computer-Vision-Lab/OmniShotCut` | 309 · 09/2026 · MIT · `pip install omnishotcut` | SOTA Shot-Boundary-Detection (arXiv 04/2026), v1.5 weniger Fehlschnitte bei Kamerafahrten/Licht | ersetzt `scene_cuts()` in `broll_index.py`; Rückfall `soCzech/TransNetV2` (1k, MIT) |
| SigLIP 2 (HF, Apache-2) / `mlfoundations/open_clip` (14k) | – | Bild-Text-Embeddings auf MPS | Dubletten per Kosinus statt dHash, Textsuche, Cluster je Szene; `octimot/StoryToolkitAI` (1k, GPL-3) zeigt das als GUI |
| `Blaizzy/mlx-vlm` + `QwenLM/Qwen3-VL` | 5,5k MIT / 20k Apache-2 | VLMs lokal auf Apple Silicon | erster Beschreibungsdurchlauf lokal, Claude für Mängel/Abschnitte |
| Apple Vision `VNFaceObservation.yaw/pitch/roll` | ohne neue Abhängigkeit | Kopfpose | `SEITE` in `kopf_beide.py` automatisch; Alternative `thohemp/6DRepNet` (677, MIT) |
| `Ahmednull/L2CS-Net` | 526 · MIT | Blickrichtung | Mangel „Blick in Kamera" je Frame |
| `deepinsight/insightface` | 30k · Gewichte nur nicht-kommerziell | Gesichts-Identität | Personen-Cluster („erster Auftritt", Gesichtsanteil je Person); wegen Lizenz eher SigLIP-Crops |
| Apple Vision `VNRecognizeTextRequest` / `PaddlePaddle/PaddleOCR` (90k, Apache-2) | – | OCR | Stand-Banner → `aussteller.md` |
| `idealo/image-quality-assessment` (NIMA), `christophschuhmann/improved-aesthetic-predictor` | 2,2k / 1,3k · Apache-2 | technische + ästhetische Bildnote | Vorsortierung A/B/C. Meiden: `chaofengc/IQA-PyTorch` (PolyForm-NC), `aesthetic-predictor-v2-5` (AGPL) |
| `codeprimate/personfromvid` | 171 · 03/2026 | Rezept: yolov8-face/-pose (AGPL), 6DRepNet, 9 Kopfrichtungen, Schärfe/Helligkeit | Bauplan, keine Abhängigkeit |
| Forschung: `dawitmureja/AVE`, `PardoAlejo/LearningToCut` (MIT), `PardoAlejo/MovieCuts`, `wentianli/awesome-video-editing` | 50–100 · 2022 | Klassifikatoren für 2b-Felder, Schnittpunkt-Vorhersage | Ideengeber Stufe 4 und A/B-Wechsel; AVE ohne Lizenz |
| `supergeniodelmale/Cinemetrica` | 21 · Apache-2 | Statistik (ASL) | Stufe 4 aus fertigen Filmen |

## D. Musik und SFX (6c, 6g, Aftermovie)

| Repo | ★ / Stand / Lizenz | Was es kann | Einsatz |
|---|---|---|---|
| `CPJKU/beat_this` | 394 · 09/2026 · MIT · CLI | Beat- und Downbeat-Tracker, CPU reicht | Beat-Raster in `musik_analyse.py`; Downbeats für `sprung_berechnen.py` |
| `mir-aidj/all-in-one` + `ssmall256/all-in-one-mlx` | 847 MIT / 8 (Port 08/2026, jung) | Tempo, Beats, Downbeats, Abschnitte mit Labels | Kapitelwechsel auf Chorus |
| `arkrow/PyMusicLooper` | 405 · 11/2025 · MIT | nahtlose Loop-Punkte, `extend` auf Ziellänge | Musikschleife automatisch |
| `LAION-AI/CLAP` | 2,3k · CC0 | Text↔Audio-Embeddings | SFX-Bins und Artlist-Ordner per Text durchsuchen |
| `facebookresearch/demucs` | 10k · MIT · archiviert 2024 | Stems | Drum-Stem für Onsets, Instrumental unter VO |
| `spotify/pedalboard` + `Rikorose/DeepFilterNet` | 6,3k GPL-3 / 4,7k MIT-Apache | Effektkette inkl. AU-Plugins; Entrauschung | `mischung_pruefen.py` mit Voice-Isolation-Ersatz |
| `bmcfee/pyrubberband` | 217 · ISC | Time-Stretch | Songende auf Videoende |
| `csteinmetz1/pyloudnorm` | 783 · MIT | BS.1770 in numpy | optional |

## E. Grading (6h)

| Repo | ★ / Lizenz | Einsatz |
|---|---|---|
| `colour-science/colour-checker-detection` | 290 · BSD-3 | ColorChecker je Setup → Matrizen je Kamera → objektiver Angleich |
| `hahnec/color-matcher` (GPL-3) / `jrosebr1/color_transfer` (MIT) | 667 / 520 | B-Roll an Hero-Look angleichen, als CDL nähern |
| `wassermanproductions/unofficial-davinci-mcp` | 35 · 09/2026 | `color_match` (Lab-Reinhard → .cube), `beat_grid`, `tighten_dialogue`, Loudness — Ideenquelle |
| `mahmoudnafifi/mixedillWB` | 126 | Mischlicht-Weißabgleich, Forschung |

## F. Kantenprüfung und QC

- ffmpeg-Filter: `freezedetect`, `signalstats` (YMIN/YMAX/SATMAX, TOUT/VREP — Ansatz von `bavc/qctools`, 389★), `cropdetect`.
- `joonson/syncnet_python` (906★, MIT): Lippen-Ton-Versatz auf dem Export.
- `slhck/ffmpeg-quality-metrics` (559★, MIT) / `Netflix/vmaf`: Qualitätsschranke für Review-Kopien.

## G. Resolve-Anbindung und Austausch

- `AcademySoftwareFoundation/OpenTimelineIO` (2k★, Apache-2): OTIO nativ über die Resolve-API → Readback/Vergleich.
- Resolve-MCP-Server (`samuelgursky/davinci-resolve-mcp` 3k★, `lordhoell`, `CiprianSpiridon`): nativer MCP deckt das ab.
  `SpaceWasTaken/Davinci-Claude-MCP` bestätigt den Split-Workaround über `AppendToTimeline` + `clipInfo`.
- `WyattBlue/auto-editor` (5,3k★, Unlicense): stillebasiert, `--export resolve` — Referenz für XML-Details.
- `AdobeDocs/frameio-api`: Frame.io v4 API. Dropbox Replay: nichts auf GitHub.
- Entwicklerkomfort: `thomjiji/dri` (Typ-Stubs), `WheheoHu/pybmd`, `Greenysmac/awesome-davinci-resolve` (307★).
- Idee aus `WDegan/metafootage-davinci-resolve`: Index-Beschreibungen per `SetMetadata` in Media-Pool-Clips (Smart Bins) — nur mit Freigabe.

## H. Reels/9:16 (später)

`ClipsAI/clipsai` (542★, MIT, ungepflegt seit 01/2024), `AhmedHisham1/pyautoflip` (23★, MIT). Resolves Smart Reframe vermutlich besser.

## Geprüft und verworfen

`carykh/jumpcutter`, `lagmoellertim/unsilence`, `mli/autocut`, `cobanov/autocut` (stillebasiert / Text-Editor-Schnitt);
`plotline`, `openclaw`, `claude-cut-marketplace` (Skelette); `TadasBaltrusaitis/OpenFace` (nicht-kommerziell);
`MoviePy`, `editly`; `OpenRV`, `Kitsu`. Nichts Brauchbares für Room Tone, Atemgeräusche, Match Cut, Kamerabewegung.

## Nebenbei: Resolve-21-API (Changelog)

IntelliSearch-Analyse per API, Audio-Klassifikation im Media Pool, Sprechererkennung in der Transkription, seit 21.0.4
Timeline-Clip-Auswahl lesen, DRT-Import mit Link/Conform. Kandidat für `resolve_probe_api.py`.

## Lizenz-Merkposten

MMS-Aligner-Gewichte (CC-BY-NC), insightface-Modelle (NC), IQA-PyTorch (PolyForm-NC), ultralytics/YOLOv8 (AGPL).
Alles andere MIT/Apache/BSD/CC0 oder als externer Prozess (GPL) unkritisch.
