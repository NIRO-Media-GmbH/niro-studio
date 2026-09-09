"""Tests für xml_patch.py — an einem Resolve-nahen FCP7-XML-Ausschnitt."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from niro_autocut import xml_patch as X
from niro_autocut.charge import AutoCutError

XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="5">
 <sequence>
  <name>T (Resolve)</name>
  <duration>300</duration>
  <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate>
  <media>
   <video>
    <track>
     <clipitem id="FX3_9557.MP4 0"><name>FX3_9557.MP4</name><duration>5688</duration>
      <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate><start>0</start><end>58</end><enabled>TRUE</enabled>
      <in>5432</in><out>5490</out>
      <file id="FX3_9557.MP4 2"><duration>5688</duration><name>FX3_9557.MP4</name></file>
      <filter><enabled>TRUE</enabled><start>0</start><end>5688</end><effect><name>Basic Motion</name><effectid>basic</effectid>
       <effecttype>motion</effecttype><mediatype>video</mediatype><effectcategory>motion</effectcategory></effect></filter>
     </clipitem>
    </track>
    <track></track>
    <track>
     <clipitem id="FX3_0010.MP4 0"><name>FX3_0010.MP4</name><duration>600</duration>
      <rate><timebase>50</timebase><ntsc>FALSE</ntsc></rate><start>120</start><end>170</end><enabled>TRUE</enabled>
      <in>50</in><out>150</out><file id="FX3_0010.MP4 2"><duration>600</duration><name>FX3_0010.MP4</name></file>
     </clipitem>
    </track>
   </video>
   <audio>
    <track>
     <clipitem id="FX3_9557.MP4 1"><name>FX3_9557.MP4</name><duration>5688</duration>
      <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate><start>0</start><end>58</end><enabled>TRUE</enabled>
      <in>5432</in><out>5490</out><file id="FX3_9557.MP4 2"/>
      <filter><enabled>TRUE</enabled><start>0</start><end>5688</end><effect><name>Audio Levels</name><effectid>audiolevels</effectid>
       <effecttype>audiolevels</effecttype><mediatype>audio</mediatype><effectcategory>audiolevels</effectcategory>
       <parameter><name>Level</name><parameterid>level</parameterid><value>1</value><valuemin>1e-05</valuemin><valuemax>31.6228</valuemax></parameter>
      </effect></filter>
     </clipitem>
     <clipitem id="FX3_9650.MP4 1"><name>FX3_9650.MP4</name><duration>15480</duration>
      <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate><start>833</start><end>975</end><enabled>TRUE</enabled>
      <in>7485</in><out>7627</out><file id="FX3_9650.MP4 2"/>
     </clipitem>
    </track>
   </audio>
  </media>
 </sequence>
</xmeml>
"""


@pytest.fixture
def xml_file(tmp_path: Path) -> Path:
    p = tmp_path / "t.xml"
    p.write_text(XML, encoding="utf-8")
    return p


def test_track_clipitems_and_find(xml_file):
    tree = X.load_xml(xml_file)
    v = X.track_clipitems(tree, "video")
    assert [(t, X.clip_name(ci), X.clip_start(ci)) for t, ci in v] == [(1, "FX3_9557.MP4", 0), (3, "FX3_0010.MP4", 120)]
    assert X.find_clipitem(tree, "audio", 1, 833, "FX3_9650.MP4") is not None
    assert X.find_clipitem(tree, "audio", 1, 834) is None


def test_set_and_get_audio_level_replaces_or_inserts(xml_file):
    tree = X.load_xml(xml_file)
    a = X.find_clipitem(tree, "audio", 1, 0)
    b = X.find_clipitem(tree, "audio", 1, 833)
    assert X.get_audio_level(a) == 1.0 and X.get_audio_level(b) is None
    X.set_audio_level(a, 2.37137)
    X.set_audio_level(b, 0.5)
    assert X.get_audio_level(a) == 2.37137 and X.get_audio_level(b) == 0.5
    assert len(a.findall("filter")) == 1                      # ersetzt, nicht dupliziert
    eff = b.find("filter/effect")
    assert eff.findtext("effectid") == "audiolevels" and b.find("filter/effect/parameter/valuemax").text == "31.6228"
    f = b.find("filter")
    assert f.findtext("start") == "0" and f.findtext("end") == "15480"   # neuer Filter: start 0, end = Clip-Dauer


