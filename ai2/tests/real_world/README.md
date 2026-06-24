# Real-World Test Cases

30 test cases lấy từ **real bugs trong production npm packages** — không phải ví dụ tự tạo.

## Mục đích

Đánh giá khách quan hơn so với `eval_baseline.py` (tự làm test cases).  
Mỗi case có nguồn gốc rõ ràng (GitHub issue URL hoặc Node.js docs).

## Nguồn

| ID | Package | Bug | Category | Source |
|----|---------|-----|----------|--------|
| rw_01 | request@2.88.0 | TOCTOU fs.exists | Race Condition | [GitHub #2484](https://github.com/request/request/issues/2484) |
| rw_02 | mysql@2.15.0 | Double callback | Double Callback | [GitHub #1260](https://github.com/mysqljs/mysql/issues/1260) |
| rw_03 | async@1.x | Zalgo cache/DB | Zalgo | [GitHub #1066](https://github.com/caolan/async/issues/1066) |
| rw_04 | express (any) | Event loop block | Event Loop Blocking | [GitHub #2471](https://github.com/expressjs/express/issues/2471) |
| rw_05 | express-async-errors@1.3.1 | Context loss this | Context Loss | [GitHub #3](https://github.com/davidbanham/express-async-errors/issues/3) |
| rw_06 | pg@6.x-7.x | Pool deadlock | Resource Exhaustion | [GitHub #1228](https://github.com/brianc/node-postgres/issues/1228) |
| rw_07 | Node.js streams | Pipe no error handler | Stream Leak | [GitHub #24941](https://github.com/nodejs/node/issues/24941) |
| rw_08 | passport@0.3.x | Session race | Race Condition | [GitHub #369](https://github.com/jaredhanson/passport/issues/369) |
| rw_09 | co@4.6.0 | Unhandled rejection | Unhandled Rejection | [GitHub #185](https://github.com/tj/co/issues/185) |
| rw_10 | Node.js streams | Backpressure OOM | Resource Exhaustion | [GitHub #23267](https://github.com/nodejs/node/issues/23267) |
| rw_11 | ioredis@2.x | Timeout double cb | Double Callback | [GitHub #419](https://github.com/luin/ioredis/issues/419) |
| rw_12 | Node.js pattern | Sequential awaits | Sequential Awaits | [nodebestpractices](https://github.com/goldbergyoni/nodebestpractices) |
| rw_13 | bull@3.x | Job double-pickup | Race Condition | [GitHub #1016](https://github.com/OptimalBits/bull/issues/1016) |
| rw_14 | async@1.5.2 | Callback hell | Callback Hell | [GitHub #1122](https://github.com/caolan/async/issues/1122) |
| rw_15 | axios (misuse) | Unbounded Promise.all | Resource Exhaustion | [GitHub #1038](https://github.com/axios/axios/issues/1038) |
| rw_16 | Node.js crypto | pbkdf2Sync blocking | Event Loop Blocking | Node.js docs |
| rw_17 | async@1.5.2 | Zalgo recursion | Zalgo | [GitHub #1122](https://github.com/caolan/async/issues/1122) |
| rw_18 | express@4.x | Async route no catch | Unhandled Rejection | [GitHub #2700](https://github.com/expressjs/express/issues/2700) |
| rw_19 | Node.js fs | TOCTOU writeFile | Race Condition | [GitHub #6718](https://github.com/nodejs/node/issues/6718) |
| rw_20 | Node.js timers | this in setTimeout | Context Loss | Node.js docs |
| rw_21 | express-session@1.x | session.save() not awaited | Sequential Awaits | [GitHub #526](https://github.com/expressjs/session/issues/526) |
| rw_22 | async@1.5.2 | done() called twice in series | Double Callback | [GitHub #559](https://github.com/caolan/async/issues/559) |
| rw_23 | sequelize@6.x | 50 concurrent txns exhaust pool | Resource Exhaustion | [GitHub #10976](https://github.com/sequelize/sequelize/issues/10976) |
| rw_24 | mongoose@5.x | createConnection() unhandled reject | Unhandled Rejection | [GitHub #8706](https://github.com/Automattic/mongoose/issues/8706) |
| rw_25 | node-redis@4.x | concurrent sUnsubscribe race | Race Condition | [GitHub #2685](https://github.com/redis/node-redis/issues/2685) |
| rw_26 | knex@0.21.x | forUpdate parallel deadlock | Event Loop Blocking | [GitHub #5025](https://github.com/knex/knex/issues/5025) |
| rw_27 | express-session@1.x | touch() + save() write race | Sequential Awaits | [GitHub #340](https://github.com/expressjs/session/issues/340) |
| rw_28 | mongoose@5.x | insertMany dual callback+promise | Unhandled Rejection | [GitHub #5784](https://github.com/Automattic/mongoose/issues/5784) |
| rw_29 | ioredis@4.x | pipeline.exec() called twice | Double Callback | [GitHub #1185](https://github.com/luin/ioredis/issues/1185) |
| rw_30 | express@4.x | async middleware no catch chain | Unhandled Rejection | [GitHub #2700](https://github.com/expressjs/express/issues/2700) |

## Phân bố category (30 cases)

| Category | Số cases | IDs |
|----------|---------|-----|
| Race Condition | 5 | rw_01, rw_08, rw_13, rw_19, rw_25 |
| Double Callback | 5 | rw_02, rw_11, rw_22, rw_29, rw_06 |
| Unhandled Rejection | 5 | rw_09, rw_18, rw_24, rw_28, rw_30 |
| Resource Exhaustion | 4 | rw_06, rw_10, rw_15, rw_23 |
| Sequential Awaits | 4 | rw_12, rw_21, rw_27, rw_28 |
| Event Loop Blocking | 3 | rw_04, rw_16, rw_26 |
| Zalgo | 2 | rw_03, rw_17 |
| Context Loss | 2 | rw_05, rw_20 |
| Callback Hell | 2 | rw_14, rw_17 |
| Stream/Buffer Leak | 2 | rw_07, rw_10 |

## Độ khó

| Level | Count | IDs |
|-------|-------|-----|
| Easy (1 pattern, code ngắn) | 8 | rw_02, rw_12, rw_18, rw_21, rw_22, rw_27, rw_29, rw_30 |
| Medium (cần hiểu async flow) | 12 | rw_01, rw_03, rw_04, rw_07, rw_10, rw_11, rw_15, rw_16, rw_19, rw_23, rw_24, rw_28 |
| Hard (multi-pattern hoặc race window ẩn) | 10 | rw_05, rw_06, rw_08, rw_09, rw_13, rw_14, rw_17, rw_20, rw_25, rw_26 |

## Dự đoán model detect rate

| Pattern | Detect rate | Lý do |
|---------|------------|-------|
| sequential_awaits | ~90% | Race Detector có regex, pattern rõ |
| double_callback | ~70% | Race Detector có regex |
| unhandled_rejection | ~60% | Regex detect async function thiếu try/catch |
| callback_hell | ~40% | Không có static pattern, model phải reason |
| race_condition (TOCTOU) | ~30% | Cần semantic understanding |
| context_loss | ~20% | Ngoài focus training |
| zalgo | ~15% | Rất subtle, cần hiểu call ordering |

## Chạy eval

```bash
cd ai2
python tests/real_world_cases/eval_real_world.py
```

## Format mỗi test case

```json
{
  "id": "rw_01",
  "category": "Race Condition",
  "source": "https://github.com/...",
  "package": "request@2.88.0",
  "description": "...",
  "code": "...",
  "expected_patterns": ["race_condition"],
  "notes": "..."
}
```
