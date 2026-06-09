import re

def fix_collector():
    with open('ai1_01_dataset_collector.py', 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Fix missing $ in template literals
    code = code.replace("`{prefix}/{{{id_name}}}/{sub}`", "`${prefix}/${{{id_name}}}/${sub}`")
    code = code.replace("`{prefix}/{{{id_name}}}`", "`${prefix}/${{{id_name}}}`")
    
    # 2. Reduce the number of sequential_await_to_parallel to balance dataset
    old_seq = """        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=2))
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=3))
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=4))
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=5))"""
    
    new_seq = """        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=3))
        generated.append(make_sequential_fetch_pair(entity, prefix, id_name, list_name, n=5))"""
    
    code = code.replace(old_seq, new_seq)

    # 3. Add long-tail category generators
    long_tail_generators = """
# --- NEW GENERATORS ---
def make_worker_threads_pair(entity):
    inp = f\"\"\"const {{ process{entity} }} = require('./cpu-heavy');

const items = [{entity}1, {entity}2, {entity}3, {entity}4];
const processed = items.map(process{entity});
\"\"\"
    out = f\"\"\"const {{ Worker }} = require('worker_threads');

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
\"\"\"
    return {"input": inp, "output": out, "category": "worker_threads", "source": "generated"}

def make_xhr_to_fetch_pair(entity, prefix):
    inp = f\"\"\"function fetch{entity}() {{
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '{prefix}/latest', false); // sync
  xhr.send(null);
  if (xhr.status === 200) {{
    return JSON.parse(xhr.responseText);
  }}
}}
\"\"\"
    out = f\"\"\"async function fetch{entity}() {{
  const res = await fetch('{prefix}/latest');
  if (res.ok) {{
    return res.json();
  }}
}}
\"\"\"
    return {"input": inp, "output": out, "category": "xhr_to_fetch", "source": "generated"}

def make_fs_callback_pair(entity):
    lower = entity.lower()
    inp = f\"\"\"const fs = require('fs');

function read{entity}Data(cb) {{
  fs.readFile('./{lower}.json', 'utf8', (err, data) => {{
    if (err) return cb(err);
    cb(null, JSON.parse(data));
  }});
}}
\"\"\"
    out = f\"\"\"const fs = require('fs').promises;

async function read{entity}Data() {{
  const data = await fs.readFile('./{lower}.json', 'utf8');
  return JSON.parse(data);
}}
\"\"\"
    return {"input": inp, "output": out, "category": "fs_callback_to_async", "source": "generated"}

def make_event_promise_pair(entity):
    inp = f\"\"\"function wait{entity}Ready(emitter, cb) {{
  emitter.once('{entity.lower()}_ready', data => {{
    cb(null, data);
  }});
  emitter.once('error', err => {{
    cb(err);
  }});
}}
\"\"\"
    out = f\"\"\"function wait{entity}Ready(emitter) {{
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
\"\"\"
    return {"input": inp, "output": out, "category": "event_to_promise", "source": "generated"}

def make_polling_generator_pair(entity, prefix, id_name):
    inp = f\"\"\"function poll{entity}Status(id, cb) {{
  const interval = setInterval(async () => {{
    const status = await fetch(`{prefix}/${{id}}/status`).then(r => r.json());
    if (status.done) {{
      clearInterval(interval);
      cb(null, status);
    }}
  }}, 1000);
}}
\"\"\"
    out = f\"\"\"async function* poll{entity}Status(id, intervalMs = 1000) {{
  while (true) {{
    const status = await fetch(`${{prefix}}/${{id}}/status`).then(r => r.json());
    yield status;
    if (status.done) break;
    await new Promise(r => setTimeout(r, intervalMs));
  }}
}}
\"\"\"
    return {"input": inp, "output": out, "category": "polling_to_generator", "source": "generated"}
"""
    
    if "def make_worker_threads_pair" not in code:
        # Append before generate_pairs
        code = code.replace("def generate_pairs(target: int, base_pairs: list) -> list:", long_tail_generators + "\ndef generate_pairs(target: int, base_pairs: list) -> list:")

    # Add calls to these generators inside generate_pairs loop
    new_calls = """        generated.append(make_worker_threads_pair(entity))
        generated.append(make_xhr_to_fetch_pair(entity, prefix))
        generated.append(make_fs_callback_pair(entity))
        generated.append(make_event_promise_pair(entity))
        generated.append(make_polling_generator_pair(entity, prefix, id_name))"""
    
    if "make_worker_threads_pair(entity)" not in code:
        code = code.replace("generated.append(make_transform_pair(entity, prefix, id_name))", "generated.append(make_transform_pair(entity, prefix, id_name))\n" + new_calls)

    with open('ai1_01_dataset_collector.py', 'w', encoding='utf-8') as f:
        f.write(code)

fix_collector()
print("Done patching ai1_01_dataset_collector.py")
