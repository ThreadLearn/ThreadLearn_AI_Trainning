import json
import random

random.seed(42)

# =============================================================================
# CHAIN-OF-THOUGHT (CoT) DATA GENERATOR
# =============================================================================

# 1. Race File Append (50 samples)
APPEND_SCENARIOS = [
    {'file': 'audit.log', 'func': 'recordAudit'},
    {'file': 'history.txt', 'func': 'writeHistory'},
    {'file': 'events.json', 'func': 'appendEvent'},
    {'file': 'debug.log', 'func': 'logDebug'},
    {'file': 'transactions.csv', 'func': 'saveTx'}
]

def generate_append_samples():
    samples = []
    for _ in range(10): 
        for s in APPEND_SCENARIOS:
            prompt = f"Fix concurrency bugs (Race conditions, Zalgo, Buffer Leaks, etc.) in the following JavaScript:\n\nfunction {s['func']}(msg) {{\n  fs.readFile('{s['file']}', 'utf8', (err, logData) => {{\n    const newData = (logData || '') + msg + '\\n';\n    fs.writeFile('{s['file']}', newData, () => {{}});\n  }});\n}}\n"
            completion = f"// THOUGHT PROCESS:\n// 1. Bug: Race condition due to non-atomic read-then-write file operations.\n// 2. Fix: Replace fs.readFile + fs.writeFile with the atomic OS-level fs.appendFile method.\n\n// CODE:\nconst {{ promises: fs }} = require('fs');\nasync function {s['func']}(msg) {{\n  await fs.appendFile('{s['file']}', msg + '\\n');\n}}\n"
            samples.append({"prompt": prompt, "completion": completion})
    return samples

# 2. Double Callback (50 samples)
CB_SCENARIOS = [
    {'call': 'redis.get', 'func': 'getUserData', 'err_msg': 'Cache miss'},
    {'call': 'db.findOne', 'func': 'fetchConfig', 'err_msg': 'Not found in DB'},
    {'call': 'User.findById', 'func': 'loadProfile', 'err_msg': 'Profile missing'},
    {'call': 'memcached.get', 'func': 'queryCache', 'err_msg': 'Miss'},
    {'call': 'Collection.findOne', 'func': 'requestItem', 'err_msg': 'No doc'}
]

def generate_double_cb_samples():
    samples = []
    for _ in range(10):
        for s in CB_SCENARIOS:
            prompt = f"Fix concurrency bugs (Race conditions, Zalgo, Buffer Leaks, etc.) in the following JavaScript:\n\nfunction {s['func']}(key, callback) {{\n  {s['call']}(key, (err, doc) => {{\n    if (err) callback(err);\n    if (!doc) callback(new Error('{s['err_msg']}'));\n    callback(null, doc);\n  }});\n}}\n"
            completion = f"// THOUGHT PROCESS:\n// 1. Bug: Double Callback. Without a return statement, the callback can be invoked multiple times if an error occurs.\n// 2. Fix: Add 'return' before every callback invocation on error paths.\n\n// CODE:\nfunction {s['func']}(key, callback) {{\n  {s['call']}(key, (err, doc) => {{\n    if (err) return callback(err);\n    if (!doc) return callback(new Error('{s['err_msg']}'));\n    return callback(null, doc);\n  }});\n}}\n"
            samples.append({"prompt": prompt, "completion": completion})
    return samples

# 3. Zalgo (50 samples)
ZALGO_SCENARIOS = [
    {'state': 'global.isLoaded', 'stateVar': 'global.loadedData', 'fetch': "db.query('SELECT * FROM users', ", 'func': 'loadUsers'},
    {'state': 'appCache.ready', 'stateVar': 'appCache.data', 'fetch': "redis.get('app_cache', ", 'func': 'getAppCache'},
    {'state': 'memoryStore.hit', 'stateVar': 'memoryStore.payload', 'fetch': "fs.readFile('data.json', 'utf8', ", 'func': 'fetchStore'},
    {'state': 'session.hasConfig', 'stateVar': 'session.configData', 'fetch': "db.findOne({ type: 'config' }, ", 'func': 'getConfig'},
    {'state': 'window.isDataLoaded', 'stateVar': 'window.appData', 'fetch': "network.get('/api/data', ", 'func': 'loadWindowData'}
]

