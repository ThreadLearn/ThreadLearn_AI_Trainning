import json
import random
import itertools

random.seed(42)  # For reproducibility

# =============================================================================
# TEMPLATES FOR THE 4 PATTERNS
# =============================================================================

# 1. Race File Append (25 samples)
APPEND_FILES = ['audit.log', 'history.txt', 'events.json', 'debug.log', 'transactions.csv']
APPEND_FUNCS = ['recordAudit', 'writeHistory', 'appendEvent', 'logDebug', 'saveTx']
APPEND_VARS = ['data', 'content', 'prev', 'log', 'text']

def generate_append_samples():
    samples = []
    for f, func, var in itertools.product(APPEND_FILES, APPEND_FUNCS, APPEND_VARS):
        if len(samples) >= 25: break
        prompt = f"""Convert to concurrent JavaScript:

function {func}(msg) {{
  fs.readFile('{f}', 'utf8', (err, {var}) => {{
    const newData = ({var} || '') + msg + '\\n';
    fs.writeFile('{f}', newData, () => {{}});
  }});
}}
"""
        completion = f"""// Fix: Use atomic appendFile instead of read-then-write
const {{ promises: fs }} = require('fs');
async function {func}(msg) {{
  await fs.appendFile('{f}', msg + '\\n');
}}
"""
        samples.append({"prompt": prompt, "completion": completion})
    return samples

# 2. Double Callback (25 samples)
DB_CALLS = ['redis.get', 'db.find', 'api.request', 'cache.fetch', 'mongo.findOne']
CB_FUNCS = ['getUserData', 'fetchConfig', 'loadProfile', 'queryCache', 'requestItem']
ERR_VARS = [('err', 'result'), ('error', 'data'), ('e', 'res'), ('err', 'doc'), ('err', 'payload')]

def generate_double_cb_samples():
    samples = []
    for db_call, func, (err, res) in itertools.product(DB_CALLS, CB_FUNCS, ERR_VARS):
        if len(samples) >= 25: break
        prompt = f"""Convert to concurrent JavaScript:

function {func}(key, callback) {{
  {db_call}(key, ({err}, {res}) => {{
    if ({err}) callback({err});
    if (!{res}) callback(new Error('Not found'));
    callback(null, {res});
  }});
}}
"""
        completion = f"""// Fix: Add return statement before calling callback on error paths
function {func}(key, callback) {{
  {db_call}(key, ({err}, {res}) => {{
    if ({err}) return callback({err});
    if (!{res}) return callback(new Error('Not found'));
    return callback(null, {res});
  }});
}}
"""
        samples.append({"prompt": prompt, "completion": completion})
    return samples

# 3. Zalgo (25 samples)
ZALGO_STATES = ['global.isLoaded', 'appCache.ready', 'memoryStore.hit', 'session.config', 'window.dataLoaded']
ZALGO_FETCHES = ['db.query', 'http.fetch', 'fs.readFile', 'network.get', 'api.load']
ZALGO_FUNCS = ['loadState', 'getAppCache', 'fetchStore', 'getConfig', 'loadWindow']

def generate_zalgo_samples():
    samples = []
    for state, fetch_call, func in itertools.product(ZALGO_STATES, ZALGO_FETCHES, ZALGO_FUNCS):
        if len(samples) >= 25: break
        prompt = f"""Convert to concurrent JavaScript:

function {func}(cb) {{
  if ({state}) {{
    cb(null, {state}Data);
    return;
  }}
  {fetch_call}('SELECT *', (err, data) => {{
    {state} = true;
    {state}Data = data;
    cb(null, data);
  }});
}}
"""
        completion = f"""// Fix: Wrap synchronous callback in process.nextTick to avoid Zalgo anti-pattern
function {func}(cb) {{
  if ({state}) {{
    return process.nextTick(() => cb(null, {state}Data));
  }}
  {fetch_call}('SELECT *', (err, data) => {{
    if (err) return cb(err);
    {state} = true;
    {state}Data = data;
    cb(null, data);
  }});
}}
"""
        samples.append({"prompt": prompt, "completion": completion})
    return samples

# 4. Buffer Leak (25 samples)
LEAK_SOURCES = ['fs.createReadStream("video.mp4")', 'http.get("http://server/stream")', 'request.get(url)', 's3.download(file)', 'aws.getStream()']
LEAK_VARS = ['audioStream', 'videoRs', 'fileStream', 'downloadStream', 'mediaRs']
LEAK_ROUTES = ['/proxy', '/stream', '/download', '/media', '/listen']

def generate_leak_samples():
    samples = []
    for source, var, route in itertools.product(LEAK_SOURCES, LEAK_VARS, LEAK_ROUTES):
        if len(samples) >= 25: break
        prompt = f"""Convert to concurrent JavaScript:

app.get('{route}', (req, res) => {{
  const {var} = {source};
  {var}.pipe(res);
  {var}.on('error', (e) => res.status(500).end());
}});
"""
        completion = f"""// Fix: Destroy stream when client disconnects to prevent buffer leak
app.get('{route}', (req, res) => {{
  const {var} = {source};
  {var}.pipe(res);
  {var}.on('error', (e) => {{
    if (!res.headersSent) res.status(500).end();
  }});
  req.on('close', () => {var}.destroy());
  res.on('finish', () => {var}.destroy());
}});
"""
        samples.append({"prompt": prompt, "completion": completion})
    return samples

def verify_samples(samples):
    assert len(samples) == 100, f"Expected 100 samples, got {len(samples)}"
    for i, s in enumerate(samples):
        assert 'prompt' in s and 'completion' in s, f"Sample {i} missing keys"
        assert s['prompt'].startswith("Convert to concurrent JavaScript:"), f"Sample {i} invalid prompt prefix"
        assert s['completion'].startswith("// Fix:"), f"Sample {i} invalid completion prefix"
    print("Verification passed: 100 valid JSONL samples generated.")

def main():
    samples = []
    samples.extend(generate_append_samples())
    samples.extend(generate_double_cb_samples())
    samples.extend(generate_zalgo_samples())
    samples.extend(generate_leak_samples())
    
    # Shuffle slightly so they are mixed in the dataset
    random.shuffle(samples)
    
    verify_samples(samples)
    
    # Write to a patch file
    patch_path = "f:/self_Learn/project/tool_dataset/ThreadLearn_AI_Trainning/ai1/data/processed/threadlearn_patch_augmented.jsonl"
    with open(patch_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"Saved 100 augmented samples to {patch_path}")
    
    # Also append to the main training file
    main_path = "f:/self_Learn/project/tool_dataset/ThreadLearn_AI_Trainning/ai1/data/processed/threadlearn_train_eval.jsonl"
    try:
        with open(main_path, "a", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"Appended 100 samples to {main_path}")
    except Exception as e:
        print(f"Failed to append to main path: {e}")

if __name__ == "__main__":
    main()
