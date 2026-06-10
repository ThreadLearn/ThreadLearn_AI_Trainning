# ThreadLearn: Research Paper Outline (English)

**One-sentence contribution:**
> ThreadLearn combines rule-based static race detection with a Hindsight CoT fine-tuned Qwen2.5-Coder-1.5B model to simultaneously detect and fix concurrency bugs in JavaScript and Python, improving detection F1 by X% and fix acceptance rate by Y% over rule-only and LLM-only baselines.

**Target venue:** ASPLOS 2027 or ICLR 2026 — 11–12 pages

---

## Abstract (150–250 words, 5 sentences)

| Sentence | Content |
|----------|---------|
| S1 | Concurrency bugs in async and multi-threaded code cause severe production failures, yet static detectors suffer high false-positive rates and LLMs lack reliable reasoning about thread interactions. |
| S2 | Rule-based detectors (NodeCB) miss complex patterns; LLM-only approaches (PCWMs) achieve only 75% accuracy on race detection without explicit structural analysis of the code. |
| S3 | ThreadLearn combines a 10-pattern static race detector with a Qwen2.5-Coder-1.5B model fine-tuned via QLoRA on Hindsight Chain-of-Thought traces grounded in static analysis outputs. |
| S4 | On [benchmark], ThreadLearn detects races with F1=X% (+Y% over NodeCB baseline) and produces accepted fixes in Z% of cases (+W% over PCWM baseline). |
| S5 | ThreadLearn is open-source at [repo]; the fine-tuning dataset and evaluation harness are publicly available. |

---

## S1. Introduction (1.5–2 pages)

### §1.1 Problem Statement (0.5 page)

| Point | Content |
|-------|---------|
| Context | Async JS and multi-threaded Python are ubiquitous in web backends |
| NodeCB evidence | 57 real-world bugs → 65% atomicity violation, 30% order violation |
| Impact | 93% of bugs cause severe failures: crashes, wrong DB state, hangs |
| Gap | Existing tools: rule-based (high FP) or LLM (unreliable) |

### §1.2 Gap Analysis (0.5 page)

| # | Gap |
|---|-----|
| G1 | Rule-based detectors cannot fix bugs, only detect them |
| G2 | LLM-only (PCWMs) achieves 75.2% but needs 27K training samples and does not exploit static structure |
| G3 | No system combines static analysis as grounding signal for LLM reasoning |
| G4 | No end-to-end pipeline from detection → explanation → fix for both JS and Python |

### §1.3 Key Insight (1 paragraph)

> *ThreadLearn is better for concurrency bug remediation in production JS/Python codebases by using static detector outputs as grounding signals for Hindsight CoT fine-tuning.*

### §1.4 Contributions (0.5 page)

| # | Contribution | Section |
|---|-------------|---------|
| 1 | **`race_detector`**: 10-pattern static analyzer for JS + Python, integrated with AST preprocessor | §3.2 |
| 2 | **Hindsight CoT dataset**: synthetic dataset grounded on static detector outputs, fine-tunes Qwen2.5-Coder-1.5B with QLoRA | §3.3 |
| 3 | **ThreadLearn pipeline**: detect → format → RAG-augmented fix via fine-tuned LLM | §3.4 |
| 4 | **Evaluation**: comparison against NodeCB and PCWM baselines across 3 metrics | §5 |

**Figure 1** (page 1): System overview diagram — code input → AST preprocessor → race detector → report formatter → RAG pipeline → fine-tuned LLM → fix output. Highlights 2 baselines for comparison.

---

## S2. Background & Motivation (1–1.5 pages)

### §2.1 Concurrency Bug Taxonomy (0.5 page)

| Bug Type | Rate (NodeCB) | Example |
|----------|--------------|---------|
| Atomicity violation | 65% | Two interleaved DB calls, lost update |
| Order violation | 30% | Upload before create completes |
| Starvation | 5% | setImmediate starved by I/O queue |
| `var i` in loop + setTimeout | JS pattern | Closure captures wrong value |
| Global var without Lock in thread | Python pattern | Race on shared variable |

### §2.2 Limitations of Prior Approaches (0.5 page)

| Approach | Limitation |
|----------|-----------|
| NodeCB study | Regex-based detection → high FP, no fix |
| PCWMs | 75.2% accuracy but does not use static structure, requires large model (7B–32B) |
| **Observation O1** | Static detector outputs (line range, pattern ID) provide causal grounding missing from LLM reasoning |
| **Observation O2** | Small model (1.5B) fine-tuned with grounded CoT outperforms large model with generic CoT |

