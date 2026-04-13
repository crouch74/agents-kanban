import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          const isNodeModule = /[/\\]node_modules[/\\]/.test(id);
          const isReactGraph = /[/\\]react([-/]|$)|[/\\]scheduler[/\\]|[/\\]@radix-ui[/\\]|[/\\]react-refresh[/\\]|[/\\]react-is[/\\]/.test(
            id,
          );

          if (isNodeModule) {
            if (isReactGraph || id.includes("react") || id.includes("react-dom")) {
              return "vendor-react";
            }
            if (id.includes("@acp")) {
              return "vendor-acp";
            }
            if (id.includes("dnd-kit")) {
              return "vendor-dnd";
            }
            if (id.includes("lucide-react")) {
              return "vendor-icons";
            }
          }
        },
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    coverage: {
      enabled: false,
      provider: "v8",
      reporter: ["text", "lcov", "json-summary"],
      reportsDirectory: "../../coverage/web",
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 60,
        statements: 70,
      },
    },
  },
});
