import { Config } from "@remotion/cli/config";
import path from "path";

Config.setOverwriteOutput(true);

Config.overrideWebpackConfig((config) => {
  return {
    ...config,
    resolve: {
      ...config.resolve,
      alias: {
        ...config.resolve?.alias,
        "@core": path.resolve(__dirname, "src/core"),
        "@components": path.resolve(__dirname, "src/components"),
        "@templates": path.resolve(__dirname, "src/templates"),
        "@utils": path.resolve(__dirname, "src/utils"),
        "@clients": path.resolve(__dirname, "src/clients"),
      },
    },
  };
});
