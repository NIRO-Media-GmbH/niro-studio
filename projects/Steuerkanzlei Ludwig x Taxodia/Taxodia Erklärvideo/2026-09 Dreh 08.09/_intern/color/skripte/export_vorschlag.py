"""Schreibt _intern/color/grading_vorschlag.json aus fit3.json + holdout_eval.json + orig_check.json + manifest*.json."""
import json, os
import numpy as np
from colorlib import lin_to_slog3, STOP

SP = os.path.dirname(os.path.abspath(__file__))
OUT = "/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/color"
fit = json.load(open(f"{SP}/fit3.json"))
hold = json.load(open(f"{SP}/holdout_eval.json"))
orig = json.load(open(f"{SP}/orig_check.json"))
man = json.load(open(f"{SP}/manifest.json"))
manh = json.load(open(f"{SP}/manifest_holdout.json"))
LUTROOT = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"
LUT = f"{LUTROOT}/Sony/SLog3SGamut3.CineToLC-709.cube"


def r4(v):
    return [round(float(x), 4) for x in v]


def cdl_block(p, hinweis):
    p = r4(p)
    return {"slope": p[0:3], "offset": p[3:6], "power": [1.0, 1.0, 1.0], "saturation": p[6],
            "resolve_SetCDL": {"Slope": " ".join(f"{x:.4f}" for x in p[0:3]), "Offset": " ".join(f"{x:.4f}" for x in p[3:6]),
                               "Power": "1.0000 1.0000 1.0000", "Saturation": round(p[6], 4)},
            "hinweis": hinweis}


look = fit["look"]
P = float(lin_to_slog3(0.18))
look_cdl = fit["look_cdl_log"]

kameras = {}
labels = {"Ludwig": ("FX3_0222", "a7MK4_20260908_0118"), "Flammann": ("FX3_0223", "a7MK4_20260908_0119"), "Hein": ("FX3_0228", "a7MK4_20260908_0752")}
for person, (fx3, a7) in labels.items():
    st = fit["sets"][person]
    h = hold[person]
    o = orig[f"{person}_2"]
    def hold_stats(key):
        v = [r[key]["dE_nachher"] for r in h if key in r]
        v0 = [r[key]["dE_vorher"] for r in h if key in r]
        return None if not v else {"dE2000_vorher_mittel": round(float(np.mean(v0)), 2), "dE2000_nachher_mittel": round(float(np.mean(v)), 2), "dE2000_nachher_max": round(float(np.max(v)), 2)}
    kameras[person] = {
        "clips": {"FX3 (B-Cam, V1, Ton)": fx3 + ".MP4", "a7 IV (A-Cam, V2)": a7 + ".MP4"},
        "FX3": {
            "node1_gesamt_log_vor_LUT": cdl_block(st["FX3_cdl_gesamt"], "In Node 1 zusammen mit dem LUT setzen (CDL = Angleich + Look, im S-Log3-Raum vor dem Node-LUT)."),
            "nur_angleich_log_vor_LUT": cdl_block(st["FX3_cdl_angleich"], "Nur fuer einen Node-Baum: Node 1 = diese CDL, Node 2 = Look-CDL, Node 3 = LUT."),
            "physikalisch": st["FX3_phys"],
        },
        "a7_IV": {
            "node1_gesamt_log_vor_LUT": cdl_block(st["A7_cdl_gesamt"], "In Node 1 zusammen mit dem LUT setzen (CDL = Angleich + Look, im S-Log3-Raum vor dem Node-LUT)."),
            "nur_angleich_log_vor_LUT": cdl_block(st["A7_cdl_angleich"], "Nur fuer einen Node-Baum: Node 1 = diese CDL, Node 2 = Look-CDL, Node 3 = LUT."),
            "physikalisch": st["A7_phys"],
        },
        "deutung": None,
        "messung_fit_6_paare": {
            "haut": st["nachher"]["skin"] | {"dE2000_vorher_nur_LUT_mittel": st["vorher_nur_LUT"]["skin"]["dE2000_mittel"]},
            "dunkle_kleidung": st["nachher"]["dark"] | {"dE2000_vorher_nur_LUT_mittel": st["vorher_nur_LUT"]["dark"]["dE2000_mittel"]},
            **({"helles_hemd": st["nachher"]["bright"] | {"dE2000_vorher_nur_LUT_mittel": st["vorher_nur_LUT"]["bright"]["dE2000_mittel"]}} if "bright" in st["nachher"] else {}),
            "wand_FX3_Lab_nachher": st["nachher"]["wand_FX3_Lab"], "wand_FX3_Lab_vorher_nur_LUT": st["vorher_nur_LUT"]["wand_FX3_Lab"],
            "haut_dE2000_je_frame": [r["skin"]["dE2000"] for r in st["frames_nachher"]],
        },
        "hold_out_3_paare": {k: v for k, v in {"haut": hold_stats("skin"), "dunkle_kleidung": hold_stats("dark"), "helles_hemd": hold_stats("bright")}.items() if v},
        "gegenprobe_10bit_original_paar_2": {
            "haut_dE2000_FX3_vs_a7_auf_originalen": o["dE2000_FX3_vs_A7_auf_Originalen"],
            "haut_dE2000_original_vs_proxy_FX3": o["FX3"]["dE2000_original_vs_proxy"], "haut_dE2000_original_vs_proxy_a7": o["A7"]["dE2000_original_vs_proxy"]},
    }

