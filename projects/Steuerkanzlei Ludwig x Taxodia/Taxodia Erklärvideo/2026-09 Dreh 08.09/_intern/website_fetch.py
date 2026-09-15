"""Websites von Taxodia und Steuerkanzlei Ludwig sichern (nur lesen).

Holt die Startseiten, folgt internen Links eine Ebene tief und legt je Seite
HTML + Klartext in _intern/website/<host>/ ab. Grundlage für die Regel
„Nur Website-Infos in Kundeninhalten" (Captions, Einblendungen, Endcard).
"""
from __future__ import annotations

import html
import re
import subprocess
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

OUT = Path(__file__).resolve().parent / "website"
START = ["https://www.taxodia.de/", "https://lbl-bw.de/"]
MAX_PER_HOST = 40
SKIP = re.compile(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|mp4|css|js|ico|woff2?)(\?|$)", re.I)


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


class Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article", "header", "footer"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        t = html.unescape("".join(self.parts))
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = re.sub(r"\n\s*\n+", "\n", t)
        return "\n".join(line.strip() for line in t.splitlines() if line.strip())


def fetch(url: str) -> str | None:
    r = subprocess.run(["curl", "-sL", "--max-time", "25", "-A", "Mozilla/5.0 (NIRO Media Recherche)", url],
                       capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def slug(url: str) -> str:
    p = urlparse(url).path.strip("/") or "startseite"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", p)[:90]


def main() -> None:
    for start in START:
        host = urlparse(start).netloc
        target = OUT / host
        target.mkdir(parents=True, exist_ok=True)
        seen: set[str] = set()
        queue = [start]
        first = True
        while queue and len(seen) < MAX_PER_HOST:
            url = queue.pop(0).split("#")[0]
            if url in seen:
                continue
            seen.add(url)
            body = fetch(url)
            if body is None:
                print(f"  FEHLER {url}")
                continue
            name = slug(url)
            (target / f"{name}.html").write_text(body, encoding="utf-8")
            tp = Text()
            tp.feed(body)
            (target / f"{name}.txt").write_text(f"URL: {url}\n\n{tp.text()}\n", encoding="utf-8")
            print(f"  {host}: {name}")
            if first:
                lp = Links()
                lp.feed(body)
                for h in lp.hrefs:
                    u = urljoin(url, h).split("#")[0]
                    pu = urlparse(u)
                    if pu.scheme in ("http", "https") and pu.netloc.removeprefix("www.") == host.removeprefix("www.") \
                            and not SKIP.search(u) and u not in seen and u not in queue:
                        queue.append(u)
                first = False
            time.sleep(0.3)
        print(f"{host}: {len(seen)} Seiten -> {target}")


if __name__ == "__main__":
    main()
