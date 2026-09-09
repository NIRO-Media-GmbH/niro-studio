"""Berichte für ``Ergebnisse/Rohschnitt/`` (Markdown) und die Zeilen für den Protokoll-Eintrag.

Drei Berichte (Spec 3.5 Punkt 7, Spec 4, Spec 5):
- ``render_rohschnitt``  → ``<video>-rohschnitt.md``: Beat-Tabelle (Nr, Szene, Quelle dreiteilig, Position,
  Dauer, V2 ja/nein), Sync-Tabelle, Warnungen, Hinweise, Sperren, Gesamtlänge.
- ``render_broll_index`` → ``broll-index.md``: Übersicht je Motiv-Ordner, dann je Standort/Ordner eine Zeile pro Clip.
- ``render_broll_plan``  → ``<video>-broll.md``: pro Beat die gewählten Clips, Grund, Abweichung.

Alle Renderer sind reine Funktionen auf Dictionaries/Dataclasses und robust gegen fehlende Felder („–“).
Geschrieben wird nur über ``write_report`` — ausschließlich nach ``<Charge>/Ergebnisse/Rohschnitt/``.
Quellen-Schreibweise nach Cutter-Standard: ``Person (Rolle) · Datei · mm:ss–mm:ss``.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .charge import AutoCutError, Charge
from .cutlist import Beat, Cutlist
from .timeline_model import TimelinePlan

TYP_LABEL = {"oton": "O-Ton", "vo": "VO", "bild": "Bild", "grafik": "Grafik"}
PLATZHALTER_TYPEN = ("vo", "bild", "grafik")


# --------------------------------------------------------------------------- #
# Formatierung
# --------------------------------------------------------------------------- #

def fmt_tc(frames: int, fps: float) -> str:
    """Frames → „mm:ss:ff“ (Minuten laufen über 59 hinaus; negative Werte mit Vorzeichen)."""
    fpi = max(1, int(round(float(fps))))
    n = int(frames)
    sign = "-" if n < 0 else ""
    n = abs(n)
    sec, ff = divmod(n, fpi)
    mm, ss = divmod(sec, 60)
    return f"{sign}{mm:02d}:{ss:02d}:{ff:02d}"


def fmt_mmss(seconds: float) -> str:
    """Sekunden → „mm:ss“, auf ganze Sekunden gerundet (Gesamtlängen, Ziellängen)."""
    n = max(0, int(round(float(seconds))))
    mm, ss = divmod(n, 60)
    return f"{mm:02d}:{ss:02d}"


def _mmss_floor(seconds: float) -> str:
    """Sekunden → „mm:ss“ abgeschnitten — so stehen Timecodes im Cutter-Plan (Wortanfang)."""
    n = max(0, int(float(seconds)))
    mm, ss = divmod(n, 60)
    return f"{mm:02d}:{ss:02d}"


def _sek(x: float, nk: int = 1, sign: bool = False) -> str:
    """Sekunden mit Komma, z. B. „2,9 s“ / „+2,000 s“."""
    fmt = f"{{:{'+' if sign else ''}.{nk}f}}"
    return fmt.format(float(x)).replace(".", ",") + " s"


def _zahl(x, nk: int = 1) -> str:
    """Zahl mit Komma; ganze Zahlen ohne Nachkommastellen („3“, „8,5“); None → „–“."""
    if x is None:
        return "–"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return _md(x)
    if v.is_integer():
        return str(int(v))
    return f"{v:.{nk}f}".replace(".", ",")


def _md(s) -> str:
    """Text tabellentauglich machen: Pipes und Zeilenumbrüche entschärfen, leer → „–“."""
    t = str(s if s is not None else "").replace("|", "/").replace("\r", " ").replace("\n", " ").strip()
    return t or "–"


def _name(path) -> str:
    return Path(str(path)).name if path else "–"


def _liste(items) -> str:
    return _md(", ".join(str(x) for x in (items or []) if str(x).strip()))


def _warnungen(d, key: str = "warnings") -> list[str]:
    v = (d or {}).get(key) if isinstance(d, dict) else None
    return [str(x) for x in (v or [])]


# --------------------------------------------------------------------------- #
# Rohschnitt-Bericht
# --------------------------------------------------------------------------- #

def _quelle(b: Beat) -> str:
    """Quelle dreiteilig: Person (Rolle) · Datei · mm:ss–mm:ss [+ weitere Teilschnitte]; Platzhalter mit Text/Bild."""
    if b.typ == "oton":
        person = b.person or "–"
        if b.rolle:
            person += f" ({b.rolle})"
        spans = " + ".join(f"{_mmss_floor(c.in_s)}–{_mmss_floor(c.out_s)}" for c in b.cuts) or "–"
        return _md(f"{person} · {_name(b.clip)} · {spans}")
    teile = [f"Platzhalter {TYP_LABEL.get(b.typ, b.typ)}"]
    if b.text:
        teile[0] += f": {b.text}"
    if b.bild_hinweis:
        teile.append(f"Bild: {b.bild_hinweis}")
    return _md(" · ".join(teile))


def _dauer(rec_in_f: int | None, rec_out_f: int | None, fps: float, plan_dauer_s: float | None) -> str:
    if rec_in_f is None or rec_out_f is None:
        return "–"
    s = _sek((rec_out_f - rec_in_f) / fps)
    if plan_dauer_s:
        s += f" (Plan ~{_zahl(plan_dauer_s)} s)"
    return s


def _v2_beats(tp: TimelinePlan) -> set[str]:
    return {i.beat_nr for i in tp.items if i.track == "V2" and i.enabled}


def _paare_genutzt(tp: TimelinePlan) -> dict[tuple[str, str], list[str]]:
    """(FX3-Clip, a7-Clip) → Beat-Nummern, deren V2-Item aus diesem Paar stammt."""
    ref_of = {bp.nr: bp.clip for bp in tp.beats}
    out: dict[tuple[str, str], list[str]] = {}
    for it in tp.items:
        if it.track != "V2":
            continue
        ref = ref_of.get(it.beat_nr)
        if not ref:
            continue
        nrs = out.setdefault((ref, it.clip), [])
        if it.beat_nr not in nrs:
            nrs.append(it.beat_nr)
    return out


def _ordner_of(media: dict, clip: str) -> str:
    rec = ((media or {}).get("clips") or {}).get(clip) if isinstance(media, dict) else None
    if isinstance(rec, dict) and rec.get("ordner"):
        return str(rec["ordner"])
    return Path(clip).parent.name or "–"


def _kopf_rohschnitt(cl: Cutlist, tp: TimelinePlan, build: dict, media: dict) -> list[str]:
    fmt = (media or {}).get("format") if isinstance(media, dict) else None
    fmt = fmt if isinstance(fmt, dict) else {}
    fps = float(fmt.get("fps") or tp.fps)
    w, h = fmt.get("width") or tp.width, fmt.get("height") or tp.height
    orient = fmt.get("orientation") or cl.format or "–"
    laenge_s = tp.total_frames / tp.fps if tp.fps else 0.0
    if cl.ziel_laenge_s:
        abw = (laenge_s - float(cl.ziel_laenge_s)) / float(cl.ziel_laenge_s) * 100
        ziel = f"{fmt_mmss(cl.ziel_laenge_s)} · Abweichung: {abw:+.0f} %".replace("-", "−")
    else:
        ziel = "–"
    n_oton = sum(1 for b in cl.beats if b.typ == "oton")
    n_platz = len(cl.beats) - n_oton
    n_v2 = len(_v2_beats(tp) & {b.nr for b in cl.beats if b.typ == "oton"})
    stand = (build or {}).get("gebaut_am") if isinstance(build, dict) else None
    stand = stand or _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    timeline = (build or {}).get("timeline") if isinstance(build, dict) else None
    return [f"# Rohschnitt {cl.video}", "",
            f"- Timeline: {_md(timeline)}",
            f"- Format: {w}×{h}, {_zahl(fps, 3)} fps ({orient})",
            f"- Gesamtlänge: {fmt_mmss(laenge_s)} ({tp.total_frames} Frames) · Ziellänge: {ziel}",
            f"- Beats: {len(cl.beats)} ({n_oton} O-Ton, {n_platz} Platzhalter) · V2 (a7IV): {n_v2} von {n_oton} O-Ton-Beats",
            f"- Stand: {stand}", ""]


def _beat_tabelle(cl: Cutlist, tp: TimelinePlan) -> list[str]:
    pos = {bp.nr: bp for bp in tp.beats}
    v2 = _v2_beats(tp)
    lines = ["## Beats", "",
             "| Nr | Szene | Typ | Quelle | Position | Dauer | V2 |",
             "|---|---|---|---|---|---|---|"]
    for b in cl.beats:
        bp = pos.get(b.nr)
        position = f"{fmt_tc(bp.rec_in_f, tp.fps)}–{fmt_tc(bp.rec_out_f, tp.fps)}" if bp else "–"
        dauer = _dauer(bp.rec_in_f if bp else None, bp.rec_out_f if bp else None, tp.fps, b.plan_dauer_s)
        if b.typ == "oton":
            v2_txt = "ja" if b.nr in v2 else "nein"
        else:
            v2_txt = "–"
        lines.append(f"| {_md(b.nr)} | {_md(b.szene)} | {TYP_LABEL.get(b.typ, _md(b.typ))} | {_quelle(b)} | "
                     f"{position} | {dauer} | {v2_txt} |")
    lines.append("")
    return lines


def _sync_tabelle(tp: TimelinePlan, sync: dict, media: dict) -> list[str]:
    paare = (sync or {}).get("paare") if isinstance(sync, dict) else None
    lines = ["## Sync (FX3 × a7IV)", ""]
    if not paare:
        lines += ["Keine Sync-Paare (sync.json fehlt oder leer) — V2 bleibt leer. `autocut_sync.py` ausführen.", ""]
        return lines
    genutzt = _paare_genutzt(tp)
    lines += ["| Ordner | FX3 | a7IV | Versatz | Sekunden | Konfidenz | Überlappung | Drift | Beats | Status |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for p in paare:
        ref, other = str(p.get("ref") or ""), str(p.get("other") or "")
        try:
            off_f = f"{int(p.get('offset_frames', 0)):+d}"
            off_s = _sek(float(p.get("offset_s", 0.0)), 3, sign=True)
        except (TypeError, ValueError):
            off_f, off_s = "–", "–"
        try:
            conf = f"{float(p.get('confidence', 0.0)):.1f}".replace(".", ",")
        except (TypeError, ValueError):
            conf = "–"
        ov = p.get("overlap_ref") or []
        ueberl = f"{_mmss_floor(ov[0])}–{_mmss_floor(ov[1])}" if len(ov) >= 2 else "–"
        try:
            drift = f"{float(p.get('drift_frames', 0.0)):.2f}".replace(".", ",")
        except (TypeError, ValueError):
            drift = "–"
        beats = ", ".join(genutzt.get((ref, other), [])) or "–"
        if p.get("ok"):
            status = "ok"
        else:
            status = "nicht ok" + (f" — {_md(p.get('note'))}" if p.get("note") else "")
        lines.append(f"| {_md(_ordner_of(media, ref))} | {_md(_name(ref))} | {_md(_name(other))} | {off_f} | {off_s} | "
                     f"{conf} | {ueberl} | {drift} | {beats} | {status} |")
    lines.append("")
    return lines


def _warnliste(tp: TimelinePlan, build: dict, verify: dict) -> list[str]:
    """Alle Warnungen eines Laufs: Prüfung (Fehler + Warnungen), Bau, rote Marker der Timeline."""
    out: list[str] = []
    out += [f"Prüfung (Fehler): {e}" for e in _warnungen(verify, "errors")]
    out += [f"Prüfung: {w}" for w in _warnungen(verify)]
    out += [f"Bau: {w}" for w in _warnungen(build)]
    for m in tp.markers:
        if m.color == "Red":
            out.append(f"Marker {fmt_tc(m.frame, tp.fps)}: {m.name}" + (f" — {m.note}" if m.note else ""))
    return out


def render_rohschnitt(cl: Cutlist, tp: TimelinePlan, sync: dict, build: dict, verify: dict, media: dict) -> str:
    """Markdown-Bericht des Rohschnitts (Spec 3.5, Punkt 7). Alle Eingaben außer cl/tp dürfen leer sein."""
    lines = _kopf_rohschnitt(cl, tp, build, media)
    lines += _beat_tabelle(cl, tp)
    lines += _sync_tabelle(tp, sync, media)
    warn = _warnliste(tp, build, verify)
    lines += ["## Warnungen", ""]
    lines += [f"- {_md(w)}" for w in warn] if warn else ["Keine Warnungen."]
    lines.append("")
    if cl.hinweise:
        lines += ["## Hinweise aus der Cutlist", ""] + [f"- {_md(h)}" for h in cl.hinweise] + [""]
    if cl.sperren:
        lines += ["## Sperren", ""]
        for s in cl.sperren:
            lines.append(f"- {_md(_name(s.clip))} {_mmss_floor(s.von_s)}–{_mmss_floor(s.bis_s)}"
                         + (f" — {_md(s.grund)}" if s.grund else ""))
        lines.append("")
    return "\n".join(lines)


def protokoll_zeilen_rohschnitt(cl: Cutlist, tp: TimelinePlan, build: dict, verify: dict,
                                report_path: str | Path) -> list[str]:
    """Zeilen für ``append_protokoll(charge, "Rohschnitt", zeilen)`` nach einem Bau."""
    laenge_s = tp.total_frames / tp.fps if tp.fps else 0.0
    ziel = fmt_mmss(cl.ziel_laenge_s) if cl.ziel_laenge_s else "–"
    n_oton = sum(1 for b in cl.beats if b.typ == "oton")
    n_v2 = len(_v2_beats(tp) & {b.nr for b in cl.beats if b.typ == "oton"})
    n_warn = len(_warnliste(tp, build, verify))
    timeline = (build or {}).get("timeline") if isinstance(build, dict) else None
    return [f"Timeline „{timeline or '–'}“ gebaut aus {cl.video}: {len(cl.beats)} Beats, Länge {fmt_mmss(laenge_s)} (Ziel {ziel})",
            f"V2 (a7IV): {n_v2} von {n_oton} O-Ton-Beats",
            f"{n_warn} Warnungen (siehe Bericht)" if n_warn else "Keine Warnungen",
            f"Bericht: {report_path}"]


# --------------------------------------------------------------------------- #
# B-Roll-Index
# --------------------------------------------------------------------------- #

def _verwendbare_abschnitte(clip: dict) -> list[dict]:
    return [a for a in (clip.get("abschnitte") or []) if isinstance(a, dict) and a.get("verwendbar")]


def _abschnitte_txt(abschnitte: list[dict]) -> str:
    return _md("; ".join(f"{_zahl(a.get('von_s'))}–{_zahl(a.get('bis_s'))} s" for a in abschnitte))


def _clip_key(c: dict) -> str:
    return str(c.get("datei") or _name(c.get("path") or c.get("pfad")))


def render_broll_index(index: dict) -> str:
    """Markdown-Bericht des B-Roll-Index (Spec 4): Übersicht je Ordner, dann je Standort/Ordner eine Zeile pro Clip."""
    index = index if isinstance(index, dict) else {}
    clips = [c for c in (index.get("clips") or []) if isinstance(c, dict)]
    fehler = [str(f) for f in (index.get("fehler") or [])]
    lines = ["# B-Roll-Index", "",
             f"Stand: {_md(index.get('erstellt_am'))} · Modell: {_md(index.get('modell'))} · "
             f"Clips: {index.get('anzahl', len(clips))} · Fehler: {len(fehler)}", ""]
    if not clips:
        lines += ["Keine Clips im Index — `autocut_index_broll.py` ausführen.", ""]
    else:
        groups: dict[str, dict[str, list[dict]]] = {}
        for c in clips:
            standort = str(c.get("standort") or "Ohne Standort")
            ordner = str(c.get("ordner") or "(Wurzel)")
            groups.setdefault(standort, {}).setdefault(ordner, []).append(c)
        standorte = sorted(groups, key=lambda s: (s == "Ohne Standort", s))
        lines += ["## Übersicht", "", "| Ordner | Standort | Clips | verwendbar | Ø Qualität |", "|---|---|---|---|---|"]
        for standort in standorte:
            for ordner in sorted(groups[standort]):
                rows = groups[standort][ordner]
                quali = [float(c["qualitaet_gesamt"]) for c in rows if isinstance(c.get("qualitaet_gesamt"), (int, float))]
                q = f"{sum(quali) / len(quali):.1f}".replace(".", ",") if quali else "–"
                lines.append(f"| {_md(ordner)} | {_md(standort)} | {len(rows)} | "
                             f"{sum(1 for c in rows if _verwendbare_abschnitte(c))} | {q} |")
        lines.append("")
        for standort in standorte:
            lines += [f"## {standort}", ""]
            for ordner in sorted(groups[standort]):
                rows = groups[standort][ordner]
                lines += [f"### {ordner} ({len(rows)} Clips)", "",
                          "| Datei | Dauer | Einstellung | Kamera | Kurzbeschreibung | Q | Abschn. | verwendbar (s) | Mängel | Tags |",
                          "|---|---|---|---|---|---|---|---|---|---|"]
                for c in sorted(rows, key=_clip_key):
                    abschnitte = [a for a in (c.get("abschnitte") or []) if isinstance(a, dict)]
                    verw = _verwendbare_abschnitte(c)
                    dauer = _sek(c["dauer_s"]) if isinstance(c.get("dauer_s"), (int, float)) else "–"
                    lines.append(f"| {_md(_clip_key(c))} | {dauer} | {_md(c.get('einstellung'))} | {_md(c.get('kamerabewegung'))} | "
                                 f"{_md(c.get('beschreibung_kurz'))} | {_zahl(c.get('qualitaet_gesamt'))} | "
                                 f"{len(verw)}/{len(abschnitte)} | {_abschnitte_txt(verw)} | "
                                 f"{_liste(c.get('maengel'))} | {_liste(c.get('tags'))} |")
                lines.append("")
    if fehler:
        lines += ["## Fehler", ""] + [f"- {_md(f)}" for f in fehler] + [""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# B-Roll-Zuordnung
# --------------------------------------------------------------------------- #

def _index_lookup(index: dict) -> dict[str, dict]:
    """Clip-Datensätze des Index nach vollem Pfad UND Dateiname (Rückfall, wenn nur der Name bekannt ist)."""
    out: dict[str, dict] = {}
    clips = (index or {}).get("clips") if isinstance(index, dict) else None
    for c in clips or []:
        if not isinstance(c, dict):
            continue
        for key in (c.get("path"), c.get("pfad")):
            if key:
                out[str(key)] = c
        name = _clip_key(c)
        out.setdefault(name, c)
    return out


def render_broll_plan(plan: dict, index: dict) -> str:
    """Markdown-Bericht der B-Roll-Zuordnung (Spec 5): pro Beat die gewählten Clips, Grund, Abweichung.

    ``plan`` ist ``BrollPlan.to_dict()`` ({"video", "beats"}); die reine Beat-Liste aus Spec 5
    (``[{beat_nr, items}]``, z. B. von Hand geschriebene broll_plan.json) wird ebenfalls angenommen."""
    if isinstance(plan, list):
        plan = {"video": "", "beats": plan}
    plan = plan if isinstance(plan, dict) else {}
    beats = [b for b in (plan.get("beats") or []) if isinstance(b, dict)]
    lookup = _index_lookup(index)
    rows: list[str] = []
    n_items = n_abw = 0
    clips_genutzt: set[str] = set()
    ohne: list[str] = []
    for b in beats:
        nr = _md(b.get("beat_nr"))
        items = [i for i in (b.get("items") or []) if isinstance(i, dict)]
        if not items:
            ohne.append(nr)
            continue
        for it in items:
            n_items += 1
            clip = str(it.get("clip") or "")
            clips_genutzt.add(clip)
            rec = lookup.get(clip) or lookup.get(_name(clip)) or {}
            try:
                in_s, out_s = float(it.get("in_s", 0.0)), float(it.get("out_s", 0.0))
                abschnitt = f"{_mmss_floor(in_s)}–{_mmss_floor(out_s)} ({_zahl(in_s)}–{_zahl(out_s)} s)"
                laenge = _sek(out_s - in_s)
            except (TypeError, ValueError):
                abschnitt, laenge = "–", "–"
            try:
                start = _sek(float(it.get("start_offset_s", 0.0)), sign=True)
            except (TypeError, ValueError):
                start = "–"
            if it.get("abweichung"):
                n_abw += 1
                abw = "ja" + (f": {_md(it.get('abweichung_grund'))}" if it.get("abweichung_grund") else "")
            else:
                abw = "–"
            kurz = _md(rec.get("beschreibung_kurz")) if rec else "nicht im Index"
            rows.append(f"| {nr} | {_md(_name(clip))} | {_md(rec.get('ordner')) if rec else '–'} | {abschnitt} | {laenge} | "
                        f"{start} | {kurz} | {_md(it.get('grund'))} | {abw} |")
    lines = [f"# B-Roll-Zuordnung {_md(plan.get('video'))}", "",
             f"- Beats mit B-Roll: {len(beats) - len(ohne)} von {len(beats)} · Items: {n_items} · "
             f"Clips: {len(clips_genutzt)} · Abweichungen: {n_abw}",
             f"- Beats ohne B-Roll: {', '.join(ohne) if ohne else '–'}", ""]
    if not rows:
        lines += ["Keine B-Roll-Items im Plan (broll_plan.json leer).", ""]
        return "\n".join(lines)
    lines += ["## Zuordnung", "",
              "| Beat | Clip | Ordner | Abschnitt | Länge | Start im Beat | Kurzbeschreibung | Grund | Abweichung |",
              "|---|---|---|---|---|---|---|---|---|"] + rows + [""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Schreiben
# --------------------------------------------------------------------------- #

def write_report(charge: Charge, filename: str, text: str) -> Path:
    """Bericht nach ``<Charge>/Ergebnisse/Rohschnitt/<filename>`` schreiben; nur einfache Dateinamen erlaubt."""
    name = str(filename or "")
    if not name or Path(name).name != name or name in (".", ".."):
        raise AutoCutError(f"Berichtsname muss ein einfacher Dateiname sein (ohne Pfad): {filename!r}\n"
                           f"Berichte liegen immer unter {charge.ergebnisse}.")
    p = charge.ergebnisse / name
    charge.assert_writable(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# Finalisieren (Pegel-Abschnitt, Merge in bestehenden Bericht)
# --------------------------------------------------------------------------- #

def render_pegel(ton: dict) -> str:
    """Abschnitt „## Pegel (True Peak)“ für den Rohschnitt-Bericht."""
    items = [i for i in (ton or {}).get("items") or [] if isinstance(i, dict)]
    lines = [f"## Pegel (True Peak {_zahl((ton or {}).get('ziel_dbtp', -3.0))} dBTP je Clip)", "",
             "| Position | Clip | Bereich (Frames) | True Peak | Gain | Hinweis |", "|---|---|---|---|---|---|"]
    for i in items:
        lines.append(f"| {i.get('rec_in_f', '–')} | {_md(i.get('name'))} | {i.get('src_in_f', '–')}–{i.get('src_out_f', '–')} | "
                     f"{_zahl(i.get('tpk_dbfs'))} dBFS | {_zahl(i.get('gain_db'))} dB | {_md(i.get('warnung')) if i.get('warnung') else ''} |")
    if not items:
        lines.append("| – | – | – | – | – | keine A1-Items |")
    lines.append("")
    return "\n".join(lines)


def merge_section(text: str, header: str, section: str) -> str:
    """Abschnitt mit ``header`` (Zeile, die so beginnt) im Bericht ersetzen oder ans Ende anhängen."""
    lines = (text or "").split("\n")
    start = next((i for i, l in enumerate(lines) if l.startswith(header)), None)
    if start is None:
        return (text or "").rstrip("\n") + "\n\n" + section.rstrip("\n") + "\n"
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[:start] + section.rstrip("\n").split("\n") + [""] + lines[end:])
