#!/usr/bin/env python3
"""Slide 14: Background concepts — event loop, BM25, QLoRA."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Background", "Three Concepts Behind ThreadLearn")

concepts = [
    ("Event Loop", "Node.js interleaves callbacks, I/O,\nand timers on one thread — no\ntrue parallelism, only scheduling\norder controls correctness.",
     "NodeCB empirical study (57 real bugs):",
     [("Atomicity violations", "65%"), ("Order violations", "30%"), ("Starvation", "5%")], BASELINE),
    ("BM25 Retrieval", "Sparse ranking by term frequency\n× inverse document frequency —\nfavors exact keyword overlap\nover semantic similarity.",
     "Formula parameters used:",
     [("k1 (term freq. saturation)", "1.5"), ("b (length normalization)", "0.75"), ("Top-k retrieved", "3 of 2,050")], GPT),
    ("QLoRA Fine-Tuning", "Quantize base weights to 4-bit,\nfreeze them, train only small\nlow-rank adapter matrices\ninjected into attention layers.",
     "LoRA adapter configuration:",
     [("Rank (r)", "16"), ("Alpha (α)", "32"), ("GPU requirement", "Single GPU")], OURS),
]

card_w, card_h = 0.27, 0.60
xs = [0.06, 0.365, 0.67]
y0 = 0.14

for (head, body, sub_label, stats, color), x in zip(concepts, xs):
    ax.add_patch(plt.Rectangle((x, y0), card_w, card_h, facecolor=CARD_BG,
                                edgecolor=color, linewidth=2.5, transform=ax.transAxes, zorder=2))
    ax.add_patch(plt.Rectangle((x, y0 + card_h - 0.08), card_w, 0.08, facecolor=color,
                                transform=ax.transAxes, zorder=3))
    fig.text(x + card_w/2, y0 + card_h - 0.04, head, fontsize=15.5, fontweight="bold",
              color="white", ha="center", va="center")
    fig.text(x + card_w/2, y0 + card_h - 0.14, body, fontsize=11, color="#444",
              ha="center", va="top", linespacing=1.55)
    stat_y0 = y0 + card_h - 0.34
    fig.text(x + card_w/2, stat_y0 + 0.03, sub_label, fontsize=9.5, color=MUTED,
              ha="center", va="top", style="italic")
    for j, (label, val) in enumerate(stats):
        sy = stat_y0 - j * 0.075
        fig.text(x + 0.02, sy, label, fontsize=10, color="#555", ha="left", va="top")
        fig.text(x + card_w - 0.02, sy, val, fontsize=12, fontweight="bold", color=color,
                  ha="right", va="top")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_14_background.png"))
print("Saved: slide_14_background.png")