### §2.3 AST Preprocessing Foundation (0.5 page)

| Function | Purpose | Notes |
|----------|---------|-------|
| `stripComments` | Remove comments and docstrings | Python: `ast.unparse` (precise); JS: regex fallback |
| `normalizeWhitespace` | Normalize whitespace | Python: `ast.unparse`; JS: regex |
| `extractFunctions` | Extract function/class list | JS: arrow functions not caught — known limitation |
| `extract_keywords` | Extract top-20 identifier tokens | Used for RAG retrieval |

---

## S3. Design (3–4 pages)

**Figure 2**: Component architecture — 5 modules with data flow arrows

### §3.1 System Architecture Overview (0.5 page)

| Component | Role |
|-----------|------|
| `ast_preprocessor` | Clean and normalize input code |
| `race_detector` | Detect 10 race condition patterns |
| `report_formatter` | Map pattern_id → severity + fix template |
| `rag_pipeline` | Retrieve similar examples, augment LLM prompt |
| Fine-tuned LLM | Generate fix with reasoning |
| FastAPI server | Expose `/analyze` endpoint |

### §3.2 Static Race Detector (1 page)

| Pattern Group | Pattern IDs | Language |
|--------------|------------|---------|
| Closure/async | `closure_loop_var`, `shared_var_settimeout`, `promise_no_await` | JS |
| Shared state | `concurrent_write_array`, `counter_no_atomic` | JS |
| Thread safety | `global_var_thread`, `shared_list_no_lock`, `thread_read_write_race` | Python |
| Lifecycle | `missing_join`, `singleton_lazy_init` | Python |

| Feature | Description |
|---------|-------------|
| FP suppression | Lock detected → skip shared_list/thread_read_write/singleton flags |
| TypeScript | Treated as JavaScript |
| Output schema | `{pattern_id, line_range, description}` |
| Rejected alternative | AST-based JS detection (rejected — requires Node.js runtime) |

### §3.3 Hindsight CoT Fine-Tuning (1 page)

| Component | Detail |
|-----------|--------|
| Inspiration | PCWMs: teacher model writes reasoning trace with known outcome |
| Training tuple | `(code, static_detector_output, CoT_trace, fix)` |
| Base model | Qwen2.5-Coder-1.5B |
| Method | QLoRA: r=16, alpha=32, 4-bit NF4 quantization |
| Framework | SFTTrainer (trl≥1.5.0) — no manual `get_peft_model()` call |
| Rejected alternatives | Full fine-tune (compute cost); RAG-only (no reasoning) |

### §3.4 RAG-Augmented Fix Pipeline (0.5 page)

| Step | Description |
|------|-------------|
| 1. Embed | Encode input code as vector |
| 2. Retrieve | Find similar fixed examples from RAG store |
| 3. Format | `report_formatter` maps pattern_id → severity + fix template |
| 4. Generate | Fine-tuned LLM + RAG context → final fix |

### §3.5 Rejected Design Alternatives (0.5 page)

| Alternative | Reason Rejected |
|------------|----------------|
| LLM-only detection | High FP, no line-level attribution |
| Static-only | Detects but cannot fix |
| Large model (7B+) | Impractical for local deployment |

---

## S4. Implementation (0.5–1 page)

| Item | Detail |
|------|--------|
| Language & Framework | Python 3.10+, FastAPI |
| Total LOC | ~1,200 LOC |
| `race_detector.py` | 320 LOC, 10 detectors, O(n) scan |
| Model adapter | LoRA SafeTensors at `./threadlearn-qwen2.5-coder-1.5b/final_adapter` |
| Infrastructure | Docker: Redis cache (localhost:6379), Atlas MongoDB |
| Concurrency control | Semaphore in server |
| Key engineering decision | Graceful fallback if `ast_preprocessor` import fails (CI isolation) |

---

## S5. Evaluation (3–4 pages)

### §5.1 Experimental Setup (0.5 page)

| Item | Detail |
|------|--------|
| Baseline 1 | NodeCB-style rule-only |
| Baseline 2 | PCWM-style LLM-only (Qwen2.5-Coder-1.5B, no fine-tune) |
| Our system | ThreadLearn (static + fine-tuned LLM) |
| Datasets | 20 synthetic test cases + [real-world dataset TBD] |
| Metrics | Detection F1, False Positive Rate, Fix Acceptance Rate, Latency (ms/request) |

