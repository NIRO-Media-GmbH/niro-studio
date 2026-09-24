"""Tests für broll_index.py — Clip-Suche, Frame-Raster, Kontaktbögen, Schema, Claude-Aufruf (Fake), Cache, Bericht."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx2 as httpx
import pytest
from PIL import Image

from niro_autocut import broll_index as B
from niro_autocut.charge import AutoCutError, Charge

CFG = {"model": "claude-opus-5", "effort": "medium", "max_tokens": 4000, "scene_threshold": 0.3,
       "frames_min": 4, "frames_max": 24, "frame_interval_s": 2.0, "tile_px": 480, "pad_px": 8, "grid": [4, 3],
       "parallel": 4}

FFMPEG = shutil.which("ffmpeg")

# Gültige Modellantwort nach CLIP_SCHEMA (wie sie Structured Outputs liefert)
ANTWORT = {
    "beschreibung_kurz": "Pflegekraft schiebt Bett durch hellen Klinikflur",
    "beschreibung": "Eine Pflegekraft in blauer Kleidung schiebt ein leeres Krankenbett durch einen hellen Flur.",
    "motive": ["Klinikflur", "Krankenbett", "Pflegekraft"],
    "personen": {"anzahl": 1, "beschreibung": "Pflegekraft in blauer Kleidung, von hinten",
                 "gesicht_erkennbar": False, "blick_in_kamera": False},
    "einstellung": "Halbtotale", "kamerabewegung": "Gimbal", "tempo": "ruhig",
    "stimmung": "ruhig, professionell", "licht": "hell, Tageslicht durch Fenster",
    "abschnitte": [{"von_s": 0.0, "bis_s": 5.35, "beschreibung": "Fahrt hinter dem Bett her",
                    "qualitaet": 4, "verwendbar": True, "maengel": []}],
    "maengel": [], "tags": ["Flur", "Bett", "Pflege", "Klinik", "Gimbal"],
    "eignung": ["Übergang", "Arbeit"], "qualitaet_gesamt": 4,
}


class FakeMessages:
    def __init__(self, payload: dict, stop_reason: str = "end_turn", fail_first: list | None = None):
        self.payload = payload
        self.stop_reason = stop_reason
        self.fail_first = list(fail_first or [])   # Exceptions, die vor der ersten Antwort geworfen werden
        self.calls: list[dict] = []

    def create(self, **kw):
        self.calls.append(kw)
        if self.fail_first:
            raise self.fail_first.pop(0)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload, ensure_ascii=False))],
            usage=SimpleNamespace(input_tokens=120, output_tokens=60, cache_read_input_tokens=1500,
                                  cache_creation_input_tokens=0),
            stop_reason=self.stop_reason, stop_details=None)


class FakeClient:
    def __init__(self, payload: dict = ANTWORT, stop_reason: str = "end_turn", fail_first: list | None = None):
        self.messages = FakeMessages(payload, stop_reason, fail_first)


def _synthetic_clip(path: Path) -> Path:
    """3 s rot + 3 s blau, 320x180, 25 fps — ein sicherer Szenenwechsel bei 3,0 s."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=3",
                    "-f", "lavfi", "-i", "color=c=blue:s=320x180:d=3", "-filter_complex",
                    "[0:v][1:v]concat=n=2:v=1:a=0", "-r", "25", str(path)], check=True)
    return path


# --- discover_broll ---------------------------------------------------------

def test_discover_broll(tmp_path):
    nas = tmp_path / "01_Footage"
    for s in ("Standort 1", "Standort 2"):
        (nas / s / "Sortiert" / "Interviews" / "Anna").mkdir(parents=True)
        (nas / s / "Sortiert" / "B-Roll" / "Flur").mkdir(parents=True)
        (nas / s / "Sortiert" / "B-Roll" / "Flur" / "FX3_1.MP4").write_bytes(b"x")
        (nas / s / "Sortiert" / "B-Roll" / "Flur" / "FX3_1.XML").write_bytes(b"<xml/>")
        (nas / s / "Sortiert" / "B-Roll" / "Flur" / "._FX3_1.MP4").write_bytes(b"applesoft")
        (nas / s / "Sortiert" / "B-Roll" / "Flur" / "Proxy").mkdir()
        (nas / s / "Sortiert" / "B-Roll" / "Flur" / "Proxy" / "FX3_1.mov").write_bytes(b"y")
    recs = [{"path": str(nas / "Standort 1" / "Sortiert" / "Interviews" / "Anna" / "FX3_9.MP4"), "kategorie": "Interviews"},
            {"path": str(nas / "Standort 2" / "Sortiert" / "Interviews" / "Anna" / "FX3_8.MP4"), "kategorie": "Interviews"}]
    clips = B.discover_broll(recs)
    assert len(clips) == 2 and {c["standort"] for c in clips} == {"Standort 1", "Standort 2"} and clips[0]["ordner"] == "Flur"
    assert all(Path(c["path"]).suffix == ".MP4" and "Proxy" not in c["path"] for c in clips)
    roots = B.broll_roots(recs)
    assert [r["standort"] for r in roots] == ["Standort 1", "Standort 2"] and all(r["vorhanden"] for r in roots)


