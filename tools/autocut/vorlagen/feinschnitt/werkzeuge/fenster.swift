// Vorlage (Stand 15.09.2026): Fenster von DaVinci Resolve auflisten — erkennt die Vollbild-Wiedergabe (Cinema Viewer),
// ohne Resolve den Fokus zu geben und ohne Verbindung zur Scripting-API.
//
// Aufruf:  swiftc -O _intern/werkzeuge/fenster.swift -o "<Scratchpad>/fenster" && "<Scratchpad>/fenster"
//          (ohne Übersetzen, langsamer: swift _intern/werkzeuge/fenster.swift)
// Ausgabe: je Fenster, dessen Besitzer „Resolve" enthält: Fenster-ID, Besitzer, layer, onscreen, Breite x Höhe, Fenstername.
// Deutung (gemessen 15.09., Resolve 21.1): Das Hauptfenster heißt wie das Projekt. Ein UNBENANNTES Fenster von
//          „DaVinci Resolve" onscreen in Bildschirmgröße (am Studio-Rechner 1920x1080) = Vollbild-Viewer → der User spielt ab.
//          Fensternamen fremder Apps liefert macOS nur mit Bildschirmaufnahme-Berechtigung des aufrufenden Programms;
//          heißt auch das Hauptfenster leer, fehlt sie → Ausgabe dann nicht deuten.
// Regel:   Während der Wiedergabe keine schreibenden Aufrufe starten — DeleteClips liefert dann sofort False oder hängt,
//          run_script (MCP) hing sogar bei project.GetName(), und ein abgebrochenes Skript hat die in Resolve schon
//          eingereihte Löschung nach dem Ende der Wiedergabe trotzdem ausgeführt. Nach jedem Abbruch den Zustand neu lesen
//          (werkzeuge/stand_lesen.py, zustand.py) und fehlende eigene Items sofort wiederherstellen.
// Inhalt eines Fensters ansehen, ohne Fokuswechsel: screencapture -l <Fenster-ID> "<Scratchpad>/resolve_fenster.png"
//
// ── ANPASSEN je Charge ─────────────────────────────
// (keine chargen-spezifischen Werte)
// ── Ende ANPASSEN ──────────────────────────────────
//
// Herkunft: Taxodia-Charge, Session-Scratchpad fenster.swift
import CoreGraphics
import Foundation
let opts = CGWindowListOption(arrayLiteral: .optionAll)
let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as! [[String: Any]]
for w in list {
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    if owner.contains("Resolve") {
        let id = w[kCGWindowNumber as String] as? Int ?? 0
        let name = w[kCGWindowName as String] as? String ?? ""
        let layer = w[kCGWindowLayer as String] as? Int ?? 0
        let onscreen = w[kCGWindowIsOnscreen as String] as? Bool ?? false
        let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
        print("\(id)\t\(owner)\tlayer=\(layer)\tonscreen=\(onscreen)\t\(b["Width"] ?? 0)x\(b["Height"] ?? 0)\t\(name)")
    }
}
