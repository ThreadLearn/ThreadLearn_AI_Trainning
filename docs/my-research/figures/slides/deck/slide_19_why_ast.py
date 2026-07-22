#!/usr/bin/env python3
"""Slide 19: Why use an AST tree?"""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Design Decision", "Why Use an AST Tree?")

fig.text(0.06, 0.775, "The problem: regex/text tokenizers break apart CamelCase API names,",
          fontsize=13, color="#444", ha="left")
fig.text(0.06, 0.735, "weakening the exact-keyword match that BM25 depends on.",
          fontsize=13, color="#444", ha="left")

# before/after comparison cards
card_w, card_h = 0.40, 0.46
y0 = 0.24

# BEFORE card
xb = 0.06
ax.add_patch(plt.Rectangle((xb, y0), card_w, card_h, facecolor=CARD_BG,
                            edgecolor=BASELINE, linewidth=2.5, transform=ax.transAxes, zorder=2))
ax.add_patch(plt.Rectangle((xb, y0 + card_h - 0.06), card_w, 0.06, facecolor=BASELINE,
                            transform=ax.transAxes, zorder=3))
fig.text(xb + card_w/2, y0 + card_h - 0.035, "BEFORE — regex tokenizer", fontsize=13, fontweight="bold",
          color="white", ha="center", va="center")

before_rows = [
    ("setTimeout(cb, 100)", "set timeout cb"),
    ("fs.appendFile(path, data)", "fs append file path data"),
    ("Promise.all([p1, p2])", "promise all p1 p2"),
]
for i, (code, tok) in enumerate(before_rows):
    y = y0 + card_h - 0.14 - i * 0.115
    fig.text(xb + 0.03, y, code, fontsize=10, color=INK, ha="left", va="top", family="monospace")
    fig.text(xb + 0.03, y - 0.042, f'-> "{tok}"', fontsize=10, color="#c0392b", ha="left", va="top", family="monospace")

# AFTER card
xa = 0.54
ax.add_patch(plt.Rectangle((xa, y0), card_w, card_h, facecolor=CARD_BG,
                            edgecolor=OURS, linewidth=2.5, transform=ax.transAxes, zorder=2))
ax.add_patch(plt.Rectangle((xa, y0 + card_h - 0.06), card_w, 0.06, facecolor=OURS,
                            transform=ax.transAxes, zorder=3))
fig.text(xa + card_w/2, y0 + card_h - 0.035, "AFTER — esprima AST extraction", fontsize=13, fontweight="bold",
          color="white", ha="center", va="center")

after_rows = [
    ("setTimeout(cb, 100)", "setTimeout cb"),
    ("fs.appendFile(path, data)", "fs appendFile path data"),
    ("Promise.all([p1, p2])", "Promise p1 p2"),
]
for i, (code, tok) in enumerate(after_rows):
    y = y0 + card_h - 0.14 - i * 0.115
    fig.text(xa + 0.03, y, code, fontsize=10, color=INK, ha="left", va="top", family="monospace")
    fig.text(xa + 0.03, y - 0.042, f'-> "{tok}"', fontsize=10, fontweight="bold", color=OURS, ha="left", va="top", family="monospace")

fig.text(0.5, 0.155, "esprima distinguishes Identifier tokens (developer-chosen names) from Keyword tokens",
          fontsize=11, color="#444", ha="center", style="italic")
fig.text(0.5, 0.118, "(async, await, for) — a regex tokenizer cannot make this distinction.",
          fontsize=11, color="#444", ha="center", style="italic")
fig.text(0.5, 0.065, "API names stay intact -> higher BM25 score against the correct reference document -> more accurate top-3 retrieval.",
          fontsize=12, fontweight="bold", color=OURS, ha="center")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_19_why_ast.png"))
print("Saved: slide_19_why_ast.png")
