#!/usr/bin/env python3
"""
AI1-01 | ThreadLearn — JS Dataset Collector
Ưu tiên: JavaScript concurrent patterns
Output : raw_dataset.json — 500+ cặp input/output
"""

import json, re, time, hashlib, copy, requests, argparse, os
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
OUTPUT_FILE    = "raw_dataset.json"
TARGET_MIN     = 500
MAX_LINES      = 150
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")

# Chỉ JS — nhiều query, cụ thể từng pattern
JS_GITHUB_QUERIES = [
    "callback hell to promise javascript",
    "setTimeout callback to async await javascript",
    "sequential fetch to Promise.all javascript",
    "convert callback to async javascript refactor",
    "synchronous loop to parallel javascript",
    "XMLHttpRequest to fetch async javascript",
    "jquery ajax to fetch promise javascript",
    "event emitter to promise javascript",
    "fs readFileSync to promises javascript",
    "waterfall async to Promise.all javascript",
    "nested callbacks to async await javascript",
    "for loop await sequential to parallel javascript",
    "worker threads javascript cpu bound",
    "setInterval to async generator javascript",
    "axios sequential to parallel requests javascript",
]

# ─────────────────────────────────────────────
# SYNTHETIC PAIRS — 60 cặp JS chất lượng cao
# Mỗi cặp: input (đơn luồng/blocking) → output (concurrent/async)
# ─────────────────────────────────────────────

