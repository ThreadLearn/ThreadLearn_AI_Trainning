#!/usr/bin/env python3
"""Slide: Mechanism detail for Case A (regex match) and Case B (AST parse) —
how each tier actually produces its query, with a visual diagram of the
mechanism instead of dense text. Same visual style as
gen_slide_keyword_extraction.py / gen_slide_bm25.py.
Real code from server/server/rag_pipeline.py + training/modules/ast_preprocessor.py."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": None,
})

INK = "#1a1a2e"
MUTED = "#5b6472"
TEAL = "#2A9D8F"; TEAL_BG = "#E4F3F1"
ORANGE = "#E76F51"; ORANGE_BG = "#FCE9E4"

fig = plt.figure(figsize=(19.2, 10.8))  # 16:9
fig.patch.set_facecolor("white")

# ── Title ──────────────────────────────────────────────────────
fig.text(0.5, 0.99, "How Case A & Case B Actually Produce Their Query",
          ha="center", va="top", fontsize=36, fontweight="bold", color=INK)
fig.text(0.5, 0.945, "Mechanism behind the two most common tiers — pattern lookup vs. real syntax parsing",
          ha="center", va="top", fontsize=17, color=MUTED)

card_top, card_bottom = 0.90, 0.015
card_gap = 0.03
card_w = (0.97 - 0.03 - card_gap) / 2
card_h = card_top - card_bottom


def draw_box(ax, cx, cy, w, h, face, edge, text, fs, lw=1.6, textcolor=None):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.03,rounding_size=0.1",
                                  facecolor=face, edgecolor=edge, linewidth=lw))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=textcolor or INK,
            fontfamily="monospace", linespacing=1.35, fontweight="bold")


def draw_down_arrow(ax, x, y_top, y_bot, color):
    ax.annotate("", xy=(x, y_bot), xytext=(x, y_top),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=3.0))


# ============================= CASE A =============================
ax = fig.add_axes([0.03, card_bottom, card_w, card_h])
ax.set_xlim(0, 10); ax.set_ylim(0, 24); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 23.7, boxstyle="round,pad=0.05,rounding_size=0.2",
                              facecolor=TEAL_BG, edgecolor=TEAL, linewidth=2.6))

ax.add_patch(plt.Circle((1.75, 22.7), 1.25, facecolor=TEAL, edgecolor="white", linewidth=2.6, zorder=3))
ax.text(1.75, 22.7, "A", ha="center", va="center", fontsize=30, fontweight="bold", color="white", zorder=4)
ax.text(3.5, 23.15, "CASE A MECHANISM", ha="left", va="center", fontsize=19, fontweight="bold", color=TEAL)
ax.text(3.5, 22.1, "regex lookup table — no code content read", ha="left", va="center", fontsize=14.5, color=MUTED, style="italic")

# ── Visual diagram: code -> regex scan -> lookup table -> fixed output ──
draw_box(ax, 5.0, 19.9, 8.6, 2.0, "white", "#D8DCE2",
         "await profile...\nawait orders...", 13.5, textcolor=INK)
ax.text(0.5, 18.55, "input code", ha="left", va="center", fontsize=11, color=MUTED, style="italic")

draw_down_arrow(ax, 5.0, 18.75, 17.6, TEAL)
ax.text(6.3, 18.15, "regex.search()\n(shape only)", ha="left", va="center", fontsize=11, color=TEAL, fontweight="bold")

draw_box(ax, 5.0, 16.3, 8.6, 2.0, "white", TEAL,
         "MATCH: rule #4 of 13\n\"2x await in a row\"", 13.5, lw=2.2, textcolor=TEAL)

draw_down_arrow(ax, 5.0, 15.15, 14.05, TEAL)
ax.text(6.3, 14.6, "lookup fixed\nkeyword string", ha="left", va="center", fontsize=11, color=TEAL, fontweight="bold")

draw_box(ax, 5.0, 12.75, 8.6, 2.1, TEAL, TEAL,
         '"sequential await\nPromise.all parallel\nconcurrent"', 13.0, lw=2.4, textcolor="white")
ax.text(0.5, 11.25, "query sent to BM25 — code content never touched again", ha="left", va="center",
        fontsize=10.8, color=MUTED, style="italic")

# 3 mechanism steps (compact, below diagram)
steps = [
    ("1", "SCAN", "Pattern checks code SHAPE only —\n2-3 \"await\" lines in a row."),
    ("2", "MATCH", "First of 13 rules to match wins.\nRest of the list is never checked."),
    ("3", "RETURN LABEL", "Returns the paired keyword string —\nnot anything from the matched text."),
]
y = 9.6
for num, head, body in steps:
    ax.add_patch(plt.Circle((1.4, y), 0.62, facecolor=TEAL, edgecolor="white", linewidth=2.2, zorder=3))
    ax.text(1.4, y, num, ha="center", va="center", fontsize=15, fontweight="bold", color="white", zorder=4)
    ax.text(2.6, y + 0.4, head, ha="left", va="center", fontsize=15, fontweight="bold", color=TEAL)
    ax.text(2.6, y - 0.55, body, ha="left", va="top", fontsize=13, color=INK, linespacing=1.4)
    y -= 2.9

# Key insight box
ax.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                              facecolor=TEAL, edgecolor=TEAL, linewidth=1.5, alpha=0.15))
ax.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                              facecolor="none", edgecolor=TEAL, linewidth=2.2))
ax.text(5.0, 1.18, "KEY: detects bug SHAPE, never reads variable names.\nSame output for every match of this rule.",
        ha="center", va="center", fontsize=13, color=TEAL, fontweight="bold", linespacing=1.5)

# ============================= CASE B =============================
ax2 = fig.add_axes([0.03 + card_w + card_gap, card_bottom, card_w, card_h])
ax2.set_xlim(0, 10); ax2.set_ylim(0, 24); ax2.axis("off")
ax2.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 23.7, boxstyle="round,pad=0.05,rounding_size=0.2",
                               facecolor=ORANGE_BG, edgecolor=ORANGE, linewidth=2.6))

ax2.add_patch(plt.Circle((1.75, 22.7), 1.25, facecolor=ORANGE, edgecolor="white", linewidth=2.6, zorder=3))
ax2.text(1.75, 22.7, "B", ha="center", va="center", fontsize=30, fontweight="bold", color="white", zorder=4)
ax2.text(3.5, 23.15, "CASE B MECHANISM", ha="left", va="center", fontsize=19, fontweight="bold", color=ORANGE)
ax2.text(3.5, 22.1, "real AST token walk — reads actual identifiers", ha="left", va="center", fontsize=14.5, color=MUTED, style="italic")

# ── Visual diagram: code -> AST tree (node boxes) -> filter -> real tokens ──
draw_box(ax2, 5.0, 19.9, 8.6, 2.0, "white", "#D8DCE2",
         "class InventoryManager\n{ syncWarehouse(...) }", 12.5, textcolor=INK)
ax2.text(0.5, 18.55, "input code", ha="left", va="center", fontsize=11, color=MUTED, style="italic")

draw_down_arrow(ax2, 5.0, 18.75, 17.6, ORANGE)
ax2.text(6.3, 18.15, "esprima.parseScript()\n(full parse)", ha="left", va="center", fontsize=11, color=ORANGE, fontweight="bold")

# Mini AST node row (3 small boxes side by side = tree nodes)
node_labels = ["ClassDecl", "MethodDef", "Identifier..."]
nx = [2.2, 5.0, 7.8]
for lbl, x in zip(node_labels, nx):
    draw_box(ax2, x, 15.9, 2.65, 1.35, "white", ORANGE, lbl, 9.8, lw=1.8, textcolor=ORANGE)
ax2.plot([2.2, 5.0], [16.6, 16.6], color=ORANGE, lw=1.4, zorder=1)
ax2.plot([5.0, 7.8], [16.6, 16.6], color=ORANGE, lw=1.4, zorder=1)
ax2.plot([5.0, 5.0], [16.6, 16.6], color=ORANGE, lw=1.4, zorder=1)
ax2.text(0.5, 14.85, "AST — every token typed (Identifier, Keyword, ...)", ha="left", va="center",
         fontsize=10.8, color=MUTED, style="italic")

draw_down_arrow(ax2, 5.0, 14.5, 13.4, ORANGE)
ax2.text(6.3, 13.9, "filter Identifier,\ndrop stopwords", ha="left", va="center", fontsize=11, color=ORANGE, fontweight="bold")

draw_box(ax2, 5.0, 12.05, 8.6, 2.1, ORANGE, ORANGE,
         'InventoryManager\nsyncWarehouse items\nreduce acc x merge...', 12.0, lw=2.4, textcolor="white")
ax2.text(0.5, 10.55, "query sent to BM25 — vocabulary = real code identifiers", ha="left", va="center",
         fontsize=10.8, color=MUTED, style="italic")

steps2 = [
    ("1", "PARSE", "Full syntax tree built — only reached\nbecause Case A found no match."),
    ("2", "WALK & FILTER", "Keep type==Identifier, drop\n_JS_STOPWORDS (class, return, this...)."),
    ("3", "DEDUP & JOIN", "Keep original casing, dedupe,\ntake first 20, join with spaces."),
]
y = 9.6
for num, head, body in steps2:
    ax2.add_patch(plt.Circle((1.4, y), 0.62, facecolor=ORANGE, edgecolor="white", linewidth=2.2, zorder=3))
    ax2.text(1.4, y, num, ha="center", va="center", fontsize=15, fontweight="bold", color="white", zorder=4)
    ax2.text(2.6, y + 0.4, head, ha="left", va="center", fontsize=15, fontweight="bold", color=ORANGE)
    ax2.text(2.6, y - 0.55, body, ha="left", va="top", fontsize=13, color=INK, linespacing=1.4)
    y -= 2.9

ax2.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                               facecolor=ORANGE, edgecolor=ORANGE, linewidth=1.5, alpha=0.15))
ax2.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                               facecolor="none", edgecolor=ORANGE, linewidth=2.2))
ax2.text(5.0, 1.18, "KEY: reads real tokens from a full parse — vocabulary\nchanges with every different input code.",
         ha="center", va="center", fontsize=13, color=ORANGE, fontweight="bold", linespacing=1.5)

fig.savefig(os.path.join(OUTPUT_DIR, "slide_keyword_mechanism_ab.png"), dpi=200, facecolor="white")
print("Saved: slide_keyword_mechanism_ab.png")
