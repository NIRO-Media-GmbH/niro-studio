// Vorlage (Stand 15.09.2026): Personenmasken (Apple Vision, VNGeneratePersonSegmentationRequest, accurate) für alle JPGs eines
// Ordners — Grundlage für die echte Kopfoberkante in kopf_oben_messen.py.
// Bauen (im Chargen-Ordner, einmal; die Binärdatei wird nicht mitkopiert):
//   swiftc -O _intern/begradigen/personenmaske.swift -o _intern/begradigen/personenmaske
// Aufruf:
//   _intern/begradigen/personenmaske "$PWD/_intern/begradigen/kopf/frames"
// Schreibt je <name>.jpg eine Maske <name>.maske.pgm (P5, 8 bit, hell = Person, Schwelle 128); vorhandene Masken werden übersprungen.
// Konsole je Bild: "<name>.jpg<TAB><Breite>x<Höhe>", bei Fehler "ERR", ohne Ergebnis "LEER".
// Befund (15.09.): bei 960×540-Frames (16:9) kommt die Maske in 2016×1512 (4:3) → nur normierte Koordinaten verwenden.
// Herkunft: Taxodia-Charge, _intern/begradigen/personenmaske.swift
import Foundation
import Vision
import CoreGraphics
import ImageIO

// Usage: personenmaske <dir> → schreibt je <name>.jpg eine Personenmaske <name>.maske.pgm (Vision, accurate)
let dir = CommandLine.arguments[1]
let files = ((try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? []).filter { $0.hasSuffix(".jpg") }.sorted()
for f in files {
    let ziel = URL(fileURLWithPath: dir).appendingPathComponent((f as NSString).deletingPathExtension + ".maske.pgm")
    if FileManager.default.fileExists(atPath: ziel.path) { continue }
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { continue }
    let req = VNGeneratePersonSegmentationRequest()
    req.qualityLevel = .accurate
    req.outputPixelFormat = kCVPixelFormatType_OneComponent8
    do { try VNImageRequestHandler(cgImage: img, options: [:]).perform([req]) } catch { print("\(f)\tERR"); continue }
    guard let pb = req.results?.first?.pixelBuffer else { print("\(f)\tLEER"); continue }
    CVPixelBufferLockBaseAddress(pb, .readOnly)
    let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb), bpr = CVPixelBufferGetBytesPerRow(pb)
    let base = CVPixelBufferGetBaseAddress(pb)!.assumingMemoryBound(to: UInt8.self)
    var data = Data("P5\n\(w) \(h)\n255\n".utf8)
    for y in 0..<h { data.append(base + y * bpr, count: w) }
    CVPixelBufferUnlockBaseAddress(pb, .readOnly)
    try? data.write(to: ziel)
    print("\(f)\t\(w)x\(h)")
}
