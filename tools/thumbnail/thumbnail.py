"""Thumbnail — saubere Standbilder aus fertigen Videos (Studio-Funktion „Thumbnail:“, nur auf Wunsch des Users).
Spec docs/superpowers/specs/2026-09-21-thumbnail-design.md · Ablauf tools/thumbnail/WORKFLOW-Thumbnail.md

Aufruf (autocut-venv, im Repo):
  thumbnail.py vorschlagen "<Charge>" --video "<Titel>" --exportordner "<…/04_Exportiert>"
               (--timeline "<Resolve-Timeline>" --projekt "<Resolve-Projekt>" | --datei <saubere Videodatei>) [--version V<n>]
      → sauberer Master, Prüfung gegen den Export, Kandidaten (jeder 5. Frame), Vision-Bewertung,
        Kontaktbogen _intern/thumbnails/<Video>_V<n>_kandidaten.jpg, Nachweis _intern/thumbnails/<Video>_V<n>.json
  thumbnail.py ablegen "<Charge>" --video "<Titel>" [--version V<n>] [--wahl <Frame,Frame,Frame>] [--grund "…"]
      → je Vorschlag JPG (lange Kante 1920) + _4K nach Ergebnisse/Thumbnails/<Video>/ und <Exportordner>/<Video>/Thumbnails/,
        nie überschreiben (Nummern zählen weiter), danach Master und Kandidaten löschen.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont

HIER = Path(__file__).resolve().parent
STUDIO = HIER.parents[1]
sys.path.insert(0, str(HIER))
import auswahl as A  # noqa: E402

SCHRITT = 5
BEWERTER = HIER / "bin" / "bewerten"
SCHRIFT = "/System/Library/Fonts/Helvetica.ttc"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def charge_pfad(charge: str) -> Path:
    p = Path(charge)
    return p if p.is_absolute() else STUDIO / p


def probe(datei: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_frames", "-of", "json", str(datei)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    z, n = s["r_frame_rate"].split("/")
    frames = int(s.get("nb_frames") or 0)
    if not frames:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                              "stream=nb_read_frames", "-of", "csv=p=0", str(datei)], capture_output=True, text=True, check=True)
        frames = int(out.stdout.strip())
    return {"breite": int(s["width"]), "hoehe": int(s["height"]), "fps": int(z) / int(n), "frames": frames}


def tc(frame: int, fps: float) -> str:
    f = int(round(fps))
    s = frame // f
    return f"00:{s // 60:02d}:{s % 60:02d}:{frame % f:02d}"


def bewerter() -> Path:
    quelle = HIER / "bewerten.swift"
    if not BEWERTER.exists() or BEWERTER.stat().st_mtime < quelle.stat().st_mtime:
        BEWERTER.parent.mkdir(exist_ok=True)
        subprocess.run(["swiftc", "-O", str(quelle), "-o", str(BEWERTER)], check=True)
    return BEWERTER


def lap_var(a: np.ndarray) -> float:
    if a.shape[0] < 5 or a.shape[1] < 5:
        return 0.0
    return float((a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]).var())


def frame_rgb(datei: Path, frame: int, fps: float) -> Image.Image:
    """Genau dieser Frame als RGB (BT.709 → sRGB-Werte). Suche per -ss knapp vor dem Frame (ProRes ist Intra-only)."""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, (frame - 0.25) / fps):.4f}", "-i", str(datei),
                          "-frames:v", "1", "-vf", "scale=iw:ih:in_color_matrix=bt709,format=rgb24",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")


def bildfolge(ordner: Path, muster: str) -> str:
    """Ausgabemuster für ffmpeg-image2: ein „%“ im Ordnernamen muss „%%“ sein (Titel „… Napoli 100%“, W&L 21.09.2026)."""
    return str(ordner).replace("%", "%%") + "/" + muster


def kandidaten_extrahieren(master: Path, ziel: Path) -> list[int]:
    """Jeder SCHRITT-te Frame als JPG, lange Kante 1920; Datei k_<i>.jpg ↔ Frame i·SCHRITT."""
    ziel.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(master), "-vf",
                    f"select='not(mod(n\\,{SCHRITT}))',scale='if(gt(iw,ih),1920,-2)':'if(gt(iw,ih),-2,1920)'"
                    ":flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt601:out_range=pc,format=yuvj420p",
                    "-fps_mode", "passthrough", "-q:v", "3", "-start_number", "0", bildfolge(ziel, "k_%05d.jpg")], check=True)
    return [int(p.stem[2:]) * SCHRITT for p in sorted(ziel.glob("k_*.jpg"))]


def bewerten_ordner(ordner: Path) -> dict[str, dict]:
    out = subprocess.run([str(bewerter()), str(ordner)], capture_output=True, text=True, check=True).stdout
    return {z["datei"]: z for z in (json.loads(l) for l in out.splitlines() if l.startswith("{"))}


def schaerfe(pfad: Path, gesicht: dict | None) -> float:
    im = Image.open(pfad).convert("L")
    w, h = im.size
    if gesicht:
        x0, y0, x1, y1 = gesicht["box"]
        dx, dy = (x1 - x0) * 0.1, (y1 - y0) * 0.1
        box = (max(0, int((x0 - dx) * w)), max(0, int((y0 - dy) * h)), min(w, int((x1 + dx) * w)), min(h, int((y1 + dy) * h)))
    else:
        box = (int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8))
    return lap_var(np.asarray(im.crop(box), dtype=np.float32))


def schnitte_aus_datei(datei: Path, frames: int) -> list[dict]:
    """Einstellungen einer Videodatei per ffmpeg scdet (Schwelle 10)."""
    err = subprocess.run(["ffmpeg", "-nostdin", "-nostats", "-i", str(datei), "-vf", "scdet=threshold=10", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    fps = probe(datei)["fps"]
    starts = sorted({0} | {int(round(float(t) * fps)) for t in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", err)})
    grenzen = starts + [frames]
    return [{"id": f"S{i}", "spur": None, "clip": None, "start": a, "ende": b} for i, (a, b) in enumerate(zip(grenzen, grenzen[1:])) if b > a]


def _grau(datei: Path, frames: list[int], breite: int = 270, hoehe: int = 480) -> list[np.ndarray]:
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(datei), "-vf", f"select='{sel}',scale={breite}:{hoehe},format=gray",
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return [np.frombuffer(raw[i * breite * hoehe:(i + 1) * breite * hoehe], np.uint8) for i in range(len(raw) // (breite * hoehe))]


def ssim_je_frame(sauber: Path, export: Path, frames: list[int]) -> list[float]:
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    with tempfile.TemporaryDirectory() as tmp:
        stats = Path(tmp) / "ssim.txt"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(sauber), "-i", str(export), "-lavfi",
                        f"[0:v]select='{sel}',scale=1080:1920:flags=lanczos,format=yuv420p,setpts=N/TB[a];"
                        f"[1:v]select='{sel}',scale=1080:1920:flags=lanczos,format=yuv420p,setpts=N/TB[b];"
                        f"[a][b]ssim=stats_file={stats}", "-f", "null", "-"], check=True)
        return [float(re.search(r"All:([0-9.]+)", z).group(1)) for z in stats.read_text(encoding="utf-8").splitlines() if "All:" in z]


def pruefen(master: Path, export: Path | None, overlays: list[dict] | None, frames: int, fps: float) -> dict:
    """Quelle = Video (Spec „Prüfung“) und Detail-Faktor. Bricht bei Abweichung ab."""
    p: dict = {}
    if export and export.exists():
        ef = probe(export)["frames"]
        if ef != frames:
            raise SystemExit(f"Export {export.name} hat {ef} Frames, die Quelle {frames} — Version/Timeline prüfen.")
        belegt = set()
        for o in overlays or []:
            belegt.update(range(o["start"], o["ende"]))
        frei = [f for f in range(frames) if f not in belegt] if overlays is not None else []
        if frei:
            probe_frames = sorted({frei[int(i * (len(frei) - 1) / 7)] for i in range(8)})
            werte = ssim_je_frame(master, export, probe_frames)
            med = float(np.median(werte))
            p.update(art="freie Frames", frames=probe_frames, ssim=[round(w, 4) for w in werte], median=round(med, 4))
            if med < 0.95:
                raise SystemExit(f"Saubere Quelle weicht vom Export ab (SSIM-Median {med:.3f} < 0,95 in freien Frames).")
        else:
            probe_frames = [int(i * (frames - 1) / 11) for i in range(12)]
            werte = ssim_je_frame(master, export, probe_frames)
            a, b = _grau(master, probe_frames), _grau(export, probe_frames)
            luma = float(np.mean([abs(x.mean() - y.mean()) / max(y.mean(), 1) for x, y in zip(a, b)]))
            med = float(np.median(werte))
            p.update(art="alle Frames", frames=probe_frames, ssim=[round(w, 4) for w in werte], median=round(med, 4),
                     luma_abweichung=round(luma, 4))
            if med < 0.80 or luma > 0.03:
                raise SystemExit(f"Saubere Quelle weicht vom Export ab (SSIM-Median {med:.3f}, Luma {luma:.1%}).")
    else:
        p["art"] = "kein Export zum Vergleich"
    detail = []
    for f in (int(frames * 0.3), int(frames * 0.5), int(frames * 0.7)):
        g = np.asarray(frame_rgb(master, f, fps).convert("L"), dtype=np.float32)
        h, w = g.shape
        c = g[int(h * 0.1):int(h * 0.5), int(w * 0.25):int(w * 0.75)]
        ci = Image.fromarray(c.astype(np.uint8))
        du = np.asarray(ci.resize((ci.width // 2, ci.height // 2), Image.LANCZOS).resize(ci.size, Image.LANCZOS), dtype=np.float32)
        detail.append(round(lap_var(c) / max(lap_var(du), 1e-6), 2))
    p["detail_faktor"] = detail
    if min(detail) < 1.15:
        p["warnung"] = "Detail-Faktor < 1,15 — womöglich aus Proxys gerendert"
    return p


def kontaktbogen(bogen: list[dict], vorschlaege: list[dict], kand_dir: Path, ziel: Path, titel: str) -> None:
    W, H, spalten, kopf, text_h = 270, 480, 6, 56, 74
    zeilen = -(-len(bogen) // spalten)
    b = Image.new("RGB", (W * spalten, kopf + zeilen * (H + text_h)), (18, 18, 18))
    d = ImageDraw.Draw(b)
    gross, klein = ImageFont.truetype(SCHRIFT, 24), ImageFont.truetype(SCHRIFT, 16)
    d.text((10, 14), f"{titel} — Kandidaten (rot = Vorschlag)", font=gross, fill=(240, 240, 240))
    for i, k in enumerate(bogen):
        x, y = (i % spalten) * W, kopf + (i // spalten) * (H + text_h)
        b.paste(Image.open(kand_dir / f"k_{k['frame'] // SCHRITT:05d}.jpg").resize((W, H), Image.LANCZOS), (x, y))
        nr = next((j + 1 for j, v in enumerate(vorschlaege) if v["frame"] == k["frame"]), None)
        if nr:
            d.rectangle([x + 1, y + 1, x + W - 2, y + H - 2], outline=(227, 6, 19), width=5)
            d.text((x + 10, y + 8), f"_{nr}", font=gross, fill=(227, 6, 19))
        g = A.hauptgesicht(k.get("gesichter") or [])
        q = f"Q {g['qualitaet']:.2f}" if g and g.get("qualitaet") is not None else "Q –"
        d.text((x + 6, y + H + 4), f"#{k['frame']}  {k['tc']}  {k['art']}", font=klein, fill=(235, 235, 235))
        d.text((x + 6, y + H + 24), f"P {k['punkte']:.2f} · Ä {k['aesthetik']:.2f} · {q} · S {k['schaerfe_n']:.2f}", font=klein, fill=(200, 200, 200))
        d.text((x + 6, y + H + 44), ", ".join(k["gruende"])[:40], font=klein, fill=(255, 150, 120))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    b.save(ziel, quality=88)


def vorschlagen(a: argparse.Namespace) -> None:
    charge = charge_pfad(a.charge)
    intern = charge / "_intern" / "thumbnails"
    work = intern / "work"
    video_ordner = Path(a.exportordner) / a.video
    version = a.version or A.hoechste_version([p.name for p in video_ordner.glob("*.mp4")], a.video)
    if not version:
        raise SystemExit(f"Keine Exportversion in {video_ordner} — --version angeben.")
    basis = f"{a.video}_{version}"
    nachweis_pfad = intern / f"{basis}.json"
    if nachweis_pfad.exists():
        alt = json.loads(nachweis_pfad.read_text(encoding="utf-8"))
        if not alt.get("abgelegt"):
            raise SystemExit(f"Offene Runde für {basis} (Nachweis ohne Ablage) — erst ablegen oder den Nachweis prüfen.")
        nachweis_pfad.rename(intern / f"{basis}_bis_{time.strftime('%Y-%m-%d_%H%M')}.json")
    t0 = time.time()
    if a.timeline:
        import resolve_sauber as R
        if not a.projekt:
            raise SystemExit("--timeline braucht --projekt (exakter Name des freigegebenen Resolve-Projekts).")
        quelle = R.sauberer_master(a.projekt, a.timeline, a.video, work)
        master, segmente, overlays = Path(quelle["master"]), quelle["einstellungen"], quelle["overlays"]
    else:
        master = Path(a.datei)
        quelle, overlays = {"datei": str(master)}, None
        segmente = schnitte_aus_datei(master, probe(master)["frames"])
    info = probe(master)
    fps, frames = info["fps"], info["frames"]
    try:
        pruefung = pruefen(master, video_ordner / f"{basis}.mp4", overlays, frames, fps)
    except SystemExit:
        if a.timeline:
            master.unlink(missing_ok=True)   # eigener Master dieses Laufs; die Quelle stimmt nicht, also weg
        raise
    kand_dir = work / f"{basis}_kandidaten"
    if kand_dir.exists():
        shutil.rmtree(kand_dir)
    nummern = kandidaten_extrahieren(master, kand_dir)
    bew = bewerten_ordner(kand_dir)
    schnitte = sorted({s["start"] for s in segmente if s["start"] > 0})
    kandidaten = []
    for f in nummern:
        datei = f"k_{f // SCHRITT:05d}.jpg"
        b = bew.get(datei) or {"fehler": "fehlt"}
        if "fehler" in b:
            continue
        gross = [g for g in b.get("gesichter", []) if g["box"][3] - g["box"][1] >= A.GESICHT_MIN_HOEHE]
        kandidaten.append({"frame": f, "zeit_s": round(f / fps, 2), "tc": tc(f, fps), "shot": A.shot_von(f, segmente),
                           "nahe_schnitt": A.nahe_schnitt(f, schnitte), "aesthetik": b.get("aesthetik") or 0.0,
                           "utility": bool(b.get("utility")), "gesichter": b.get("gesichter", []),
                           "schaerfe": round(schaerfe(kand_dir / datei, A.hauptgesicht(gross)), 2)})
    for k, n in zip(kandidaten, A.rang_normiert([k["schaerfe"] for k in kandidaten])):
        k["schaerfe_n"] = round(n, 4)
        A.bewerte(k)
    vorschlaege = A.waehle(kandidaten, fps)
    bogen_pfad = intern / f"{basis}_kandidaten.jpg"
    kontaktbogen(A.fuer_bogen(kandidaten, vorschlaege, fps), vorschlaege, kand_dir, bogen_pfad, f"{a.video} {version}")
    nachweis = {"video": a.video, "version": version, "charge": str(a.charge), "exportordner": str(a.exportordner),
                "angelegt": time.strftime("%Y-%m-%d %H:%M"), "quelle": {k: v for k, v in quelle.items() if k != "einstellungen"},
                "master": str(master), "master_eigen": bool(a.timeline), "fps": fps, "frames": frames,
                "aufloesung": [info["breite"], info["hoehe"]], "einstellungen": segmente, "pruefung": pruefung,
                "kandidaten": kandidaten, "vorschlaege": [v["frame"] for v in vorschlaege], "kandidaten_ordner": str(kand_dir),
                "kontaktbogen": str(bogen_pfad), "dauer_s": round(time.time() - t0, 1), "abgelegt": None}
    intern.mkdir(parents=True, exist_ok=True)
    nachweis_pfad.write_text(json.dumps(nachweis, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"video": a.video, "version": version, "kandidaten": len(kandidaten), "vorschlaege": nachweis["vorschlaege"],
                      "pruefung": pruefung, "kontaktbogen": str(bogen_pfad), "nachweis": str(nachweis_pfad),
                      "dauer_s": nachweis["dauer_s"]}, ensure_ascii=False, default=str))


def speichern(bild: Image.Image, ziel: Path, lange_kante: int | None) -> None:
    if lange_kante and max(bild.size) != lange_kante:
        f = lange_kante / max(bild.size)
        bild = bild.resize((round(bild.width * f), round(bild.height * f)), Image.LANCZOS)
    bild.save(ziel, "JPEG", quality=92, optimize=True, icc_profile=SRGB, subsampling=0)


def ablegen(a: argparse.Namespace) -> None:
    charge = charge_pfad(a.charge)
    intern = charge / "_intern" / "thumbnails"
    kandidaten_json = [p for p in intern.glob(f"{a.video}_V*.json") if "_bis_" not in p.name]
    if a.version:
        nachweis_pfad = intern / f"{a.video}_{a.version}.json"
    elif kandidaten_json:
        nachweis_pfad = max(kandidaten_json, key=lambda p: int(re.search(r"_V(\d+)\.json$", p.name).group(1)))
    else:
        raise SystemExit(f"Kein Nachweis für {a.video} — erst vorschlagen.")
    n = json.loads(nachweis_pfad.read_text(encoding="utf-8"))
    if n.get("abgelegt"):
        raise SystemExit(f"{nachweis_pfad.name} ist schon abgelegt — für neue Bilder erst vorschlagen.")
    master = Path(n["master"])
    if not master.exists():
        raise SystemExit(f"Master fehlt: {master}")
    wahl = [int(x) for x in a.wahl.split(",")] if a.wahl else n["vorschlaege"]
    if any(not 0 <= f < n["frames"] for f in wahl):
        raise SystemExit(f"Frame außerhalb 0–{n['frames'] - 1}: {wahl}")
    studio_dir = charge / "Ergebnisse" / "Thumbnails" / a.video
    nas_dir = Path(n["exportordner"]) / a.video / "Thumbnails"
    studio_dir.mkdir(parents=True, exist_ok=True)
    nas_dir.mkdir(parents=True, exist_ok=True)
    vorhanden = [p.name for d in (studio_dir, nas_dir) for p in d.iterdir()]
    start = A.naechste_nummer(vorhanden, a.video, n["version"])
    kand = {k["frame"]: k for k in n["kandidaten"]}
    abgelegt = []
    for i, f in enumerate(wahl):
        bild = frame_rgb(master, f, n["fps"])
        varianten = [(False, 1920)] + ([(True, None)] if max(bild.size) > 1920 else [])
        for vier_k, kante in varianten:
            name = A.dateiname(a.video, n["version"], start + i, vier_k)
            lokal, fern = studio_dir / name, nas_dir / name
            if lokal.exists() or fern.exists():
                raise SystemExit(f"{name} existiert schon — nichts überschrieben.")
            speichern(bild, lokal, kante)
            subprocess.run(["cp", "-n", str(lokal), str(fern)], check=True)
            if subprocess.run(["cmp", "-s", str(lokal), str(fern)]).returncode != 0:
                raise SystemExit(f"NAS-Kopie von {name} weicht ab.")
            with Image.open(lokal) as im:
                abgelegt.append({"datei": name, "frame": f, "tc": tc(f, n["fps"]), "groesse": list(im.size),
                                 "kb": round(lokal.stat().st_size / 1024), "punkte": (kand.get(f) or {}).get("punkte"),
                                 "art": (kand.get(f) or {}).get("art")})
    n["abgelegt"] = {"am": time.strftime("%Y-%m-%d %H:%M"), "wahl": wahl, "grund": a.grund,
                     "studio": str(studio_dir), "nas": str(nas_dir), "dateien": abgelegt}
    if n.get("master_eigen"):
        master.unlink()
    shutil.rmtree(n["kandidaten_ordner"], ignore_errors=True)
    nachweis_pfad.write_text(json.dumps(n, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(n["abgelegt"], ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="befehl", required=True)
    v = sub.add_parser("vorschlagen")
    v.add_argument("charge")
    v.add_argument("--video", required=True)
    v.add_argument("--exportordner", required=True)
    v.add_argument("--timeline")
    v.add_argument("--projekt")
    v.add_argument("--datei")
    v.add_argument("--version")
    ab = sub.add_parser("ablegen")
    ab.add_argument("charge")
    ab.add_argument("--video", required=True)
    ab.add_argument("--version")
    ab.add_argument("--wahl")
    ab.add_argument("--grund")
    a = ap.parse_args()
    if a.befehl == "vorschlagen":
        if bool(a.timeline) == bool(a.datei):
            raise SystemExit("Genau eine Quelle angeben: --timeline (mit --projekt) oder --datei.")
        vorschlagen(a)
    else:
        ablegen(a)


if __name__ == "__main__":
    main()