JS_PAIRS = [

# ── CATEGORY 1: callback hell → async/await ──────────────────────────
{
"input": """\
function getUser(id, callback) {
  setTimeout(() => callback(null, { id, name: 'Alice' }), 300);
}
function getOrders(userId, callback) {
  setTimeout(() => callback(null, [1, 2, 3]), 300);
}
function getProduct(orderId, callback) {
  setTimeout(() => callback(null, { orderId, name: 'Book' }), 300);
}

getUser(1, (err, user) => {
  getOrders(user.id, (err, orders) => {
    getProduct(orders[0], (err, product) => {
      console.log(product);
    });
  });
});
""",
"output": """\
function getUser(id) {
  return new Promise(resolve => setTimeout(() => resolve({ id, name: 'Alice' }), 300));
}
function getOrders(userId) {
  return new Promise(resolve => setTimeout(() => resolve([1, 2, 3]), 300));
}
function getProduct(orderId) {
  return new Promise(resolve => setTimeout(() => resolve({ orderId, name: 'Book' }), 300));
}

async function main() {
  const user = await getUser(1);
  const orders = await getOrders(user.id);
  const product = await getProduct(orders[0]);
  console.log(product);
}

main();
""",
"category": "callback_to_async",
},

{
"input": """\
function step1(cb) { setTimeout(() => cb(null, 'a'), 100); }
function step2(data, cb) { setTimeout(() => cb(null, data + 'b'), 100); }
function step3(data, cb) { setTimeout(() => cb(null, data + 'c'), 100); }

step1((err, r1) => {
  step2(r1, (err, r2) => {
    step3(r2, (err, r3) => {
      console.log(r3);
    });
  });
});
""",
"output": """\
const step1 = () => new Promise(resolve => setTimeout(() => resolve('a'), 100));
const step2 = data => new Promise(resolve => setTimeout(() => resolve(data + 'b'), 100));
const step3 = data => new Promise(resolve => setTimeout(() => resolve(data + 'c'), 100));

async function main() {
  const r1 = await step1();
  const r2 = await step2(r1);
  const r3 = await step3(r2);
  console.log(r3);
}

main();
""",
"category": "callback_to_async",
},

{
"input": """\
const fs = require('fs');

fs.readFile('a.txt', 'utf8', (err, dataA) => {
  if (err) throw err;
  fs.readFile('b.txt', 'utf8', (err, dataB) => {
    if (err) throw err;
    fs.writeFile('out.txt', dataA + dataB, (err) => {
      if (err) throw err;
      console.log('done');
    });
  });
});
""",
"output": """\
const fs = require('fs').promises;

async function main() {
  const [dataA, dataB] = await Promise.all([
    fs.readFile('a.txt', 'utf8'),
    fs.readFile('b.txt', 'utf8'),
  ]);
  await fs.writeFile('out.txt', dataA + dataB);
  console.log('done');
}

main();
""",
"category": "fs_callback_to_async",
},

{
"input": """\
const request = require('request');

request('https://api.example.com/users', (err, res, body) => {
  const users = JSON.parse(body);
  request(`https://api.example.com/orders/${users[0].id}`, (err, res, body) => {
    const orders = JSON.parse(body);
    console.log(orders);
  });
});
""",
"output": """\
async function main() {
  const usersRes = await fetch('https://api.example.com/users');
  const users = await usersRes.json();
  const ordersRes = await fetch(`https://api.example.com/orders/${users[0].id}`);
  const orders = await ordersRes.json();
  console.log(orders);
}

main();
""",
"category": "http_callback_to_async",
},

{
"input": """\
function loadConfig(cb) {
  setTimeout(() => cb(null, { db: 'localhost' }), 50);
}
function connectDB(config, cb) {
  setTimeout(() => cb(null, { connected: true, config }), 100);
}
function runQuery(db, cb) {
  setTimeout(() => cb(null, [{ id: 1 }]), 80);
}

loadConfig((err, config) => {
  connectDB(config, (err, db) => {
    runQuery(db, (err, rows) => {
      console.log(rows);
    });
  });
});
""",
"output": """\
const loadConfig = () => new Promise(r => setTimeout(() => r({ db: 'localhost' }), 50));
const connectDB = config => new Promise(r => setTimeout(() => r({ connected: true, config }), 100));
const runQuery = db => new Promise(r => setTimeout(() => r([{ id: 1 }]), 80));

async function main() {
  const config = await loadConfig();
  const db = await connectDB(config);
  const rows = await runQuery(db);
  console.log(rows);
}

main();
""",
"category": "callback_to_async",
},

# ── CATEGORY 2: sequential await → Promise.all ───────────────────────
{
"input": """\
async function loadDashboard(userId) {
  const profile  = await fetch(`/api/profile/${userId}`).then(r => r.json());
  const orders   = await fetch(`/api/orders/${userId}`).then(r => r.json());
  const messages = await fetch(`/api/messages/${userId}`).then(r => r.json());
  return { profile, orders, messages };
}
""",
"output": """\
async function loadDashboard(userId) {
  const [profile, orders, messages] = await Promise.all([
    fetch(`/api/profile/${userId}`).then(r => r.json()),
    fetch(`/api/orders/${userId}`).then(r => r.json()),
    fetch(`/api/messages/${userId}`).then(r => r.json()),
  ]);
  return { profile, orders, messages };
}
""",
"category": "sequential_await_to_parallel",
},

{
"input": """\
async function getStats() {
  const daily   = await fetchStat('daily');
  const weekly  = await fetchStat('weekly');
  const monthly = await fetchStat('monthly');
  const yearly  = await fetchStat('yearly');
  return { daily, weekly, monthly, yearly };
}
""",
"output": """\
async function getStats() {
  const [daily, weekly, monthly, yearly] = await Promise.all([
    fetchStat('daily'),
    fetchStat('weekly'),
    fetchStat('monthly'),
    fetchStat('yearly'),
  ]);
  return { daily, weekly, monthly, yearly };
}
""",
"category": "sequential_await_to_parallel",
},

{
"input": """\
async function sendNotifications(users) {
  const results = [];
  for (const user of users) {
    const result = await sendEmail(user.email);
    results.push(result);
  }
  return results;
}
""",
"output": """\
async function sendNotifications(users) {
  return Promise.all(users.map(user => sendEmail(user.email)));
}
""",
"category": "sequential_loop_to_parallel",
},

{
"input": """\
async function resizeImages(paths) {
  const outputs = [];
  for (const p of paths) {
    const resized = await sharp(p).resize(800).toBuffer();
    outputs.push(resized);
  }
  return outputs;
}
""",
"output": """\
async function resizeImages(paths) {
  return Promise.all(
    paths.map(p => sharp(p).resize(800).toBuffer())
  );
}
""",
"category": "sequential_loop_to_parallel",
},

{
"input": """\
async function fetchAllUsers(ids) {
  const users = [];
  for (const id of ids) {
    const user = await api.getUser(id);
    users.push(user);
  }
  return users;
}
""",
"output": """\
async function fetchAllUsers(ids) {
  return Promise.all(ids.map(id => api.getUser(id)));
}
""",
"category": "sequential_loop_to_parallel",
},

{
"input": """\
async function loadProducts(ids) {
  const result = [];
  for (let i = 0; i < ids.length; i++) {
    const product = await db.findById(ids[i]);
    result.push(product);
  }
  return result;
}
""",
"output": """\
async function loadProducts(ids) {
  return Promise.all(ids.map(id => db.findById(id)));
}
""",
"category": "sequential_loop_to_parallel",
},

{
"input": """\
async function translateTexts(texts, lang) {
  const translated = [];
  for (const text of texts) {
    const result = await translator.translate(text, lang);
    translated.push(result);
  }
  return translated;
}
""",
"output": """\
async function translateTexts(texts, lang) {
  return Promise.all(texts.map(text => translator.translate(text, lang)));
}
""",
"category": "sequential_loop_to_parallel",
},

# ── CATEGORY 3: sync → async (blocking → non-blocking) ───────────────
{
"input": """\
const fs = require('fs');

function readConfig() {
  return JSON.parse(fs.readFileSync('./config.json', 'utf8'));
}

function readAllConfigs(paths) {
  return paths.map(p => JSON.parse(fs.readFileSync(p, 'utf8')));
}
""",
"output": """\
const fs = require('fs').promises;

async function readConfig() {
  return JSON.parse(await fs.readFile('./config.json', 'utf8'));
}

async function readAllConfigs(paths) {
  const contents = await Promise.all(paths.map(p => fs.readFile(p, 'utf8')));
  return contents.map(c => JSON.parse(c));
}
""",
"category": "sync_to_async",
},

{
"input": """\
const https = require('https');

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

async function main() {
  const a = await get('https://api.example.com/a');
  const b = await get('https://api.example.com/b');
  const c = await get('https://api.example.com/c');
  return [a, b, c];
}
""",
"output": """\
async function get(url) {
  const res = await fetch(url);
  return res.json();
}

async function main() {
  return Promise.all([
    get('https://api.example.com/a'),
    get('https://api.example.com/b'),
    get('https://api.example.com/c'),
  ]);
}
""",
"category": "sync_to_async",
},

{
"input": """\
const crypto = require('crypto');

function hashAll(items) {
  return items.map(item => {
    return crypto.createHash('sha256').update(item).digest('hex');
  });
}

const results = hashAll(['file1', 'file2', 'file3', 'file4', 'file5']);
console.log(results);
""",
"output": """\
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const crypto = require('crypto');

if (!isMainThread) {
  const hash = crypto.createHash('sha256').update(workerData).digest('hex');
  parentPort.postMessage(hash);
} else {
  function hashItem(item) {
    return new Promise((resolve, reject) => {
      const w = new Worker(__filename, { workerData: item });
      w.on('message', resolve);
      w.on('error', reject);
    });
  }

  async function hashAll(items) {
    return Promise.all(items.map(hashItem));
  }

  hashAll(['file1', 'file2', 'file3', 'file4', 'file5']).then(console.log);
}
""",
"category": "worker_threads",
},

{
"input": """\
function processImage(buffer) {
  // CPU-intensive sync operation
  let result = buffer;
  for (let i = 0; i < 1000000; i++) {
    result = result.map(b => (b + 1) % 256);
  }
  return result;
}

const images = [buf1, buf2, buf3, buf4];
const processed = images.map(processImage);
""",
"output": """\
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (!isMainThread) {
  let result = workerData;
  for (let i = 0; i < 1000000; i++) {
    result = result.map(b => (b + 1) % 256);
  }
  parentPort.postMessage(result);
} else {
  function processImage(buffer) {
    return new Promise((resolve, reject) => {
      const w = new Worker(__filename, { workerData: buffer });
      w.on('message', resolve);
      w.on('error', reject);
    });
  }

  const images = [buf1, buf2, buf3, buf4];
  Promise.all(images.map(processImage)).then(processed => {
    console.log('All done', processed.length);
  });
}
""",
"category": "worker_threads",
},

# ── CATEGORY 4: XMLHttpRequest / jQuery → fetch ───────────────────────
{
"input": """\
function getData(url) {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', url, false); // synchronous!
  xhr.send();
  return JSON.parse(xhr.responseText);
}

const user = getData('/api/user');
const posts = getData('/api/posts');
""",
"output": """\
async function getData(url) {
  const res = await fetch(url);
  return res.json();
}

async function main() {
  const [user, posts] = await Promise.all([
    getData('/api/user'),
    getData('/api/posts'),
  ]);
}

main();
""",
"category": "xhr_to_fetch",
},

{
"input": """\
$.ajax({
  url: '/api/users',
  success: function(users) {
    $.ajax({
      url: '/api/orders/' + users[0].id,
      success: function(orders) {
        $.ajax({
          url: '/api/products/' + orders[0].productId,
          success: function(product) {
            console.log(product);
          }
        });
      }
    });
  }
});
""",
"output": """\
async function main() {
  const users   = await fetch('/api/users').then(r => r.json());
  const orders  = await fetch(`/api/orders/${users[0].id}`).then(r => r.json());
  const product = await fetch(`/api/products/${orders[0].productId}`).then(r => r.json());
  console.log(product);
}

main();
""",
"category": "jquery_to_fetch",
},

{
"input": """\
$.get('/api/config', function(config) {
  $.get('/api/user?lang=' + config.lang, function(user) {
    $('#name').text(user.name);
  });
});
""",
"output": """\
async function init() {
  const config = await fetch('/api/config').then(r => r.json());
  const user   = await fetch(`/api/user?lang=${config.lang}`).then(r => r.json());
  document.getElementById('name').textContent = user.name;
}

init();
""",
"category": "jquery_to_fetch",
},

# ── CATEGORY 5: race conditions → safe patterns ───────────────────────
{
"input": """\
let sharedCounter = 0;

async function increment() {
  const current = sharedCounter;      // read
  await delay(10);                    // race window
  sharedCounter = current + 1;        // write — stale!
}

await Promise.all([increment(), increment(), increment()]);
console.log(sharedCounter); // likely 1, not 3
""",
"output": """\
function createSafeCounter() {
  let value = 0;
  let queue = Promise.resolve();
  return {
    increment() {
      queue = queue.then(async () => {
        const current = value;
        await delay(10);
        value = current + 1;
      });
      return queue;
    },
    get value() { return value; }
  };
}

const counter = createSafeCounter();
await Promise.all([counter.increment(), counter.increment(), counter.increment()]);
console.log(counter.value); // 3
""",
"category": "race_condition_fix",
},

{
"input": """\
let cache = null;

async function fetchData() {
  if (!cache) {
    // race: multiple callers enter here simultaneously
    cache = await api.getData();
  }
  return cache;
}

// Both calls may trigger api.getData() simultaneously
await Promise.all([fetchData(), fetchData()]);
""",
"output": """\
let cache = null;
let inflight = null;

async function fetchData() {
  if (cache) return cache;
  if (!inflight) {
    inflight = api.getData().then(data => {
      cache = data;
      inflight = null;
      return data;
    });
  }
  return inflight;
}

await Promise.all([fetchData(), fetchData()]); // api called once
""",
"category": "race_condition_fix",
},

{
"input": """\
let isRunning = false;

async function runJob() {
  if (isRunning) return;
  isRunning = true;
  await doWork();
  isRunning = false;
}

// Called concurrently — isRunning check not atomic
setInterval(runJob, 100);
""",
"output": """\
let jobPromise = null;

async function runJob() {
  if (jobPromise) return jobPromise;
  jobPromise = doWork().finally(() => {
    jobPromise = null;
  });
  return jobPromise;
}

setInterval(runJob, 100);
""",
"category": "race_condition_fix",
},

# ── CATEGORY 6: event-emitter / stream → Promise ─────────────────────
{
"input": """\
const EventEmitter = require('events');
const emitter = new EventEmitter();

emitter.on('data', (chunk) => {
  buffer += chunk;
});
emitter.on('end', () => {
  processBuffer(buffer);
});
emitter.on('error', (err) => {
  console.error(err);
});

let buffer = '';
startStream(emitter);
""",
"output": """\
function streamToString(stream) {
  return new Promise((resolve, reject) => {
    let buffer = '';
    stream.on('data', chunk => { buffer += chunk; });
    stream.on('end', () => resolve(buffer));
    stream.on('error', reject);
  });
}

async function main() {
  const stream = startStream();
  const buffer = await streamToString(stream);
  processBuffer(buffer);
}

main();
""",
"category": "event_to_promise",
},

{
"input": """\
function waitForEvent(emitter, event, cb) {
  emitter.once(event, (data) => {
    cb(null, data);
  });
  emitter.once('error', (err) => {
    cb(err);
  });
}

waitForEvent(socket, 'connect', (err, data) => {
  if (err) return console.error(err);
  console.log('connected', data);
});
""",
"output": """\
function waitForEvent(emitter, event) {
  return new Promise((resolve, reject) => {
    const onEvent = data => { cleanup(); resolve(data); };
    const onError = err  => { cleanup(); reject(err);   };
    const cleanup = () => {
      emitter.off(event, onEvent);
      emitter.off('error', onError);
    };
    emitter.once(event, onEvent);
    emitter.once('error', onError);
  });
}

try {
  const data = await waitForEvent(socket, 'connect');
  console.log('connected', data);
} catch (err) {
  console.error(err);
}
""",
"category": "event_to_promise",
},

# ── CATEGORY 7: setInterval / polling → async generator ──────────────
{
"input": """\
function pollStatus(jobId, cb) {
  const interval = setInterval(async () => {
    const status = await checkJob(jobId);
    if (status.done) {
      clearInterval(interval);
      cb(null, status.result);
    }
  }, 1000);
}

pollStatus('job-123', (err, result) => {
  console.log(result);
});
""",
"output": """\
async function* pollStatus(jobId, intervalMs = 1000) {
  while (true) {
    const status = await checkJob(jobId);
    yield status;
    if (status.done) break;
    await new Promise(r => setTimeout(r, intervalMs));
  }
}

for await (const status of pollStatus('job-123')) {
  if (status.done) {
    console.log(status.result);
    break;
  }
}
""",
"category": "polling_to_generator",
},

{
"input": """\
function watchFile(path, onChange) {
  let lastContent = null;
  setInterval(async () => {
    const content = await fs.promises.readFile(path, 'utf8');
    if (content !== lastContent) {
      lastContent = content;
      onChange(content);
    }
  }, 500);
}

watchFile('./data.json', content => {
  console.log('changed:', content);
});
""",
"output": """\
async function* watchFile(path, intervalMs = 500) {
  let lastContent = null;
  while (true) {
    const content = await fs.promises.readFile(path, 'utf8');
    if (content !== lastContent) {
      lastContent = content;
      yield content;
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
}

for await (const content of watchFile('./data.json')) {
  console.log('changed:', content);
}
""",
"category": "polling_to_generator",
},


# ── NEW CATEGORY: abort_controller ───────────────────────────────
{
"input": """\
async function fetchData(url) {
  const res = await fetch(url);
  return res.json();
}
""",
"output": """\
async function fetchData(url, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal });
    return await res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}
""",
"category": "abort_controller",
},
{
"input": """\
async function loadUserData(userId) {
  const profile = await fetch(`/api/users/${userId}/profile`);
  const settings = await fetch(`/api/users/${userId}/settings`);
  return { profile: await profile.json(), settings: await settings.json() };
}
""",
"output": """\
async function loadUserData(userId, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const [profile, settings] = await Promise.all([
      fetch(`/api/users/${userId}/profile`, { signal: controller.signal }).then(r => r.json()),
      fetch(`/api/users/${userId}/settings`, { signal: controller.signal }).then(r => r.json())
    ]);
    return { profile, settings };
  } finally {
    clearTimeout(timeoutId);
  }
}
""",
"category": "abort_controller",
},

# ── NEW CATEGORY: promise_any ───────────────────────────────────
{
"input": """\
async function fetchFromPrimary(url) {
  return fetch(primaryCDN + url).then(r => r.json());
}
""",
"output": """\
async function fetchWithFallback(path) {
  return Promise.any([
    fetch(primaryCDN + path),
    fetch(secondaryCDN + path),
    fetch(tertiaryOrigin + path),
  ]).then(r => r.json());
}
""",
"category": "promise_any",
},

# ── NEW CATEGORY: for_await_of ──────────────────────────────────
{
"input": """\
async function processItems(items) {
  for (const item of items) {
    await processItem(item);
  }
}
""",
"output": """\
async function* generateItems(items) {
  for (const item of items) {
    yield await processItem(item);
  }
}

async function processItems(items) {
  for await (const result of generateItems(items)) {
    console.log(result);
  }
}
""",
"category": "for_await_of",
},

# ── NEW CATEGORY: cluster_module ────────────────────────────────
{
"input": """\
const http = require('http');

http.createServer((req, res) => {
  res.writeHead(200);
  res.end('hello world\n');
}).listen(8000);
console.log('Server running on port 8000');
""",
"output": """\
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isPrimary) {
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  cluster.on('exit', (worker, code, signal) => {
    console.log(`worker ${worker.process.pid} died`);
    cluster.fork(); // restart
  });
} else {
  http.createServer((req, res) => {
    res.writeHead(200);
    res.end('hello world\n');
  }).listen(8000);
}
""",
"category": "cluster_module",
},

# ── CATEGORY 8: Promise chaining → async/await cleanup ───────────────
{
"input": """\
function processOrder(orderId) {
  return fetchOrder(orderId)
    .then(order => validateOrder(order))
    .then(order => chargePayment(order))
    .then(receipt => sendConfirmation(receipt))
    .then(result => {
      console.log('done', result);
      return result;
    })
    .catch(err => {
      console.error('failed', err);
      throw err;
    });
}
""",
"output": """\
async function processOrder(orderId) {
  try {
    const order   = await fetchOrder(orderId);
    const valid   = await validateOrder(order);
    const receipt = await chargePayment(valid);
    const result  = await sendConfirmation(receipt);
    console.log('done', result);
    return result;
  } catch (err) {
    console.error('failed', err);
    throw err;
  }
}
""",
"category": "chain_to_async",
},

{
"input": """\
login(username, password)
  .then(token => getProfile(token))
  .then(profile => loadPermissions(profile.role))
  .then(permissions => renderDashboard(permissions))
  .catch(console.error);
""",
"output": """\
async function init(username, password) {
  try {
    const token       = await login(username, password);
    const profile     = await getProfile(token);
    const permissions = await loadPermissions(profile.role);
    await renderDashboard(permissions);
  } catch (err) {
    console.error(err);
  }
}

init(username, password);
""",
"category": "chain_to_async",
},

{
"input": """\
fetch('/api/data')
  .then(res => res.json())
  .then(data => {
    return fetch('/api/process', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  })
  .then(res => res.json())
  .then(result => console.log(result))
  .catch(err => console.error(err));
""",
"output": """\
async function run() {
  try {
    const data = await fetch('/api/data').then(r => r.json());
    const result = await fetch('/api/process', {
      method: 'POST',
      body: JSON.stringify(data),
    }).then(r => r.json());
    console.log(result);
  } catch (err) {
    console.error(err);
  }
}

run();
""",
"category": "chain_to_async",
},

# ── CATEGORY 9: concurrency limits (semaphore) ───────────────────────
{
"input": """\
async function processAll(urls) {
  // No rate limiting — hammers the server
  return Promise.all(urls.map(url => fetch(url).then(r => r.json())));
}

await processAll(largeListOf1000Urls);
""",
"output": """\
async function withConcurrency(tasks, limit) {
  const semaphore = new Array(limit).fill(Promise.resolve());
  let i = 0;
  return Promise.all(tasks.map(task => {
    const slot = i++ % limit;
    return (semaphore[slot] = semaphore[slot].then(task));
  }));
}

async function processAll(urls, concurrency = 5) {
  return withConcurrency(
    urls.map(url => () => fetch(url).then(r => r.json())),
    concurrency
  );
}

await processAll(largeListOf1000Urls, 5);
""",
"category": "concurrency_limit",
},

{
"input": """\
async function uploadFiles(files) {
  // All files at once — may overwhelm server
  const results = await Promise.all(
    files.map(f => uploadToS3(f))
  );
  return results;
}
""",
"output": """\
async function uploadFiles(files, batchSize = 3) {
  const results = [];
  for (let i = 0; i < files.length; i += batchSize) {
    const batch = files.slice(i, i + batchSize);
    const batchResults = await Promise.all(batch.map(f => uploadToS3(f)));
    results.push(...batchResults);
  }
  return results;
}
""",
"category": "concurrency_limit",
},

# ── CATEGORY 10: async error handling ────────────────────────────────
{
"input": """\
async function fetchWithRetry(url) {
  const res = await fetch(url);
  return res.json();
}

// No retry, no timeout, no error recovery
const data = await fetchWithRetry('/api/data');
""",
"output": """\
async function fetchWithRetry(url, retries = 3, delayMs = 500) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const res = await fetch(url, { signal: controller.signal });
        return await res.json();
      } finally {
        clearTimeout(timeout);
      }
    } catch (err) {
      if (attempt === retries) throw err;
      await new Promise(r => setTimeout(r, delayMs * attempt));
    }
  }
}

const data = await fetchWithRetry('/api/data');
""",
"category": "error_handling",
},

{
"input": """\
async function loadAll(ids) {
  try {
    const results = await Promise.all(ids.map(id => api.get(id)));
    return results;
  } catch (err) {
    // One failure kills all
    console.error(err);
    return [];
  }
}
""",
"output": """\
async function loadAll(ids) {
  const settled = await Promise.allSettled(ids.map(id => api.get(id)));
  const results = [];
  const errors  = [];
  for (const r of settled) {
    if (r.status === 'fulfilled') results.push(r.value);
    else errors.push(r.reason);
  }
  if (errors.length) console.warn(`${errors.length} failed:`, errors);
  return results;
}
""",
"category": "error_handling",
},

]  # end JS_PAIRS (30 cặp cơ bản)

