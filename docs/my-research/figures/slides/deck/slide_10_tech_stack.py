#!/usr/bin/env python3
"""Slide 10: Technology stack — 6 tech cards used in ThreadLearn."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Implementation", "Technology Stack")

tech = [
    ("Qwen2.5-Coder-1.5B", "Base Model", "Open-weight code LLM,\nfine-tuned via QLoRA.", OURS),
    ("QLoRA + LoRA", "Fine-Tuning", "4-bit quantized base +\nLoRA adapters (r=16, α=32).\nSingle-GPU training.", FT),
    ("BM25", "Retrieval", "Sparse retrieval (k1=1.5,\nb=0.75) over 2,050-doc\nknowledge base.", GPT),
    ("Esprima", "AST Parsing", "ECMAScript AST for keyword\nextraction & function-scope\ndetection.", BASELINE),
    ("FastAPI", "Serving", "Async Python microservice.\nJWT auth, Redis cache,\nMongoDB history.", GPT),
    ("Hindsight CoT", "Training Data", "892 reasoning-trace\nexamples, teacher-model\nassisted + human-verified.", OURS),
]

card_w, card_h = 0.28, 0.34
xs = [0.06, 0.36, 0.66]
ys = [0.52, 0.14]

for i, (name, tag, body, color) in enumerate(tech):
    col = i % 3
    row = i // 3
    x, y = xs[col], ys[row]
    ax.add_patch(plt.Rectangle((x, y), card_w, card_h, facecolor=CARD_BG,
                                edgecolor=color, linewidth=2.5, transform=ax.transAxes, zorder=2))
    ax.add_patch(plt.Rectangle((x, y), 0.012, card_h, facecolor=color, transform=ax.transAxes, zorder=3))
    fig.text(x + 0.03, y + card_h - 0.045, tag.upper(), fontsize=10.5, fontweight="bold",
              color=color, ha="left", va="top")
    fig.text(x + 0.03, y + card_h - 0.10, name, fontsize=15, fontweight="bold",
              color=INK, ha="left", va="top")
    fig.text(x + 0.03, y + card_h - 0.16, body, fontsize=10.5, color="#555",
              ha="left", va="top", linespacing=1.5)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_10_tech_stack.png"))
print("Saved: slide_10_tech_stack.png")
