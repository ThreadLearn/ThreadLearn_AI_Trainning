#!/usr/bin/env python3
"""Slide 12: Related work comparison table — ThreadLearn vs existing tools."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Related Work", "How ThreadLearn Compares")

cols = ["Tool", "Detect", "Fix\nSuggestion", "JavaScript", "Fine-\nTuned"]
rows = [
    ("ThreadSanitizer", "✗", "✗", "✗", "✗", BASELINE),
    ("ESLint async",    "✓", "✗", "✓", "✗", BASELINE),
    ("NodeCB (rules)",  "✓", "✗", "✓", "✗", BASELINE),
    ("PCWMs (LLM-only, 7B–32B)", "✓", "✓", "✓", "✓", GPT),
    ("ThreadLearn (ours, 1.5B)", "✓", "✓", "✓", "✓", OURS),
]

x0, y0 = 0.08, 0.72
col_x = [x0, x0+0.40, x0+0.53, x0+0.68, x0+0.81]
row_h = 0.105

# header
for cx, label in zip(col_x, cols):
    fig.text(cx, y0 + 0.04, label, fontsize=12.5, fontweight="bold", color=INK, ha="left", va="bottom", linespacing=1.2)
ax.add_patch(plt.Rectangle((x0-0.01, y0), 0.86, 0.008, facecolor=INK, transform=ax.transAxes))

for i, (name, det, fix, js, ft, color) in enumerate(rows):
    y = y0 - (i+1) * row_h
    is_ours = (i == len(rows)-1)
    if is_ours:
        ax.add_patch(plt.Rectangle((x0-0.02, y-0.015), 0.90, row_h-0.01, facecolor=color, alpha=0.10,
                                    transform=ax.transAxes, zorder=1))
    fig.text(col_x[0], y + row_h/2 - 0.01, name, fontsize=12.5,
              fontweight="bold" if is_ours else "normal",
              color=color if is_ours else "#333", ha="left", va="center")
    for cx, val in zip(col_x[1:], [det, fix, js, ft]):
        c = "#2A9D8F" if val == "✓" else "#B0BEC5"
        fig.text(cx + 0.03, y + row_h/2 - 0.01, val, fontsize=15, fontweight="bold",
                  color=c, ha="center", va="center", family="DejaVu Sans")
    ax.add_patch(plt.Rectangle((x0-0.02, y-0.015), 0.90, 0.001, facecolor="#DDD", transform=ax.transAxes))

fig.text(0.5, 0.10, "ThreadLearn is the only approach combining all four capabilities at 1.5B scale",
          fontsize=13, color=OURS, fontweight="bold", ha="center")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_12_related_work.png"))
print("Saved: slide_12_related_work.png")