def test_discover_broll_nested_and_extra(tmp_path):
    nas = tmp_path / "Footage"
    (nas / "Sortiert" / "Interviews").mkdir(parents=True)
    (nas / "Sortiert" / "B-Roll" / "Flur" / "Detail").mkdir(parents=True)
    (nas / "Sortiert" / "B-Roll" / "Flur" / "Detail" / "a.mov").write_bytes(b"x")
    (nas / "Sortiert" / "B-Roll" / "b.MP4").write_bytes(b"x")
    (nas / "Sortiert" / "B-Roll" / "Notaufnahme ").mkdir()          # Ordnername mit Leerzeichen am Ende (MEK)
    (nas / "Sortiert" / "B-Roll" / "Notaufnahme " / "c.MP4").write_bytes(b"x")
    extra = tmp_path / "Mavic"
    (extra / "Flug").mkdir(parents=True)
    (extra / "Flug" / "DJI_1.MP4").write_bytes(b"x")
    clips = B.discover_broll([{"path": str(nas / "Sortiert" / "Interviews" / "x.MP4")}], extra_roots=[extra])
    by_name = {Path(c["path"]).name: c for c in clips}
    assert by_name["a.mov"]["ordner"] == "Flur/Detail" and by_name["a.mov"]["standort"] is None
    assert by_name["b.MP4"]["ordner"] == ""
    assert by_name["c.MP4"]["ordner"] == "Notaufnahme" and by_name["c.MP4"]["path"].endswith("Notaufnahme /c.MP4")
    assert by_name["DJI_1.MP4"]["ordner"] == "Flug" and by_name["DJI_1.MP4"]["standort"] is None


def test_discover_broll_without_sortiert_root():
    assert B.discover_broll([{"path": "/irgendwo/ohne/struktur/x.MP4"}]) == []
    assert B.broll_roots([{"path": "/irgendwo/ohne/struktur/x.MP4"}]) == []


# --- frame_times ------------------------------------------------------------

def test_frame_times_grid_and_cuts():
    t = B.frame_times(20.0, [8.0], CFG)
    assert t[0] == pytest.approx(0.5) and 8.5 in [round(x, 1) for x in t]
    assert CFG["frames_min"] <= len(t) <= CFG["frames_max"] and t == sorted(t)
    t2 = B.frame_times(300.0, [], CFG)
    assert len(t2) == CFG["frames_max"] and t2[0] == pytest.approx(0.5) and t2[-1] == pytest.approx(299.5)


def test_frame_times_short_clip_and_invalid():
    t = B.frame_times(0.8, [], CFG)
    assert len(t) >= CFG["frames_min"] and all(0 <= x <= 0.8 for x in t) and len(set(t)) == len(t)
    with pytest.raises(AutoCutError):
        B.frame_times(0.0, [], CFG)


# --- contact_sheets ---------------------------------------------------------

def _frames(tmp_path: Path, n: int, size=(480, 270)) -> list[tuple[Path, float]]:
    frames = []
    for i in range(n):
        p = tmp_path / f"f{i}.jpg"
        Image.new("RGB", size, (i * 30 % 256, 0, 0)).save(p)
        frames.append((p, i * 2.0))
    return frames


def test_contact_sheet_layout(tmp_path):
    sheets = B.contact_sheets(_frames(tmp_path, 7), (4, 3), tmp_path / "sheet")
    assert len(sheets) == 1 and sheets[0].name == "sheet_1.jpg"
    im = Image.open(sheets[0])
    # 4 Spalten, nur 2 belegte Zeilen (7 Kacheln), 8 px Steg innen und außen
    assert im.width == 4 * 480 + 5 * 8 and im.height == 2 * 270 + 3 * 8


