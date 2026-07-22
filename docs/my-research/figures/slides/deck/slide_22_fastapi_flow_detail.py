#!/usr/bin/env python3
"""Slide 22: FastAPI Server request flow — accurate detail, verified against main.py + rag_pipeline.py.
Replaces old Canva slide (wrong order: cache-before-detector, top-3 docs, 1 LLM call/file, P50/P95 mislabeled as steps)."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Architecture — Verified Against main.py / rag_pipeline.py", "FastAPI Server: POST /api/v1/ai/analyze")

steps = [
    ("1", "JWT Verify", "Depends(get_current_user) — HS256, shared secret with Node.js backend", BASELINE),
    ("2", "Redis Cache Check", "SHA256(code+language) key. HIT -> return cached, cached=true. MISS -> continue.", GPT),
    ("3", "Race Detector", "detectRaceConditions() — regex scan, 18 patterns (14 JS + 4 Python), O(n)", FT),
    ("4", "Keyword Extraction", "Semantic pattern match first; fallback to esprima AST; fallback to tokenize()", FT),
    ("5", "BM25 Retrieval", "retriever.search(query, top_k=1) — production uses top_k=1, not top_k=3", GPT),
    ("6", "Prompt Construction", "Context docs + code assembled in training-matched format (rag_pipeline._build_prompt)", FT),
    ("7", "LLM Fix — per issue", "Semaphore(3) limits concurrent calls. One LLM call PER ISSUE (capped at 5), not 1 call/file", OURS),
    ("8", "Persist + Respond", "Save to Redis (TTL 24h) + MongoDB (ai_analysis_history) -> JSON response to frontend", BASELINE),
]

y0 = 0.80
row_h = 0.082
for i, (num, head, detail, color) in enumerate(steps):
    y = y0 - i * row_h
    ax.add_patch(plt.Rectangle((0.06, y - row_h + 0.015), 0.04, row_h - 0.02, facecolor=color, transform=ax.transAxes))
    fig.text(0.08, y - row_h/2 + 0.005, num, fontsize=13, fontweight="bold", color="white", ha="center", va="center")
    fig.text(0.12, y - 0.01, head, fontsize=11.5, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.32, y - 0.01, detail, fontsize=9.5, color="#555", ha="left", va="top", family="monospace")
    if i < len(steps) - 1:
        ax.add_patch(plt.Rectangle((0.06, y - row_h + 0.01), 0.90, 0.001, facecolor="#DDD", transform=ax.transAxes))

fig.text(0.06, 0.085, "Timeout: asyncio.timeout(30s) -> 504 if LLM hangs.  Queue full (>3 concurrent) -> 429 retry_after=10.",
          fontsize=9.5, color=MUTED, ha="left", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_22_fastapi_flow_detail.png"))
print("Saved: slide_22_fastapi_flow_detail.png")