**Table 1**: Detection results — Method × (Precision / Recall / F1 / FPR)

### §5.2 End-to-End Detection Comparison (1 page)

| Comparison | Hypothesis |
|-----------|-----------|
| ThreadLearn vs rule-only | F1 improvement on complex patterns (order violation, API misuse) |
| ThreadLearn vs LLM-only | F1 improvement with grounded CoT vs generic reasoning |

**Figure 3**: F1 bar chart — 3 methods × JS/Python split

### §5.3 Fix Quality Evaluation (1 page)

| Metric | Measurement Method |
|--------|-------------------|
| Fix Acceptance Rate | Human evaluation or compile + test pass |
| Case study 1 | `var i` closure → fixed to `let i` |
| Case study 2 | Global var in thread → add Lock |
| Comparison | PCWM original: +2.7%–11.1% with world model feedback |

**Figure 4**: Fix acceptance rate — ThreadLearn vs LLM-only vs rule-only (no fix)

### §5.4 Ablation Study (1 page)

| Component Removed | Expected Impact |
|------------------|----------------|
| Static grounding | F1 drops X% |
| RAG retrieval | Fix quality drops Y% |
| Hindsight CoT | Accuracy drops Z% (validates PCWMs finding) |
| QLoRA r=8 vs r=16 | Accuracy vs memory tradeoff |

**Table 2**: Ablation — Component × Metric

### §5.5 Scalability & Latency (0.5 page)

| Metric | Source |
|--------|--------|
| Requests/second | Locust load test results |
| P95 latency | Locust load test results |
| Semaphore impact | Effect on throughput |

---

## S6. Related Work (1 page)

| Group | Representative Works | How ThreadLearn Differs |
|-------|---------------------|------------------------|
| Static race detectors | ThreadSanitizer, Helgrind, ESLint async rules | Detect without fixing, no LLM reasoning |
| Empirical bug studies | NodeCB (Wang et al. 2017), Android concurrency bugs | Taxonomy source, no automated fix |
| LLM for code analysis | PCWMs (Singh et al. 2026), CodeBERT, CodeT5 | LLM-only, does not exploit static structure |
| Fine-tuning for code | QLoRA, SFT on code, PEFT | Training methodology, not targeting race detection |

**Table 3** (optional): Comparison matrix — Method × (Detect / Fix / JS / Python / Fine-tuned)

---

## S7. Conclusion (0.5 page)

| Sentence | Content |
|----------|---------|
| S1 | Concurrency bugs remain a leading cause of production failures in async and multi-threaded applications, yet no existing tool both detects and fixes them reliably. |
| S2 | ThreadLearn combines a 10-pattern static race detector with a Hindsight CoT fine-tuned Qwen2.5-Coder-1.5B model to provide an end-to-end detection and fix generation pipeline for JavaScript and Python. |
| S3 | ThreadLearn achieves F1=X% on race detection (+Y% over NodeCB) and fix acceptance rate Z% (+W% over PCWMs baseline), demonstrating that static grounding significantly improves LLM concurrency reasoning. |

**Future work:** Expand to TypeScript AST (replace regex fallback), add MPI/CUDA patterns (PCWMs direction), cross-file multi-language analysis.

---

## Figures & Tables Summary

| # | Type | Section | Content |
|---|------|---------|---------|
| Figure 1 | System diagram | Introduction | End-to-end pipeline overview |
| Figure 2 | Architecture | Design | 5-component data flow |
| Figure 3 | Bar chart | Eval §5.2 | F1 — 3 methods × JS/Python split |
| Figure 4 | Bar chart | Eval §5.3 | Fix acceptance rate |
| Table 1 | Results | Eval §5.2 | Precision / Recall / F1 / FPR |
| Table 2 | Ablation | Eval §5.4 | Per-component contribution |
| Table 3 | Comparison | Related Work | Method × feature matrix |

---

## Experimental Data Status

| Item | Status |
|------|--------|
| Fine-tuned model | Not yet run (AI1-07 blocked — GPU needed) → F1 TBD |
| Real-world benchmark dataset | Not yet selected |
| Load test results | AI2-10 incomplete |
| 20 synthetic test cases | Complete ✅ (`test_race_detector.py`) |
