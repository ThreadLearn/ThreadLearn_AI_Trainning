import json
import os

test_cases = [
    # 1-5: Race Conditions
    {"id": "test_01", "category": "Race Condition", "code": "let counter = 0;\nfunction increment() {\n  setTimeout(() => {\n    counter++;\n  }, Math.random() * 100);\n}\nincrement(); increment();"},
    {"id": "test_02", "category": "Race Condition", "code": "const updateAccount = async (id, amount) => {\n  const balance = await db.getBalance(id);\n  setTimeout(() => db.setBalance(id, balance + amount), 10);\n};"},
    {"id": "test_03", "category": "Race Condition", "code": "const checkAndCreateUser = (email) => {\n  db.find({email}).then(user => {\n    if (!user) db.create({email});\n  });\n};"},
    {"id": "test_04", "category": "Race Condition", "code": "let cache = null;\nfunction getCache() {\n  if (!cache) {\n    fetchData().then(d => cache = d);\n  }\n  return cache;\n}"},
    {"id": "test_05", "category": "Race Condition", "code": "let logs = '';\nfunction appendLog(msg) {\n  fs.readFile('log.txt', 'utf8', (err, data) => {\n    fs.writeFile('log.txt', data + msg, () => {});\n  });\n}"},
    # 6-10: Event Loop Blocking (Sync loops/crypto)
    {"id": "test_06", "category": "Event Loop Blocking", "code": "function processHugeArray(arr) {\n  for(let i=0; i < arr.length; i++) {\n    heavyMath(arr[i]);\n  }\n}"},
    {"id": "test_07", "category": "Event Loop Blocking", "code": "const crypto = require('crypto');\nfunction encryptPasswords(users) {\n  users.forEach(u => {\n    u.hash = crypto.pbkdf2Sync(u.password, 'salt', 100000, 64, 'sha512');\n  });\n}"},
    {"id": "test_08", "category": "Event Loop Blocking", "code": "const parseJSONLines = (lines) => {\n  lines.forEach(line => {\n    JSON.parse(line);\n  });\n};"},
    {"id": "test_09", "category": "Event Loop Blocking", "code": "function renderPages(pages) {\n  return pages.map(page => renderSync(page));\n}"},
    {"id": "test_10", "category": "Event Loop Blocking", "code": "const fs = require('fs');\nfunction backupLogs(files) {\n  files.forEach(f => {\n    const data = fs.readFileSync(f);\n    fs.writeFileSync(f + '.bak', data);\n  });\n}"},
    # 11-15: Callback Hell / Unhandled Rejections / Zalgo
    {"id": "test_11", "category": "Unhandled Rejection", "code": "app.get('/', (req, res) => {\n  db.query().then(data => res.json(data)); // Missing catch\n});"},
    {"id": "test_12", "category": "Double Callback", "code": "function getUser(id, cb) {\n  db.findById(id, (err, user) => {\n    if (err) cb(err);\n    if (!user) cb(new Error('Not found'));\n    cb(null, user);\n  });\n}"},
    {"id": "test_13", "category": "Zalgo", "code": "const cache = {};\nfunction fetchObj(id, cb) {\n  if (cache[id]) return cb(cache[id]); // Sync call\n  networkFetch(id, (data) => {\n    cache[id] = data; cb(data); // Async call\n  });\n}"},
    {"id": "test_14", "category": "Context Loss", "code": "class Service {\n  constructor() { this.name = 'Serv'; }\n  run() {\n    setTimeout(function() {\n      console.log(this.name + ' running');\n    }, 100);\n  }\n}"},
    {"id": "test_15", "category": "Callback Hell", "code": "function doTask(cb) {\n  step1(r1 => {\n    step2(r1, r2 => {\n      step3(r2, r3 => {\n        cb(r3);\n      });\n    });\n  });\n}"},
    # 16-20: Missing Promise.all / Resource Exhaustion
    {"id": "test_16", "category": "Resource Exhaustion", "code": "async function downloadAll(urls) {\n  return await Promise.all(urls.map(url => fetch(url))); // Crashes on 100k urls\n}"},
    {"id": "test_17", "category": "Sequential Awaits", "code": "async function getDashboard(id) {\n  const user = await db.getUser(id);\n  const stats = await db.getStats(id);\n  const friends = await db.getFriends(id);\n  return {user, stats, friends};\n}"},
    {"id": "test_18", "category": "Missing Promise.all", "code": "async function sendEmails(users) {\n  for(let i=0; i<users.length; i++) {\n    await emailService.send(users[i].email);\n  }\n}"},
    {"id": "test_19", "category": "Buffer Leak", "code": "function streamData(req, res) {\n  const rs = fs.createReadStream('file.mp4');\n  rs.pipe(res);\n  // rs stays open if res crashes\n}"},
    {"id": "test_20", "category": "Event Loop Ordering", "code": "let init = false;\nprocess.nextTick(() => init = true);\nsetTimeout(() => console.log(init), 0);\n"}
]

os.makedirs('ai1/evaluation', exist_ok=True)
with open('ai1/evaluation/test_cases.json', 'w', encoding='utf-8') as f:
    json.dump(test_cases, f, indent=2, ensure_ascii=False)