def test_contact_sheet_splits_and_labels(tmp_path):
    sheets = B.contact_sheets(_frames(tmp_path, 13), (4, 3), tmp_path / "s", pad_px=0)
    assert [s.name for s in sheets] == ["s_1.jpg", "s_2.jpg"]
    im1, im2 = Image.open(sheets[0]), Image.open(sheets[1])
    assert im1.size == (4 * 480, 3 * 270) and im2.size == (4 * 480, 270)
    # Label-Kasten links oben in jeder Kachel: dunkler Grund mit heller Schrift
    box = im1.crop((0, 0, 200, 40)).convert("L")
    assert box.getextrema()[1] > 200 and box.getextrema()[0] < 40


def test_contact_sheet_empty():
    assert B.contact_sheets([], (4, 3), Path("/nirgends/x")) == []


def test_tile_label():
    assert B.tile_label(3, 4.85) == "3 · 00:04.9"
    assert B.tile_label(12, 125.0) == "12 · 02:05.0"


# --- ffmpeg: Szenenwechsel + Frames -------------------------------------------

@pytest.mark.skipif(not FFMPEG, reason="ffmpeg fehlt")
def test_scene_cuts_and_extract_on_synthetic_clip(tmp_path):
    clip = _synthetic_clip(tmp_path / "t.mp4")
    cuts = B.scene_cuts(clip, 0.3)
    assert any(abs(c - 3.0) < 0.2 for c in cuts)
    frames = B.extract_frames(clip, [0.5, 4.5], tmp_path / "fr", 240, False)
    assert len(frames) == 2 and Image.open(frames[0][0]).width == 240
    assert frames[0][1] == 0.5 and frames[1][1] == 4.5
    # Hochkant: tile_px ist die Höhe
    frames_p = B.extract_frames(clip, [1.0], tmp_path / "frp", 240, True)
    assert Image.open(frames_p[0][0]).height == 240
    # Zeiten hinter dem Clip-Ende liefern keinen Frame, aber auch keinen Abbruch
    assert B.extract_frames(clip, [99.0], tmp_path / "fr", 240, False) == []


@pytest.mark.skipif(not FFMPEG, reason="ffmpeg fehlt")
def test_scene_cuts_missing_file(tmp_path):
    with pytest.raises(AutoCutError):
        B.scene_cuts(tmp_path / "fehlt.mp4", 0.3)


# --- Schema -------------------------------------------------------------------

def _walk(node, path="$"):
    yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def test_schema_has_required_fields():
    req = set(B.CLIP_SCHEMA["required"])
    assert {"beschreibung_kurz", "abschnitte", "maengel", "einstellung", "kamerabewegung", "qualitaet_gesamt"} <= req


def test_schema_obeys_structured_output_rules():
    for path, node in _walk(B.CLIP_SCHEMA):
        if isinstance(node, dict):
            for verboten in ("minimum", "maximum", "minLength", "maxLength", "pattern", "format"):
                assert verboten not in node, f"{verboten} bei {path}"
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, f"additionalProperties bei {path}"
                assert set(node["required"]) == set(node["properties"]), f"required unvollständig bei {path}"
            if "minItems" in node:
                assert node["minItems"] in (0, 1)
    scores = B.CLIP_SCHEMA["properties"]
    assert scores["qualitaet_gesamt"]["enum"] == [1, 2, 3, 4, 5]
    assert scores["abschnitte"]["items"]["properties"]["qualitaet"]["enum"] == [1, 2, 3, 4, 5]
    assert "Blick in Kamera" in scores["maengel"]["items"]["enum"]
    assert "Crew im Bild" in scores["maengel"]["items"]["enum"]  # identisch zu broll.forbidden_maengel
    assert "Logo/Marke" in scores["maengel"]["items"]["enum"]
    assert {"Opener", "Detail", "Übergang", "Emotion", "Beweis", "Team", "Ort", "Arbeit"} <= set(scores["eignung"]["items"]["enum"])


def test_schema_maengel_match_defaults():
    from niro_autocut.charge import load_config
    cfg = load_config(Path("/nirgendwo"))
    assert set(cfg["broll"]["forbidden_maengel"]) <= set(B.MAENGEL)


def test_validate_clip_record():
    assert B.validate_clip_record(ANTWORT) == []
    kaputt = dict(ANTWORT)
    del kaputt["tags"]
    kaputt["abschnitte"] = [{"von_s": 2.0, "bis_s": 1.0, "beschreibung": "x", "qualitaet": 9, "verwendbar": True}]
    kaputt["einstellung"] = "Superweit"
    probs = B.validate_clip_record(kaputt)
    assert any("tags" in p for p in probs) and any("bis_s" in p for p in probs) and any("qualitaet" in p for p in probs)
    assert any("einstellung" in p for p in probs)
    assert B.validate_clip_record({**ANTWORT, "personen": {**ANTWORT["personen"], "anzahl": True}})


