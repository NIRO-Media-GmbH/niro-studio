"""DaVinci Resolve Scripting API — nur Anlegen neuer Bins/Timelines/Media-Pool-Einträge, nie Bestehendes ändern.

Alle Resolve-Aufrufe laufen über ``ResolveSession``; Tests injizieren ein Fake-Resolve (tests/fake_resolve.py).

Verbindliche Erkenntnisse (Recherche 03.09., README/CHANGELOG 21.0):
- ``recordFrame`` in ``AppendToTimeline`` ist ABSOLUT (Timeline-Startframe + Offset; 01:00:00:00 @ 25 fps = 90000).
  ``Timeline.AddMarker(frameId)`` ist dagegen RELATIV zum Timeline-Start (README „timeline offset").
- ``endFrame`` gilt als inklusiv (``END_FRAME_INCLUSIVE``); die tatsächliche Semantik misst ``scripts/resolve_probe.py``
  und legt sie in ``probe.json`` ab (``end_frame_inclusive``) — ``ResolveSession(resolve, probe=…)`` übernimmt sie.
  Readback nach jedem Append nur über ``GetStart()``/``GetDuration()`` (``GetEnd()`` ist uneinheitlich).
- Alle clipInfos in EINEM ``AppendToTimeline``-Aufruf; davor ``SetSelectedClip`` (Workaround CHANGELOG 20.3.2)
  und ``SetCurrentTimeline`` (Append schreibt nur in die aktuelle Timeline).
- ``useCustomSettings='1'`` setzt Color-Management-Keys zurück (BMD-Bug, Forum t=212784) → vorher sichern, danach
  zurückschreiben; Auflösung per Readback prüfen. ``timelineFrameRate`` ist ein Projekt-Setting: nur prüfen.
- Proxy nur verknüpfen, wenn ``GetClipProperty('Proxy')`` noch keine Auflösung („1920x1080") nennt.
- Cloud-/Multi-User-Projekte: ``RefreshFolders()`` vor Schreibzugriffen, ``SaveProject()`` danach (Rückgabe loggen).
"""
from __future__ import annotations

import datetime as _dt
import os
import re
import sys
import unicodedata
from pathlib import Path

from .charge import AutoCutError
from .timeline_model import Item, MarkerSpec, TimelinePlan

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
TRACK_INDEX = {"V1": 1, "V2": 2, "V3": 3, "A1": 1, "A2": 2}
APPEND_ORDER = {"V1": 0, "A1": 1, "V2": 2, "A2": 3, "V3": 4}   # je Cut: V1/A1/V2/A2, B-Roll zuletzt
END_FRAME_INCLUSIVE = True      # Annahme (README-Beispiel 7); Probe misst und überschreibt per probe.json
MARKER_NAME_MAX = 80
MARKER_NOTE_MAX = 2000
BIN_NAME_MAX = 60
# Keys, die useCustomSettings='1' zurücksetzt (BMD-Bug) — werden vor dem Umschalten gesichert und zurückgeschrieben
COLOR_KEYS = ("colorScienceMode", "colorSpaceTimeline", "colorSpaceTimelineGamma", "colorSpaceOutput",
              "colorSpaceOutputGamma", "separateColorSpaceAndGamma", "isAutoColorManage", "rcmPresetMode",
              "useCATransform", "disableFusionToneMapping", "timelineInputResMismatchBehavior",
              "timelineOutputResMismatchBehavior", "videoMonitorFormat")
_TIMESTAMP_RE = re.compile(r"\s+\d{4}-\d{2}-\d{2} \d{4}$")
_ROH_RE = re.compile(r"\s*\(roh\)\s*$")


# --------------------------------------------------------------------------- #
# Verbindung
# --------------------------------------------------------------------------- #

