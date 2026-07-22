import { useCallback, useRef, useState } from 'react';

const RUN_TIMEOUT_MS = 5000;

const SANDBOX_HTML = `
<!doctype html>
<html><head><meta charset="utf-8"></head><body><script>
  const send = (level, args) => {
    let text;
    try {
      text = args.map((a) => {
        if (a instanceof Error) return a.stack || a.message;
        if (typeof a === 'object') return JSON.stringify(a, null, 2);
        return String(a);
      }).join(' ');
    } catch {
      text = '[unserializable]';
    }
    parent.postMessage({ __sandbox: true, level, text }, '*');
  };

  console.log = (...a) => send('log', a);
  console.warn = (...a) => send('warn', a);
  console.error = (...a) => send('error', a);

  window.addEventListener('message', async (e) => {
    if (!e.data || e.data.__run !== true) return;
    try {
      const asyncWrapped = new Function(
        'return (async () => {\\n' + e.data.code + '\\n})()'
      );
      const result = await asyncWrapped();
      if (result !== undefined) send('result', [result]);
    } catch (err) {
      send('error', [err]);
    }
    // Code often fires promises without awaiting them (e.g. .then(console.log)
    // with no return/await) — give pending microtasks/macrotasks a chance to
    // flush their console output before signalling done, otherwise those logs
    // never reach the parent.
    setTimeout(() => {
      parent.postMessage({ __sandbox: true, done: true }, '*');
    }, 300);
  });

  parent.postMessage({ __sandbox: true, ready: true }, '*');
<\/script></body></html>
`;

// Sample/demo code snippets reference fake db/fs/app/etc. globals that don't
// exist in a real browser sandbox — inject lightweight stand-ins so "Run"
// still produces meaningful console output instead of ReferenceErrors.
const SANDBOX_MOCKS = `
const db = {
  getStock: async (id) => 3,
  setStock: async (id, v) => { console.log('[mock] setStock', id, v); },
  createOrder: async (o) => { console.log('[mock] createOrder', o); },
  findUser: async (id) => ({ id, name: 'Demo User' }),
  users: { findById: async (id) => ({ id, name: 'User ' + id }) },
  orders: { find: async (id) => [{ id: 1, total: 42 }] },
  reviews: { find: async (id) => [{ id: 1, rating: 5 }] },
  find: (id, cb) => cb(null, { id, name: 'Demo User' }),
  connect: async () => ({ query: async () => [] }),
  getOrder: async (id) => ({ id, userId: 1, total: 42 }),
  getUser: async (id) => ({ id, email: 'demo@example.com', card: 'tok_demo' }),
};
const fs = {
  readFileSync: (p) => JSON.stringify({ mock: true, path: p }),
  createReadStream: (p) => ({ on(evt, cb){ if(evt==='data') setTimeout(()=>cb(Buffer.from('mock')),10); if(evt==='end') setTimeout(cb,20); return this; }, pipe(dest){ return dest; } }),
};
const app = { get: (path, handler) => console.log('[mock] route registered:', path) };
const res = { json: (o) => console.log('[mock] res.json', o), status: (c) => ({ json: (o) => console.log('[mock] res.status', c, o), end: () => console.log('[mock] res.end', c) }) };
const payment = { charge: async (card, amt) => ({ id: 'ch_demo', amount: amt }) };
const email = { send: async (to, subj) => console.log('[mock] email sent to', to, ':', subj) };
const emailService = { send: async (to) => console.log('[mock] emailService.send', to) };
const cache = { has: () => false, get: () => null, set: (k, v) => console.log('[mock] cache.set', k) };
const zlib = { createGzip: () => ({ on(evt, cb){ return this; }, pipe(dest){ return dest; } }) };
`;

export function useRunCode() {
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState(null);
  const [hasRun, setHasRun] = useState(false);
  const iframeRef = useRef(null);
  const timeoutRef = useRef(null);
  const listenerRef = useRef(null);

  const cleanup = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (listenerRef.current) {
      window.removeEventListener('message', listenerRef.current);
      listenerRef.current = null;
    }
    if (iframeRef.current) {
      iframeRef.current.remove();
      iframeRef.current = null;
    }
  }, []);

  const run = useCallback((code) => {
    cleanup();
    setLogs([]);
    setRunError(null);
    setIsRunning(true);
    setHasRun(true);

    const iframe = document.createElement('iframe');
    iframe.setAttribute('sandbox', 'allow-scripts');
    iframe.style.position = 'absolute';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    iframe.style.left = '-9999px';
    iframeRef.current = iframe;

    const collected = [];

    function onMessage(e) {
      if (!e.data || !e.data.__sandbox) return;

      if (e.data.ready) {
        iframe.contentWindow?.postMessage({ __run: true, code: SANDBOX_MOCKS + '\n' + code }, '*');
        return;
      }

      if (e.data.level) {
        collected.push({ level: e.data.level, text: e.data.text });
        setLogs([...collected]);
      }

      if (e.data.done) {
        finish();
      }
    }

    function finish() {
      window.removeEventListener('message', onMessage);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setIsRunning(false);
      cleanup();
    }

    listenerRef.current = onMessage;
    window.addEventListener('message', onMessage);

    timeoutRef.current = setTimeout(() => {
      setRunError(`Execution timed out after ${RUN_TIMEOUT_MS / 1000}s (infinite loop?)`);
      finish();
    }, RUN_TIMEOUT_MS);

    document.body.appendChild(iframe);
    iframe.srcdoc = SANDBOX_HTML;
  }, [cleanup]);

  const reset = useCallback(() => {
    cleanup();
    setLogs([]);
    setRunError(null);
    setIsRunning(false);
    setHasRun(false);
  }, [cleanup]);

  return { logs, isRunning, runError, hasRun, run, reset };
}