# --- describe_clip (Fake-Client) ---------------------------------------------

def _sheets(tmp_path: Path, n: int = 2) -> list[Path]:
    out = []
    for i in range(1, n + 1):
        p = tmp_path / f"sheet_{i}.jpg"
        Image.new("RGB", (64, 32), (10, 10, 10)).save(p)
        out.append(p)
    return out


META = {"name": "FX3_9502.MP4", "ordner": "Notaufnahme", "standort": "Standort 1", "dauer_s": 5.35,
        "orientierung": "16:9", "cuts": [2.4], "kacheln": [{"nr": 1, "s": 0.5}, {"nr": 2, "s": 2.7}, {"nr": 3, "s": 4.85}]}


def test_describe_clip_request_shape(tmp_path):
    client = FakeClient()
    data = B.describe_clip(client, _sheets(tmp_path), META, CFG, "SYSTEM " * 300)
    assert data["beschreibung_kurz"] == ANTWORT["beschreibung_kurz"]
    assert data["_usage"] == {"input": 120, "output": 60, "cache_read": 1500, "cache_write": 0}
    kw = client.messages.calls[0]
    assert kw["model"] == "claude-opus-5" and kw["max_tokens"] == 4000
    assert kw["output_config"] == {"format": {"type": "json_schema", "schema": B.CLIP_SCHEMA}, "effort": "medium"}
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"} and kw["system"][0]["text"].startswith("SYSTEM")
    content = kw["messages"][0]["content"]
    types = [c["type"] for c in content]
    # Label „Kontaktbogen n:" vor jedem Bild, alle Bilder vor dem Meta-Text
    assert types == ["text", "image", "text", "image", "text"]
    assert content[0]["text"].startswith("Kontaktbogen 1:") and content[2]["text"].startswith("Kontaktbogen 2:")
    assert content[1]["source"]["media_type"] == "image/jpeg" and content[1]["source"]["type"] == "base64"
    text = content[-1]["text"]
    assert "FX3_9502.MP4" in text and "Kachel" in text and "3 = 4.85" in text and "Notaufnahme" in text


def test_describe_clip_rejects_too_many_images(tmp_path):
    with pytest.raises(AutoCutError, match="20"):
        B.describe_clip(FakeClient(), _sheets(tmp_path, 21), {"name": "x", "dauer_s": 1, "orientierung": "16:9"}, CFG, "s")


def test_describe_clip_reports_truncation(tmp_path):
    with pytest.raises(AutoCutError, match="max_tokens"):
        B.describe_clip(FakeClient(stop_reason="max_tokens"), _sheets(tmp_path, 1),
                        {"name": "x", "dauer_s": 1, "orientierung": "16:9"}, CFG, "s")


def test_describe_clip_reports_refusal(tmp_path):
    with pytest.raises(AutoCutError, match="abgelehnt"):
        B.describe_clip(FakeClient(stop_reason="refusal"), _sheets(tmp_path, 1),
                        {"name": "x", "dauer_s": 1, "orientierung": "16:9"}, CFG, "s")


def test_describe_clip_reports_schema_violation(tmp_path):
    with pytest.raises(AutoCutError, match="tags"):
        B.describe_clip(FakeClient(payload={k: v for k, v in ANTWORT.items() if k != "tags"}), _sheets(tmp_path, 1),
                        {"name": "x", "dauer_s": 1, "orientierung": "16:9"}, CFG, "s")


def _rate_limit() -> anthropic.RateLimitError:
    resp = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    return anthropic.RateLimitError("zu viele Anfragen", response=resp, body=None)


def test_describe_clip_retries_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(B.time, "sleep", lambda s: None)
    client = FakeClient(fail_first=[_rate_limit(), _rate_limit()])
    data = B.describe_clip(client, _sheets(tmp_path, 1), META, CFG, "s")
    assert data["beschreibung_kurz"] == ANTWORT["beschreibung_kurz"] and len(client.messages.calls) == 3


def test_describe_clip_gives_up_after_retries(tmp_path, monkeypatch):
    monkeypatch.setattr(B.time, "sleep", lambda s: None)
    client = FakeClient(fail_first=[_rate_limit()] * 10)
    with pytest.raises(AutoCutError, match="FX3_9502.MP4"):
        B.describe_clip(client, _sheets(tmp_path, 1), META, CFG, "s")
    assert len(client.messages.calls) == B.API_ATTEMPTS