def _import_module():
    """DaVinciResolveScript laden (Umgebung setzen, Modulpfad ergänzen). Getrennt, damit Tests es ersetzen können."""
    os.environ.setdefault("RESOLVE_SCRIPT_API", API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", LIB)
    mod_dir = Path(os.environ["RESOLVE_SCRIPT_API"]) / "Modules"
    if not (mod_dir / "DaVinciResolveScript.py").is_file():
        raise AutoCutError(f"Resolve-Scripting-Modul nicht gefunden: {mod_dir / 'DaVinciResolveScript.py'}\n"
                           f"Ist DaVinci Resolve Studio installiert?")
    if str(mod_dir) not in sys.path:
        sys.path.append(str(mod_dir))
    import DaVinciResolveScript as dvr  # type: ignore
    return dvr


def connect():
    """Resolve-Objekt holen; AutoCutError mit Handlungsanweisung, wenn Resolve nicht erreichbar ist."""
    try:
        dvr = _import_module()
    except AutoCutError:
        raise
    except Exception as e:
        raise AutoCutError(f"Resolve-Scripting-Modul nicht ladbar ({e}). Ist DaVinci Resolve Studio installiert und "
                           f"läuft es? Pfade: RESOLVE_SCRIPT_API={os.environ.get('RESOLVE_SCRIPT_API')}, "
                           f"RESOLVE_SCRIPT_LIB={os.environ.get('RESOLVE_SCRIPT_LIB')}") from e
    r = dvr.scriptapp("Resolve")
    if not r:
        raise AutoCutError("DaVinci Resolve ist nicht erreichbar. Resolve starten, Projekt öffnen und in den "
                           "Einstellungen (System → Allgemein) 'Externes Scripting: Lokal' erlauben.")
    return r


# --------------------------------------------------------------------------- #
# Hilfen
# --------------------------------------------------------------------------- #

def _norm(path) -> str:
    """Pfad vergleichbar machen: normpath + Unicode-NFC (macOS liefert Dateinamen teils in NFD)."""
    return unicodedata.normalize("NFC", os.path.normpath(str(path)))


def _safe(fn, default=None, *args):
    try:
        return fn(*args)
    except Exception:
        return default


def _fps_str(fps: float) -> str:
    s = f"{float(fps):.3f}".rstrip("0").rstrip(".")
    return s or "0"


def _fps_matches(setting, fps: float) -> bool:
    try:
        return abs(float(str(setting).replace("DF", "").strip()) - float(fps)) < 0.01
    except (TypeError, ValueError):
        return False


def timeline_name(prefix: str, video_kurz: str, now: _dt.datetime | None = None) -> str:
    """Timeline-Name „<prefix> <Video-Kurzname> <JJJJ-MM-TT HHMM>" (Spec 3.5)."""
    now = now or _dt.datetime.now()
    return f"{prefix} {video_kurz} {now:%Y-%m-%d %H%M}"


def bin_name_for(name: str, prefix: str) -> str:
    """Bin-Name aus dem Timeline-Namen: Präfix, Zeitstempel und „(roh)"-Suffix weg → „<Video-Kurzname>"
    (eine Bin je Video — Stufe-1- und finalisierte Timeline landen im selben Bin)."""
    base = _ROH_RE.sub("", name.strip())
    if prefix and base.startswith(prefix + " "):
        base = base[len(prefix) + 1:]
    base = _TIMESTAMP_RE.sub("", base).strip() or name.strip()
    return base.replace("/", "-")[:BIN_NAME_MAX]


# --------------------------------------------------------------------------- #
# Session
# --------------------------------------------------------------------------- #

class ResolveSession:
    """Offenes Projekt in Resolve; alle Schreibzugriffe legen nur Neues an.

    ``probe``: Inhalt von probe.json (``scripts/resolve_probe.py``); Schlüssel ``end_frame_inclusive`` bestimmt
    die endFrame-Semantik. Fehlt die Probe, gilt ``END_FRAME_INCLUSIVE`` — der Readback deckt Abweichungen auf.
    Nicht-fatale Befunde (Proxy, Marker verschoben, Clip nicht stummgeschaltet) sammelt ``warnings``.
    """

    def __init__(self, resolve, probe: dict | None = None):
        self.resolve = resolve
        self.pm = resolve.GetProjectManager()
        self.project = self.pm.GetCurrentProject()
        if not self.project:
            raise AutoCutError("In Resolve ist kein Projekt geöffnet. Zielprojekt öffnen und erneut starten.")
        self.media_pool = self.project.GetMediaPool()
        self.version = str(_safe(resolve.GetVersionString, "?"))
        self.project_name = str(_safe(self.project.GetName, "?"))
        self.project_id = str(_safe(self.project.GetUniqueId, "") or "")
        self.end_frame_inclusive = END_FRAME_INCLUSIVE
        if isinstance(probe, dict) and probe.get("end_frame_inclusive") is not None:
            self.end_frame_inclusive = bool(probe["end_frame_inclusive"])
        self.warnings: list[str] = []
        self.current_timeline = None     # zuletzt von dieser Session angelegte Timeline (Fehlerfall: umbenennen)
        self.user_timeline = _safe(self.project.GetCurrentTimeline, None)   # wird am Ende jedes Laufs wieder aktiviert

    # --- Media Pool ------------------------------------------------------
    def _walk(self, folder):
        yield folder
        for sub in folder.GetSubFolderList() or []:
            yield from self._walk(sub)

    def _path_index(self) -> dict[str, object]:
        """Alle Clips des Media Pools nach normalisiertem Dateipfad (Timelines haben keinen Pfad und fehlen)."""
        out: dict[str, object] = {}
        for folder in self._walk(self.media_pool.GetRootFolder()):
            for clip in folder.GetClipList() or []:
                getter = getattr(clip, "GetClipProperty", None)
                fp = _safe(getter, None, "File Path") if getter else None
                if fp and isinstance(fp, str):
                    out.setdefault(_norm(fp), clip)
        return out

    def find_media_item(self, path: str):
        """Vorhandenes Media-Pool-Item zum Dateipfad (über alle Bins), sonst None."""
        return self._path_index().get(_norm(path))

    def ensure_bin(self, parts: list[str]):
        """Bin-Pfad unter dem Master-Ordner anlegen (nur fehlende Ebenen) und als aktuellen Ordner setzen."""
        folder = self.media_pool.GetRootFolder()
        for name in parts:
            existing = next((f for f in (folder.GetSubFolderList() or []) if f.GetName() == name), None)
            folder = existing or self.media_pool.AddSubFolder(folder, name)
            if not folder:
                raise AutoCutError(f"Bin '{name}' konnte nicht angelegt werden (Media Pool gesperrt oder Name ungültig?).")
        self.media_pool.SetCurrentFolder(folder)
        return folder

    def import_media(self, paths: list[str], folder) -> dict:
        """Media-Pool-Items je Pfad: vorhandene wiederverwenden (Dedupe per Dateipfad), nur fehlende importieren."""
        self.media_pool.SetCurrentFolder(folder)
        index = self._path_index()
        out: dict[str, object] = {}
        missing: list[str] = []
        for p in paths:
            item = index.get(_norm(p))
            if item is None:
                missing.append(p)
            else:
                out[p] = item
        if missing:
            imported = self.media_pool.ImportMedia(list(missing)) or []
            by_path = {}
            for it in imported:
                fp = _safe(it.GetClipProperty, None, "File Path")
                if fp:
                    by_path[_norm(fp)] = it
            fresh = None
            for p in missing:
                item = by_path.get(_norm(p))
                if item is None:
                    fresh = fresh if fresh is not None else self._path_index()
                    item = fresh.get(_norm(p))
                if item is None:
                    raise AutoCutError(f"Import in den Media Pool fehlgeschlagen: {p}\n"
                                       f"Ist das NAS gemountet und die Datei lesbar?")
                out[p] = item
        return out

    def link_proxy(self, item, proxy_path: str | None) -> bool:
        """Proxy verknüpfen, falls noch keiner verknüpft ist (Clip-Eigenschaft 'Proxy' nennt sonst z. B. 1920x1080)."""
        if not proxy_path:
            return False
        current = _safe(item.GetClipProperty, "", "Proxy")
        if isinstance(current, str) and "x" in current.lower() and any(ch.isdigit() for ch in current):
            return True
        try:
            return bool(item.LinkProxyMedia(str(proxy_path)))
        except Exception:
            return False

    # --- Timeline --------------------------------------------------------
    def list_timelines(self) -> list:
        n = int(_safe(self.project.GetTimelineCount, 0) or 0)
        return [t for t in (self.project.GetTimelineByIndex(i) for i in range(1, n + 1)) if t]

    def find_timeline(self, name: str):
        return next((t for t in self.list_timelines() if t.GetName() == name), None)

    def create_timeline(self, name: str, fps: float, width: int, height: int, start_tc: str):
        """Neue, leere Timeline mit eigener Auflösung; Bildrate muss zum Projekt passen (Projekt-Setting)."""
        if self.find_timeline(name) is not None:
            raise AutoCutError(f"Timeline '{name}' existiert bereits — anderen Namen wählen.")
        proj_fps = self.project.GetSetting("timelineFrameRate")
        if not _fps_matches(proj_fps, fps):
            raise AutoCutError(f"Bildrate passt nicht: Projekt {proj_fps} fps, Material {_fps_str(fps)} fps. "
                               f"'timelineFrameRate' ist ein Projekt-Setting — im Zielprojekt umstellen (oder passendes "
                               f"Projekt öffnen), dann erneut bauen.")
        t = self.media_pool.CreateEmptyTimeline(name)
        if not t:
            raise AutoCutError(f"Timeline '{name}' konnte nicht angelegt werden.")
        self.current_timeline = t
        # Live-Probe 04.09.: useCustomSettings=1 setzt Color-Management-Keys zurück, drei davon lassen sich per
        # Skript nicht wiederherstellen (BMD-Bug). Deshalb nur dann eigene Timeline-Einstellungen, wenn das
        # Material-Format vom Projekt abweicht (z. B. Hochkant in einem Querformat-Projekt).
        proj_w = _safe(lambda: int(float(self.project.GetSetting("timelineResolutionWidth"))), None)
        proj_h = _safe(lambda: int(float(self.project.GetSetting("timelineResolutionHeight"))), None)
        if (proj_w, proj_h) == (int(width), int(height)):
            self.custom_settings_used = False
        else:
            self.custom_settings_used = True
            self.warnings.append(f"Timeline '{name}': Format {width}x{height} weicht vom Projekt ({proj_w}x{proj_h}) ab — "
                                 f"eigene Timeline-Einstellungen aktiv; Color-Management der Timeline in Resolve prüfen.")
            saved = {k: t.GetSetting(k) for k in COLOR_KEYS}
            if not t.SetSetting("useCustomSettings", "1"):
                raise AutoCutError(f"Timeline '{name}': eigene Timeline-Einstellungen (useCustomSettings) nicht aktivierbar.")
            for key, val in (("timelineResolutionWidth", width), ("timelineResolutionHeight", height)):
                if not t.SetSetting(key, str(int(val))):
                    raise AutoCutError(f"Timeline '{name}': {key}={val} wurde von Resolve abgelehnt.")
            for key, val in (("timelineOutputResolutionWidth", width), ("timelineOutputResolutionHeight", height)):
                if not t.SetSetting(key, str(int(val))):
                    self.warnings.append(f"Timeline '{name}': {key}={val} nicht gesetzt (Ausgabeauflösung von Hand prüfen).")
            for key, val in saved.items():
                if val in (None, ""):
                    continue
                t.SetSetting(key, str(val))
                if str(t.GetSetting(key)) != str(val):
                    self.warnings.append(f"Timeline '{name}': Color-Management-Einstellung {key} nach useCustomSettings "
                                         f"nicht wiederhergestellt (war {val!r}, ist {t.GetSetting(key)!r}).")
        got = (_safe(lambda: int(float(t.GetSetting("timelineResolutionWidth"))), None),
               _safe(lambda: int(float(t.GetSetting("timelineResolutionHeight"))), None))
        if got != (int(width), int(height)):
            raise AutoCutError(f"Timeline '{name}': Auflösung nicht übernommen — Soll {width}x{height}, "
                               f"Ist {got[0]}x{got[1]} (BMD-Bug useCustomSettings, Forum t=212784). Timeline in Resolve "
                               f"löschen und Projekt-Auflösung auf {width}x{height} stellen, dann erneut bauen.")
        if not t.SetStartTimecode(start_tc) or str(_safe(t.GetStartTimecode, start_tc)) != start_tc:
            self.warnings.append(f"Timeline '{name}': Start-Timecode {start_tc} nicht gesetzt "
                                 f"(ist {_safe(t.GetStartTimecode, '?')}); Positionen bleiben trotzdem konsistent.")
        self.project.SetCurrentTimeline(t)
        return t

    def ensure_tracks(self, timeline, video: int, audio: int, names: dict) -> None:
        """Spuren anlegen (nur fehlende; Audio stereo) und benennen. names: {"V1": "FX3", "A2": "…"}."""
        unknown = [k for k in names if k not in TRACK_INDEX]
        if unknown:
            raise AutoCutError(f"Unbekannte Spur(en) in track_names: {unknown} — erlaubt sind {list(TRACK_INDEX)}.")
        while int(timeline.GetTrackCount("video")) < video:
            if not timeline.AddTrack("video"):
                raise AutoCutError("Videospur konnte nicht angelegt werden.")
        while int(timeline.GetTrackCount("audio")) < audio:
            if not timeline.AddTrack("audio", "stereo"):
                raise AutoCutError("Audiospur (stereo) konnte nicht angelegt werden.")
        for key, name in names.items():
            kind = "video" if key.startswith("V") else "audio"
            idx = TRACK_INDEX[key]
            if idx <= int(timeline.GetTrackCount(kind)) and not timeline.SetTrackName(kind, idx, str(name)):
                self.warnings.append(f"Spurname {key}='{name}' nicht gesetzt.")

    def timeline_start_frame(self, timeline) -> int:
        return int(timeline.GetStartFrame())

    def restore_user_timeline(self) -> bool:
        """Die beim Start aktive Timeline des Users wieder aktivieren (der User arbeitet parallel in Resolve)."""
        tl = self.user_timeline
        if tl is None:
            return False
        return bool(_safe(self.project.SetCurrentTimeline, False, tl))

    def save_project(self) -> bool:
        """SaveProject() am ProjectManager; Cloud-Projekte speichern ohnehin live. Rückgabe nur fürs Protokoll, nie Abbruch."""
        for owner in (self.pm, self.project):
            fn = getattr(owner, "SaveProject", None)
            if fn is None:
                continue
            try:
                return bool(fn())
            except Exception:
                continue
        return False

    def _clip_info(self, it: Item, media_items: dict, start_frame: int) -> dict:
        mi = media_items.get(it.clip)
        if mi is None:
            norm = _norm(it.clip)
            mi = next((v for k, v in media_items.items() if _norm(k) == norm), None)
        if mi is None:
            raise AutoCutError(f"Kein Media-Pool-Eintrag für {it.clip} — Clip wurde nicht importiert.")
        if it.track not in TRACK_INDEX:
            raise AutoCutError(f"Unbekannte Spur '{it.track}' für {Path(it.clip).name}.")
        if it.src_out_f <= it.src_in_f:
            raise AutoCutError(f"{Path(it.clip).name} auf {it.track}: leerer Bereich {it.src_in_f}–{it.src_out_f}.")
        end = int(it.src_out_f) - 1 if self.end_frame_inclusive else int(it.src_out_f)
        return {"mediaPoolItem": mi, "startFrame": int(it.src_in_f), "endFrame": end,
                "recordFrame": int(start_frame + it.rec_in_f), "trackIndex": TRACK_INDEX[it.track],
                "mediaType": 1 if it.track.startswith("V") else 2}

    def append_items(self, timeline, items: list[Item], media_items: dict, start_frame: int) -> list:
        """Alle Items in einem AppendToTimeline-Aufruf setzen (recordFrame absolut), per Readback prüfen,
        deaktivierte Items stummschalten, Video/Audio eines Cuts best effort verknüpfen."""
        if not items:
            return []
        infos = [self._clip_info(it, media_items, start_frame) for it in items]
        self.project.SetCurrentTimeline(timeline)
        _safe(self.media_pool.SetSelectedClip, None, infos[0]["mediaPoolItem"])   # Workaround 20.3.2
        added = self.media_pool.AppendToTimeline(infos) or []
        if len(added) != len(infos):
            first = infos[0]
            raise AutoCutError(f"AppendToTimeline fehlgeschlagen: {len(added)} von {len(infos)} Items gesetzt "
                               f"(erstes: {Path(items[0].clip).name} auf {items[0].track} bei Frame "
                               f"{first['recordFrame']}). Timeline '{timeline.GetName()}' in Resolve prüfen.")
        for it, info, tl in zip(items, infos, added):
            # Erwartete Dauer in TIMELINE-Frames (rec), nicht in Quellframes: B-Roll-Clips können 50/100 fps haben,
            # dann sind Quellframes ≠ Timeline-Frames (Resolve konformiert 50p in 25p-Timeline auf halbe Framezahl).
            soll_start, soll_dur = info["recordFrame"], int(it.rec_out_f) - int(it.rec_in_f)
            ist_start, ist_dur = int(tl.GetStart()), int(tl.GetDuration())
            if (ist_start, ist_dur) != (soll_start, soll_dur):
                raise AutoCutError(
                    f"Readback weicht ab für {Path(it.clip).name} auf {it.track}: Soll Start {soll_start} / Dauer "
                    f"{soll_dur}, Ist Start {ist_start} / Dauer {ist_dur} (endFrame {'inklusiv' if self.end_frame_inclusive else 'exklusiv'} "
                    f"angenommen). scripts/resolve_probe.py ausführen und probe.json prüfen.")
        self.disable_items([tl for it, tl in zip(items, added) if not it.enabled])
        self._link_pairs(timeline, items, added)
        return list(added)

    def _link_pairs(self, timeline, items: list[Item], added: list) -> None:
        """V1+A1 bzw. V2+A2 desselben Cuts verknüpfen (best effort, Fehler ignorieren)."""
        by_key: dict[tuple, dict[str, object]] = {}
        for it, tl in zip(items, added):
            by_key.setdefault((it.clip, it.src_in_f, it.src_out_f, it.rec_in_f), {})[it.track] = tl
        for group in by_key.values():
            for v, a in (("V1", "A1"), ("V2", "A2")):
                if v in group and a in group:
                    _safe(timeline.SetClipsLinked, None, [group[v], group[a]], True)

    def disable_items(self, timeline_items) -> None:
        """Clips deaktivieren (A2 stumm); Verweigerung wird als Warnung gemeldet, nicht als Abbruch."""
        for tl in timeline_items:
            ok = _safe(tl.SetClipEnabled, False, False)
            if not ok or _safe(tl.GetClipEnabled, False) is True:
                self.warnings.append(f"Clip {_safe(tl.GetName, '?')} bei Frame {_safe(tl.GetStart, '?')} konnte nicht "
                                     f"deaktiviert (stumm) werden — in Resolve von Hand ausschalten.")

    def add_markers(self, timeline, markers: list[MarkerSpec], start_frame: int) -> None:
        """Marker setzen. frameId ist RELATIV zum Timeline-Start — start_frame wird NICHT addiert.
        Marker hinter dem letzten Clip lehnt Resolve ab: dann auf den letzten freien Frame davor verschieben."""
        taken: set[int] = set()
        for m in markers:
            frame = int(m.frame)
            name, note = str(m.name)[:MARKER_NAME_MAX], str(m.note or "")[:MARKER_NOTE_MAX]
            dur = max(1, int(m.duration))
            if timeline.AddMarker(frame, m.color, name, note, dur, ""):
                taken.add(frame)
                continue
            end_rel = int(_safe(timeline.GetEndFrame, start_frame) or start_frame) - int(start_frame)
            placed = None
            if frame >= end_rel > 0:
                cand = end_rel - 1
                while cand >= 0 and cand >= end_rel - 25 and placed is None:
                    if cand not in taken and timeline.AddMarker(cand, m.color, name, note, 1, ""):
                        placed = cand
                    cand -= 1
            if placed is not None:
                taken.add(placed)
                self.warnings.append(f"Marker '{name}' bei Frame {frame} liegt hinter dem letzten Clip (Ende {end_rel}) — "
                                     f"auf Frame {placed} verschoben (Platzhalter am Ende der Timeline).")
            else:
                self.warnings.append(f"Marker '{name}' bei Frame {frame} konnte nicht gesetzt werden "
                                     f"(Frame belegt oder außerhalb der Timeline).")

    def export_timeline(self, timeline, path: str | Path, kind: str = "fcp7xml") -> Path:
        r = self.resolve
        kinds = {"fcp7xml": getattr(r, "EXPORT_FCP_7_XML", None), "otio": getattr(r, "EXPORT_OTIO", None),
                 "edl": getattr(r, "EXPORT_EDL", None)}
        if kind not in kinds:
            raise AutoCutError(f"Unbekannte Export-Art '{kind}' — erlaubt: {', '.join(kinds)}.")
        k = kinds[kind]
        if k is None:
            raise AutoCutError(f"Resolve kennt die Export-Konstante für '{kind}' nicht (Version {self.version}).")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if kind == "edl":
            ok = timeline.Export(str(path), k, getattr(r, "EXPORT_NONE", None))
        else:
            ok = timeline.Export(str(path), k)
        if not ok:
            raise AutoCutError(f"Export ({kind}) fehlgeschlagen: {path}")
        return path

    def read_timeline(self, timeline) -> dict:
        """Alle Items je Spur (name, file, start, end, duration, src_in, src_out, enabled), Marker, Settings.

        Beobachtet am MEK-Projekt (Readback 04.09., 92 Timelines): ``end - start == duration`` (GetEnd exklusiv);
        ``src_out - src_in`` weicht bis zu ±1 Frame von ``duration`` ab (GetSourceEndFrame ist nicht frame-exakt) —
        für Berechnungen ``src_in`` + ``duration`` verwenden, nicht ``src_out``.
        """
        markers = {}
        for k, v in (_safe(timeline.GetMarkers, None) or {}).items():
            key = str(int(k)) if isinstance(k, (int, float)) and float(k).is_integer() else str(k)
            markers[key] = dict(v) if isinstance(v, dict) else v
        out = {"name": timeline.GetName(), "unique_id": str(_safe(timeline.GetUniqueId, "") or ""),
               "start_frame": int(_safe(timeline.GetStartFrame, 0) or 0),
               "end_frame": _safe(timeline.GetEndFrame, None),
               "start_timecode": _safe(timeline.GetStartTimecode, None),
               "fps": _safe(timeline.GetSetting, None, "timelineFrameRate"),
               "width": _safe(lambda: int(float(timeline.GetSetting("timelineResolutionWidth"))), None),
               "height": _safe(lambda: int(float(timeline.GetSetting("timelineResolutionHeight"))), None),
               "tracks": {}, "markers": markers, "n_items": 0}
        for kind in ("video", "audio"):
            for i in range(1, int(_safe(timeline.GetTrackCount, 0, kind) or 0) + 1):
                rows = []
                for it in _safe(timeline.GetItemListInTrack, None, kind, i) or []:
                    mpi = _safe(it.GetMediaPoolItem, None)
                    file = _safe(mpi.GetClipProperty, None, "File Path") if mpi else None
                    rows.append({"name": _safe(it.GetName, None), "file": file or None,
                                 "start": _safe(lambda: int(it.GetStart()), None),
                                 "end": _safe(lambda: int(it.GetEnd()), None),
                                 "duration": _safe(lambda: int(it.GetDuration()), None),
                                 "src_in": _safe(it.GetSourceStartFrame, None),
                                 "src_out": _safe(it.GetSourceEndFrame, None),
                                 "enabled": _safe(it.GetClipEnabled, None)})
                out["tracks"][f"{kind[0].upper()}{i}"] = {"name": _safe(timeline.GetTrackName, None, kind, i), "items": rows}
                out["n_items"] += len(rows)
        return out

    # --- v2: XML-Roundtrip, eigene Objekte löschen, Farben, Probe-Hilfen -------------
    def all_folders(self) -> list:
        """Alle Bins des Media Pools (Wurzel zuerst, rekursiv) — Suchpfad für den XML-Import, damit Resolve die
        vorhandenen Einträge wiederfindet, statt Offline-Platzhalter anzulegen (Live-Probe 04.09.: nur der eigene Bin
        reicht nicht, weil ``import_media`` bestehende Einträge anderer Bins wiederverwendet)."""
        return list(self._walk(self.media_pool.GetRootFolder()))

    def import_timeline_xml(self, path: str | Path, name: str, folders: list | None = None):
        """FCP7-XML als NEUE Timeline importieren; Medien aus ``folders`` (Standard: alle Bins, keine Neuimporte).
        Name muss frei sein."""
        p = Path(path)
        if not p.is_file():
            raise AutoCutError(f"XML für den Import fehlt: {p}")
        if self.find_timeline(name) is not None:
            raise AutoCutError(f"Timeline '{name}' existiert bereits — Import abgebrochen (anderen Namen wählen).")
        opts = {"timelineName": name, "importSourceClips": False,
                "sourceClipsFolders": list(folders) if folders is not None else self.all_folders()}
        tl = self.media_pool.ImportTimelineFromFile(str(p), opts)
        if not tl:
            raise AutoCutError(f"Resolve hat das XML nicht importiert: {p}\nMedien-Bins und XML prüfen (work/xml).")
        self.current_timeline = tl
        return tl

    def delete_own_timeline(self, timeline, suffix: str, expected_name: str) -> bool:
        """Nur die eigene roh-Timeline desselben Laufs löschen: Name endet mit ``suffix`` UND ist ``expected_name``."""
        name = str(_safe(timeline.GetName, "") or "")
        if not suffix or not name.endswith(suffix) or name != expected_name:
            raise AutoCutError(f"Löschen verweigert: '{name}' ist nicht die eigene roh-Timeline dieses Laufs "
                               f"(erwartet '{expected_name}' mit Suffix '{suffix}').")
        return bool(self.media_pool.DeleteTimelines([timeline]))

    def color_items(self, timeline, track_index: int, starts_abs: set[int], color: str) -> int:
        """Clip-Farbe für Items einer Videospur, deren Start (absolut) in ``starts_abs`` liegt; liefert die Anzahl."""
        n = 0
        for it in _safe(timeline.GetItemListInTrack, None, "video", int(track_index)) or []:
            if int(_safe(it.GetStart, -1)) in starts_abs and _safe(it.SetClipColor, False, color):
                n += 1
        return n

    def add_duplicate_media(self, path: str, folder):
        """Denselben Pfad als ZUSÄTZLICHES Media-Pool-Item in ``folder`` anlegen (Probe/Konform-Rückfall); None wenn Resolve verweigert."""
        self.media_pool.SetCurrentFolder(folder)
        items = _safe(self.media_pool.AddItemListToMediaPool, None, [str(path)]) or []
        return items[0] if items else None

    def set_clip_fps(self, item, fps: float) -> bool:
        ok = bool(_safe(item.SetClipProperty, False, "FPS", _fps_str(fps)))
        return ok and _fps_matches(_safe(item.GetClipProperty, None, "FPS"), fps)

    def delete_probe_objects(self, timelines: list, clips: list, folders: list) -> dict:
        """Nur für Probe-Skripte: eigene Probe-Timelines, Duplikat-Clips und den Probe-Bin entfernen."""
        rep = {"timelines": True, "clips": True, "folders": True}
        if timelines:
            rep["timelines"] = bool(_safe(self.media_pool.DeleteTimelines, False, list(timelines)))
        if clips:
            rep["clips"] = bool(_safe(self.media_pool.DeleteClips, False, list(clips)))
        if folders:
            rep["folders"] = bool(_safe(self.media_pool.DeleteFolders, False, list(folders)))
        return rep


# --------------------------------------------------------------------------- #
# Bau aus dem TimelinePlan (Spec 3.5, Schritte 1–6)
# --------------------------------------------------------------------------- #

def build_from_plan(session: ResolveSession, tp: TimelinePlan, media: dict, name: str, cfg: dict) -> dict:
    """Bin → Media (Dedupe, Proxy) → Timeline → Spuren → Items (ein Append) → Marker → SaveProject.

    Gibt {"timeline", "items", "markers", "warnings", "start_frame", …} zurück. Wirft AutoCutError; das
    aufrufende Skript benennt die angefangene Timeline dann in „… FEHLER" um (Spec 6).
    """
    rcfg = cfg["resolve"]
    n_warn = len(session.warnings)
    warnings: list[str] = []
    _safe(session.media_pool.RefreshFolders, None)      # Multi-User/Cloud: Ordnerstand aktualisieren
    bin_parts = [str(rcfg["bin_root"]), bin_name_for(name, str(rcfg.get("timeline_prefix", "")))]
    folder = session.ensure_bin(bin_parts)
    clips = sorted({it.clip for it in tp.items})
    media_items = session.import_media(clips, folder)
    linked = 0
    for c in clips:
        proxy = ((media.get("clips") or {}).get(c) or {}).get("proxy_path")
        if not proxy:
            continue
        if session.link_proxy(media_items[c], proxy):
            linked += 1
        else:
            warnings.append(f"Proxy nicht verknüpft: {Path(c).name}")
    timeline = session.create_timeline(name, tp.fps, tp.width, tp.height, str(rcfg["start_timecode"]))
    session.ensure_tracks(timeline, 3, 1, dict(rcfg.get("track_names") or {}))
    start = session.timeline_start_frame(timeline)
    items = sorted(tp.items, key=lambda it: (it.rec_in_f, APPEND_ORDER.get(it.track, 9)))
    session.append_items(timeline, items, media_items, start)
    session.add_markers(timeline, tp.markers, start)
    saved = session.save_project()
    warnings.extend(session.warnings[n_warn:])
    return {"timeline": name, "timeline_id": str(_safe(timeline.GetUniqueId, "") or ""), "items": len(items),
            "markers": len(tp.markers), "warnings": warnings, "start_frame": start,
            "end_frame_inclusive": session.end_frame_inclusive, "bin": "/".join(bin_parts),
            "clips": len(clips), "proxies_linked": linked, "project": session.project_name,
            "project_id": session.project_id, "resolve_version": session.version, "saved": saved}
