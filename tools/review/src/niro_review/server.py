"""HTTP-Server: Oberfläche (ui/), JSON-API, Medien mit Range-Streaming aus Cache oder NAS (Cache-Füllung im
Hintergrund). Nur 127.0.0.1, kein Login. Spec „Server und API"."""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlsplit

from . import WERKZEUG_VERSION
from . import kommentare as km
from . import modell
from .ablage import ReviewFehler, cache_wurzel, jetzt, mac_name, name_ok, nfc, review_wurzel, sicherer_pfad

UI_ORDNER = Path(__file__).resolve().parents[2] / "ui"
BLOCK = 1024 * 1024
MEDIEN_DATEIEN = ("video.mp4", "thumb.jpg")
TYPEN = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".svg": "image/svg+xml", ".otf": "font/otf", ".ttf": "font/ttf", ".woff2": "font/woff2", ".mp4": "video/mp4",
         ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json", ".ico": "image/x-icon"}
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


class HttpFehler(Exception):
    def __init__(self, status: int, text: str):
        super().__init__(text)
        self.status = status


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, adresse, wurzel: Path, cache: Path, ui: Path = UI_ORDNER, index_ttl: float = 15.0):
        super().__init__(adresse, Handler)
        self.wurzel = Path(wurzel)
        self.cache = Path(cache)
        self.ui = Path(ui)
        self.index_ttl = index_ttl
        self.sperre = threading.RLock()
        self._index: Optional[dict] = None
        self._index_zeit = 0.0
        self.cache_laeuft: set = set()

    def nas_verbunden(self) -> bool:
        return self.wurzel.parent.is_dir()

    def index(self, frisch: bool = False) -> dict:
        with self.sperre:
            if frisch or self._index is None or time.time() - self._index_zeit > self.index_ttl:
                self._index = modell.index_bauen(self.wurzel)
                self._index_zeit = time.time()
            return self._index

    def index_verwerfen(self) -> None:
        with self.sperre:
            self._index = None

    def cache_fuellen(self, quelle: Path, ziel: Path, schluessel: str) -> None:
        with self.sperre:
            if schluessel in self.cache_laeuft:
                return
            self.cache_laeuft.add(schluessel)

        def lauf():
            tmp = ziel.with_name(ziel.name + ".teil")
            try:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(quelle, tmp)
                os.replace(tmp, ziel)
            except OSError:
                try:
                    tmp.unlink()
                except OSError:
                    pass
            finally:
                with self.sperre:
                    self.cache_laeuft.discard(schluessel)

        threading.Thread(target=lauf, daemon=True).start()


def _q1(q: dict, name: str) -> str:
    werte = q.get(name) or [""]
    return nfc(werte[0])


