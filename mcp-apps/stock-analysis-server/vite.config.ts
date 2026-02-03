import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  root: "web",
  build: {
    outDir: "../dist",
    rollupOptions: {
      input: process.env.INPUT ? `web/${process.env.INPUT}` : undefined,
    },
  },
});
