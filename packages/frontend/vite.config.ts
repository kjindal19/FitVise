import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

// Custom service worker (injectManifest) so we can handle Web Push `push` and
// `notificationclick` events alongside Workbox precaching/offline support.
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      strategies: "injectManifest",
      srcDir: "src",
      filename: "sw.ts",
      registerType: "autoUpdate",
      injectManifest: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
      },
      manifest: {
        name: "FitVise",
        short_name: "FitVise",
        description: "Your fitness journal — coached by your own AI.",
        theme_color: "#c2410c",
        background_color: "#f6f3ec",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/icons/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" },
        ],
      },
      devOptions: { enabled: true, type: "module" },
    }),
  ],
  server: { host: true, port: 5173 },
});