def test_describe_clip_bad_request_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(B.time, "sleep", lambda s: None)
    resp = httpx.Response(400, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    client = FakeClient(fail_first=[anthropic.BadRequestError("schema kaputt", response=resp, body=None)])
    with pytest.raises(AutoCutError, match="400"):
        B.describe_clip(client, _sheets(tmp_path, 1), META, CFG, "s")
    assert len(client.messages.calls) == 1


# --- System-Prompt, Client -------------------------------------------------------

def test_system_prompt_file():
    text = B.load_system_prompt()
    # ≥ 1024 Token, sonst greift der Prompt-Cache nicht (grobe Schätzung: 3,5 Zeichen je Token)
    assert len(text) >= 1024 * 3.5
    for wort in ("Kachel", "Namen", "abschnitte", "verwendbar", "beschreibung_kurz") + tuple(B.MAENGEL) + tuple(B.EIGNUNG):
        assert wort in text, wort


def test_make_client_requires_key(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(B, "ENV_FILE", tmp_path / "keine.env")
    with pytest.raises(AutoCutError, match="ANTHROPIC_API_KEY"):
        B._make_client(CFG)


def test_make_client_reads_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = tmp_path / "test.env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-test-nur-fuer-den-test\n", encoding="utf-8")
    monkeypatch.setattr(B, "ENV_FILE", env)
    client = B._make_client(CFG)
    assert isinstance(client, anthropic.Anthropic) and client.max_retries == 5


# --- index_clip / index_broll -------------------------------------------------

@pytest.fixture
def charge(charge_dir) -> Charge:
    return Charge.open(charge_dir)


def test_index_clip_uses_cache(charge, tmp_path):
    clip = tmp_path / "nas" / "B-Roll" / "Flur" / "FX3_0002.MP4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"video")
    from niro_autocut.media import fingerprint
    fp = fingerprint(clip)
    cache_dir = charge.autocut / "broll_index"
    cache_dir.mkdir()
    rec = {**ANTWORT, "path": str(clip), "fingerprint": fp, "beschreibung_kurz": "aus dem Cache"}
    (cache_dir / f"{fp}.json").write_text(json.dumps(rec), encoding="utf-8")
    client = FakeClient()
    out = B.index_clip(charge, {"path": str(clip), "ordner": "Flur", "standort": None}, client, {"index": CFG})
    assert out["beschreibung_kurz"] == "aus dem Cache" and out["_cache"] is True
    assert client.messages.calls == []
    assert B.cached_record(charge, clip) is not None


def test_index_clip_cache_hit_refreshes_path_and_folder(charge, tmp_path):
    """Fingerprint hängt nicht am Pfad: ein umsortierter Clip bekommt Ordner/Standort/Pfad aus der aktuellen Suche."""
    clip = tmp_path / "nas" / "B-Roll" / "Neu" / "FX3_0004.MP4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"video")
    from niro_autocut.media import fingerprint
    fp = fingerprint(clip)
    cache_dir = charge.autocut / "broll_index"
    cache_dir.mkdir()
    alt = {**ANTWORT, "path": "/alt/B-Roll/Alt/FX3_0004.MP4", "datei": "FX3_0004.MP4", "fingerprint": fp,
           "ordner": "Alt", "standort": "Standort 2"}
    (cache_dir / f"{fp}.json").write_text(json.dumps(alt), encoding="utf-8")
    out = B.index_clip(charge, {"path": str(clip), "ordner": "Neu", "standort": "Standort 1"}, FakeClient(), {"index": CFG})
    assert out["_cache"] is True and out["path"] == str(clip) and out["ordner"] == "Neu" and out["standort"] == "Standort 1"
    # ohne Ordner/Standort in der Suche bleiben die Cache-Werte stehen
    out2 = B.index_clip(charge, {"path": str(clip)}, FakeClient(), {"index": CFG})
    assert out2["ordner"] == "Alt" and out2["standort"] == "Standort 2"


@pytest.mark.skipif(not FFMPEG, reason="ffmpeg fehlt")
def test_index_clip_full_pipeline_without_proxy(charge, tmp_path):
    clip = _synthetic_clip(tmp_path / "nas" / "B-Roll" / "Flur" / "FX3_0003.mp4")
    client = FakeClient()
    rec = B.index_clip(charge, {"path": str(clip), "ordner": "Flur", "standort": "Standort 1"}, client,
                       {"index": CFG}, system_prompt="SYSTEM")
    assert rec["datei"] == "FX3_0003.mp4" and rec["ordner"] == "Flur" and rec["standort"] == "Standort 1"
    assert rec["proxy"] is None and any("Proxy" in w for w in rec["warnungen"])
    assert rec["orientierung"] == "16:9" and abs(rec["dauer_s"] - 6.0) < 0.2 and rec["fps"] == 25.0
    assert any(abs(c - 3.0) < 0.2 for c in rec["szenenwechsel_s"])
    assert rec["kacheln"][0]["nr"] == 1 and len(rec["kacheln"]) >= CFG["frames_min"]
    assert rec["beschreibung_kurz"] == ANTWORT["beschreibung_kurz"] and rec["_cache"] is False
    assert rec["usage"]["cache_read"] == 1500 and rec["modell"] == "claude-opus-5" and rec["effort"] == "medium"
    # Cache geschrieben (ohne Laufzeit-Flag), Kontaktbögen und Frames unter work/
    cached = charge.autocut / "broll_index" / f"{rec['fingerprint']}.json"
    saved = json.loads(cached.read_text(encoding="utf-8"))
    assert saved["datei"] == "FX3_0003.mp4" and "_cache" not in saved and "_usage" not in saved
    assert all(Path(s).is_file() and Path(s).is_relative_to(charge.work) for s in rec["kontaktboegen"])
    # Der Meta-Text der Anfrage nennt die Kachel-Tabelle
    text = client.messages.calls[0]["messages"][0]["content"][-1]["text"]
    assert "Kachel 1 = " in text
    # zweiter Aufruf: Cache-Treffer ohne API; mit force wird neu angefragt
    rec2 = B.index_clip(charge, {"path": str(clip)}, client, {"index": CFG}, system_prompt="SYSTEM")
    assert rec2["_cache"] is True and len(client.messages.calls) == 1
    rec3 = B.index_clip(charge, {"path": str(clip)}, client, {"index": CFG}, system_prompt="SYSTEM", force=True)
    assert rec3["_cache"] is False and len(client.messages.calls) == 2


def test_index_broll_aggregates_and_limits(charge, tmp_path, monkeypatch):
    from niro_autocut.media import fingerprint
    cache_dir = charge.autocut / "broll_index"
    cache_dir.mkdir()
    clips = []
    for i in range(3):
        p = tmp_path / "nas" / "B-Roll" / "Flur" / f"FX3_000{i}.MP4"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"v" * (i + 1))
        fp = fingerprint(p)
        (cache_dir / f"{fp}.json").write_text(json.dumps({"path": str(p), "datei": p.name, "fingerprint": fp, **ANTWORT}),
                                               encoding="utf-8")
        clips.append({"path": str(p), "ordner": "Flur", "standort": "Standort 1"})
    fake = FakeClient()
    monkeypatch.setattr(B, "_make_client", lambda cfg_index: fake)
    out = B.index_broll(charge, clips, {"index": CFG}, limit=2, parallel=2)
    assert out["anzahl"] == 2 and out["fehler"] == [] and out["cache_treffer"] == 2
    assert [c["datei"] for c in out["clips"]] == ["FX3_0000.MP4", "FX3_0001.MP4"]
    assert all("_cache" not in c for c in out["clips"])
    assert fake.messages.calls == []
    saved = charge.read_json("broll_index.json")
    assert saved["anzahl"] == 2 and saved["clips"][0]["path"] == clips[0]["path"] and saved["modell"] == "claude-opus-5"


