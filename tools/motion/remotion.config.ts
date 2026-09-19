import { Config } from "@remotion/cli/config";
import path from "path";

Config.setOverwriteOutput(true);

// WebGL im Headless-Render (Remocn-Shader über @paper-design/shaders-react):
// ohne GL-Backend bleiben Shader-Flächen schwarz („WebGL is not supported").
// ANGLE = Metal auf macOS; Nicht-WebGL-Kompositionen rendern identisch
// (Pixelvergleich 19.09.2026: nur AA-Kanten, RMSE 0,3 %).
Config.setChromiumOpenGlRenderer("angle");

Config.overrideWebpackConfig((config) => {
  return {
    ...config,
    resolve: {
      ...config.resolve,
      alias: {
        ...config.resolve?.alias,
        "@": path.resolve(process.cwd(), "src"),
        "@core": path.resolve(process.cwd(), "src/core"),
        "@components": path.resolve(process.cwd(), "src/components"),
        "@templates": path.resolve(process.cwd(), "src/templates"),
        "@utils": path.resolve(process.cwd(), "src/utils"),
        "@clients": path.resolve(process.cwd(), "src/clients"),
      },
    },
  };
});
