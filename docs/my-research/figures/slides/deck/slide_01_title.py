#!/usr/bin/env python3
"""Slide 1: Title slide."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

# accent bar
ax.add_patch(plt.Rectangle((0, 0.94), 1, 0.06, color=OURS, transform=ax.transAxes))

# kicker
fig.text(0.5, 0.72, "ICTA 2026", fontsize=15, fontweight="bold", color=OURS, ha="center")

# title
fig.text(0.5, 0.60, "ThreadLearn", fontsize=52, fontweight="bold", color=INK, ha="center")
fig.text(0.5, 0.49, "A RAG-Augmented Fine-Tuned Language Model for\nJavaScript Concurrency Bug Detection and Fix Suggestion",
         fontsize=17, color="#444", ha="center", linespacing=1.5)

# decorative dots — 4 palette colors
colors = [BASELINE, GPT, FT, OURS]
for i, c in enumerate(colors):
    ax.add_patch(plt.Circle((0.42 + i * 0.055, 0.35), 0.012, color=c, transform=ax.transAxes))

fig.text(0.5, 0.15, "[ Authors — replace on Canva ]", fontsize=13, color=MUTED, ha="center", style="italic")
fig.text(0.5, 0.10, "[ FPT University — replace on Canva ]", fontsize=12, color=MUTED, ha="center")

fig.savefig(os.path.join(OUTPUT_DIR, "slide_01_title.png"))
print("Saved: slide_01_title.png")
