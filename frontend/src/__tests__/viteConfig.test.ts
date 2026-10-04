import { readFileSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";
import { describe, expect, it } from "vitest";
import type { ConfigEnv, PluginOption, UserConfig } from "vite";
import viteConfig from "../../vite.config";

const frontendRoot = fileURLToPath(new URL("../../", import.meta.url));

function resolveConfig(command: ConfigEnv["command"]): UserConfig {
  if (typeof viteConfig !== "function") throw new Error("vite.config.ts must export a config function");
  return viteConfig({ command, mode: command === "build" ? "production" : "development" }) as UserConfig;
}

function pluginNames(config: UserConfig): string[] {
  const flat = (config.plugins ?? []).flat(Infinity as 1) as PluginOption[];
  return flat
    .filter((p): p is { name: string } => !!p && typeof p === "object" && "name" in p)
    .map((p) => p.name);
}

describe("plain vite config", () => {
  it("keeps the dev server on port 8080, which the backend's CORS defaults expect", () => {
    const config = resolveConfig("serve");
    expect(config.server?.port).toBe(8080);
    expect(config.server?.host).toBe("::");
  });

  it("maps the @ alias to src/", () => {
    const alias = resolveConfig("serve").resolve?.alias as Record<string, string>;
    expect(alias["@"]).toBe(`${frontendRoot}src`);
  });

  it("declares Tailwind, tsconfig paths, TanStack Start and React explicitly", () => {
    const names = pluginNames(resolveConfig("serve"));
    expect(names.some((n) => n.startsWith("@tailwindcss/vite"))).toBe(true);
    expect(names).toContain("vite-tsconfig-paths");
    expect(names.some((n) => n.startsWith("tanstack-start"))).toBe(true);
    expect(names.some((n) => n.startsWith("vite:react"))).toBe(true);
  });

  it("adds nitro and the prerender shim only for builds", () => {
    const serve = pluginNames(resolveConfig("serve"));
    const build = pluginNames(resolveConfig("build"));
    expect(serve.some((n) => n.startsWith("nitro"))).toBe(false);
    expect(serve).not.toContain("prerender-preview-shim");
    expect(build.some((n) => n.startsWith("nitro"))).toBe(true);
    expect(build).toContain("prerender-preview-shim");
    expect(build).toContain("prerender-preview-shim-cleanup");
  });
});

describe("root error boundary", () => {
  it("keeps its copy and logging", () => {
    const root = readFileSync(`${frontendRoot}src/routes/__root.tsx`, "utf8");
    expect(root).toContain("console.error(error);");
    expect(root).toContain("This page didn't load");
    expect(root).toContain("Try again");
    expect(root).toContain("router.invalidate();");
  });
});
