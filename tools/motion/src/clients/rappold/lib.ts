// ============================================================
// Autohaus Rappold — CI und Basis-Maße
// Farben aus dem Logo (autohaus-rappold.de, im Chat bestätigt 16.09.2026),
// Schrift Open Sans v29 von der Website (public/clients/rappold/fonts).
// ============================================================
export const BLAU = "#0D69B3";
export const ANTHRAZIT = "#434F4F";
export const HELLGRAU = "#EBE9E8";
export const WEISS = "#FFFFFF";

export const FONT = '"RappoldOpenSans", "Open Sans", Arial, sans-serif';

// Basis-Bühne 1080×1920 — die Komposition skaliert uniform auf die Leinwand
export const BASE_W = 1080;
export const BASE_H = 1920;
export const RAND_X = 54;
export const TEXT_BREITE = BASE_W - 2 * RAND_X;
export const GRENZE_UNTEN = 1500; // darunter liegt die Plattform-UI
export const KINN_ABSTAND = 110;

// Feedback 16.09.: Schatten zu groß → eng und kurz
export const SCHATTEN = "0 2px 8px rgba(0,0,0,0.42), 0 1px 2px rgba(0,0,0,0.45)";
export const SCHATTEN_BLAU = "0 2px 10px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.45)";