d = {"Ludwig": fit["sets"]["Ludwig"], "Flammann": fit["sets"]["Flammann"], "Hein": fit["sets"]["Hein"]}
for person in d:
    fb, fa = d[person]["FX3_phys"], d[person]["A7_phys"]
    kameras[person]["deutung"] = {
        "a7_dunkler_als_FX3_blenden": round(fa["belichtung_blenden"] - fb["belichtung_blenden"], 2),
        "a7_waermer_rot_mehr_blenden": round(fb["wb_r_blenden"] - fa["wb_r_blenden"], 3),
        "a7_waermer_blau_weniger_blenden": round(fa["wb_b_blenden"] - fb["wb_b_blenden"], 3),
        "a7_kontrast_anhebung": fa["kontrast_delta"], "a7_saettigung_delta": fa["saettigung_delta"],
        "FX3_schatten_blau_neutralisiert": {"slope_delta_r": fb["schwarz_slope_delta_r"], "slope_delta_b": fb["schwarz_slope_delta_b"]},
        "FX3_belichtung_blenden": fb["belichtung_blenden"],
    }

br = fit["broll"]
out = {
    "titel": "Color-Grading-Vorschlag Taxodia Erklärvideo – Kamera-Angleich FX3/a7 IV + cleaner Look",
    "stand": "2026-09-15",
    "status": "Nur Analyse/Vorschlag. In Resolve wurde nichts geschrieben, auf dem NAS nichts veraendert.",
    "charge": "projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09",
    "resolve_projekt_laut_timeline_json": "Taxodia 09.26",
    "material": {
        "kameras_laut_sony_xml": {
            "FX3 (Kamera-B, V1, Ton)": "ILME-FX3, Sigma 24-70 F2.8 DG DN II, s-log3-cine / s-gamut3-cine, H.264 140 Mbit/s 4:2:2 10 Bit Long-GOP, 25p. Monitor-LUT laut XML: SL3SG3CtoR709-800.cube (in Resolve nicht vorhanden)",
            "a7 IV (Kamera-A, V2)": "ILCE-7M4, Tamron E 70-180 F2.8 A065, s-log3-cine / s-gamut3-cine, H.264 140 Mbit/s 4:2:2 10 Bit Long-GOP, 25p",
            "B-Roll": "ILME-FX3A, FE 24-70 F2.8 GM, s-log3-cine / s-gamut3-cine, H.264 200 Mbit/s 4:2:2 10 Bit Long-GOP, 50p",
        },
        "proxys": "H.264 Main 8 Bit 4:2:0 1920x1080 (Blackmagic Proxy Generator), getaggt bt709/tv, Inhalt ist S-Log3 (nicht gegradet).",
        "pegel_befund": "Originale sind als Full Range geflaggt. Der Proxy Generator hat sie als Full Range gelesen und nach Legal umgesetzt: Y8 = 16 + CV10*219/1023 (Fit rms 0,08). Ein Proxy, normal als TV-Range dekodiert, liefert also CV/1023 = genau das, was die Sony-LUTs ('full in full out') erwarten. Chroma im Proxy ca. 2 % flacher als im Original (betrifft alle Kameras gleich).",
    },
    "lut": {
        "empfohlen": LUT,
        "empfohlen_relativ_fuer_SetLUT": "Sony/SLog3SGamut3.CineToLC-709.cube",
        "details": "Sony LookProfile LUT v1.08.04, 33er Wuerfel, 'full in full out'; auf der Neutralachse der sauberste (kein Farbdrift bis 500 %).",
        "alternativen": {
            f"{LUTROOT}/Sony/SLog3SGamut3.CineToLC-709TypeA.cube": "33er, v1.04.04 – weicher, Schwarz angehoben, Lichter leicht magenta; im Vergleich milchiger (look_varianten.jpg, Spalte C)",
            f"{LUTROOT}/Sony/SLog3SGamut3.CineToCine+709.cube": "65er, v1.04.04 – kontrastreicher, Lichter warm (Blau faellt ab) = Stil-Farbstich",
            f"{LUTROOT}/Sony/SLog3SGamut3.CineToSLog2-709.cube": "33er – Legacy-Kurve",
            f"{LUTROOT}/Sony SLog3 to Rec709.ilut": "1D-Input-LUT nur Gamma, keine Gamut-Wandlung – nicht verwenden",
        },
        "kopien": "Identische Dateien (gleiche SHA-1) unter .../LUT/05_Davinci/Sony/",
    },
    "reihenfolge": {
        "grundsatz": "ALLE CDLs sind im S-Log3-Raum (normierter Codewert CV/1023) VOR dem LUT gerechnet. Der Look ist ebenfalls eine Log-CDL (Kontrast um 18 % Grau), kein Display-Grade nach dem LUT.",
        "variante_A_ein_node_empfohlen": "Node 1: SetCDL(Gesamt-CDL je Kamera/Set) + SetLUT(LC-709). Resolve wendet den Node-LUT am Ende des Nodes an, also CDL -> LUT. Vollstaendig per API setzbar (keine Node-Erzeugung noetig).",
        "variante_B_node_baum": "Node 1: Angleich-CDL (Log) -> Node 2: Look-CDL (Log) -> Node 3: nur LUT. Die API kann keine Nodes anlegen; Baum vorher im UI oder per DRX-Vorlage (Graph.ApplyGradeFromDRX) anlegen.",
        "komposition": f"Gesamt = Look(Angleich(x)): slope = k*slope_angleich, offset = k*offset_angleich + P*(1-k), saturation = sat_angleich*sat_look; P = 18-%-Grau in S-Log3 = {P:.4f}, k = {look['k']:.2f}. Exakt, weil Look-Slope/Offset je Kanal gleich und Power = 1.",
        "power": "Power ueberall 1.0 (robust gegen Unterschiede in Resolves Gamma-Umsetzung).",
        "farbmanagement_voraussetzung": "DaVinci YRGB ohne Color Management (bzw. keine Input-Transformation auf den Clips). Bei RCM/ACES gilt der Vorschlag so nicht.",
    },
    "look_cdl_global_log_vor_LUT": cdl_block(look_cdl, "Dezenter cleaner Look fuer alle Clips: Log-Kontrast 1,20 um 18 % Grau, Saettigung 1,03 – ergibt mit LC-709 neutrale Weissen, tiefes aber zeichnendes Schwarz, natuerliche Haut. In den Gesamt-CDLs bereits enthalten."),
    "look_ziele_final": {"haut_L*": fit["cfg"]["t_skin"], "helle_wand_L*": fit["cfg"]["t_wall"], "wand_a*b*": "0/0 (neutral)", "schwarzes_polo_a*b*": "0/0 (neutral)", "b_roll_haut_L*": fit["cfg"]["t_skin_broll"],
                        "hinweis": "Belichtung je Set = Kompromiss aus Haut- und Wand-Ziel (gleich gewichtet); FX3 bekommt keinen eigenen Kontrast, den setzt nur der Look."},
    "cdl_je_kamera_und_set": kameras,
    "b_roll_FX3A": {
        "clips": "alle C0235–C0262 aus broll_auswahl.json (50p)",
        "node1_gesamt_log_vor_LUT": cdl_block(br["FX3A_cdl_gesamt"], "Gemeinsame Basis fuer alle B-Roll-Shots, Node 1 mit LC-709-LUT."),
        "nur_angleich_log_vor_LUT": cdl_block(br["FX3A_cdl_angleich"], "Fuer Node-Baum (Angleich -> Look -> LUT)."),
        "physikalisch": br["FX3A_phys"],
        "deutung": "B-Roll rund 1 Blende heller (Gegenlicht-Szenen), warmes Innenlicht neutralisiert (Blau +0,24 Blende, Rot -0,12), FX3A-Schatten leicht entblaut. Stimmung bleibt dunkler als die Interviews.",
        "shots_Lab_vorher_nachher": br["shots"],
        "einzel_trims": "Szenen stark unterschiedlich: C0261/C0251/C0255 bleiben dunkel (Haut L* 25–30), C0259/C0235 hell (L* 47–52), C0262 Fenster clippt (Wand L* 96). Pro Shot +-0,3–0,5 Blende Offset nachtrimmen.",
    },
    "resolve_api": {
        "quelle": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/DaVinciResolveScript.pyi + README.md (Resolve 21.1, Stand 31.08./01.09.2026)",
        "grading": {
            "TimelineItem.GetNodeGraph": "def GetNodeGraph(self, layerIdx: int | None = None) -> Graph   (Z. 2506)",
            "Graph.GetNumNodes": "def GetNumNodes(self) -> int   (Z. 2692)",
            "Graph.SetLUT": "def SetLUT(self, nodeIndex: int, lutPath: str) -> bool   (Z. 2695; 1-basiert; README: Pfad absolut oder relativ zum LUT-Ordner, muss von Resolve entdeckt sein -> Project.RefreshLUTList)",
            "Graph.GetLUT": "def GetLUT(self, nodeIndex: int) -> str   (Z. 2698)",
            "TimelineItem.SetCDL": "def SetCDL(self, CDL: CDL) -> bool   (Z. 2449); CDL = TypedDict {NodeIndex: int, Slope: str 'r g b', Offset: str 'r g b', Power: str 'r g b', Saturation: float}   (Z. 146–156)",
            "Graph.GetNodeLabel / GetToolsInNode": "def GetNodeLabel(self, nodeIndex: int) -> str (Z. 2707); def GetToolsInNode(self, nodeIndex: int) -> list[str] (Z. 2710)",
            "Graph.SetNodeEnabled": "def SetNodeEnabled(self, nodeIndex: int, isEnabled: bool) -> bool   (Z. 2713)",
            "Graph.ApplyGradeFromDRX": "def ApplyGradeFromDRX(self, path: str, gradeMode: int) -> bool   (Z. 2719; 0 = ohne Keyframes, 1 = Quell-TC, 2 = Startframes)",
            "Graph.ResetAllGrades": "def ResetAllGrades(self) -> bool   (Z. 2722)",
            "TimelineItem.CopyGrades": "def CopyGrades(self, tgtTimelineItems: list[TimelineItem]) -> bool   (Z. 2473; kopiert den Grade der aktuellen Node-Stack-Ebene)",
            "TimelineItem.AddVersion / LoadVersionByName / GetCurrentVersion": "def AddVersion(self, versionName: str, versionType: int) -> bool (Z. 2443); def LoadVersionByName(self, versionName: str, versionType: int) -> bool (Z. 2440); def GetCurrentVersion(self) -> VersionInfo (Z. 2482) – eigene Farbversion anlegen = nicht-destruktiv",
            "TimelineItem.ExportLUT": "def ExportLUT(self, exportType: ExportLutType, path: str) -> bool   (Z. 2518; z. B. resolve.EXPORT_LUT_33PTCUBE – fuer Readback-Vergleich mit dieser Rechnung)",
            "Project.RefreshLUTList": "def RefreshLUTList(self) -> bool   (Z. 1846)",
            "Project.GetColorGroupsList / AddColorGroup / DeleteColorGroup": "def GetColorGroupsList(self) -> list[ColorGroup] (Z. 1861); def AddColorGroup(self, groupName: str) -> ColorGroup (Z. 1864); def DeleteColorGroup(self, colorGroup: ColorGroup) -> bool (Z. 1867)",
            "TimelineItem.AssignToColorGroup / GetColorGroup / RemoveFromColorGroup": "def AssignToColorGroup(self, colorGroup: ColorGroup) -> bool (Z. 2512); def GetColorGroup(self) -> ColorGroup | None (Z. 2509); def RemoveFromColorGroup(self) -> bool (Z. 2515)",
            "ColorGroup.GetPreClipNodeGraph / GetPostClipNodeGraph / GetClipsInTimeline": "def GetPreClipNodeGraph(self) -> Graph (Z. 2590); def GetPostClipNodeGraph(self) -> Graph (Z. 2593); def GetClipsInTimeline(self, timeline: Timeline | None = None) -> list[TimelineItem] (Z. 2587)",
            "Timeline.GetNodeGraph": "def GetNodeGraph(self) -> Graph   (Z. 2266; Timeline-Grade)",
            "Timeline.GrabStill + GalleryStillAlbum.ExportStills": "def GrabStill(self) -> GalleryStill (Z. 2206); def ExportStills(self, galleryStill: list[GalleryStill], folderPath: str, filePrefix: str, format: str) -> bool (Z. 2683) – DRX-Vorlage erzeugen",
            "Project.ExportCurrentFrameAsStill": "def ExportCurrentFrameAsStill(self, filePath: str) -> bool   (Z. 1858; Sichtkontrolle)",
            "MediaPoolItem.GetClipProperty": "def GetClipProperty(self, propertyName: str | None = None) -> str | ClipProperties   (Z. 2050; 'Data Level' = Auto/Full/Video, Z. 169; 'Input LUT', 'Input Color Space')",
        },
        "fehlt_in_der_api": [
            "Kein AddNode/InsertNode: Nodes koennen per Skript nicht angelegt werden (nur vorhandene per NodeIndex ansprechen, oder Baum per ApplyGradeFromDRX).",
            "SetCDL gibt es nur am TimelineItem (Clip-Graph). Color-Group-Pre/Post-Clip- und Timeline-Graphen koennen nur SetLUT/ApplyGradeFromDRX, keine CDL.",
            "Kein Zugriff auf Primaries/Kurven/Color-Space-Transform-OFX; keine dokumentierte Einstellung fuer die 3D-LUT-Interpolation.",
        ],
        "stabilize_und_speed": {
            "TimelineItem.Stabilize": "def Stabilize(self) -> bool   (Z. 2500; ohne Parameter, nutzt die Stabilizer-Einstellungen des Clips)",
            "TimelineItem.SmartReframe": "def SmartReframe(self) -> bool   (Z. 2503)",
            "TimelineItem.SetSpeed": "def SetSpeed(self, speedOptions: SpeedOptions) -> bool   (Z. 2386); SpeedOptions = {Percentage: float (0.0 = Standbild), PitchCorrection: bool, StretchKeyframesToFit: bool, RippleTimeline: bool} (Z. 947–955)",
            "TimelineItem.GetSpeed": "def GetSpeed(self) -> SpeedOptions   (Z. 2389)",
            "Retime-Qualitaet": "TimelineItem.SetProperties(properties: TimelineItemProperties) -> bool (Z. 2380) mit RetimeAndScalingEnabled, RetimeProcess = resolve.RETIME_USE_PROJECT/NEAREST/FRAME_BLEND/OPTICAL_FLOW, MotionEstimation = resolve.MOTION_EST_* (u. a. SPEED_WARP_BETTER) (Z. 1029–1033, 1431–1442)",
            "studio_notiz": "Laut Resolve-21.1-Notiz vom 09.09.: SetSpeed behaelt die Clip-Dauer (Laenge vorher/nachher pruefen).",
        },
    },
    "umsetzung_spaeter_nicht_ausgefuehrt": [
        "1. User gibt das Resolve-Projekt ausdruecklich frei; Projektname lesen und mit 'Taxodia 09.26' abgleichen (CLAUDE.md-Resolve-Regeln).",
        "2. Nur lesen: Project.GetSettings()['colorScienceMode'] (davinciYRGB, kein RCM), MediaPoolItem.GetClipProperty('Data Level') der Originale (Annahme hier: Full bzw. Auto = wie Proxy Generator), TimelineItem.GetNodeGraph().GetNumNodes().",
        "3. Project.RefreshLUTList(). Pro Clip eigene Version: TimelineItem.AddVersion('Claude Angleich v1', 0) + LoadVersionByName(...) – Grade des Users bleibt erhalten.",
        "4. Graph.SetLUT(1, 'Sony/SLog3SGamut3.CineToLC-709.cube'); TimelineItem.SetCDL({'NodeIndex': 1, ...Gesamt-CDL der Kamera/des Sets...}).",
        "5. Erst an EINEM Clip je Kamera: Readback GetLUT(1) + ExportLUT(resolve.EXPORT_LUT_33PTCUBE, '<_intern/color/readback_...cube>') und offline mit dieser Rechnung vergleichen (prueft SetCDL-Zuordnung und Reihenfolge CDL -> Node-LUT).",
        "6. Danach CopyGrades auf alle Items derselben Kamera/Person (FX3_0222/0223/0228, a7 0118/0119/0752, B-Roll C02xx). Optional Color Groups je Kamera/Set zur Ordnung.",
        "6a. Die Werte haengen am Quellclip und gelten fuer Rohschnitt- und Feinschnitt-Timeline gleichermassen (Feinschnitt laut feinschnitt.json: V1 = FX3, V2 = a7, V3 = B-Roll FX3A mit Speed 50 % und Stabilize). NICHT auf Grafik-/Alpha-Spuren (V4) anwenden.",
        "7. Am Ende die Timeline des Users wieder aktivieren; Bericht mit Projekt, Timeline, Anzahl gesetzter Clips.",
    ],
    "kontaktboegen": {
        "Ludwig": f"{OUT}/kontaktbogen_Ludwig.jpg",
        "Flammann": f"{OUT}/kontaktbogen_Flammann.jpg",
        "Hein": f"{OUT}/kontaktbogen_Hein.jpg",
        "B-Roll": f"{OUT}/kontaktbogen_BRoll.jpg",
        "Gesichter Ludwig": f"{OUT}/gesichter_Ludwig.jpg",
        "Gesichter Flammann": f"{OUT}/gesichter_Flammann.jpg",
        "Gesichter Hein": f"{OUT}/gesichter_Hein.jpg",
        "Übersicht final": f"{OUT}/uebersicht_final.jpg",
        "Look-Varianten": f"{OUT}/look_varianten.jpg",
        "spalten": "Kontaktboegen: Log roh | LC-709 | LC-709 + Angleich + Look, je FX3 und a7 nebeneinander, 6 zeitgleiche Paare",
    },
    "methode": {
        "frames": "Je Person 6 zeitgleiche Paare aus Timeline-Items mit Ueberlappung V1/V2 (Mitte der Ueberlappung), Sync geprueft: a7_frame = fx3_frame + offset (sync.json, 0223x0748 nicht genutzt); 3 Hold-out-Paare je Person (20 % in die Ueberlappung); 8 B-Roll-Shots aus verschiedenen Clips.",
        "messung": "Proxy -> S-Log3 (CV/1023) -> CDL -> LC-709 (trilinear) -> Rec.709/BT.1886 -> CIELAB. Gesichtsboxen per macOS Vision; Haut = innere Gesichtsbox + Hautfilter; dunkle Kleidung = dunkelste 30 % des Oberkoerpers; helles Hemd (nur Flammann) = hellste 25 % im Hemdbereich; Wand = helle, glatte, chromaarme Flaechen ausserhalb der Person (nur FX3 fuer den Neutralpunkt).",
        "fit": "Robuste Least-Squares je Set (soft-L1): FX3 = Neutralisierung Wand + schwarzes Polo, Belichtung Kompromiss Haut/Wand; a7 = Match auf korrigierte FX3 (Haut L*a*b*, dunkle Kleidung, Hemd), plus Belichtung, WB, Schatten-Slopes, Kontrast, Saettigung; alles regularisiert.",
        "ffmpeg_gegenprobe": "LUT per ffmpeg lut3d (trilinear) gegen numpy: mittlere Abweichung 0,0037 (< 1 Codewert 8 Bit).",
        "frames_fit": [{"id": m["id"], "beat": m["beat"], "FX3": f"{m['FX3']['clip']} Frame {m['FX3']['src_frame']}", "a7": f"{m['A7']['clip']} Frame {m['A7']['src_frame']}"} for m in man if "person" in m],
        "frames_hold_out": [{"id": m["id"], "beat": m["beat"], "FX3": f"{m['FX3']['clip']} Frame {m['FX3']['src_frame']}", "a7": f"{m['A7']['clip']} Frame {m['A7']['src_frame']}"} for m in manh],
        "frames_b_roll": [{"id": m["id"], "clip": m["clip"], "t_s": m["t_s"]} for m in man if "broll_nr" in m and m["id"] in br["shots"]],
        "skripte": f"{OUT}/skripte (extract -> lutjpg/faces -> measure -> fit cfg3.json -> sheets/compare -> holdout_* -> orig_check -> export_vorschlag)",
    },
    "grenzen": [
        "Messbasis 8-Bit-H.264-Proxys (4:2:0). Gegenprobe auf 10-Bit-Originalen (je Set 1 Paar): nach dem Grade Haut 0,6–1,2 dE2000 Abweichung Proxy vs. Original (Original minimal gelber, b* ca. +1); der A/B-Angleich haelt auf den Originalen (dE2000 FX3 vs. a7: Ludwig 1,64 / Flammann 1,25 / Hein 0,14).",
        "Pegel-Annahme: Resolve liest die full-range-geflaggten XAVC-Originale wie der Proxy Generator (CV/1023). Wird 'Data Level' auf Video gezwungen, verschieben sich Offsets und Schwarzwerte – vorher lesen.",
        "Nur statistisch angeglichen: Mittelwerte ueber Haut, dunkle Kleidung und (Flammann) Hemd auf 6 Paaren je Set, keine Pixelkorrespondenz (andere Winkel/Brennweiten). Einzelframes koennen durch Kopfhaltung/Lichtwinkel bis ca. 6 L* in der Gesichtshelligkeit abweichen (Ludwig #6, Ludwig H2), der Farbton liegt dort innerhalb ca. 1 dE.",
        "Hold-out nur teilweise unabhaengig (andere Zeitpunkte, teils in denselben Beats). Ergebnis: Haut 0,4–3,7 dE2000 (Mittel ca. 1,5), vorher 7,9–17,0.",
        "CDL kann keine gezielten Farbton-Drehungen: sensorbedingte Rest-Unterschiede bleiben (Flammanns hellblaues Hemd 0,8–1,2 dE2000, navy Blazer im Mittel 1,9, einzeln bis 3,8).",
        "a7 IV unterdrueckt Chroma in tiefen Schatten kameraintern (Cb/Cr ca. +-1/1023 im Original); deshalb wurden die blaustichigen FX3-Schatten neutralisiert statt die a7 einzufaerben.",
        "Die a7-Kontrastanhebung (+0,08 bis +0,11 im Log) gleicht vermutlich Streulicht des 70-180 gegen helle Hintergruende aus – sie wirkt global, nicht nur in den Schatten.",
        "SetCDL-Semantik und die Reihenfolge CDL -> Node-LUT sind nicht live in Resolve geprueft (Handbuch-Verhalten angenommen); vor dem Ausrollen per ExportLUT-Readback an einem Clip verifizieren. Rechnung mit trilinearer LUT-Interpolation.",
        "Look und Belichtungsziele (Haut L* 70, Wand L* 88) sind Geschmacksvorschlag; Flammanns Halle bleibt High-Key mit fast clippenden Waenden, Ludwigs Fenster clippt.",
        "B-Roll: eine CDL fuer alle FX3A-Shots, gemessen an 8 von 30 Shots; Gegenlicht-Szenen brauchen Einzel-Trims.",
        "Gesamt-CDL setzt DaVinci YRGB ohne Color Management voraus.",
    ],
    "protokoll_hinweis": "Protokoll.md der Charge wurde bewusst nicht fortgeschrieben (Schreibrecht nur _intern/color) – Eintrag durch die Hauptsession.",
}
json.dump(out, open(f"{OUT}/grading_vorschlag.json", "w"), ensure_ascii=False, indent=1)
print("geschrieben", f"{OUT}/grading_vorschlag.json")
