"""Fake-Resolve für Tests — bildet die benutzten Teile der Scripting-API nach (Aufrufreihenfolge, Frames, Settings).

Nachgebildete Eigenheiten (Recherche 03.09. + README/CHANGELOG):
- ``AppendToTimeline`` schreibt nur in die aktuelle Timeline und schlägt ohne ``SetSelectedClip`` fehl (20.3.2).
- ``endFrame``-Semantik ist per Klassenattribut ``FakeTimeline.inclusive`` umschaltbar (Probe misst sie live).
- ``useCustomSettings='1'`` setzt die Color-Management-Keys zurück (BMD-Bug, Forum t=212784).
- ``AddMarker`` erlaubt nur einen Marker pro Frame; mit ``reject_beyond_end`` auch keinen hinter dem letzten Clip.
- ``recordFrame`` ist absolut (Startframe 90000 bei 01:00:00:00 @ 25 fps), ``AddMarker(frameId)`` relativ.
- 21.1: Properties/Speed/Fades/Transition/Normalize/AutoAlign/QuickExport (Semantiken per Klassen-Flags, siehe Probe resolve_probe_api.py).
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

COLOR_DEFAULTS = {
    "colorScienceMode": "davinciYRGBColorManagedv2", "colorSpaceTimeline": "DaVinci WG/Intermediate",
    "colorSpaceTimelineGamma": "", "colorSpaceOutput": "Rec.709 Gamma 2.4", "colorSpaceOutputGamma": "",
    "separateColorSpaceAndGamma": "0", "isAutoColorManage": "1", "rcmPresetMode": "SDR Rec.709",
    "useCATransform": "1", "disableFusionToneMapping": "0", "timelineInputResMismatchBehavior": "scaleToFit",
    "timelineOutputResMismatchBehavior": "scaleToFit", "videoMonitorFormat": "HD 1080p 25",
}


def _tc_to_frames(tc: str, fps: int = 25) -> int:
    h, m, s, f = (int(x) for x in tc.split(":"))
    return ((h * 60 + m) * 60 + s) * fps + f


class FakeItem:
    """MediaPoolItem."""

    _uid_counter = 0    # laufende Nummer über alle Items — macht Duplikate (gleicher Pfad) unterscheidbar

    def __init__(self, path: str):
        self.path = path
        self.proxy = None
        self.props = {"File Path": path, "Proxy": "None", "Video Codec": "H.264", "FPS": "25", "Alpha mode": "None"}
        self.link_calls = 0
        FakeItem._uid_counter += 1
        self._uid_n = FakeItem._uid_counter

    def GetClipProperty(self, key=None):
        return dict(self.props) if key is None else self.props.get(key, "")

    def SetClipProperty(self, k, v):
        self.props[k] = str(v)
        return True

    def LinkProxyMedia(self, p):
        self.link_calls += 1
        self.proxy = p
        self.props["Proxy"] = "1920x1080"
        return True

    def GetName(self):
        return self.path.split("/")[-1]

    def GetUniqueId(self):
        return f"mpi-{self.GetName()}-{self._uid_n}"


class FakeFolder:
    def __init__(self, name: str):
        self.name = name
        self.clips: list = []
        self.subs: list = []

    def GetName(self):
        return self.name

    def GetClipList(self):
        return list(self.clips)

    def GetSubFolderList(self):
        return list(self.subs)

    def GetUniqueId(self):
        return "folder-" + self.name


class FakeTransition:
    """Rückgabe von TimelineItem.AddTransition (21.1): eigenes Item mit GetType() == 'transition'."""

    def __init__(self, opts: dict):
        self.opts = dict(opts)
        self.dur = int(opts.get("duration") or 12)

    def GetType(self):
        return "transition"

    def GetDuration(self, *a):
        return self.dur

    def GetName(self):
        return str(self.opts.get("type", ""))


class FakeTLItem:
    """TimelineItem — Dauer nach der endFrame-Semantik der Timeline."""

    def __init__(self, info: dict, inclusive: bool, kind: str, index: int):
        self.info = info
        self.enabled = True
        self.kind, self.index = kind, index
        self.start = int(info["recordFrame"])
        # Resolve konformiert Quellframes auf die Timeline-Bildrate (25p): 50p-Quellmaterial liefert die
        # halbe Framezahl. mediaPoolItem ist normalerweise ein FakeItem; in seltenen Fällen (Import) auch
        # eine FakeTimeline ohne .props — dann gilt die Standard-FPS 25.
        mpi = info["mediaPoolItem"]
        src_n = int(info["endFrame"]) - int(info["startFrame"]) + (1 if inclusive else 0)
        fps = float(getattr(mpi, "props", {}).get("FPS", 25))
        self.dur = int(round(src_n * 25 / fps))
        self.refuse_disable = False
        self.level = 1.0
        self.speed = 100.0
        self.color = ""
        self.timeline = None                 # setzt AppendToTimeline/ImportTimelineFromFile (SetSpeed braucht die Nachbarn)
        self.src0 = (int(info["startFrame"]), int(info["endFrame"]))   # Quellbereich bei 100 % — Basis für SetSpeed ohne Verkettung
        self.props = {"AudioVolume": 0.0, "AudioVolumeEnabled": True, "Opacity": 100.0}
        self.fades = {"FadeIn": 0, "FadeOut": 0}

    # Plan-Test greift auf .enabled zu
    def SetClipEnabled(self, v):
        if self.refuse_disable:
            return False
        self.enabled = bool(v)
        return True

    def GetClipEnabled(self):
        return self.enabled

    def GetStart(self, *a):
        return self.start

    def GetEnd(self, *a):
        return self.start + self.dur

    def GetDuration(self, *a):
        return self.dur

    def GetName(self):
        return self.info["mediaPoolItem"].GetName()

    def GetMediaPoolItem(self):
        return self.info["mediaPoolItem"]

    def GetSourceStartFrame(self):
        return int(self.info["startFrame"])

    def GetSourceEndFrame(self):
        return int(self.info["endFrame"])

    def GetUniqueId(self):
        return f"tli-{self.kind}{self.index}-{self.start}"

    def SetClipColor(self, c):
        self.color = c
        return True

    def GetClipColor(self):
        return self.color

    # --- 21.1 -----------------------------------------------------------
    def GetType(self):
        return self.kind

    def GetProperties(self):
        return dict(self.props)

    def SetProperties(self, props):
        """Wie Resolve: alle Schlüssel werden vorab geprüft — entweder alles oder nichts."""
        for k, v in props.items():
            if k not in self.props:
                return False
            if k == "AudioVolume" and not (-100.0 <= float(v) <= 30.0):
                return False
        for k, v in props.items():
            self.props[k] = float(v) if isinstance(self.props[k], float) else v
        return True

    def GetFades(self):
        return dict(self.fades)

    def SetFades(self, fades):
        tl = self.timeline
        if tl is not None and tl.fades_need_active and tl.project.current is not tl:
            return False
        for k in ("FadeIn", "FadeOut"):
            if k in fades:
                self.fades[k] = int(fades[k])
        return True

    def GetSpeed(self):
        return {"Percentage": float(self.speed)}

    def SetSpeed(self, opts):
        """Semantik per FakeTimeline.speed_extends: True = Clip verlängert sich in eine Lücke (bleibt am Nachbarn
        stehen), False = Timeline-Dauer bleibt, Quellbereich schrumpft. RippleTimeline verschiebt Nachfolger."""
        pct = float(opts.get("Percentage", 100.0))
        if pct <= 0:
            return False
        ripple = bool(opts.get("RippleTimeline", False))
        tl = self.timeline
        new_dur = int(round(self.dur * self.speed / pct))
        self.speed = pct
        later = sorted((o for o in (tl.GetItemListInTrack(self.kind, self.index) if tl is not None else [])
                        if o.start > self.start), key=lambda o: o.start)
        if ripple:
            delta = new_dur - self.dur
            for o in later:
                o.start += delta
            self.dur = new_dur
        elif tl is None or tl.speed_extends:
            limit = later[0].start if later else None
            self.dur = new_dur if limit is None or self.start + new_dur <= limit else max(self.dur, limit - self.start)
        else:
            start, end0 = self.src0
            n = int(round((end0 - start) * pct / 100.0))
            self.info["endFrame"] = start + n          # in place: FakeTimeline.items teilt dasselbe Dict
        return True

    def AddTransition(self, opts):
        if opts.get("category") not in ("simple", "fusion", "ofx", "audio") or opts.get("position") not in ("start", "end"):
            return None
        tr = FakeTransition(opts)
        if self.timeline is not None:
            self.timeline.transitions.append(tr)
        return tr


class FakeTimeline:
    inclusive = True            # endFrame-Semantik (Probe misst sie live)
    reject_beyond_end = False   # Marker hinter dem letzten Clip ablehnen (Resolve-Verhalten)
    speed_extends = True        # SetSpeed: True = verlängert in Lücken, False = behält Timeline-Dauer (Probe misst live)
    fades_need_active = False   # SetFades nur auf der aktiven Timeline erlaubt?
    align_moves = "V2"          # AutoAlignClips bewegt das zweite ("V2") oder erste ("V1") Item
    align_offset_frames = -50   # … um so viele Frames (V2 nach vorn)
    tpk_dbfs = -12.0            # True Peak, den NormalizeAudioLevel „misst"
    NORMALIZE_MODES = ["Sample Peak Program", "True Peak", "ITU-R BS.1770-4", "EBU R128"]

    def __init__(self, name: str, project: "FakeProject"):
        self.name = name
        self.project = project
        # Wie Resolve: eine neue Timeline erbt die Projekt-Auflösung (useCustomSettings=0)
        pw = str(project.settings.get("timelineResolutionWidth", "1920")) if project is not None else "1920"
        ph = str(project.settings.get("timelineResolutionHeight", "1080")) if project is not None else "1080"
        self.settings = {"timelineResolutionWidth": pw, "timelineResolutionHeight": ph,
                         "timelineOutputResolutionWidth": pw, "timelineOutputResolutionHeight": ph,
                         "useCustomSettings": "0", "timelineFrameRate": "25", **COLOR_DEFAULTS}
        self.tracks = {"video": 1, "audio": 1}
        self.items: list[dict] = []           # clipInfos in Append-Reihenfolge (Plan-Test liest t.items)
        self.tl_items: list[FakeTLItem] = []
        self.markers: list[tuple] = []        # (frame, color, name) — Plan-Test liest t.markers[0]
        self.marker_data: dict[int, dict] = {}
        self.names: dict[tuple, str] = {}
        self.start_tc = "01:00:00:00"
        self.start_frame = 90000
        self.linked: list[list] = []
        self.exports: list[tuple] = []
        self.transitions: list = []
        self.align_calls: list[tuple] = []
        self.normalize_calls: list[tuple] = []

    def GetName(self):
        return self.name

    def SetName(self, n):
        if any(t.name == n for t in self.project.timelines):
            return False
        self.name = n
        return True

    def GetUniqueId(self):
        return "tl-" + self.name

    def GetClipProperty(self, key=None):
        """Timelines liegen als MediaPoolItem im Media Pool — ohne Dateipfad."""
        props = {"File Path": "", "Proxy": "None"}
        return props if key is None else props.get(key, "")

    def SetSetting(self, k, v):
        if k == "useCustomSettings" and str(v) == "1":
            for key in COLOR_DEFAULTS:      # BMD-Bug: Color-Keys werden zurückgesetzt
                self.settings[key] = ""
        self.settings[k] = str(v)
        return True

    def GetSetting(self, k):
        return self.settings.get(k)

    def GetTrackCount(self, t):
        return self.tracks[t]

    def AddTrack(self, t, *a):
        self.tracks[t] += 1
        return True

    def SetTrackName(self, t, i, n):
        # Wie Resolve live (04.09.2026, finalize.py): Spurnamen lassen sich nur auf der aktiven Timeline setzen.
        if self.project is not None and self.project.current is not self:
            return False
        self.names[(t, i)] = n
        return True

    def GetTrackName(self, t, i):
        return self.names.get((t, i), f"{t[0].upper()}{i}")

    def GetStartFrame(self):
        return self.start_frame

    def content_end_rel(self) -> int:
        return max((it.start + it.dur for it in self.tl_items), default=0) - self.start_frame

    def GetEndFrame(self):
        return self.start_frame + self.content_end_rel()

    def SetStartTimecode(self, tc):
        self.start_tc = tc
        self.start_frame = _tc_to_frames(tc)
        return True

    def GetStartTimecode(self):
        return self.start_tc

    def AddMarker(self, frame, color, name, note, dur, custom=""):
        frame = int(frame)
        if frame in self.marker_data:
            return False
        if self.reject_beyond_end and frame >= self.content_end_rel():
            return False
        self.markers.append((frame, color, name))
        self.marker_data[frame] = {"color": color, "name": name, "note": note, "duration": dur, "customData": custom}
        return True

    def GetMarkers(self):
        return {float(k): dict(v) for k, v in self.marker_data.items()}

    def GetItemListInTrack(self, kind, idx):
        return [it for it in self.tl_items if it.kind == kind and it.index == idx]

    def SetClipsLinked(self, items, flag):
        self.linked.append(list(items))
        return True

    # --- 21.1 -----------------------------------------------------------
    def GetNormalizeAudioModes(self):
        return list(self.NORMALIZE_MODES)

    def NormalizeAudioLevel(self, items, opts=None):
        opts = dict(opts or {})
        mode = opts.get("normalizationMode", "Sample Peak Program")
        if mode not in self.NORMALIZE_MODES:
            return False
        self.normalize_calls.append((list(items), opts))
        target = float(opts.get("targetLevel", -9.0))
        for it in items:
            it.props["AudioVolume"] = round(target - float(self.tpk_dbfs), 3)
            it.props["AudioVolumeEnabled"] = True
        return True

    def AutoAlignClips(self, items, opts=None):
        """Bewegt ein Item samt gleich startendem Ton derselben Spurnummer (verknüpftes Paar)."""
        if len(items) < 2:
            return False
        self.align_calls.append((list(items), dict(opts or {})))
        first, second = items[0], items[1]
        mover = second if self.align_moves == "V2" else first
        delta = int(self.align_offset_frames) if mover is second else -int(self.align_offset_frames)
        start = mover.start
        for it in self.tl_items:
            if it.index == mover.index and it.start == start:
                it.start += delta
        return True

    def _xmeml(self) -> str:
        def clip(it, media):
            rel = it.start - self.start_frame
            src_in, src_out = it.GetSourceStartFrame(), it.GetSourceEndFrame()
            name = escape(it.GetName())               # Clip-Namen/Pfade können XML-Sonderzeichen enthalten
            path = escape(it.GetMediaPoolItem().path)  # (&, <, >) — roh interpoliert würde das XML kaputt machen
            lvl = ""
            if media == "video" and getattr(it, "speed", 100.0) != 100.0:
                lvl = (f"<filter><enabled>TRUE</enabled><start>-1</start><end>-1</end><effect><name>Time Remap</name><effectid>timeremap</effectid>"
                       f"<effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>"
                       f"<parameter><parameterid>variablespeed</parameterid><name>variablespeed</name><value>0</value></parameter>"
                       f"<parameter><parameterid>speed</parameterid><name>speed</name><value>{it.speed:g}</value></parameter></effect></filter>")
            if media == "audio" and it.level != 1.0:
                lvl = (f"<filter><enabled>TRUE</enabled><start>0</start><end>{it.dur}</end><effect><name>Audio Levels</name>"
                       f"<effectid>audiolevels</effectid><effecttype>audiolevels</effecttype><mediatype>audio</mediatype>"
                       f"<effectcategory>audiolevels</effectcategory><parameter><name>Level</name><parameterid>level</parameterid>"
                       f"<value>{it.level:g}</value><valuemin>1e-05</valuemin><valuemax>31.6228</valuemax></parameter></effect></filter>")
            return (f'<clipitem id="{name} {rel}"><name>{name}</name><duration>99999</duration>'
                    f"<rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate><start>{rel}</start><end>{rel + it.dur}</end>"
                    f"<enabled>{'TRUE' if it.enabled else 'FALSE'}</enabled><in>{src_in}</in><out>{src_out}</out>"
                    f'<file id="{name} f"><name>{name}</name><pathurl>file://{path}</pathurl></file>{lvl}</clipitem>')
        parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<!DOCTYPE xmeml>", '<xmeml version="5"><sequence>',
                 f"<name>{escape(self.name)} (Resolve)</name><rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate>",
                 f"<timecode><string>{self.start_tc}</string><frame>{self.start_frame}</frame></timecode><media>"]
        for media in ("video", "audio"):
            parts.append(f"<{media}>")
            for idx in range(1, self.tracks[media] + 1):
                parts.append("<track>" + "".join(clip(it, media) for it in self.GetItemListInTrack(media, idx)) + "</track>")
            parts.append(f"</{media}>")
        parts.append("</media></sequence></xmeml>")
        return "\n".join(parts)

    def Export(self, path, kind, sub=None):
        self.exports.append((str(path), kind, sub))
        Path(path).write_text(self._xmeml(), encoding="utf-8")
        return True


class FakeMediaPool:
    def __init__(self, project: "FakeProject"):
        self.project = project
        self.root = FakeFolder("Master")
        self.current = self.root
        self.selected = None
        self.calls: list[tuple] = []
        self.refreshed = 0
        self.fps_by_path: dict[str, object] = {}   # Tests füllen vorab (Konform-Simulation 50p/100p)
        self.alpha_by_path: dict[str, str] = {}

    def GetRootFolder(self):
        return self.root

    def GetCurrentFolder(self):
        return self.current

    def SetCurrentFolder(self, f):
        self.current = f
        return True

    def RefreshFolders(self):
        self.refreshed += 1
        return True

    def AddSubFolder(self, parent, name):
        f = FakeFolder(name)
        parent.subs.append(f)
        self.calls.append(("AddSubFolder", name))
        return f

    def ImportMedia(self, paths):
        items = [FakeItem(p) for p in paths]
        for it in items:
            it.props["FPS"] = str(self.fps_by_path.get(it.path, "25"))
            it.props["Alpha mode"] = str(self.alpha_by_path.get(it.path, "None"))
        self.current.clips.extend(items)
        self.calls.append(("ImportMedia", list(paths)))
        return items

    def SetSelectedClip(self, item):
        self.selected = item
        self.calls.append(("SetSelectedClip", item.GetName()))
        return True

    def CreateEmptyTimeline(self, name):
        t = FakeTimeline(name, self.project)
        self.project.timelines.append(t)
        self.root.clips.append(t)     # Timelines erscheinen im Media Pool wie Clips
        self.project.current = t
        return t

    def DeleteTimelines(self, tls):
        for t in tls:
            self.project.timelines.remove(t)
            if t in self.root.clips:
                self.root.clips.remove(t)
        self.calls.append(("DeleteTimelines", [t.name for t in tls]))
        return True

    def AppendToTimeline(self, infos):
        self.calls.append(("AppendToTimeline", len(infos)))
        t = self.project.current
        if t is None or self.selected is None:      # 20.3.2: ohne selektierten Clip schlägt Append fehl
            return None
        out = []
        for info in infos:
            kind = "audio" if info.get("mediaType") == 2 else "video"
            tl = FakeTLItem(info, t.inclusive, kind, int(info.get("trackIndex", 1)))
            tl.timeline = t
            t.items.append(info)
            t.tl_items.append(tl)
            out.append(tl)
        return out

    def ImportTimelineFromFile(self, path, opts):
        from niro_autocut import xml_patch as X
        tree = X.load_xml(path)
        t = FakeTimeline(opts.get("timelineName") or "Import", self.project)
        self.project.timelines.append(t)
        self.root.clips.append(t)
        self.project.current = t
        folders = list(opts.get("sourceClipsFolders") or [])
        by_name = {c.GetName(): c for f in folders for c in f.GetClipList()}
        # Spur-Anzahl aus der XML-STRUKTUR übernehmen (auch leere, nachgestellte Spuren wie ein
        # ungenutztes B-Roll-V3) — nur aus belegten Clipitems abzuleiten würde solche Spuren beim
        # Re-Import verlieren, weil eine leere Spur gar kein Clipitem zum Zählen liefert.
        for media in ("video", "audio"):
            t.tracks[media] = max(1, len(tree.getroot().findall(f"sequence/media/{media}/track")))
        for media in ("video", "audio"):
            for idx, ci in X.track_clipitems(tree, media):
                while t.tracks[media] < idx:
                    t.tracks[media] += 1
                name = X.clip_name(ci)
                mpi = by_name.get(name) or FakeItem("/import/" + name)
                start, end = X.clip_start(ci), int(float(ci.findtext("end")))
                src_in, src_out = int(float(ci.findtext("in"))), int(float(ci.findtext("out")))
                info = {"mediaPoolItem": mpi, "startFrame": src_in, "endFrame": src_out, "recordFrame": t.start_frame + start,
                        "trackIndex": idx, "mediaType": 2 if media == "audio" else 1}
                it = FakeTLItem(info, False, media, idx)
                it.timeline = t
                it.dur = end - start
                it.enabled = (ci.findtext("enabled") or "TRUE").upper() == "TRUE"
                lv = X.get_audio_level(ci)
                if lv is not None:
                    it.level = lv
                sp = X.get_speed(ci)
                if sp is not None:
                    it.speed = sp
                t.tl_items.append(it)
                t.items.append(info)
        self.calls.append(("ImportTimelineFromFile", t.name))
        return t

    def AddItemListToMediaPool(self, paths):
        items = [FakeItem(p) for p in paths]
        self.current.clips.extend(items)
        self.calls.append(("AddItemListToMediaPool", list(paths)))
        return items

    def DeleteClips(self, clips):
        for f in self._all_folders():
            f.clips = [c for c in f.clips if c not in clips]
        self.calls.append(("DeleteClips", len(clips)))
        return True

    def DeleteFolders(self, folders):
        for parent in self._all_folders():
            parent.subs = [s for s in parent.subs if s not in folders]
        self.calls.append(("DeleteFolders", [f.name for f in folders]))
        return True

    def _all_folders(self):
        out, stack = [], [self.root]
        while stack:
            f = stack.pop()
            out.append(f)
            stack.extend(f.subs)
        return out

    @property
    def timeline(self):
        return self.project.current


class FakeProject:
    def __init__(self, name: str = "Test"):
        self.name = name
        self.mp = FakeMediaPool(self)
        self.settings = {"timelineFrameRate": "25", "timelineResolutionWidth": "3840", "timelineResolutionHeight": "2160"}
        self.timelines: list[FakeTimeline] = []
        self.current: FakeTimeline | None = None
        self.saved = 0
        self.quick_presets = ["H.264 Master", "H.265 Master", "ProRes 422 HQ", "YouTube"]
        self.renders: list[tuple] = []

    def GetMediaPool(self):
        return self.mp

    def GetName(self):
        return self.name

    def GetUniqueId(self):
        return "proj-1"

    def GetSetting(self, k):
        return self.settings.get(k)

    def SetSetting(self, k, v):
        self.settings[k] = v
        return True

    def GetCurrentTimeline(self):
        return self.current

    def SetCurrentTimeline(self, t):
        self.current = t
        return True

    def GetTimelineCount(self):
        return len(self.timelines)

    def GetTimelineByIndex(self, i):
        return self.timelines[i - 1]

    def SaveProject(self):
        self.saved += 1
        return True

    # --- 21.1 -----------------------------------------------------------
    def GetQuickExportRenderPresets(self):
        return list(self.quick_presets)

    def IsRenderingInProgress(self):
        return False

    def RenderWithQuickExport(self, preset, settings=None):
        settings = dict(settings or {})
        if preset not in self.quick_presets or self.current is None:
            return {"JobStatus": "Render Failed", "CompletionPercentage": 0,
                    "Error": f"Preset '{preset}' unbekannt oder keine aktuelle Timeline"}
        target = Path(settings.get("TargetDir", "."))
        target.mkdir(parents=True, exist_ok=True)
        out = target / f"{settings.get('CustomName') or self.current.name}.mov"
        out.write_bytes(b"fake render")
        self.renders.append((preset, str(out)))
        return {"JobStatus": "Render Complete", "CompletionPercentage": 100, "TimeTakenToRenderInMs": 1234}


class FakeResolve:
    EXPORT_FCP_7_XML = 11
    EXPORT_OTIO = 16
    EXPORT_EDL = 2
    EXPORT_NONE = 0
    NORMALIZE_AUDIO_SET_LEVEL_RELATIVE = 0
    NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT = 1
    AUTO_ALIGN_CLIPS_USING_TIMECODE = 0
    AUTO_ALIGN_CLIPS_USING_WAVEFORM = 1
    AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_AUTOMATIC = -1
    AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_MIX = -2

    def __init__(self, project: FakeProject | None = None):
        self.p = project or FakeProject()

    def GetProjectManager(self):
        return self

    def GetCurrentProject(self):
        return self.p

    def GetVersionString(self):
        return "21.1.0.14"