# ─────────────────────────────────────────────
# AUGMENT ENGINE — sinh biến thể thực sự khác nhau
# ─────────────────────────────────────────────

# Các template slot để tạo biến thể
FETCH_SLOTS = [
    ("fetchUser",   "getUser",    "loadUser",   "readUser"),
    ("fetchOrder",  "getOrder",   "loadOrder",  "readOrder"),
    ("fetchProduct","getProduct", "loadProduct","readProduct"),
    ("userId",      "customerId", "memberId",   "clientId"),
    ("orders",      "invoices",   "bookings",   "purchases"),
    ("profile",     "account",    "settings",   "preferences"),
]

DOMAIN_TEMPLATES = [
    # (entity, api_prefix, id_name, list_name)
    ("Post",    "/api/posts",    "postId",    "posts"),
    ("Comment", "/api/comments", "commentId", "comments"),
    ("Product", "/api/products", "productId", "products"),
    ("Article", "/api/articles", "articleId", "articles"),
    ("Report",  "/api/reports",  "reportId",  "reports"),
    ("Invoice", "/api/invoices", "invoiceId", "invoices"),
    ("Task",    "/api/tasks",    "taskId",    "tasks"),
    ("Event",   "/api/events",   "eventId",   "events"),
    ("Message", "/api/messages", "messageId", "messages"),
    ("Session", "/api/sessions", "sessionId", "sessions"),
]