def test_index_broll_collects_errors(charge, tmp_path, monkeypatch):
    clips = [{"path": str(tmp_path / "fehlt.MP4"), "ordner": "", "standort": None}]
    monkeypatch.setattr(B, "_make_client", lambda cfg_index: FakeClient())
    out = B.index_broll(charge, clips, {"index": CFG}, limit=None, parallel=1)
    assert out["anzahl"] == 0 and len(out["fehler"]) == 1 and "fehlt.MP4" in out["fehler"][0]


# --- Kosten, Bericht ----------------------------------------------------------

def test_estimate_cost():
    s = B.estimate_cost(464)
    assert "464" in s and "€" in s
    assert "0 Clips" in B.estimate_cost(0)


def test_render_broll_index_md():
    index = {"clips": [{"datei": "FX3_1.MP4", "ordner": "Flur", "standort": "Standort 1", "dauer_s": 5.35,
                        **ANTWORT},
                       {"datei": "FX3_2.MP4", "ordner": "Kapelle", "standort": "Standort 1", "dauer_s": 12.0,
                        **ANTWORT, "maengel": ["Blick in Kamera"], "qualitaet_gesamt": 2},
                       {"datei": "DJI_1.MP4", "ordner": "Flug", "standort": None, "dauer_s": 30.0, **ANTWORT}],
             "fehler": ["FX3_9.MP4: Proxy defekt"], "anzahl": 3, "modell": "claude-opus-5"}
    md = B.render_broll_index_md(index)
    assert "## Standort 1" in md and "### Flur" in md and "### Kapelle" in md and "## Ohne Standort" in md
    assert "| FX3_1.MP4 |" in md and "Blick in Kamera" in md and "FX3_9.MP4" in md and "| DJI_1.MP4 |" in md


