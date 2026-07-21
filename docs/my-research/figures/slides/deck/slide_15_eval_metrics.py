#!/usr/bin/env python3
"""Slide 15: Evaluation metrics — PASS/PARTIAL/FAIL scoring scheme."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Methodology", "How We Score a Fix")

fig.text(0.5, 0.76, "6 configurations evaluated: {base, fine-tuned, GPT-3.5-turbo} × {no-pipeline, +pipeline}",
          fontsize=13, color="#444", ha="center", style="italic")

scores = [
    ("PASS", "1.0", "Output contains the expected fix\npattern AND is syntactically\nvalid code.", GPT),
    ("PARTIAL", "0.5", "Syntactically valid code generated,\nbut without the expected\nfix pattern.", FT),
    ("FAIL", "0.0", "No code generated.", OURS),
]

card_w, card_h = 0.27, 0.42
xs = [0.06, 0.365, 0.67]
y0 = 0.20

for (head, val, body, color), x in zip(scores, xs):
    ax.add_patch(plt.Rectangle((x, y0), card_w, card_h, facecolor=CARD_BG,
                                edgecolor=color, linewidth=2.5, transform=ax.transAxes, zorder=2))
    fig.text(x + card_w/2, y0 + card_h - 0.06, head, fontsize=17, fontweight="bold",
              color=color, ha="center", va="center")
    fig.text(x + card_w/2, y0 + card_h - 0.15, val, fontsize=30, fontweight="bold",
              color=INK, ha="center", va="center")
    fig.text(x + card_w/2, y0 + card_h - 0.25, body, fontsize=11.5, color="#444",
              ha="center", va="top", linespacing=1.5)

fig.text(0.5, 0.10, "Score = PASS-count + 0.5 × PARTIAL-count  (out of 30 cases)",
          fontsize=13.5, fontweight="bold", color=INK, ha="center", family="monospace")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_15_eval_metrics.png"))
print("Saved: slide_15_eval_metrics.png")
