# Prüft das erzeugte QR-Asset: dekodierbar und exakt die Ziel-URL.
import os, sys
import cv2

PNG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "..", "..",
    "tools", "motion", "public", "clients", "man", "wz", "qr-jobs-man-eu.png",
)

def main():
    assert os.path.exists(PNG), f"fehlt: {PNG}"
    img = cv2.imread(PNG)
    daten, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    assert daten == "https://jobs.man.eu/", f"dekodiert: {daten!r}"
    h, w = img.shape[:2]
    assert min(h, w) >= 1000, f"zu klein fuer 4K-Downscale: {w}x{h}"
    print("QR OK:", daten, f"{w}x{h}")

if __name__ == "__main__":
    main()