def test_describe_clip_retries_once_with_doubled_max_tokens(tmp_path):
    class Once(FakeMessages):
        def create(self, **kw):
            r = super().create(**kw)
            r.stop_reason = "max_tokens" if len(self.calls) == 1 else "end_turn"
            return r
    client = FakeClient()
    client.messages = Once(ANTWORT)
    data = B.describe_clip(client, _sheets(tmp_path, 1), META, CFG, "s")
    assert data["beschreibung_kurz"] == ANTWORT["beschreibung_kurz"]
    assert [c["max_tokens"] for c in client.messages.calls] == [4000, 8000]


def test_estimate_cost_small_numbers_keep_decimals():
    s = B.estimate_cost(2)
    assert "0,00" not in s.split("≈")[1].split("(")[0] and "€" in s


# --- CLI-Skript (ohne API: Fake-Client, synthetischer Clip als Extra-Wurzel) ------------------

def _script():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "autocut_index_broll", Path(__file__).resolve().parents[1] / "scripts" / "autocut_index_broll.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not FFMPEG, reason="ffmpeg fehlt")
def test_script_dry_run_and_full_run(charge_dir, tmp_path, monkeypatch, capsys):
    extra = tmp_path / "Mavic"
    _synthetic_clip(extra / "Flug" / "DJI_1.mp4")
    mod = _script()
    assert mod.main([str(charge_dir), "--dry-run", "--extra", str(extra)]) == 0
    out = capsys.readouterr().out
    assert "DJI_1.mp4" in out and "Probelauf" in out and "1 Clips" in out
    assert not (charge_dir / "_intern" / "autocut" / "broll_index.json").exists()
    monkeypatch.setattr(B, "_make_client", lambda cfg_index: FakeClient())
    assert mod.main([str(charge_dir), "--extra", str(extra), "--parallel", "1"]) == 0
    out = capsys.readouterr().out
    assert "API" in out and "Token: Eingabe 120, Ausgabe 60, Cache gelesen 1.500" in out
    saved = json.loads((charge_dir / "_intern" / "autocut" / "broll_index.json").read_text(encoding="utf-8"))
    assert saved["anzahl"] == 1 and saved["clips"][0]["ordner"] == "Flug" and saved["clips"][0]["standort"] is None
    md = (charge_dir / "Ergebnisse" / "Rohschnitt" / "broll-index.md").read_text(encoding="utf-8")
    assert "## Ohne Standort" in md and "| DJI_1.mp4 |" in md
    assert "AutoCut: B-Roll-Index" in (charge_dir / "Protokoll.md").read_text(encoding="utf-8")
    # zweiter Lauf: alles aus dem Cache, Fehlerpfad bei fehlender Wurzel
    assert mod.main([str(charge_dir), "--extra", str(extra)]) == 0
    assert "Cache" in capsys.readouterr().out
    assert mod.main([str(charge_dir)]) == 1
    assert "Sortiert" in capsys.readouterr().err


# --- index_broll: Testlauf/Teillauf ergänzt den vorhandenen Index, statt ihn zu ersetzen ---------------------------

class _ChIdx:
    """Charge-Stand-in mit read_json/write_json (index_broll braucht nur diese beiden)."""

    def __init__(self, root: Path):
        self.autocut = root
        self.work = root / "work"

    def assert_writable(self, p):
        return None

    def read_json(self, name):
        p = self.autocut / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def write_json(self, name, data):
        p = self.autocut / name
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return p


def _alt_index(ch: _ChIdx, names: tuple[str, ...]) -> None:
    ch.write_json("broll_index.json", {"erstellt_am": "2026-09-04T00:57:00", "modell": "claude-opus-5", "effort": "medium",
                                       "clips": [{"path": f"/nas/B/{n}.MP4", "beschreibung_kurz": f"alt {n}"} for n in names]})


