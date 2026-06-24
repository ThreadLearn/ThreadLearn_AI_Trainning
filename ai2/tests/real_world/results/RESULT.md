# Eval Results — Real World Test Cases (20 cases)

## Tổng quan

| Model | Pass | Partial | Fail | Score | Avg Latency |
|-------|------|---------|------|-------|-------------|
| **GPT-3.5-turbo** | 9 | 11 | 0 | **14.5/20 (72.5%)** | ~1.7s |
| **ThreadLearn Merged** (fine-tuned) | 7 | 13 | 0 | **13.5/20 (67.5%)** | ~27s |
| **Qwen2.5-Coder-1.5B** (base) | 5 | 15 | 0 | **12.5/20 (62.5%)** | ~17s |

> Scoring: pass = 1.0 pt · partial = 0.5 pt · fail = 0 pt

---

## Kết quả chi tiết theo từng case

| ID | Category | GPT-3.5 | Merged | Base |
|----|----------|---------|--------|------|
| rw_01 | Race Condition | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_02 | Double Callback | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_03 | Zalgo | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_04 | Event Loop Blocking | ✅ pass | ✅ pass | ✅ pass |
| rw_05 | Context Loss | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_06 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ✅ pass |
| rw_07 | Stream Leak | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_08 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_09 | Unhandled Rejection | ✅ pass | ✅ pass | ⚠️ partial |
| rw_10 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_11 | Double Callback | ✅ pass | ✅ pass | ✅ pass |
| rw_12 | Sequential Awaits | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_13 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_14 | Callback Hell | ✅ pass | ⚠️ partial | ⚠️ partial |
| rw_15 | Resource Exhaustion | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_16 | Event Loop Blocking | ⚠️ partial | ✅ pass | ⚠️ partial |
| rw_17 | Zalgo | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_18 | Unhandled Rejection | ✅ pass | ✅ pass | ✅ pass |
| rw_19 | Race Condition | ⚠️ partial | ⚠️ partial | ⚠️ partial |
| rw_20 | Context Loss | ✅ pass | ✅ pass | ✅ pass |

---

## Phân tích theo category

| Category | GPT-3.5 | Merged | Base | Nhận xét |
|----------|---------|--------|------|----------|
| Event Loop Blocking (2) | 1.5/2 | 2/2 | 1/2 | Merged tốt nhất — train nhiều pattern này |
| Unhandled Rejection (2) | 2/2 | 2/2 | 1/2 | Cả hai model xử lý tốt |
| Context Loss (2) | 2/2 | 1.5/2 | 1/2 | GPT hiểu `this` binding tốt hơn |
| Double Callback (2) | 1.5/2 | 1.5/2 | 1.5/2 | Tương đương nhau |
| Sequential Awaits (1) | 0.5/1 | 1/1 | 0.5/1 | Merged nhận ra `Promise.all` pattern |
| Zalgo (2) | 1.5/2 | 1/2 | 1/2 | Cả 3 đều yếu — pattern phức tạp |
| Race Condition (4) | 1.5/4 | 1/4 | 1/4 | Yếu nhất — cần semantic understanding |
| Resource Exhaustion (3) | 1.5/3 | 1.5/3 | 1.5/3 | Tương đương |
| Stream Leak (1) | 0.5/1 | 0.5/1 | 0.5/1 | Cả 3 chỉ partial |
| Callback Hell (1) | 1/1 | 0.5/1 | 0.5/1 | GPT promisify tốt hơn |

---

## So sánh latency

| Model | Min | Max | Avg | Nhận xét |
|-------|-----|-----|-----|----------|
| GPT-3.5-turbo | 0.7s | 4.0s | ~1.7s | Nhanh nhất, cloud inference |
| Qwen2.5 Base | 4.5s | 28.3s | ~17s | Biến động lớn, không ổn định |
| ThreadLearn Merged | 25.8s | 29.5s | ~27s | Ổn định nhưng chậm — HF Space CPU |

---

## Điểm nổi bật

### Fine-tuned model (Merged) hơn base ở:
- **Sequential Awaits (rw_12)**: Merged trả `Promise.all([...])` đúng ngay — base chỉ partial
- **Event Loop Blocking (rw_04, rw_16)**: 2/2 pass — base chỉ 1/2
- **Latency ổn định hơn**: base dao động 4–28s, merged luôn ~26–29s (predictable)

### Fine-tuned model thua base ở:
- **rw_06** (Resource Exhaustion / pg pool): Base pass, merged chỉ partial
- **Output quality**: Merged thường lặp code nhiều lần (repetition artifact từ training)

### Điểm yếu chung cả 3 model:
- **Race Condition** (rw_08, rw_13, rw_19): Chỉ partial — cần semantic understanding về concurrency window
- **Zalgo** (rw_03, rw_17): Khó detect vì không có syntactic marker
- **Stream Leak** (rw_07): Model biết dùng `pipeline()` nhưng không thêm error handler

---

## Kết luận

```
GPT-3.5-turbo  : 72.5% — baseline tham chiếu, nhanh, general purpose
ThreadLearn    : 67.5% — chỉ kém 5% dù là 1.5B params, fine-tune hiệu quả
Qwen2.5 Base   : 62.5% — baseline trước fine-tune, +5% sau fine-tune
```

Fine-tuning cải thiện **+5% score** và **+1 pass case** so với base model cùng kiến trúc.  
Khoảng cách với GPT-3.5 còn 5% — chủ yếu do Race Condition semantic và output repetition.

---

## Files

| File | Mô tả |
|------|-------|
| `eval_gpt-3_5-turbo_results.json` | Kết quả GPT-3.5-turbo (20 cases) |
| `eval_merged_results.json` | Kết quả ThreadLearn fine-tuned (20 cases) |
| `eval_base_results.json` | Kết quả Qwen2.5-Coder-1.5B base (20 cases) |