def make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=3):
    """Tạo cặp sequential await → Promise.all cho mỗi domain."""
    sub_paths = ["details", "history", "permissions", "metrics", "settings"]
    fields = [f"{list_name[:-1]}_{sub}" for sub in sub_paths[:n]]
    urls_in  = "\n".join(f"  const {f} = await fetch(`${prefix}/${{{id_name}}}/${sub}`).then(r => r.json());" for f, sub in zip(fields, sub_paths))
    urls_out = "\n".join(f"    fetch(`${prefix}/${{{id_name}}}/${sub}`).then(r => r.json())," for sub in sub_paths[:n])
    dest_out = ", ".join(fields)

    inp = f"""\
async function load{entity}Data({id_name}) {{
{urls_in}
  return {{ {dest_out} }};
}}
"""
    out = f"""\
async function load{entity}Data({id_name}) {{
  const [{dest_out}] = await Promise.all([
{urls_out}
  ]);
  return {{ {dest_out} }};
}}
"""
    return {"input": inp, "output": out, "category": "sequential_await_to_parallel", "source": "generated"}


def make_loop_parallel_pair(entity, prefix, id_name):
    """Tạo cặp for-loop sequential → Promise.all."""
    inp = f"""\
async function fetchAll{entity}s(ids) {{
  const results = [];
  for (const {id_name} of ids) {{
    const item = await fetch(`{prefix}/${{{id_name}}}`).then(r => r.json());
    results.push(item);
  }}
  return results;
}}
"""
    out = f"""\
async function fetchAll{entity}s(ids) {{
  return Promise.all(
    ids.map({id_name} => fetch(`{prefix}/${{{id_name}}}`).then(r => r.json()))
  );
}}
"""
    return {"input": inp, "output": out, "category": "sequential_loop_to_parallel", "source": "generated"}


