// Vorlage (Stand 15.09.2026): Gesichtsboxen per Apple Vision (VNDetectFaceRectanglesRequest) für alle .jpg eines Ordners.
// Build:   swiftc -O _intern/gesichtscheck/faces.swift -o _intern/gesichtscheck/faces
// Aufruf:  _intern/gesichtscheck/faces <Ordner>   → je .jpg (sortiert) eine Zeile auf stdout:
//          „datei.jpg<TAB>x0,y0,x1,y1,konfidenz;…"  (normiert 0–1, Ursprung oben links; leer = kein Gesicht; „ERR" = Lesefehler)
// Genutzt als Binärdatei _intern/gesichtscheck/faces von gesichtscheck.py, begradigen/* (Kopf-/Linienmessung) und für
// color/skripte (faces.tsv / faces_h.tsv der Grading-Analyse). Erkennt auch Profile, keine Hinterköpfe.
// Herkunft: Taxodia-Charge, _intern/gesichtscheck/faces.swift
import Foundation
import Vision
import CoreGraphics
import ImageIO

// Usage: faces <dir>  → prints "filename<TAB>x0,y0,x1,y1;..." (normalized, origin top-left)
let dir = CommandLine.arguments[1]
let fm = FileManager.default
let files = (try? fm.contentsOfDirectory(atPath: dir))?.filter { $0.hasSuffix(".jpg") }.sorted() ?? []
for f in files {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("\(f)\tERR"); continue }
    let req = VNDetectFaceRectanglesRequest()
    let handler = VNImageRequestHandler(cgImage: img, options: [:])
    do { try handler.perform([req]) } catch { print("\(f)\tERR"); continue }
    var parts: [String] = []
    for obs in (req.results ?? []) {
        let b = obs.boundingBox
        let x0 = b.minX, x1 = b.maxX
        let y0 = 1 - b.maxY, y1 = 1 - b.minY
        parts.append(String(format: "%.4f,%.4f,%.4f,%.4f,%.2f", x0, y0, x1, y1, obs.confidence))
    }
    print("\(f)\t\(parts.joined(separator: ";"))")
}
