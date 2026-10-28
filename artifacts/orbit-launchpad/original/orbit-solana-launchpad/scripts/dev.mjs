import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
try {
  process.loadEnvFile(path.join(root, '.env'));
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}

const apiPort = process.env.API_PORT || '3000';
const webPort = process.env.PORT || '5173';
const api = spawn(process.execPath, ['server/app.mjs'], {
  cwd: root,
  stdio: 'inherit',
  env: { ...process.env, PORT: apiPort },
});
const vite = spawn('vite', ['--host', '0.0.0.0'], {
  cwd: root,
  stdio: 'inherit',
  env: { ...process.env, PORT: webPort, API_PORT: apiPort },
});

let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  api.kill();
  vite.kill();
}

process.once('SIGINT', stop);
process.once('SIGTERM', stop);
for (const child of [api, vite]) {
  child.once('error', (error) => {
    console.error('Unable to start ORBIT development process:', error.message);
    stop();
    process.exitCode = 1;
  });
  child.once('exit', (code) => {
    if (!stopping && code !== 0) {
      console.error('ORBIT development process exited with code', code);
      stop();
      process.exitCode = code ?? 1;
    }
  });
}
