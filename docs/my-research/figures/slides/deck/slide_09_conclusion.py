#!/usr/bin/env python3
"""Slide 9: Conclusion — key numbers + thank you."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

ax.add_patch(plt.Rectangle((0, 0.94), 1, 0.06, color=OURS, transform=ax.transAxes))

fig.text(0.5, 0.83, "Conclusion", fontsize=15, fontweight="bold", color=OURS, ha="center")
fig.text(0.5, 0.74, "Small Model + Structure Beats Scale Alone", fontsize=28, fontweight="bold", color=INK, ha="center")

stats = [
    ("73.3%", "ThreadLearn score\non 30-case benchmark", OURS),
    ("+13.3pp", "gain over base\nmodel", GPT),
    ("1.5B", "parameters — vs. 7B–32B\nfor comparable LLM tools", FT),
    ("3×", "pipeline amplification\nof fine-tuning gain", BASELINE),
]

xs = [0.10 + i * 0.225 for i in range(4)]
for (num, label, color), x in zip(stats, xs):
    fig.text(x + 0.09, 0.50, num, fontsize=34, fontweight="bold", color=color, ha="center")
    fig.text(x + 0.09, 0.40, label, fontsize=11.5, color="#555", ha="center", va="top", linespacing=1.4)

fig.text(0.5, 0.18, "Thank you — Questions?", fontsize=20, fontweight="bold", color=INK, ha="center")
fig.text(0.5, 0.12, "[ Contact / GitHub — replace on Canva ]", fontsize=12, color=MUTED, ha="center", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_09_conclusion.png"))
print("Saved: slide_09_conclusion.png")
