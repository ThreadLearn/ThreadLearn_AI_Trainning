#!/usr/bin/env python3
"""Slide 13: Key references grid — foundational papers/tools cited."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Foundations", "Key References")

refs = [
    ("NodeCB", "Wang et al., ASE 2017", "Empirical study: 93% of\nNode.js concurrency bugs\ncause crashes/corruption.", BASELINE),
    ("ThreadSanitizer", "Serebryany & Iskhodzhanov,\nWBIA 2009", "Runtime data-race detection\nvia instrumentation.", BASELINE),
    ("QLoRA", "Dettmers et al.,\nNeurIPS 2023", "4-bit quantized fine-tuning\non a single GPU.", FT),
    ("LoRA", "Hu et al., ICLR 2022", "Low-rank adapters for\nefficient fine-tuning.", FT),
    ("RAG", "Lewis et al.,\nNeurIPS 2020", "Retrieval-augmented\ngeneration for grounding.", GPT),
    ("BM25", "Robertson & Zaragoza,\nFound. Trends IR 2009", "Sparse term-frequency\nretrieval ranking.", GPT),
    ("Chain-of-Thought", "Wei et al.,\nNeurIPS 2022", "Reasoning traces improve\nLLM problem-solving.", OURS),
    ("PCWMs", "Singh et al.,\narXiv 2026", "Reasoning world models\nfor parallel code (7B–32B).", OURS),
]

card_w, card_h = 0.205, 0.32
xs = [0.06 + i * 0.235 for i in range(4)]
ys = [0.55, 0.16]

for i, (name, cite, body, color) in enumerate(refs):
    col = i % 4
    row = i // 4
    x, y = xs[col], ys[row]
    ax.add_patch(plt.Rectangle((x, y), card_w, card_h, facecolor=CARD_BG,
                                edgecolor=color, linewidth=2, transform=ax.transAxes, zorder=2))
    fig.text(x + card_w/2, y + card_h - 0.035, name, fontsize=12.5, fontweight="bold",
              color=color, ha="center", va="top")
    fig.text(x + card_w/2, y + card_h - 0.085, cite, fontsize=9, color=MUTED,
              ha="center", va="top", style="italic", linespacing=1.3)
    fig.text(x + card_w/2, y + card_h - 0.15, body, fontsize=9.5, color="#444",
              ha="center", va="top", linespacing=1.4)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_13_references.png"))
print("Saved: slide_13_references.png")
