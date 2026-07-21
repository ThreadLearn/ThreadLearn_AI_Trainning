#!/usr/bin/env python3
"""Slide 3: Pipeline — 5-step flow diagram."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Architecture", "End-to-End Pipeline")

steps = [
    ("1", "Static\nDetection", "race_detector\nO(n) scan",
     "Outputs {pattern_id,\nline_range,\ndescription} per match", BASELINE),
    ("2", "Keyword\nExtraction", "esprima AST\ntop-20 idents",
     "Preserves CamelCase\nAPI names\n(e.g. setTimeout)", FT),
    ("3", "BM25\nRetrieval", "top-3 of 2,050\ndocuments",
     "k1=1.5, b=0.75\nsparse term-\nfrequency ranking", GPT),
    ("4", "Prompt\nConstruction", "detector +\ndocs + code",
     "Assembles structured\ncontext into a\nsingle LLM prompt", FT),
    ("5", "Fix\nGeneration", "fine-tuned LLM\n+ reasoning",
     "Qwen2.5-Coder-1.5B\noutputs code +\nreasoning trace", OURS),
]

n = len(steps)
box_w, box_h = 0.15, 0.26
gap = (1 - 0.10 - n * box_w) / (n - 1)
y = 0.56

for i, (num, head, sub, detail, color) in enumerate(steps):
    x = 0.05 + i * (box_w + gap)
    ax.add_patch(FancyBboxPatch((x, y), box_w, box_h,
                 boxstyle="round,pad=0.008,rounding_size=0.02",
                 facecolor=color, edgecolor="white", linewidth=2,
                 transform=ax.transAxes, zorder=3))
    fig.text(x + box_w/2, y + box_h - 0.05, num, fontsize=18, fontweight="bold",
              color="white", ha="center", va="center", alpha=0.85)
    fig.text(x + box_w/2, y + box_h - 0.12, head, fontsize=12.5, fontweight="bold",
              color="white", ha="center", va="center", linespacing=1.3)
    fig.text(x + box_w/2, y - 0.035, sub, fontsize=9.5, color="#555",
              ha="center", va="top", linespacing=1.3, fontweight="bold")

    # detail card below the sub-label
    detail_y = y - 0.28
    ax.add_patch(plt.Rectangle((x, detail_y), box_w, 0.15, facecolor="#FAFAFA",
                                edgecolor=color, linewidth=1.5, transform=ax.transAxes, zorder=2))
    fig.text(x + box_w/2, detail_y + 0.12, detail, fontsize=8.5, color="#444",
              ha="center", va="top", linespacing=1.35)

    if i < n - 1:
        arrow_x0 = x + box_w
        arrow_x1 = arrow_x0 + gap
        ax.annotate("", xy=(arrow_x1, y + box_h/2), xytext=(arrow_x0, y + box_h/2),
                    xycoords="figure fraction", textcoords="figure fraction",
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, linewidth=2))

fig.text(0.5, 0.10, "buggy code  →  static + retrieval-augmented context  →  fix suggestion",
          fontsize=13, color=INK, ha="center", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_03_pipeline.png"))
print("Saved: slide_03_pipeline.png")