class Handler(BaseHTTPRequestHandler):
    server: ReviewServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # still
        pass

    # --- Einstiege -----------------------------------------------------------------------------------------------
    def do_GET(self):
        self._bedienen(False)

    def do_HEAD(self):
        self._bedienen(True)

    def do_POST(self):
        try:
            teile = urlsplit(self.path)
            pfad = unquote(teile.path)
            if not pfad.startswith("/api/"):
                raise HttpFehler(404, "Unbekannter Pfad.")
            if not self.server.nas_verbunden():
                raise HttpFehler(503, f"NAS nicht verbunden ({self.server.wurzel}).")
            self._json(self._api_post(pfad[5:], self._body()))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except HttpFehler as e:
            self._json({"fehler": str(e)}, e.status)
        except ReviewFehler as e:
            self._json({"fehler": str(e)}, 400 if e.code == 1 else 503)
        except Exception as e:  # noqa: BLE001 — Server bleibt oben, Fehler sichtbar im Browser
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    def _bedienen(self, kopf_nur: bool):
        try:
            teile = urlsplit(self.path)
            pfad = unquote(teile.path)
            q = parse_qs(teile.query)
            if pfad in ("/", "/index.html"):
                return self._datei(self.server.ui / "index.html", kopf_nur, cache="no-store")
            if pfad.startswith("/ui/"):
                ziel = sicherer_pfad(self.server.ui, pfad[4:])
                if not ziel or not ziel.is_file():
                    raise HttpFehler(404, "Datei fehlt.")
                return self._datei(ziel, kopf_nur, cache="no-store")
            if pfad.startswith("/media/"):
                return self._medien(pfad[7:], kopf_nur)
            if pfad == "/api/zustand":
                return self._json({"nas_verbunden": self.server.nas_verbunden(), "wurzel": str(self.server.wurzel),
                                   "cache": str(self.server.cache), "version": WERKZEUG_VERSION, "mac": mac_name(),
                                   "stand": jetzt()})
            if pfad.startswith("/api/"):
                if not self.server.nas_verbunden():
                    raise HttpFehler(503, f"NAS nicht verbunden ({self.server.wurzel}).")
                return self._json(self._api_get(pfad[5:], q))
            raise HttpFehler(404, "Unbekannter Pfad.")
        except (BrokenPipeError, ConnectionResetError):
            pass
        except HttpFehler as e:
            self._json({"fehler": str(e)}, e.status)
        except ReviewFehler as e:
            self._json({"fehler": str(e)}, 400 if e.code == 1 else 503)
        except Exception as e:  # noqa: BLE001
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    # --- API -----------------------------------------------------------------------------------------------------
    def _api_get(self, weg: str, q: dict):
        if weg == "index":
            return self.server.index(frisch=_q1(q, "frisch") == "1")
        if weg == "video":
            ordner, _ = self._video({k: _q1(q, k) for k in ("kunde", "projekt", "video")})
            detail = modell.video_detail(ordner)
            if not detail:
                raise HttpFehler(404, "Video unbekannt.")
            return detail
        raise HttpFehler(404, "Unbekannter API-Pfad.")

    def _api_post(self, weg: str, body: dict):
        srv = self.server
        with srv.sperre:
            if weg == "kommentar":
                ordner, _ = self._video(body)
                nr, version = self._version(ordner, body)
                if version.get("abgeschlossen"):
                    raise HttpFehler(409, f"V{nr} ist abgeschlossen — erst „Wieder öffnen“, dann kommentieren.")
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                k = km.anlegen(daten, body.get("autor"), body.get("text"), _int(body.get("frame")), _int(body.get("bis_frame")))
                km.speichern(vo, daten)
                srv.index_verwerfen()
                return k
            if weg == "kommentar/aendern":
                ordner, _ = self._video(body)
                nr, _ = self._version(ordner, body)
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                kid = str(body.get("id") or "")
                if body.get("loeschen"):
                    km.loeschen(daten, kid, body.get("autor"))
                    km.speichern(vo, daten)
                    srv.index_verwerfen()
                    return {"geloescht": kid}
                k = km.aendern(daten, kid, body.get("autor"), body.get("text"), body.get("status"))
                km.speichern(vo, daten)
                srv.index_verwerfen()
                return k
            if weg == "antwort":
                ordner, _ = self._video(body)
                nr, _ = self._version(ordner, body)
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                a = km.antworten(daten, str(body.get("id") or ""), body.get("autor"), body.get("text"))
                km.speichern(vo, daten)
                return a
            if weg in ("version/abschliessen", "version/wieder_oeffnen"):
                ordner, _ = self._video(body)
                nr, version = self._version(ordner, body)
                version["abgeschlossen"] = {"am": jetzt(), "von": _autor(body)} if weg.endswith("abschliessen") else None
                modell.version_schreiben(ordner, nr, version)
                srv.index_verwerfen()
                return version
            if weg in ("video/freigeben", "video/freigabe_zuruecknehmen"):
                ordner, video = self._video(body)
                video["freigegeben"] = {"am": jetzt(), "von": _autor(body)} if weg.endswith("freigeben") else None
                modell.video_schreiben(ordner, video)
                srv.index_verwerfen()
                return video
        raise HttpFehler(404, "Unbekannter API-Pfad.")

    def _video(self, q: dict):
        kunde, projekt, video = (str(q.get(k) or "") for k in ("kunde", "projekt", "video"))
        if not all(name_ok(x) for x in (kunde, projekt, video)):
            raise HttpFehler(404, "Video unbekannt.")
        ordner = modell.video_ordner(kunde, projekt, video, self.server.wurzel)
        daten = modell.video_lesen(ordner)
        if not daten:
            raise HttpFehler(404, "Video unbekannt.")
        return ordner, daten

    def _version(self, ordner: Path, body: dict):
        nr = _int(body.get("version"))
        if nr is None:
            raise HttpFehler(400, "Version fehlt.")
        version = modell.version_lesen(ordner, nr)
        if not version:
            raise HttpFehler(404, f"V{nr} unbekannt.")
        return nr, version

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        roh = self.rfile.read(n) if n > 0 else b""
        try:
            daten = json.loads(roh.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HttpFehler(400, "Kein gültiges JSON.")
        if not isinstance(daten, dict):
            raise HttpFehler(400, "JSON-Objekt erwartet.")
        return {k: (nfc(v) if isinstance(v, str) else v) for k, v in daten.items()}

    # --- Medien --------------------------------------------------------------------------------------------------
    def _medien(self, rel: str, kopf_nur: bool):
        if rel.rsplit("/", 1)[-1] not in MEDIEN_DATEIEN:
            raise HttpFehler(404, "Datei fehlt.")
        nas = sicherer_pfad(self.server.wurzel, rel)
        cache = sicherer_pfad(self.server.cache, rel)
        nas_da = nas is not None and nas.is_file()
        quelle, herkunft = None, "nas"
        if cache is not None and cache.is_file():
            if not nas_da or cache.stat().st_size == nas.stat().st_size:
                quelle, herkunft = cache, "cache"
        if quelle is None and nas_da:
            quelle = nas
            if cache is not None and rel.endswith("video.mp4"):
                self.server.cache_fuellen(nas, cache, nfc(rel))
        if quelle is None:
            raise HttpFehler(404, "Datei fehlt.")
        self._datei(quelle, kopf_nur, cache="private, max-age=86400", range_header=self.headers.get("Range"),
                    extra={"X-Quelle": herkunft})

    def _datei(self, pfad: Path, kopf_nur: bool, cache: str = "no-cache", range_header: Optional[str] = None,
               extra: Optional[dict] = None):
        groesse = pfad.stat().st_size
        typ = TYPEN.get(pfad.suffix.lower(), "application/octet-stream")
        start, ende, status = 0, groesse - 1, 200
        if range_header:
            m = _RANGE.match(range_header.strip())
            a, b = (m.group(1), m.group(2)) if m else ("", "")
            if not m or (a == "" and b == ""):
                return self._416(groesse)
            if a == "":
                start, ende = max(0, groesse - int(b)), groesse - 1
            else:
                start, ende = int(a), (int(b) if b else groesse - 1)
            if start >= groesse or start > ende:
                return self._416(groesse)
            ende = min(ende, groesse - 1)
            status = 206
        laenge = max(0, ende - start + 1)
        self.send_response(status)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(laenge))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", cache)
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{ende}/{groesse}")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if kopf_nur or laenge == 0:
            return
        with open(pfad, "rb") as f:
            f.seek(start)
            rest = laenge
            while rest > 0:
                block = f.read(min(BLOCK, rest))
                if not block:
                    break
                self.wfile.write(block)
                rest -= len(block)

    def _416(self, groesse: int):
        self.send_response(416)
        self.send_header("Content-Range", f"bytes */{groesse}")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, daten, status: int = 200):
        roh = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(roh)


def _int(wert) -> Optional[int]:
    if wert is None or wert == "":
        return None
    try:
        return int(wert)
    except (TypeError, ValueError):
        raise HttpFehler(400, f"Zahl erwartet, nicht „{wert}“.")


def _autor(body: dict) -> str:
    return str(body.get("autor") or "").strip() or "Unbekannt"


def starten(port: int = 4711, wurzel: Optional[Path] = None, cache: Optional[Path] = None) -> None:
    srv = ReviewServer(("127.0.0.1", port), wurzel or review_wurzel(), cache or cache_wurzel())
    print(f"NIRO Review {WERKZEUG_VERSION} · http://localhost:{port} · Wurzel {srv.wurzel} · Cache {srv.cache}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
