#!/usr/bin/env python3
"""Slide 18: Why BM25 instead of Vector Search?"""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Design Decision", "Why BM25 Instead of Vector Search?")

# Comparison table
headers = ["Criterion", "BM25 (ours)", "Vector Search (FAISS/Chroma)"]
rows = [
    ("Index build speed", "<500 ms for 2,050 docs", "Slow — embeds every doc"),
    ("VRAM required", "0 (RAM only)", "Needs GPU to embed"),
    ("Library footprint", "rank-bm25 (~50 KB)", "sentence-transformers (500+ MB)"),
    ("Offline capability", "Fully offline", "Needs an embedding model"),
    ("Best suited for", "Exact technical keywords", "Semantic / paraphrase similarity"),
]

x0, y0 = 0.06, 0.70
col_x = [x0, x0 + 0.32, x0 + 0.58]
row_h = 0.078

for cx, h in zip(col_x, headers):
    fig.text(cx, y0 + 0.03, h, fontsize=13, fontweight="bold", color=INK, ha="left", va="bottom")
ax.add_patch(plt.Rectangle((x0 - 0.01, y0), 0.90, 0.006, facecolor=INK, transform=ax.transAxes))

for i, (crit, bm25, vec) in enumerate(rows):
    y = y0 - (i + 1) * row_h
    fig.text(col_x[0], y + row_h/2 - 0.008, crit, fontsize=11, color="#333", ha="left", va="center")
    fig.text(col_x[1], y + row_h/2 - 0.008, bm25, fontsize=11, fontweight="bold", color=OURS, ha="left", va="center")
    fig.text(col_x[2], y + row_h/2 - 0.008, vec, fontsize=10.5, color="#777", ha="left", va="center")
    ax.add_patch(plt.Rectangle((x0 - 0.01, y - 0.008), 0.90, 0.001, facecolor="#DDD", transform=ax.transAxes))

# Bottom reasoning card
y_card = 0.10
ax.add_patch(plt.Rectangle((0.06, y_card), 0.88, 0.17, facecolor=CARD_BG,
                            edgecolor=OURS, linewidth=2, transform=ax.transAxes, zorder=2))
fig.text(0.10, y_card + 0.14, "Why this matters for JavaScript code specifically:", fontsize=12.5,
          fontweight="bold", color=OURS, ha="left", va="top")
fig.text(0.10, y_card + 0.10, "Code uses precise technical terms — setTimeout, Promise.all, async/await.\n"
          "A developer searching for a fix knows the exact API name they need: exact keyword\n"
          "match matters more than semantic paraphrase similarity here.",
          fontsize=11, color="#444", ha="left", va="top", linespacing=1.5)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_18_why_bm25.png"))
print("Saved: slide_18_why_bm25.png")
