# Real-World Test Cases

20 test cases lấy từ **real bugs trong production npm packages** — không phải ví dụ tự tạo.

## Mục đích

Đánh giá khách quan hơn so với `eval_baseline.py` (tự làm test cases).  
Mỗi case có nguồn gốc rõ ràng (GitHub issue URL hoặc Node.js docs).

## Nguồn

| ID | Package | Bug | Source |
|----|---------|-----|--------|
| rw_01 | request@2.88.0 | TOCTOU fs.exists | [GitHub #2484](https://github.com/request/request/issues/2484) |
| rw_02 | mysql@2.15.0 | Double callback | [GitHub #1260](https://github.com/mysqljs/mysql/issues/1260) |
| rw_03 | async@1.x | Zalgo cache/DB | [GitHub #1066](https://github.com/caolan/async/issues/1066) |
| rw_04 | express (any) | Event loop block | [GitHub #2471](https://github.com/expressjs/express/issues/2471) |
| rw_05 | express-async-errors@1.3.1 | Context loss this | [GitHub #3](https://github.com/davidbanham/express-async-errors/issues/3) |
| rw_06 | pg@6.x-7.x | Pool deadlock | [GitHub #1228](https://github.com/brianc/node-postgres/issues/1228) |
| rw_07 | Node.js streams | Pipe no error handler | [GitHub #24941](https://github.com/nodejs/node/issues/24941) |
| rw_08 | passport@0.3.x | Session race | [GitHub #369](https://github.com/jaredhanson/passport/issues/369) |
| rw_09 | co@4.6.0 | Unhandled rejection | [GitHub #185](https://github.com/tj/co/issues/185) |
| rw_10 | Node.js streams | Backpressure OOM | [GitHub #23267](https://github.com/nodejs/node/issues/23267) |
| rw_11 | ioredis@2.x | Timeout double cb | [GitHub #419](https://github.com/luin/ioredis/issues/419) |
| rw_12 | Node.js pattern | Sequential awaits | [nodebestpractices](https://github.com/goldbergyoni/nodebestpractices) |
| rw_13 | bull@3.x | Job double-pickup | [GitHub #1016](https://github.com/OptimalBits/bull/issues/1016) |
| rw_14 | async@1.5.2 | Callback hell | [GitHub #1122](https://github.com/caolan/async/issues/1122) |
| rw_15 | axios (misuse) | Unbounded Promise.all | [GitHub #1038](https://github.com/axios/axios/issues/1038) |
| rw_16 | Node.js crypto | pbkdf2Sync blocking | Node.js docs |
| rw_17 | async@1.5.2 | Zalgo recursion | [GitHub #1122](https://github.com/caolan/async/issues/1122) |
| rw_18 | express@4.x | Async route no catch | [GitHub #2700](https://github.com/expressjs/express/issues/2700) |
| rw_19 | Node.js fs | TOCTOU writeFile | [GitHub #6718](https://github.com/nodejs/node/issues/6718) |
| rw_20 | Node.js timers | this in setTimeout | Node.js docs |

## Phân bố category

| Category | Số cases |
|----------|---------|
| Race Condition | 4 (rw_01, rw_08, rw_13, rw_19) |
| Double Callback | 3 (rw_02, rw_06, rw_11) |
| Zalgo | 2 (rw_03, rw_17) |
| Event Loop Blocking | 2 (rw_04, rw_16) |
| Context Loss | 2 (rw_05, rw_20) |
| Resource Exhaustion | 3 (rw_06, rw_10, rw_15) |
| Stream/Buffer Leak | 2 (rw_07, rw_10) |
| Unhandled Rejection | 2 (rw_09, rw_18) |
| Sequential Awaits | 1 (rw_12) |
| Callback Hell | 2 (rw_14, rw_17) |

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
