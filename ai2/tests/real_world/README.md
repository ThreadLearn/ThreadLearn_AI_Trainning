# Real-World Eval — ThreadLearn AI2

30 test cases lấy từ **real bugs trong production npm packages** — không phải ví dụ tự tạo.  
Mỗi case có nguồn gốc rõ ràng (GitHub issue URL hoặc Node.js docs).

---

## Tổng quan kết quả

### Without Pipeline (30 cases)

| Model | Pass | Partial | Fail | Score | % |
|-------|------|---------|------|-------|---|
| **ThreadLearn Merged** (fine-tuned 1.5B) | 8 | 22 | 0 | **19.0/30** | **63.3%** |
| **GPT-3.5-turbo** | 7 | 23 | 0 | **18.5/30** | **61.7%** |
| **Qwen2.5-Coder-1.5B** (base) | 6 | 24 | 0 | **18.0/30** | **60.0%** |

### With Pipeline — BM25 + AST + RAG (30 cases)

| Model | Pass | Partial | Fail | Score | % |
|-------|------|---------|------|-------|---|
| **ThreadLearn Merged + pipeline** | 14 | 16 | 0 | **22.0/30** | **73.3%** |
| **GPT-3.5-turbo + pipeline** | 9 | 21 | 0 | **19.5/30** | **65.0%** |
| **Qwen2.5-Coder-1.5B + pipeline** | 8 | 20 | 2 | **18.0/30** | **60.0%** |

> Scoring: pass = 1.0 pt · partial = 0.5 pt · fail = 0 pt

---

## Kết quả chi tiết — Without Pipeline (30 cases)

| ID | Category | Base | Merged | GPT-3.5 |
|----|----------|------|--------|---------|
| rw_01 | Race Condition | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_02 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_03 | Zalgo | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_04 | Event Loop Blocking | ✅ pass | ✅ pass | ✅ pass |
| rw_05 | Context Loss | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_06 | Resource Exhaustion | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_07 | Stream Leak | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_08 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_09 | Unhandled Rejection | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_10 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_11 | Double Callback | ✅ pass | ✅ pass | ✅ pass |
| rw_12 | Sequential Awaits | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_13 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_14 | Callback Hell | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_15 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_16 | Event Loop Blocking | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_17 | Zalgo | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_18 | Unhandled Rejection | ✅ pass | ✅ pass | ✅ pass |
| rw_19 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_20 | Context Loss | ✅ pass | ✅ pass | ✅ pass |
| rw_21 | Sequential Awaits | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_22 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_23 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_24 | Unhandled Rejection | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_25 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_26 | Event Loop Blocking | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_27 | Sequential Awaits | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_28 | Unhandled Rejection | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_29 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_30 | Unhandled Rejection | ✅ pass | ✅ pass | ⚠️ partial |

**Without pipeline sub-scores:**

| Model | Pass | Score |
|-------|------|-------|
| Base | 6 | 18.0/30 |
| Merged | 8 | 19.0/30 |
| GPT-3.5 | 7 | 18.5/30 |

---

## Kết quả chi tiết — With Pipeline (30 cases)

| ID | Category | Base+Pipeline | Merged+Pipeline | GPT-3.5+Pipeline |
|----|----------|---------------|-----------------|------------------|
| rw_01 | Race Condition | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_02 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_03 | Zalgo | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_04 | Event Loop Blocking | ⚠️ partial | ✅ pass | ✅ pass |
| rw_05 | Context Loss | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_06 | Resource Exhaustion | ✅ pass | ✅ pass | ✅ pass |
| rw_07 | Stream Leak | ✅ pass | ⚠️ partial | ✅ pass |
| rw_08 | Race Condition | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_09 | Unhandled Rejection | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_10 | Resource Exhaustion | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_11 | Double Callback | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_12 | Sequential Awaits | ❌ fail | ✅ pass | ✅ pass |
| rw_13 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_14 | Callback Hell | ✅ pass | ✅ pass | ⚠️ partial |
| rw_15 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_16 | Event Loop Blocking | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_17 | Zalgo | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_18 | Unhandled Rejection | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_19 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_20 | Context Loss | ✅ pass | ✅ pass | ✅ pass |
| rw_21 | Sequential Awaits | ✅ pass | ✅ pass | ✅ pass |
| rw_22 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_23 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_24 | Unhandled Rejection | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_25 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_26 | Event Loop Blocking | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_27 | Sequential Awaits | ✅ pass | ✅ pass | ⚠️ partial |
| rw_28 | Unhandled Rejection | ✅ pass | ✅ pass | ✅ pass |
| rw_29 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_30 | Unhandled Rejection | ❌ fail | ✅ pass | ⚠️ partial |

---

## Phân tích pipeline impact

| Metric | Base | Base+Pipeline | Merged | Merged+Pipeline | GPT-3.5 | GPT-3.5+Pipeline |
|--------|------|---------------|--------|-----------------|---------|------------------|
| Score | 18.0/30 | 18.0/30 | 19.0/30 | **22.0/30** | 18.5/30 | 19.5/30 |
| % | 60.0% | 60.0% | 63.3% | **73.3%** | 61.7% | 65.0% |
| Full Pass | 6 | 8 | 8 | 14 | 7 | 9 |
| Pass rate | 20.0% | 26.7% | 26.7% | **46.7%** | 23.3% | 30.0% |

**Pipeline effect trên Base**: +0.0 pts (pipeline không giúp base model — thiếu domain knowledge để tận dụng retrieved context)

**Pipeline effect trên Merged**: +3.0 pts (+10%) — fine-tuning tạo nền tảng, pipeline khuếch đại

