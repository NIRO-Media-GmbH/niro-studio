import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import resolve_sauber as R  # noqa: E402


class Mpi:
    def __init__(self, alpha="None"):
        self.alpha = alpha

    def GetClipProperty(self, key):
        return self.alpha if key == "Alpha mode" else None


class Item:
    def __init__(self, mpi, composite=0):
        self.mpi, self.composite = mpi, composite

    def GetMediaPoolItem(self):
        return self.mpi

    def GetProperty(self, key):
        return self.composite if key == "CompositeMode" else None


def test_normaler_clip_ist_kein_overlay():
    assert R.ist_overlay(Item(Mpi()), "A-Roll Perspektive A") is False


def test_alpha_ohne_datei_und_safezone_sind_overlays():
    assert R.ist_overlay(Item(Mpi("Straight")), "Edit Track02") is True
    assert R.ist_overlay(Item(None), "Edit Track02") is True
    assert R.ist_overlay(Item(Mpi()), "SAFEZONE! (control + s)") is True


def test_film_burn_im_modus_screen_ist_overlay():
    assert R.ist_overlay(Item(Mpi(), composite=5), "Edit Track04") is True
    assert R.ist_overlay(Item(Mpi(), composite=None), "Edit Track04") is False