def _fake_index_clip(fail: set[str] | None = None):
    def index_clip(charge, clip, client, cfg, system_prompt, force):
        if fail and Path(clip["path"]).stem in fail:
            raise AutoCutError("Claude-Anfrage abgewiesen (HTTP 400)")
        return {"path": clip["path"], "beschreibung_kurz": "neu", "_cache": False,
                "usage": {"input": 10, "output": 5, "cache_read": 0, "cache_write": 0}}
    return index_clip


def _run(ch: _ChIdx, monkeypatch, names: tuple[str, ...], fail: set[str] | None = None, **kw) -> dict:
    monkeypatch.setattr(B, "_make_client", lambda cfg: object())
    monkeypatch.setattr(B, "load_system_prompt", lambda: "prompt")
    monkeypatch.setattr(B, "index_clip", _fake_index_clip(fail))
    clips = [{"path": f"/nas/B/{n}.MP4", "ordner": "B", "standort": "Standort 1"} for n in names]
    return B.index_broll(ch, clips, {"index": CFG}, parallel=1, **kw)


def test_index_broll_limit_merges_into_existing_index(tmp_path, monkeypatch):
    """Live 04.09.: --limit 5 nach einem 461-Clip-Index hätte broll_index.json auf 5 Einträge ersetzt (Cache rettet die
    Daten, aber --compact/--raster/verify arbeiten bis zum nächsten Volllauf auf 5 Clips)."""
    ch = _ChIdx(tmp_path)
    _alt_index(ch, ("a", "b", "c"))
    out = _run(ch, monkeypatch, ("a", "b", "c"), limit=1)
    written = ch.read_json("broll_index.json")
    assert [c["beschreibung_kurz"] for c in written["clips"]] == ["neu", "alt b", "alt c"]
    assert out["anzahl"] == 1 and out["clips_gesamt"] == 3 and written["clips_gesamt"] == 3
    assert [c["beschreibung_kurz"] for c in out["clips"]] == ["neu", "alt b", "alt c"]


def test_index_broll_full_run_drops_clips_no_longer_discovered(tmp_path, monkeypatch):
    ch = _ChIdx(tmp_path)
    _alt_index(ch, ("a", "b", "c", "d"))                       # d liegt nicht mehr unter den B-Roll-Wurzeln
    out = _run(ch, monkeypatch, ("a", "b", "c"))
    written = ch.read_json("broll_index.json")
    assert [c["path"] for c in written["clips"]] == ["/nas/B/a.MP4", "/nas/B/b.MP4", "/nas/B/c.MP4"]
    assert all(c["beschreibung_kurz"] == "neu" for c in written["clips"]) and out["anzahl"] == 3


def test_index_broll_keeps_previous_entry_when_clip_fails(tmp_path, monkeypatch):
    ch = _ChIdx(tmp_path)
    _alt_index(ch, ("a", "b", "c"))
    out = _run(ch, monkeypatch, ("a", "b", "c"), fail={"b"})
    written = ch.read_json("broll_index.json")
    assert [c["beschreibung_kurz"] for c in written["clips"]] == ["neu", "alt b", "neu"]
    assert len(out["fehler"]) == 1 and "b.MP4" in out["fehler"][0]


def test_index_broll_without_previous_index_writes_only_this_run(tmp_path, monkeypatch):
    ch = _ChIdx(tmp_path)
    out = _run(ch, monkeypatch, ("a", "b", "c"), limit=2)
    written = ch.read_json("broll_index.json")
    assert [c["path"] for c in written["clips"]] == ["/nas/B/a.MP4", "/nas/B/b.MP4"] and out["clips_gesamt"] == 2


def test_clip_schema_kennt_maengel_je_abschnitt():
    """Spec 2026-09-23: die Verortung eines Mangels gehört in den Abschnitt, nicht nur in den Clip."""
    absch = B.CLIP_SCHEMA["properties"]["abschnitte"]["items"]
    assert absch["properties"]["maengel"] == {"type": "array", "items": {"type": "string", "enum": B.MAENGEL}}
    assert "maengel" in absch["required"]          # Structured Outputs: alle Felder required
    assert absch["additionalProperties"] is False


def test_prompt_verlangt_maengel_je_abschnitt():
    text = (B.TOOL_ROOT / "prompts" / "index-clip.md").read_text(encoding="utf-8")
    assert "maengel je Abschnitt" in text
    # Beispiel 2 (Kapelle) zeigt den Fall: Mangel nur im zweiten Abschnitt
    assert '"maengel": ["Blick in Kamera"]}], "maengel": ["Blick in Kamera"]' in text
