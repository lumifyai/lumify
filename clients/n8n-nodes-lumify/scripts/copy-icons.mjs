// Copies node icon assets into dist/ after tsc compiles the TypeScript
// sources. tsc does not touch non-.ts files, so icons need a manual copy.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const pairs = [
  [
    join(root, "nodes/Lumify/lumify.svg"),
    join(root, "dist/nodes/Lumify/lumify.svg"),
  ],
  [
    join(root, "credentials/lumify.svg"),
    join(root, "dist/credentials/lumify.svg"),
  ],
];

for (const [src, dest] of pairs) {
  mkdirSync(dirname(dest), { recursive: true });
  copyFileSync(src, dest);
  console.log(`copied ${src} -> ${dest}`);
}
