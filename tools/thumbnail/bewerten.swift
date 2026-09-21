// Thumbnail-Bewertung (Stand 21.09.2026) per Apple Vision für alle .jpg eines Ordners.
// Build:  swiftc -O tools/thumbnail/bewerten.swift -o tools/thumbnail/bin/bewerten   (erledigt thumbnail.py beim ersten Lauf)
// Aufruf: bewerten <Ordner>  → je .jpg (sortiert) eine JSON-Zeile auf stdout:
//   {"datei": …, "aesthetik": −1…1, "utility": bool,
//    "gesichter": [{"box": [x0, y0, x1, y1], "qualitaet": 0–1, "augen": Lidöffnung, "mund": Mundöffnung}]}
// Box normiert, Ursprung oben links. augen = Mittel beider Augen (Höhe/Breite der Landmark-Punkte), mund = Innenlippen
// Höhe/Breite; fehlende Werte = null. Lesefehler: {"datei": …, "fehler": …}. Vision schreibt Logzeilen auf stderr.
import Foundation
import Vision
import CoreGraphics
import ImageIO

func oeffnung(_ r: VNFaceLandmarkRegion2D?) -> Double? {
    guard let r = r, r.pointCount >= 4 else { return nil }
    let xs = r.normalizedPoints.map { Double($0.x) }, ys = r.normalizedPoints.map { Double($0.y) }
    let w = xs.max()! - xs.min()!, h = ys.max()! - ys.min()!
    return w > 0 ? h / w : nil
}

func zeile(_ d: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: d), let s = String(data: data, encoding: .utf8) { print(s) }
}

let ordner = URL(fileURLWithPath: CommandLine.arguments[1])
let dateien = ((try? FileManager.default.contentsOfDirectory(atPath: ordner.path)) ?? []).filter { $0.hasSuffix(".jpg") }.sorted()
for f in dateien {
    autoreleasepool {
        guard let src = CGImageSourceCreateWithURL(ordner.appendingPathComponent(f) as CFURL, nil),
              let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { zeile(["datei": f, "fehler": "lesen"]); return }
        let handler = VNImageRequestHandler(cgImage: img, options: [:])
        let aest = VNCalculateImageAestheticsScoresRequest()
        let marks = VNDetectFaceLandmarksRequest()
        do { try handler.perform([aest, marks]) } catch { zeile(["datei": f, "fehler": "\(error)"]); return }
        let faces = marks.results ?? []
        var qualitaet = [Double](repeating: -1, count: faces.count)
        if !faces.isEmpty {
            let q = VNDetectFaceCaptureQualityRequest()
            q.inputFaceObservations = faces
            if (try? handler.perform([q])) != nil, let res = q.results, res.count == faces.count {
                qualitaet = res.map { Double($0.faceCaptureQuality ?? -1) }
            }
        }
        var gesichter: [[String: Any]] = []
        for (i, o) in faces.enumerated() {
            let b = o.boundingBox
            var g: [String: Any] = ["box": [b.minX, 1 - b.maxY, b.maxX, 1 - b.minY].map { (Double($0) * 10000).rounded() / 10000 }]
            g["qualitaet"] = qualitaet[i] >= 0 ? qualitaet[i] as Any : NSNull()
            if let l = oeffnung(o.landmarks?.leftEye), let r = oeffnung(o.landmarks?.rightEye) { g["augen"] = (l + r) / 2 } else { g["augen"] = NSNull() }
            if let m = oeffnung(o.landmarks?.innerLips) { g["mund"] = m } else { g["mund"] = NSNull() }
            gesichter.append(g)
        }
        var d: [String: Any] = ["datei": f, "gesichter": gesichter, "utility": aest.results?.first?.isUtility ?? false]
        if let a = aest.results?.first { d["aesthetik"] = Double(a.overallScore) } else { d["aesthetik"] = NSNull() }
        zeile(d)
    }
}