def make_callback_promise_pair(entity, prefix, id_name):
    """Tạo cặp callback → async/await."""
    lower = entity.lower()
    inp = f"""\
function get{entity}(id, callback) {{
  setTimeout(() => callback(null, {{ id, type: '{lower}' }}), 200);
}}

get{entity}(1, (err, data) => {{
  if (err) return console.error(err);
  console.log(data);
}});
"""
    out = f"""\
function get{entity}(id) {{
  return new Promise(resolve =>
    setTimeout(() => resolve({{ id, type: '{lower}' }}), 200)
  );
}}

async function main() {{
  const data = await get{entity}(1);
  console.log(data);
}}

main();
"""
    return {"input": inp, "output": out, "category": "callback_to_async", "source": "generated"}


def make_batch_upload_pair(entity, method="POST"):
    """Tạo cặp sequential upload → batched parallel."""
    lower = entity.lower()
    inp = f"""\
async function save{entity}s(items) {{
  const saved = [];
  for (const item of items) {{
    const res = await fetch('/api/{lower}s', {{
      method: '{method}',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(item),
    }});
    saved.push(await res.json());
  }}
  return saved;
}}
"""
    out = f"""\
async function save{entity}s(items, concurrency = 4) {{
  const results = [];
  for (let i = 0; i < items.length; i += concurrency) {{
    const batch = items.slice(i, i + concurrency);
    const batchRes = await Promise.all(
      batch.map(item =>
        fetch('/api/{lower}s', {{
          method: '{method}',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(item),
        }}).then(r => r.json())
      )
    );
    results.push(...batchRes);
  }}
  return results;
}}
"""
    return {"input": inp, "output": out, "category": "concurrency_limit", "source": "generated"}


# Extended domain list for more coverage
DOMAIN_TEMPLATES_EXT = [
    ("User",      "/api/users",      "userId",      "users"),
    ("Order",     "/api/orders",     "orderId",     "orders"),
    ("Payment",   "/api/payments",   "paymentId",   "payments"),
    ("Review",    "/api/reviews",    "reviewId",    "reviews"),
    ("Category",  "/api/categories", "categoryId",  "categories"),
    ("Tag",       "/api/tags",       "tagId",       "tags"),
    ("File",      "/api/files",      "fileId",      "files"),
    ("Ticket",    "/api/tickets",    "ticketId",    "tickets"),
    ("Campaign",  "/api/campaigns",  "campaignId",  "campaigns"),
    ("Survey",    "/api/surveys",    "surveyId",    "surveys"),
    ("Project",   "/api/projects",   "projectId",   "projects"),
    ("Document",  "/api/documents",  "documentId",  "documents"),
    ("Image",     "/api/images",     "imageId",     "images"),
    ("Video",     "/api/videos",     "videoId",     "videos"),
    ("Playlist",  "/api/playlists",  "playlistId",  "playlists"),
]