def generate_zalgo_samples():
    samples = []
    for _ in range(10):
        for s in ZALGO_SCENARIOS:
            prompt = f"Fix concurrency bugs (Race conditions, Zalgo, Buffer Leaks, etc.) in the following JavaScript:\n\nfunction {s['func']}(cb) {{\n  if ({s['state']}) {{\n    cb(null, {s['stateVar']});\n    return;\n  }}\n  {s['fetch']}(err, data) => {{\n    {s['state']} = true;\n    {s['stateVar']} = data;\n    cb(null, data);\n  }});\n}}\n"
            completion = f"// THOUGHT PROCESS:\n// 1. Bug: Zalgo anti-pattern. The callback is sometimes called synchronously (if cached) and sometimes asynchronously, creating unpredictable execution order.\n// 2. Fix: Wrap the synchronous callback execution in process.nextTick() to normalize the behavior to always be asynchronous.\n\n// CODE:\nfunction {s['func']}(cb) {{\n  if ({s['state']}) {{\n    return process.nextTick(() => cb(null, {s['stateVar']}));\n  }}\n  {s['fetch']}(err, data) => {{\n    if (err) return cb(err);\n    {s['state']} = true;\n    {s['stateVar']} = data;\n    cb(null, data);\n  }});\n}}\n"
            samples.append({"prompt": prompt, "completion": completion})
    return samples

# 4. Buffer Leak (50 samples)
LEAK_SCENARIOS = [
    {'source': 'fs.createReadStream("video.mp4")', 'var': 'videoRs', 'route': '/stream/video'},
    {'source': 'fs.createReadStream("audio.mp3")', 'var': 'audioRs', 'route': '/stream/audio'},
    {'source': 'request.get("http://server/video.mp4")', 'var': 'downloadStream', 'route': '/proxy/video'},
    {'source': 's3.getObject({ Bucket: "b", Key: "k" }).createReadStream()', 'var': 's3Stream', 'route': '/download/s3'},
    {'source': 'fs.createReadStream("large_archive.zip")', 'var': 'fileStream', 'route': '/download/zip'}
]

def generate_leak_samples():
    samples = []
    for _ in range(10):
        for s in LEAK_SCENARIOS:
            prompt = f"Fix concurrency bugs (Race conditions, Zalgo, Buffer Leaks, etc.) in the following JavaScript:\n\napp.get('{s['route']}', (req, res) => {{\n  const {s['var']} = {s['source']};\n  {s['var']}.pipe(res);\n  {s['var']}.on('error', (e) => res.status(500).end());\n}});\n"
            completion = f"// THOUGHT PROCESS:\n// 1. Bug: Stream Buffer Leak. If the client drops the HTTP connection early, the readable stream keeps pumping data into memory.\n// 2. Fix: Listen for the 'close' event on the client request and the 'finish' event on the response to manually destroy() the source stream.\n\n// CODE:\napp.get('{s['route']}', (req, res) => {{\n  const {s['var']} = {s['source']};\n  {s['var']}.pipe(res);\n  {s['var']}.on('error', (e) => {{\n    if (!res.headersSent) res.status(500).end();\n  }});\n  req.on('close', () => {s['var']}.destroy());\n  res.on('finish', () => {s['var']}.destroy());\n}});\n"
            samples.append({"prompt": prompt, "completion": completion})
    return samples

def main():
    samples = []
    samples.extend(generate_append_samples())
    samples.extend(generate_double_cb_samples())
    samples.extend(generate_zalgo_samples())
    samples.extend(generate_leak_samples())
    
    random.shuffle(samples)
    
    patch_path = "f:/self_Learn/project/tool_dataset/ThreadLearn_AI_Trainning/ai1/data/processed/threadlearn_patch_cot.jsonl"
    with open(patch_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"Saved 200 CoT samples to {patch_path}")

if __name__ == "__main__":
    main()
