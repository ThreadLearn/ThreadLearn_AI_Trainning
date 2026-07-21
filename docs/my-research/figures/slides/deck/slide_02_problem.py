#!/usr/bin/env python3
"""Slide 2: Problem / Motivation — 4 gap cards."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Motivation", "Four Gaps in Existing Tools")

gaps = [
    ("G1", "Detectors can't fix", "Rule-based tools (ESLint,\nThreadSanitizer) flag bugs but\ngenerate no fix suggestion.",
     "e.g. ESLint reports\n\"no-async-promise-\nexecutor\" — no patch.", BASELINE),
    ("G2", "LLMs need scale", "LLM-only approaches require\n7B–32B parameters for\ncompetitive accuracy.",
     "PCWMs: 7B–32B params,\nnot deployable\non-premise at low cost.", GPT),
    ("G3", "No structured bridge", "No tool feeds detector output\nas structured context to\nguide an LLM.",
     "LLMs prompted with raw\ncode alone must re-derive\nwhat a detector already knows.", FT),
    ("G4", "No end-to-end path", "No tool covers detect → explain\n→ fix-suggestion for JS\nconcurrency bugs.",
     "Prior work stops at detect-\nonly (rules) or fix-only\n(LLM, no grounding).", OURS),
]

card_w, card_h = 0.21, 0.56
xs = [0.06 + i * 0.235 for i in range(4)]
y0 = 0.22

for (tag, head, body, example, color), x in zip(gaps, xs):
    ax.add_patch(plt.Rectangle((x, y0), card_w, card_h, facecolor=CARD_BG,
                                edgecolor=color, linewidth=2.5, transform=ax.transAxes, zorder=2))
    ax.add_patch(plt.Rectangle((x, y0 + card_h - 0.05), card_w, 0.05, facecolor=color,
                                transform=ax.transAxes, zorder=3))
    fig.text(x + card_w/2, y0 + card_h - 0.025, tag, fontsize=15, fontweight="bold",
              color="white", ha="center", va="center")
    fig.text(x + card_w/2, y0 + card_h - 0.10, head, fontsize=13.5, fontweight="bold",
              color=INK, ha="center", va="top")
    fig.text(x + card_w/2, y0 + card_h - 0.18, body, fontsize=10.5, color="#555",
              ha="center", va="top", linespacing=1.4)
    ax.add_patch(plt.Rectangle((x + 0.015, y0 + 0.04), card_w - 0.03, 0.16,
                                facecolor="white", edgecolor=color, linewidth=1.2,
                                alpha=0.9, transform=ax.transAxes, zorder=2))
    fig.text(x + card_w/2, y0 + 0.17, example, fontsize=9, color="#444",
              ha="center", va="top", linespacing=1.4, style="italic")

fig.text(0.5, 0.12, "ThreadLearn addresses all four gaps in a single pipeline", fontsize=14,
          fontweight="bold", color=OURS, ha="center", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_02_problem.png"))
print("Saved: slide_02_problem.png")
