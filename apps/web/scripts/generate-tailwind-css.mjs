import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "tailwindcss";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webRoot = path.resolve(__dirname, "..");
const sourceCssPath = path.join(webRoot, "src", "index.css");
const outputCssPath = path.join(webRoot, "src", "tailwind.generated.css");
const sourceDir = path.join(webRoot, "src");

const CLASS_CANDIDATE_PATTERN = /[^<>"'`\s]*[^<>"'`\s:]/g;
const SOURCE_FILE_PATTERN = /\.(tsx|ts|jsx|js|html|css)$/;

async function walkFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walkFiles(entryPath)));
      continue;
    }
    if (SOURCE_FILE_PATTERN.test(entry.name) && entry.name !== "tailwind.generated.css") {
      files.push(entryPath);
    }
  }
  return files;
}

async function collectCandidates() {
  const sourceFiles = await walkFiles(sourceDir);
  const candidates = new Set();

  for (const filePath of sourceFiles) {
    const content = await fs.readFile(filePath, "utf8");
    for (const match of content.matchAll(CLASS_CANDIDATE_PATTERN)) {
      candidates.add(match[0]);
    }
  }

  return [...candidates];
}

async function loadStylesheet(id, base) {
  let resolvedPath;
  if (id === "tailwindcss") {
    resolvedPath = path.join(webRoot, "..", "..", "node_modules", "tailwindcss", "index.css");
  } else {
    resolvedPath = path.resolve(base ?? webRoot, id);
  }

  const content = await fs.readFile(resolvedPath, "utf8");
  return { content, base: path.dirname(resolvedPath) };
}

async function run() {
  const sourceCss = await fs.readFile(sourceCssPath, "utf8");
  const compiler = await compile(sourceCss, {
    base: path.dirname(sourceCssPath),
    loadStylesheet,
  });
  const candidates = await collectCandidates();
  const compiledCss = compiler.build(candidates);
  await fs.writeFile(outputCssPath, compiledCss, "utf8");
  console.log(`🧪 generated ${path.relative(webRoot, outputCssPath)} (${candidates.length} candidates)`);
}

run().catch((error) => {
  console.error("⚠️ failed to generate Tailwind CSS", error);
  process.exitCode = 1;
});
