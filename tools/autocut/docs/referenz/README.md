# Referenzmaterial (nicht im Produktivpfad)

- `sync_offset_gccphat.py` — zweistufiges Sync-Rezept aus der Recherche vom 03.09.2026
  (Onset-Flux-Kreuzkorrelation → GCC-PHAT-Feinstufe, Konfidenz PSR/z-Score, Drift in ppm).
  Validiert am MAN-Paar FX3_0547 × a7MK4_0015 (+4,2745 s) gegen audio-offset-finder, audalign,
  Praat, syncstart. Kandidat für einen späteren Austausch der Engine in `src/niro_autocut/sync.py`,
  falls Frame-Genauigkeit einmal nicht reicht. Empfohlene Gates: PSR ≥ 1,8, z ≥ 12, ≥ 2 Feinfenster,
  Spread < 40 ms.
