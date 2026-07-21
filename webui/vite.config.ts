import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../ktoolbox/webui/static",
    emptyOutDir: true,
    sourcemap: false,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "react-runtime",
              test: /node_modules\/(react|react-dom|react-router|scheduler)\//,
            },
            {
              name: "heroui",
              test: /node_modules\/(@heroui|react-aria|@react-aria|@react-stately|@react-types)\//,
            },
            {
              name: "data-runtime",
              test: /node_modules\/(@tanstack|i18next|react-i18next)\//,
            },
          ],
        },
      },
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8789",
    },
  },
});