DOMAIN_TEMPLATES_EXT2 = [
    ("Notification", "/api/notifications", "notifId",    "notifications"),
    ("Subscription", "/api/subscriptions", "subId",      "subscriptions"),
    ("Transaction",  "/api/transactions",  "txId",       "transactions"),
    ("Permission",   "/api/permissions",   "permId",     "permissions"),
    ("Audit",        "/api/audits",        "auditId",    "audits"),
    ("Export",       "/api/exports",       "exportId",   "exports"),
    ("Import",       "/api/imports",       "importId",   "imports"),
    ("Webhook",      "/api/webhooks",      "webhookId",  "webhooks"),
    ("Schedule",     "/api/schedules",     "scheduleId", "schedules"),
    ("Analytics",    "/api/analytics",     "analyticsId","analytics"),
    ("Log",          "/api/logs",          "logId",      "logs"),
    ("Config",       "/api/configs",       "configId",   "configs"),
    ("Token",        "/api/tokens",        "tokenId",    "tokens"),
    ("Cache",        "/api/caches",        "cacheId",    "caches"),
    ("Job",          "/api/jobs",          "jobId",      "jobs"),
]

ALL_DOMAINS = DOMAIN_TEMPLATES + DOMAIN_TEMPLATES_EXT + DOMAIN_TEMPLATES_EXT2

METHOD_VARIANTS = [
    ("update", "PUT"),
    ("patch",  "PATCH"),
    ("create", "POST"),
    ("delete", "DELETE"),
]

def make_retry_pair(entity, prefix, id_name):
    lower = entity.lower()
    inp = f"""async function fetch{entity}(id) {{
  const res = await fetch(`{prefix}/${{id}}`);
  return res.json();
}}

async function loadAll{entity}s(ids) {{
  const results = [];
  for (const id of ids) {{
    const item = await fetch{entity}(id);
    results.push(item);
  }}
  return results;
}}
"""
    out = f"""async function fetch{entity}WithRetry(id, retries = 2) {{
  for (let i = 0; i <= retries; i++) {{
    try {{
      const res = await fetch(`{prefix}/${{id}}`);
      if (!res.ok) throw new Error(res.status);
      return await res.json();
    }} catch (err) {{
      if (i === retries) throw err;
      await new Promise(r => setTimeout(r, 300 * (i + 1)));
    }}
  }}
}}

async function loadAll{entity}s(ids) {{
  return Promise.allSettled(ids.map(id => fetch{entity}WithRetry(id)))
    .then(results => results
      .filter(r => r.status === \'fulfilled\')
      .map(r => r.value)
    );
}}
"""
    return {"input": inp, "output": out, "category": "error_handling", "source": "generated"}


def make_cache_pair(entity, prefix, id_name):
    inp = f"""const cache = {{}};

async function get{entity}(id) {{
  if (cache[id]) return cache[id];
  const res = await fetch(`{prefix}/${{id}}`);
  const data = await res.json();
  cache[id] = data;
  return data;
}}
"""
    out = f"""const cache = new Map();
let inflight = new Map();

async function get{entity}(id) {{
  if (cache.has(id)) return cache.get(id);
  if (inflight.has(id)) return inflight.get(id);
  const promise = fetch(`{prefix}/${{id}}`)
    .then(r => r.json())
    .then(data => {{
      cache.set(id, data);
      inflight.delete(id);
      return data;
    }});
  inflight.set(id, promise);
  return promise;
}}
"""
    return {"input": inp, "output": out, "category": "race_condition_fix", "source": "generated"}


def make_stream_pair(entity, prefix):
    inp = f"""async function export{entity}s(filters) {{
  const res = await fetch(`{prefix}/export`, {{
    method: 'POST',
    body: JSON.stringify(filters),
  }});
  return res.json(); // loads entire response into memory
}}
"""
    out = f"""async function* stream{entity}s(filters) {{
  const res = await fetch(`{prefix}/export`, {{
    method: 'POST',
    body: JSON.stringify(filters),
  }});
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = \'\';
  while (true) {{
    const {{ done, value }} = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, {{ stream: true }});
    const lines = buffer.split('\\n');
    buffer = lines.pop();
    for (const line of lines) {{
      if (line.trim()) yield JSON.parse(line);
    }}
  }}
}}
"""
    return {"input": inp, "output": out, "category": "streaming", "source": "generated"}


def make_debounce_pair(entity):
    lower = entity.lower()
    inp = f"""async function search{entity}s(query) {{
  const res = await fetch(`/api/{lower}s/search?q=${{query}}`);
  return res.json();
}}

// Called on every keystroke — hammers server
input.addEventListener('input', e => {{
  search{entity}s(e.target.value).then(render);
}});
"""
    out = f"""function debounce(fn, ms) {{
  let timer;
  return (...args) => {{
    clearTimeout(timer);
    return new Promise(resolve => {{
      timer = setTimeout(() => resolve(fn(...args)), ms);
    }});
  }};
}}

async function search{entity}s(query) {{
  const res = await fetch(`/api/{lower}s/search?q=${{query}}`);
  return res.json();
}}

const debouncedSearch = debounce(search{entity}s, 300);
input.addEventListener('input', e => {{
  debouncedSearch(e.target.value).then(render);
}});
"""
    return {"input": inp, "output": out, "category": "debounce", "source": "generated"}



def make_pagination_pair(entity, prefix):
    lower = entity.lower()
    inp = f"""async function getAll{entity}s() {{
  const results = [];
  let page = 1;
  let hasMore = true;
  while (hasMore) {{
    const res = await fetch(`{prefix}?page=${{page}}&limit=100`);
    const data = await res.json();
    results.push(...data.items);
    hasMore = data.hasNext;
    page++;
  }}
  return results;
}}
"""
    out = f"""async function getAll{entity}s(concurrency = 3) {{
  const firstRes  = await fetch(`{prefix}?page=1&limit=100`);
  const firstPage = await firstRes.json();
  const totalPages = firstPage.totalPages;

  const pageNums = Array.from({{ length: totalPages - 1 }}, (_, i) => i + 2);
  const results  = [...firstPage.items];

  for (let i = 0; i < pageNums.length; i += concurrency) {{
    const batch = pageNums.slice(i, i + concurrency);
    const pages = await Promise.all(
      batch.map(p => fetch(`{prefix}?page=${{p}}&limit=100`).then(r => r.json()))
    );
    pages.forEach(p => results.push(...p.items));
  }}
  return results;
}}
"""
    return {"input": inp, "output": out, "category": "pagination_parallel", "source": "generated"}


