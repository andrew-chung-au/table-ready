import { defineConfig, type Plugin } from "vite";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import { nitro } from "nitro/vite";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { fileURLToPath, URL } from "node:url";

const root = fileURLToPath(new URL(".", import.meta.url));

// TanStack Start prerenders the SPA shell through `vite preview`, which loads
// dist/server/server.js. nitro writes the real server to .output/server/index.mjs
// instead, so point the preview at it for the prerender pass, then remove the shim.
function prerenderPreviewShim(): Plugin[] {
  const shim = `${root}dist/server/server.js`;
  return [
    {
      name: "prerender-preview-shim",
      apply: "build",
      buildApp: {
        order: "post",
        async handler() {
          await mkdir(`${root}dist/server`, { recursive: true });
          await writeFile(
            shim,
            [
              'import server from "../../.output/server/index.mjs";',
              "const ctx = { waitUntil() {}, passThroughOnException() {}, props: {} };",
              "export default {",
              "  fetch(request) {",
              '    Object.defineProperty(request, "ip", { value: undefined, writable: true, configurable: true });',
              "    return server.fetch(request, {}, ctx);",
              "  },",
              "};",
              "",
            ].join("\n"),
          );
        },
      },
    },
    {
      name: "prerender-preview-shim-cleanup",
      apply: "build",
      enforce: "post",
      buildApp: {
        order: "post",
        async handler() {
          await rm(shim, { force: true });
        },
      },
    },
  ];
}

// Plain Vite config for the TanStack Start app. Plugin order matters: Tailwind and
// tsconfig paths first, then TanStack Start, then nitro (build only), then React.
export default defineConfig(({ command }) => ({
  plugins: [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      // Keep server-only code out of the client bundle.
      importProtection: {
        behavior: "error",
        client: {
          files: ["**/server/**"],
          specifiers: ["server-only"],
        },
      },
      // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
      // nitro/vite builds from this
      server: { entry: "server" },
      // Export a static SPA shell (.output/public/_shell.html + assets) so the build can be
      // served as plain static files by the FastAPI backend, with no Node server at runtime.
      spa: { enabled: true },
    }),
    // nitro packages the build; NITRO_PRESET / SERVER_PRESET can still override the default.
    ...(command === "build"
      ? [nitro({ defaultPreset: "cloudflare-module" }), ...prerenderPreviewShim()]
      : []),
    viteReact(),
  ],
  css: { transformer: "lightningcss" },
  resolve: {
    alias: { "@": `${root}src` },
    dedupe: [
      "react",
      "react-dom",
      "react/jsx-runtime",
      "react/jsx-dev-runtime",
      "@tanstack/react-query",
      "@tanstack/query-core",
    ],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react-dom/client", "react/jsx-runtime", "react/jsx-dev-runtime"],
  },
  // The backend's default CORS origins (backend/config.py) expect the dev server on 8080.
  server: { host: "::", port: 8080 },
}));