def test_set_speed_adds_time_remap_and_end(xml_file):
    tree = X.load_xml(xml_file)
    ci = X.find_clipitem(tree, "video", 3, 120)
    assert X.get_speed(ci) is None
    X.set_speed(ci, 2, 220)
    assert X.get_speed(ci) == 50.0 and ci.findtext("end") == "220" and ci.findtext("in") == "50"
    names = [p.findtext("parameterid") for p in ci.findall("filter/effect/parameter")]
    assert names == ["variablespeed", "speed", "reverse", "frameblending"]


def test_set_speed_raises_when_timeremap_filter_missing_speed_param(xml_file):
    tree = X.load_xml(xml_file)
    ci = X.find_clipitem(tree, "video", 3, 120)
    f = ET.SubElement(ci, "filter")
    eff = ET.SubElement(f, "effect")
    ET.SubElement(eff, "effectid").text = "timeremap"
    with pytest.raises(AutoCutError):
        X.set_speed(ci, 2, 220)


def test_apply_patches_reports_missing_and_save_keeps_doctype(xml_file, tmp_path):
    tree = X.load_xml(xml_file)
    rep = X.apply_patches(tree, [{"track": 1, "start": 833, "name": "FX3_9650.MP4", "level": 3.0},
                                 {"track": 1, "start": 999, "name": "x", "level": 1.0}],
                          [{"track": 3, "start": 120, "name": "FX3_0010.MP4", "tempo": 2, "end": 220}])
    assert rep == {"levels_set": 1, "speeds_set": 1, "missing": ["audio Spur 1 Start 999 (x)"]}
    out = X.save_xml(tree, tmp_path / "o.xml")
    text = out.read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml')
    again = X.load_xml(out)
    assert X.read_levels(again) == [{"start": 0, "name": "FX3_9557.MP4", "level": 1.0}, {"start": 833, "name": "FX3_9650.MP4", "level": 3.0}]
    assert X.read_speeds(again) == [{"start": 120, "name": "FX3_0010.MP4", "speed": 50.0, "end": 220}]


def test_save_xml_keeps_resolve_self_closing_form(xml_file, tmp_path):
    """load_xml -> save_xml ohne Patches lässt Resolves eigene <tag/>-Form (kein Leerzeichen vor />) unangetastet."""
    tree = X.load_xml(xml_file)
    out = X.save_xml(tree, tmp_path / "roundtrip.xml")
    text = out.read_text(encoding="utf-8")
    assert '<file id="FX3_9557.MP4 2"/>' in text
    assert " />" not in text


def test_load_xml_rejects_non_xmeml(tmp_path):
    p = tmp_path / "x.xml"
    p.write_text("<foo/>", encoding="utf-8")
    with pytest.raises(AutoCutError):
        X.load_xml(p)


def test_new_filter_lands_before_link_and_comments():
    """Ein neuer Filter darf <link>/<comments> nicht ans Ende verdrängen — Resolve erwartet Filter davor
    (Review-Fund: ET.SubElement() hängt sonst ans Ende an und schiebt diese Elemente vor den neuen Filter)."""
    ci = ET.fromstring(
        '<clipitem id="c1"><name>c1</name><duration>100</duration>'
        '<filter><enabled>TRUE</enabled><start>0</start><end>100</end><effect><name>Basic Motion</name>'
        '<effectid>basic</effectid></effect></filter>'
        '<link><linkclipref>x</linkclipref></link><comments/></clipitem>')
    f = X._new_filter(ci)
    assert [c.tag for c in ci] == ["name", "duration", "filter", "filter", "link", "comments"]
    assert list(ci).index(f) == 3          # zweiter <filter> — hinter dem vorhandenen, vor <link>
    assert f.findtext("end") == "100"      # end = Clip-Dauer, unverändert