def make_transform_pair(entity, prefix, id_name):
    inp = f"""async function process{entity}Batch(ids) {{
  const results = [];
  for (const id of ids) {{
    const raw  = await fetch(`{prefix}/${{id}}`).then(r => r.json());
    const transformed = transform(raw);
    const saved = await fetch(`{prefix}/${{id}}`, {{
      method: 'PUT',
      body: JSON.stringify(transformed),
    }}).then(r => r.json());
    results.push(saved);
  }}
  return results;
}}
"""
    out = f"""async function process{entity}Batch(ids, concurrency = 4) {{
  const process = async (id) => {{
    const raw         = await fetch(`{prefix}/${{id}}`).then(r => r.json());
    const transformed = transform(raw);
    return fetch(`{prefix}/${{id}}`, {{
      method: 'PUT',
      body: JSON.stringify(transformed),
    }}).then(r => r.json());
  }};

  const results = [];
  for (let i = 0; i < ids.length; i += concurrency) {{
    const batch = await Promise.all(ids.slice(i, i + concurrency).map(process));
    results.push(...batch);
  }}
  return results;
}}
"""
    return {"input": inp, "output": out, "category": "read_transform_write_parallel", "source": "generated"}


# --- NEW GENERATORS ---
def make_worker_threads_pair(entity):
    inp = f"""const {{ process{entity} }} = require('./cpu-heavy');

const items = [{entity}1, {entity}2, {entity}3, {entity}4];
const processed = items.map(process{entity});
"""
    out = f"""const {{ Worker }} = require('worker_threads');

function process{entity}(data) {{
  return new Promise((resolve, reject) => {{
    const worker = new Worker('./worker-{entity.lower()}.js', {{ workerData: data }});
    worker.on('message', resolve);
    worker.on('error', reject);
  }});
}}

const items = [{entity}1, {entity}2, {entity}3, {entity}4];
Promise.all(items.map(process{entity})).then(processed => {{
  console.log('done');
}});
"""
    return {"input": inp, "output": out, "category": "worker_threads", "source": "generated"}

def make_xhr_to_fetch_pair(entity, prefix):
    inp = f"""function fetch{entity}() {{
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '{prefix}/latest', false); // sync
  xhr.send(null);
  if (xhr.status === 200) {{
    return JSON.parse(xhr.responseText);
  }}
}}
"""
    out = f"""async function fetch{entity}() {{
  const res = await fetch('{prefix}/latest');
  if (res.ok) {{
    return res.json();
  }}
}}
"""
    return {"input": inp, "output": out, "category": "xhr_to_fetch", "source": "generated"}

def make_fs_callback_pair(entity):
    lower = entity.lower()
    inp = f"""const fs = require('fs');

function read{entity}Data(cb) {{
  fs.readFile('./{lower}.json', 'utf8', (err, data) => {{
    if (err) return cb(err);
    cb(null, JSON.parse(data));
  }});
}}
"""
    out = f"""const fs = require('fs').promises;

async function read{entity}Data() {{
  const data = await fs.readFile('./{lower}.json', 'utf8');
  return JSON.parse(data);
}}
"""
    return {"input": inp, "output": out, "category": "fs_callback_to_async", "source": "generated"}

def make_abort_controller_pair(entity, prefix):
    inp = f"""async function fetch{entity}Data(url) {{
  const res = await fetch(url);
  return res.json();
}}
"""
    out = f"""async function fetch{entity}Data(url, timeoutMs = 5000) {{
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {{
    const res = await fetch(url, {{ signal: controller.signal }});
    return await res.json();
  }} finally {{
    clearTimeout(timeoutId);
  }}
}}
"""
    return {"input": inp, "output": out, "category": "abort_controller", "source": "generated"}

def make_promise_any_pair(entity, prefix, id_name):
    inp = f"""async function fetch{entity}FromPrimary(id) {{
  return fetch(`{prefix}/${{id}}`).then(r => r.json());
}}
"""
    out = f"""async function fetch{entity}WithFallback(id) {{
  return Promise.any([
    fetch(`https://primary.api.com{prefix}/${{id}}`),
    fetch(`https://secondary.api.com{prefix}/${{id}}`),
    fetch(`https://fallback.api.com{prefix}/${{id}}`),
  ]).then(r => r.json());
}}
"""
    return {"input": inp, "output": out, "category": "promise_any", "source": "generated"}

def make_for_await_of_pair(entity, prefix):
    inp = f"""async function process{entity}Items(items) {{
  for (const item of items) {{
    await processItem(item);
  }}
}}
"""
    out = f"""async function* generate{entity}Items(items) {{
  for (const item of items) {{
    yield await processItem(item);
  }}
}}

async function process{entity}Items(items) {{
  for await (const result of generate{entity}Items(items)) {{
    console.log(result);
  }}
}}
"""
    return {"input": inp, "output": out, "category": "for_await_of", "source": "generated"}


def make_event_promise_pair(entity):
    inp = f"""function wait{entity}Ready(emitter, cb) {{
  emitter.once('{entity.lower()}_ready', data => {{
    cb(null, data);
  }});
  emitter.once('error', err => {{
    cb(err);
  }});
}}
"""
    out = f"""function wait{entity}Ready(emitter) {{
  return new Promise((resolve, reject) => {{
    const onReady = data => {{ cleanup(); resolve(data); }};
    const onError = err => {{ cleanup(); reject(err); }};
    const cleanup = () => {{
      emitter.off('{entity.lower()}_ready', onReady);
      emitter.off('error', onError);
    }};
    emitter.once('{entity.lower()}_ready', onReady);
    emitter.once('error', onError);
  }});
}}
"""
    return {"input": inp, "output": out, "category": "event_to_promise", "source": "generated"}

def make_polling_generator_pair(entity, prefix, id_name):
    inp = f"""function poll{entity}Status(id, cb) {{
  const interval = setInterval(async () => {{
    const status = await fetch(`{prefix}/${{id}}/status`).then(r => r.json());
    if (status.done) {{
      clearInterval(interval);
      cb(null, status);
    }}
  }}, 1000);
}}
"""
    out = f"""async function* poll{entity}Status(id, intervalMs = 1000) {{
  while (true) {{
    const status = await fetch(`${{prefix}}/${{id}}/status`).then(r => r.json());
    yield status;
    if (status.done) break;
    await new Promise(r => setTimeout(r, intervalMs));
  }}
}}
"""
    return {"input": inp, "output": out, "category": "polling_to_generator", "source": "generated"}