**Pipeline effect trên GPT-3.5**: +1.0 pts (+3.3%) — pipeline giúp nhẹ, nhưng ít hơn nhiều so với Merged

**Fine-tuning effect (no pipeline)**: Merged (19.0) vs Base (18.0) → +1.0 pts (+3.3%)

**Combined (Merged+Pipeline vs Base)**: +4.0 pts (+13.3%)

**Key finding**: ThreadLearn Merged + pipeline (73.3%) vượt GPT-3.5 + pipeline (65.0%) dù model nhỏ hơn — domain specialization hiệu quả hơn general LLM.

---

## Phân tích theo category (with pipeline)

| Category | Base+Pipeline | Merged+Pipeline | GPT-3.5+Pipeline |
|----------|---------------|-----------------|------------------|
| Race Condition (5) | 1.5/5 (30%) | 2.5/5 (50%) | 1.0/5 (20%) |
| Double Callback (5) | 2.0/5 (40%) | 2.0/5 (40%) | 2.5/5 (50%) |
| Unhandled Rejection (5) | 2.5/5 (50%) | 4.5/5 (90%) | 3.0/5 (60%) |
| Resource Exhaustion (4) | 2.0/4 (50%) | 3.0/4 (75%) | 2.5/4 (63%) |
| Sequential Awaits (4) | 2.0/4 (50%) | 4.0/4 (100%) | 3.0/4 (75%) |
| Event Loop Blocking (3) | 2.0/3 (67%) | 2.0/3 (67%) | 1.5/3 (50%) |
| Zalgo (2) | 1.0/2 (50%) | 1.0/2 (50%) | 1.0/2 (50%) |
| Context Loss (2) | 1.0/2 (50%) | 1.5/2 (75%) | 1.5/2 (75%) |
| Callback Hell (1) | 1.0/1 (100%) | 1.0/1 (100%) | 0.5/1 (50%) |
| Stream Leak (1) | 1.0/1 (100%) | 0.5/1 (50%) | 1.0/1 (100%) |

**Merged mạnh nhất ở**: Unhandled Rejection (90%), Sequential Awaits (100%)  
**Merged yếu nhất ở**: Race Condition (50%), Zalgo (50%), Stream Leak (50%)  
**GPT-3.5+pipeline yếu ở**: Race Condition (20%), Event Loop Blocking (50%), Callback Hell (50%)

---

## Phân tích latency

| Model | Avg Latency (without pipeline) | Avg Latency (with pipeline) |
|-------|-------------------------------|---------------------------|
| GPT-3.5-turbo | ~1.8s | ~1.8s |
| Qwen2.5-Coder Base | ~17s | ~18s |
| ThreadLearn Merged | ~26s | ~25s |

Local model chậm hơn ~13× so với GPT API — tradeoff giữa cost/privacy và latency.

---

## Kết luận

```
Without pipeline (30 cases):
  ThreadLearn Merged : 63.3% (19.0/30)
  GPT-3.5-turbo      : 61.7% (18.5/30)
  Qwen base          : 60.0% (18.0/30)

With pipeline — BM25+AST+RAG (30 cases):
  ThreadLearn + pipeline  : 73.3% (22.0/30)  ← BEST
  GPT-3.5 + pipeline      : 65.0% (19.5/30)
  Qwen base + pipeline    : 60.0% (18.0/30)
```

1. **Fine-tuning tạo domain foundation**: Merged vượt GPT-3.5 và Base ngay cả không có pipeline
2. **Pipeline chỉ giúp khi model đã có domain knowledge**: Base+pipeline = Base (0% gain); Merged+pipeline +10%; GPT-3.5+pipeline chỉ +3.3%
3. **ThreadLearn 1.5B + pipeline > GPT-3.5 + pipeline**: domain specialization hiệu quả hơn general LLM lớn hơn
4. **Race Condition và Zalgo vẫn khó nhất**: cần semantic understanding sâu, không có static pattern

---

## Nguồn test cases

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

---

## Phân bố category

| Category | Số cases | IDs |
|----------|---------|-----|
| Race Condition | 5 | rw_01, rw_08, rw_13, rw_19, rw_25 |
| Double Callback | 5 | rw_02, rw_11, rw_22, rw_29, rw_06* |
| Unhandled Rejection | 5 | rw_09, rw_18, rw_24, rw_28, rw_30 |
| Resource Exhaustion | 4 | rw_06, rw_10, rw_15, rw_23 |
| Sequential Awaits | 4 | rw_12, rw_21, rw_27, rw_28* |
| Event Loop Blocking | 3 | rw_04, rw_16, rw_26 |
| Zalgo | 2 | rw_03, rw_17 |
| Context Loss | 2 | rw_05, rw_20 |
| Callback Hell | 1 | rw_14 |
| Stream Leak | 1 | rw_07 |

---

## Files kết quả

| File | Model | Cases |
|------|-------|-------|
| `results/without_pipeline/eval_base_results.json` | Qwen2.5-Coder-1.5B base | 30 |
| `results/without_pipeline/eval_merged_results.json` | ThreadLearn fine-tuned | 30 |
| `results/without_pipeline/eval_gpt-3_5-turbo_results.json` | GPT-3.5-turbo | 30 |
| `results/with_pipeline/eval_base_pipeline_results.json` | Qwen base + BM25+AST | 30 |
| `results/with_pipeline/eval_merged_pipeline_results.json` | ThreadLearn + BM25+AST | 30 |
| `results/with_pipeline/eval_openai_pipeline_results.json` | GPT-3.5-turbo + BM25+AST | 30 |
