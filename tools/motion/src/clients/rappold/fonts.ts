// Lädt Open Sans (Website-Dateien) für alle Rappold-Kompositionen
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

for (const [weight, datei] of [["600", "OpenSans-600.woff2"], ["800", "OpenSans-800.woff2"]] as const) {
  loadFont({ family: "RappoldOpenSans", url: staticFile(`clients/rappold/fonts/${datei}`), weight, format: "woff2" });
}
