// The size of every file that the browser downloads, as on the wire (gzip) and unpacked.
// 1 kB = 1,000 bytes, as Vite prints. Vite compresses a little differently: its gzip numbers differ by about 1%.
//   npm run build && node scripts/bundle-report.mjs
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';

const dir = process.argv[2] ?? 'dist';
const files = [];
(function walk(d) {
  for (const name of readdirSync(d)) {
    const p = join(d, name);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(js|css|html)$/.test(name)) files.push(p);
  }
})(dir);
const rows = files
  .map((p) => {
    const data = readFileSync(p);
    return { file: p.slice(dir.length + 1), kb: data.length / 1000, gzipKb: gzipSync(data).length / 1000 };
  })
  .sort((a, b) => b.gzipKb - a.gzipKb);
const pad = (s, n) => String(s).padEnd(n);
console.log(pad('File', 44), pad('Size', 10), 'Gzip');
for (const r of rows) console.log(pad(r.file, 44), pad(`${r.kb.toFixed(1)} kB`, 10), `${r.gzipKb.toFixed(1)} kB`);
const js = rows.filter((r) => r.file.endsWith('.js'));
console.log(`JavaScript: ${js.length} files, ${js.reduce((s, r) => s + r.gzipKb, 0).toFixed(1)} kB gzip in all`);
