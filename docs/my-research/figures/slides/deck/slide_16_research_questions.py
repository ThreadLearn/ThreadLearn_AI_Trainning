#!/usr/bin/env python3
"""Slide 16: Research questions answered — RQ1/RQ2/RQ3 summary."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Summary", "Research Questions Answered")

rqs = [
    ("RQ1", "Does the detector + fine-tuned small LLM\noutperform a general-purpose LLM?",
     "Yes — ThreadLearn (73.3%) scores higher\nthan GPT-3.5-turbo + pipeline (65.0%)\non this benchmark.", OURS),
    ("RQ2", "Does the pipeline benefit every model\nequally, or does it depend on fine-tuning?",
     "Depends on fine-tuning — +10 pp for\nthe fine-tuned model vs. 0 pp\n(and regression) for the base model.", GPT),
    ("RQ3", "Which bug categories remain hard, and\nwhat does that reveal about training data?",
     "Cross-boundary callback-order bugs\n(Zalgo, Double Callback) — a semantic\nproperty absent from syntactic templates.", FT),
]

y0 = 0.70
row_h = 0.20
for i, (tag, q, a, color) in enumerate(rqs):
    y = y0 - i * row_h
    ax.add_patch(plt.Rectangle((0.06, y), 0.05, row_h - 0.03, facecolor=color, transform=ax.transAxes))
    fig.text(0.085, y + (row_h-0.03)/2, tag, fontsize=16, fontweight="bold",
              color="white", ha="center", va="center")
    fig.text(0.14, y + row_h - 0.055, q, fontsize=12.5, fontweight="bold", color=INK,
              ha="left", va="top", linespacing=1.4)
    fig.text(0.58, y + row_h - 0.055, "→ " + a, fontsize=12, color="#444",
              ha="left", va="top", linespacing=1.4)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_16_research_questions.png"))
print("Saved: slide_16_research_questions.png")
