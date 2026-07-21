#!/usr/bin/env python3
"""Slide 8: Limitations / Threats to Validity."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Honest Reflection", "Limitations & Threats to Validity")

items = [
    ("Small benchmark", "30 cases — differences of 2-3 cases (~7 pp) are\nnot statistically significant without formal testing\n(e.g., McNemar's test).", BASELINE),
    ("Proxy metric", "PASS/PARTIAL/FAIL rewards identifying the correct\nfix class, not guaranteed behavioral correctness.\nUnit-test validation is future work.", FT),
    ("Higher latency", "~26s/case on T4 vs. ~1.8s for GPT-3.5-turbo API —\npositions ThreadLearn for offline review, not\nreal-time production monitoring.", GPT),
]

y0 = 0.68
for i, (head, body, color) in enumerate(items):
    y = y0 - i * 0.19
    ax.add_patch(plt.Rectangle((0.06, y), 0.03, 0.14, facecolor=color, transform=ax.transAxes))
    fig.text(0.12, y + 0.135, head, fontsize=16, fontweight="bold", color=INK)
    fig.text(0.12, y + 0.095, body, fontsize=12, color="#555", va="top", linespacing=1.5)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_08_limitations.png"))
print("Saved: slide_08_limitations.png")
