// Checks the production files (dist/) before they are delivered: no secret may be in them.
// Everything in dist/ is public: every visitor's browser downloads it.
//   npm run build && npm run check:bundle
// It fails (exit code 1) when it finds:
//   - the value of a variable from .env that does NOT start with VITE_ (those are server secrets),
//     or of a VITE_ variable named like a secret;
//   - a VITE_ variable whose name says it is a secret (KEY, SECRET, TOKEN, PASSWORD): Vite puts it in the bundle;
//   - text that looks like a key (sk-…, a private key block, "api_key": "…").
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export function readEnv(text) {
  const out = {};
  for (const line of text.split(/\r?\n/)) {
    const m = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/.exec(line);
    if (m && !line.trim().startsWith('#')) out[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
  return out;
}

const PATTERNS = [
  [/sk-[A-Za-z0-9_-]{20,}/, 'a key that starts with sk-'],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'a private key'],
  [/["']?(?:api[_-]?key|secret|password)["']?\s*[:=]\s*["'][^"'\s]{12,}["']/i, 'a key or password written in the code'],
];

/** Gives back the problems found in the files, as a list of sentences. */
export function findSecrets(files, env) {
  const problems = [];
  for (const name of Object.keys(env)) {
    if (name.startsWith('VITE_') && /KEY|SECRET|TOKEN|PASSWORD/i.test(name)) {
      problems.push(`${name}: a VITE_ variable is public, but its name says that it is a secret. Keep it on the server.`);
    }
  }
  // Server secrets, and VITE_ variables named like a secret: where is their value in the files?
  const secretName = (name) => !name.startsWith('VITE_') || /KEY|SECRET|TOKEN|PASSWORD/i.test(name);
  const secrets = Object.entries(env).filter(([name, value]) => secretName(name) && value.length >= 8);
  for (const [file, text] of files) {
    for (const [name, value] of secrets) {
      if (text.includes(value)) problems.push(`${file}: contains the value of ${name} from .env.`);
    }
    for (const [pattern, what] of PATTERNS) {
      if (pattern.test(text)) problems.push(`${file}: contains ${what}.`);
    }
  }
  return problems;
}

function listFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...listFiles(p));
    else out.push(p);
  }
  return out;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  const dir = process.argv[2] ?? 'dist';
  if (!existsSync(dir)) {
    console.error(`There is no ${dir}/ folder. Run npm run build first.`);
    process.exit(2);
  }
  const env = existsSync('.env') ? readEnv(readFileSync('.env', 'utf8')) : {};
  const files = listFiles(dir)
    .filter((p) => /\.(js|css|html|map|json|txt)$/.test(p))
    .map((p) => [p, readFileSync(p, 'utf8')]);
  const problems = findSecrets(files, { ...env, ...Object.fromEntries(Object.entries(process.env).filter(([k]) => /KEY|SECRET|TOKEN|PASSWORD/i.test(k))) });
  if (problems.length) {
    console.error(`Secrets in the browser files (${problems.length}):`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`No secret found in ${files.length} files of ${dir}/.`);
}
