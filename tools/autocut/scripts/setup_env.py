"""Legt tools/autocut/.env mit ANTHROPIC_API_KEY an (Quelle: macOS-Schlüsselbund, Dienst niro_autocut)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"


def main() -> None:
    if ENV.exists() and "ANTHROPIC_API_KEY=" in ENV.read_text(encoding="utf-8"):
        print(f".env vorhanden: {ENV}")
        return
    r = subprocess.run(["security", "find-generic-password", "-s", "niro_autocut", "-a", "anthropic", "-w"],
                       capture_output=True, text=True)
    key = r.stdout.strip()
    if r.returncode != 0 or not key.startswith("sk-ant-"):
        sys.exit("Kein Anthropic-Key im Schlüsselbund (Dienst niro_autocut, Konto anthropic). "
                 "Bitte ANTHROPIC_API_KEY=... von Hand in tools/autocut/.env eintragen.")
    ENV.write_text(f"# NIRO AutoCut — nicht versionieren\nANTHROPIC_API_KEY={key}\n", encoding="utf-8")
    ENV.chmod(0o600)
    print(f".env geschrieben: {ENV} (Key endet auf …{key[-4:]})")


if __name__ == "__main__":
    main()
