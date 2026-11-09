// SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
// Optional maintainer staging only. Python builds never execute this file.
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, readdir, readFile, writeFile, cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const { values } = parseArgs({ options: {
  archive: { type: "string" }, modules: { type: "string" },
  stage: { type: "string" }, out: { type: "string" },
} });
if (!values.archive || !values.modules || !values.stage || !values.out) {
  throw new Error("Required: --archive <accepted UI tgz> --modules <Web node_modules> --stage <empty private directory> --out <data/ui>");
}
const archive = resolve(values.archive);
const modules = resolve(values.modules);
const stage = resolve(values.stage);
const out = resolve(values.out);
const here = dirname(fileURLToPath(import.meta.url));
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const archiveSha = sha256(await readFile(archive));
if (archiveSha !== "237a3bf306bdb6fec5088783c425381bcf125540ba7ad25e1aec0604198d7728") {
  throw new Error("UI archive does not match the accepted UI.2 cohort");
}
for (const directory of [stage, out]) {
  await mkdir(directory, { recursive: true });
  if ((await readdir(directory)).length) throw new Error(`Refusing nonempty staging/output directory: ${directory}`);
}
execFileSync("tar", ["-xzf", archive, "-C", stage]);
const ui = join(stage, "package");
const uiPackage = JSON.parse(await readFile(join(ui, "package.json"), "utf8"));
const require = createRequire(import.meta.url);
const esbuild = require(join(modules, "esbuild"));
const dependencies = {};
for (const name of ["react", "react-dom", "scheduler"]) {
  dependencies[name] = JSON.parse(await readFile(join(modules, name, "package.json"), "utf8")).version;
}
const result = await esbuild.build({
  entryPoints: [join(here, "papers-ui.tsx")],
  outfile: join(out, "papers-ui.js"),
  bundle: true, format: "iife", platform: "browser", target: "es2020",
  jsx: "automatic", minify: true, legalComments: "inline", write: false, metafile: true,
  banner: { js: "/*! Papers UI presentation — SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later; dependency licences: licenses/ */" },
  define: { "process.env.NODE_ENV": '"production"' },
  nodePaths: [modules],
  alias: {
    "nirs4all-ui/qualification": join(ui, uiPackage.exports["./qualification"].import),
    react: join(modules, "react"), "react-dom": join(modules, "react-dom"), scheduler: join(modules, "scheduler"),
  },
});
if (Object.values(result.metafile.outputs).some((output) => output.imports.length)) {
  throw new Error("Consumer bundle must not retain external imports");
}
await writeFile(join(out, "papers-ui.js"), result.outputFiles[0].contents);
await cp(join(ui, "assets/qualification.css"), join(out, "qualification.css"));
await cp(join(here, "papers-ui.css"), join(out, "papers-ui.css"));
const licenses = join(out, "licenses");
await mkdir(join(licenses, "ui"), { recursive: true });
for (const name of ["LICENSE", "LICENSING.md", "THIRD_PARTY_NOTICES.md", "LICENSES"]) {
  await cp(join(ui, name), join(licenses, "ui", name), { recursive: true });
}
for (const name of Object.keys(dependencies)) {
  await mkdir(join(licenses, name), { recursive: true });
  await cp(join(modules, name, "LICENSE"), join(licenses, name, "LICENSE"));
}
await writeFile(join(licenses, "NOTICE.txt"),
  `Papers presentation bundle: nirs4all-ui ${uiPackage.version} StatTile (CeCILL-2.1 OR AGPL-3.0-or-later).\n`
  + Object.entries(dependencies).map(([name, version]) => `${name} ${version}: MIT; see ${name}/LICENSE.\n`).join("")
  + "UI upstream notices under ui/ describe the upstream distribution, including its separate optional browser bundle.\n"
  + "That upstream browser bundle is not used here; the actual bundled React versions are listed above.\n");
const files = {};
async function record(directory, prefix = "") {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const name = prefix + entry.name;
    if (entry.isDirectory()) await record(join(directory, entry.name), name + "/");
    else files[name] = sha256(await readFile(join(directory, entry.name)));
  }
}
await record(out);
await writeFile(join(out, "manifest.json"), JSON.stringify({
  ui: { version: uiPackage.version, archive_sha256: archiveSha, export: "nirs4all-ui/qualification:StatTile" },
  dependencies, tools: { node: process.version, esbuild: esbuild.version },
  entrypoint_sha256: sha256(await readFile(join(here, "papers-ui.tsx"))), files,
}, null, 2) + "\n");
console.log(`Staged Papers UI resources in ${out}; no UI/owner rebuild or install.`);
