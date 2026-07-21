#!/usr/bin/env python3
"""Slide 6: Pipeline amplifies fine-tuning — key finding."""
import matplotlib.pyplot as plt
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
title_block(fig, "Key Finding", "Pipeline Amplifies Fine-Tuning, Not the Reverse")

ax = fig.add_axes([0.08, 0.16, 0.55, 0.62])

models = ["Base", "GPT-3.5-turbo", "ThreadLearn\n(fine-tuned)"]
no_pipe = [60.0, 61.7, 63.3]
with_pipe = [60.0, 65.0, 73.3]
gains = [w - n for w, n in zip(with_pipe, no_pipe)]

x = np.arange(len(models))
width = 0.32
b1 = ax.bar(x - width/2, no_pipe, width, color=BASELINE, label="No pipeline", edgecolor="white", zorder=3)
b2 = ax.bar(x + width/2, with_pipe, width, color=OURS, label="+ Pipeline", edgecolor="white", zorder=3)

for bar, s in zip(b1, no_pipe):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f"{s:.1f}%", ha="center", fontsize=11, color="#555")
for bar, s in zip(b2, with_pipe):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f"{s:.1f}%", ha="center", fontsize=11, fontweight="bold", color=INK)
for i, g in enumerate(gains):
    label = f"+{g:.1f} pp" if g > 0 else "±0 pp"
    color = "#c0392b" if g > 0 else MUTED
    ax.annotate(label, xy=(x[i]+width/2, with_pipe[i]+7), ha="center", fontsize=12, fontweight="bold", color=color)

ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=12)
ax.set_ylabel("Score (%)")
ax.set_ylim(0, 90)
ax.legend(loc="upper left", fontsize=11, frameon=True)

# Right side: takeaway cards
cards = [
    ("Prerequisite", "Base model gains nothing\nfrom the pipeline (+0 pp)\nand adds 2 FAILs.", BASELINE),
    ("Amplifier", "Pipeline adds +3.0 pts on\ntop of fine-tuning's +1.0 pt\n— a 3× multiplier.", OURS),
]
y0 = 0.50
for i, (head, body, color) in enumerate(cards):
    y = y0 - i * 0.28
    ax.figure.add_artist(plt.Rectangle((0.68, y), 0.26, 0.20, transform=fig.transFigure,
                          facecolor="#FAFAFA", edgecolor=color, linewidth=2.5))
    fig.text(0.70, y + 0.16, head, fontsize=14, fontweight="bold", color=color)
    fig.text(0.70, y + 0.11, body, fontsize=11, color="#444", va="top", linespacing=1.4)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_06_pipeline_gain.png"))
print("Saved: slide_06_pipeline_gain.png")