def generate_pairs(target: int, base_pairs: list) -> list:
    """Sinh đủ cặp bằng domain templates — mở rộng nhiều pattern."""
    all_pairs = list(base_pairs)
    generated = []

    for entity, prefix, id_name, list_name in ALL_DOMAINS:
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=3))
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=5))
        generated.append(make_loop_parallel_pair(entity, prefix, id_name))
        generated.append(make_callback_promise_pair(entity, prefix, id_name))
        generated.append(make_batch_upload_pair(entity, "POST"))
        generated.append(make_batch_upload_pair(entity, "PUT"))
        generated.append(make_retry_pair(entity, prefix, id_name))
        generated.append(make_cache_pair(entity, prefix, id_name))
        generated.append(make_stream_pair(entity, prefix))
        generated.append(make_debounce_pair(entity))

        generated.append(make_pagination_pair(entity, prefix))
        generated.append(make_transform_pair(entity, prefix, id_name))
        
        # New long-tail generators
        generated.append(make_worker_threads_pair(entity))
        generated.append(make_xhr_to_fetch_pair(entity, prefix))
        generated.append(make_fs_callback_pair(entity))
        generated.append(make_event_promise_pair(entity))
        generated.append(make_polling_generator_pair(entity, prefix, id_name))
        
        # Additional long-tail patterns
        generated.append(make_abort_controller_pair(entity, prefix))
        generated.append(make_promise_any_pair(entity, prefix, id_name))
        generated.append(make_for_await_of_pair(entity, prefix))
        
    all_pairs.extend(generated)
    return all_pairs


# ─────────────────────────────────────────────
# GITHUB SEARCH
# ─────────────────────────────────────────────

def search_github(query: str, token: str) -> list[dict]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    pairs = []
    try:
        resp = requests.get(
            "https://api.github.com/search/code",
            headers=headers,
            params={"q": f"{query} language:javascript", "per_page": 20, "sort": "indexed"},
            timeout=10,
        )
        if resp.status_code == 403:
            print("  ⚠️  Rate limit — thêm --token")
            return []
        if resp.status_code != 200:
            return []

        items = resp.json().get("items", [])
        print(f"  → {len(items)} files: '{query}'")

        for item in items[:8]:
            raw_url = (item.get("html_url", "")
                       .replace("github.com", "raw.githubusercontent.com")
                       .replace("/blob/", "/"))
            try:
                r = requests.get(raw_url, timeout=8)
                if r.status_code == 200:
                    code = r.text
                    lines = code.splitlines()
                    if 5 <= len(lines) <= MAX_LINES:
                        pairs.append({
                            "input": code, "output": "",
                            "language": "javascript",
                            "category": "github_raw",
                            "source": item.get("html_url", ""),
                            "needs_label": True,
                        })
            except Exception:
                pass
            time.sleep(0.3)
    except Exception as e:
        print(f"  ⚠️  {e}")

    return pairs


# ─────────────────────────────────────────────
# VALIDATE & DEDUP
# ─────────────────────────────────────────────

def validate(pair: dict) -> bool:
    try:
        inp = pair.get("input", "")
        if not inp or len(inp.strip()) < 20:
            return False
        if len(inp.splitlines()) > MAX_LINES:
            return False
        inp.encode("utf-8")
        pair.get("output", "").encode("utf-8")
        return True
    except Exception:
        return False


def dedup(pairs: list) -> list:
    seen, unique = set(), []
    for p in pairs:
        key = hashlib.md5(p.get("input", "").encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def stats(pairs: list):
    total      = len(pairs)
    has_output = sum(1 for p in pairs if p.get("output", "").strip())
    cats       = {}
    sources    = {}
    for p in pairs:
        cats[p.get("category","?")] = cats.get(p.get("category","?"), 0) + 1
        src = "synthetic" if p.get("source") in ("synthetic","generated") else "github"
        sources[src] = sources.get(src, 0) + 1

    print("\n" + "━"*52)
    print(f"📊  DATASET STATS")
    print(f"  Tổng cặp        : {total}")
    print(f"  Có output       : {has_output}")
    print(f"  Cần label       : {total - has_output}")
    print(f"  Nguồn           : {sources}")
    print(f"  Categories ({len(cats)}):")
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<35} {cnt}")
    if total >= TARGET_MIN:
        print(f"\n  ✅  Đạt mục tiêu {TARGET_MIN}+ cặp!")
    else:
        print(f"\n  ⚠️   Thiếu {TARGET_MIN - total} cặp")
    print("━"*52)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI1-01 JS Dataset Collector")
    parser.add_argument("--token",    default=GITHUB_TOKEN)
    parser.add_argument("--output",   default=OUTPUT_FILE)
    parser.add_argument("--github",   action="store_true", help="Bật GitHub search")
    parser.add_argument("--no-cache", action="store_true", help="Bỏ cache cũ")
    args = parser.parse_args()

    out_path = Path(args.output)
    all_pairs = []

    if out_path.exists() and not args.no_cache:
        with open(out_path, encoding="utf-8") as f:
            all_pairs = json.load(f)
        print(f"📂  Load {len(all_pairs)} cặp từ cache")

    print(f"\n[1/4] 📝  Nạp {len(JS_PAIRS)} synthetic JS pairs...")
    for p in JS_PAIRS:
        p.setdefault("language", "javascript")
        p.setdefault("source", "synthetic")
    all_pairs.extend(JS_PAIRS)

    print(f"\n[2/4] 🔄  Generate domain-template pairs...")
    all_pairs = generate_pairs(TARGET_MIN, all_pairs)
    print(f"  → {len(all_pairs)} cặp sau generate")

    if args.github:
        print(f"\n[3/4] 🔍  GitHub search ({len(JS_GITHUB_QUERIES)} queries)...")
        for q in JS_GITHUB_QUERIES:
            found = search_github(q, args.token)
            all_pairs.extend(found)
            time.sleep(1.5)
    else:
        print(f"\n[3/4] ⏭️   Skip GitHub  (dùng --github --token ghp_xxx để bật)")

    print(f"\n[4/4] ✅  Validate & deduplicate...")
    all_pairs = [p for p in all_pairs if validate(p)]
    before = len(all_pairs)
    all_pairs = dedup(all_pairs)
    print(f"  → Loại {before - len(all_pairs)} duplicate, còn {len(all_pairs)}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, ensure_ascii=False, indent=2)
    print(f"\n💾  Đã lưu → {out_path}")

    stats(all_pairs)
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  NEXT: python ai1_02_format_jsonl.py --input {out_path}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
# patch: expand generator — appended
