#!/usr/bin/env python3
"""Slide 5: Main results — horizontal bar."""
import matplotlib.pyplot as plt
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
title_block(fig, "Results", "Main Results — 30-Case Benchmark")

ax = fig.add_axes([0.30, 0.14, 0.65, 0.66])

configs = [
    "ThreadLearn + pipeline",
    "GPT-3.5-turbo + pipeline",
    "Base + pipeline",
    "Fine-tuned only (no pipe)",
    "GPT-3.5-turbo (no pipe)",
    "Base (no pipe)",
][::-1]
scores = [73.3, 65.0, 60.0, 63.3, 61.7, 60.0][::-1]
colors = [OURS, GPT, BASELINE, FT, GPT, BASELINE][::-1]

y = np.arange(len(configs))
bars = ax.barh(y, scores, color=colors, edgecolor="white", height=0.62, zorder=3)

for bar, s in zip(bars, scores):
    ax.text(bar.get_width() + 1.2, bar.get_y() + bar.get_height()/2, f"{s:.1f}%",
            va="center", ha="left", fontsize=14, fontweight="bold", color=INK)

ax.set_yticks(y)
ax.set_yticklabels(configs, fontsize=13)
ax.set_xlabel("Score (%)")
ax.set_xlim(0, 90)
ax.axvline(60.0, color=MUTED, linestyle="--", linewidth=1, alpha=0.6, zorder=0)
ax.grid(axis="x", alpha=0.18)

fig.text(0.5, 0.06, "ThreadLearn scores 73.3% — +13.3 pp over base, +8.3 pp over GPT-3.5-turbo + pipeline",
          fontsize=13, color=OURS, fontweight="bold", ha="center")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_05_main_results.png"))
print("Saved: slide_05_main_results.png")
