#!/usr/bin/env python3
"""Slide: BM25 explained — visual/component style, single 16:9 slide.
4x2 grid of colored step cards instead of a tall vertical stack — fits one slide,
larger readable text. Based on real code from server/server/bm25_module.py."""

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
GOLD = "#C9971F"; GOLD_BG = "#FBF3DE"
BLUE = "#5B6EA8"; BLUE_BG = "#E7EAF4"
CARD_BORDER = "#D8DCE2"

fig = plt.figure(figsize=(19.2, 10.8))  # 16:9
fig.patch.set_facecolor("white")

# ── Title ──────────────────────────────────────────────────────
fig.text(0.5, 0.988, "BM25: What It Is & How ThreadLearn Uses It",
          ha="center", va="top", fontsize=34, fontweight="bold", color=INK)
fig.text(0.5, 0.945, "Best Match 25 — ranks documents by relevance to a query,"
                      " improving TF-IDF with term-frequency saturation + length normalization",
          ha="center", va="top", fontsize=14.5, color=MUTED)

# ── Formula strip (compact, single row, bold framed box) ──────────
ax_f = fig.add_axes([0.03, 0.79, 0.60, 0.125])
ax_f.set_xlim(0, 10); ax_f.set_ylim(0, 2); ax_f.axis("off")
ax_f.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor="#FAFBFC", edgecolor=INK, linewidth=3.0))
formula = (r"$\mathrm{score}(q, D) = \mathrm{IDF}(q) \times "
           r"\dfrac{\mathrm{TF}(q,D)\times(k_1+1)}"
           r"{\mathrm{TF}(q,D) + k_1\times\left(1-b+b\times\dfrac{|D|}"
           r"{\mathrm{avgDL}}\right)}$")
ax_f.text(5, 1.0, formula, ha="center", va="center", fontsize=18.5, color=INK)

# ── Legend chips + param badges (right side) ─────────────────────
ax_l = fig.add_axes([0.645, 0.79, 0.335, 0.125])
ax_l.set_xlim(0, 10); ax_l.set_ylim(0, 2); ax_l.axis("off")
chips = [(1.7, TEAL, TEAL_BG, "IDF(q)", "term rarity"),
         (5.0, ORANGE, ORANGE_BG, "TF(q,D)", "term freq. in D"),
         (8.3, BLUE, BLUE_BG, "|D|/avgDL", "length norm")]
for x, edge, bg, label, sub in chips:
    ax_l.add_patch(FancyBboxPatch((x - 1.55, 1.02), 3.0, 0.9, boxstyle="round,pad=0.03,rounding_size=0.12",
                                    facecolor=bg, edgecolor=edge, linewidth=1.8))
    ax_l.text(x, 1.62, label, ha="center", va="center", fontsize=17, fontweight="bold", color=edge)
    ax_l.text(x, 1.18, sub, ha="center", va="center", fontsize=12, color=MUTED)
badge_text = "N=2,050 docs   k1=1.5 (saturation)   b=0.75 (length norm)"
ax_l.text(5, 0.30, badge_text, ha="center", va="center", fontsize=13, fontfamily="monospace", color=INK,
          bbox=dict(boxstyle="round,pad=0.45", facecolor="#F0F1F3", edgecolor="#C7CBD1", linewidth=1.0))

# ── 4x2 STEP GRID ──────────────────────────────────────────────
STEPS = [
    (1, TEAL, TEAL_BG, "BUILD INDEX", "server startup, once",
     ["2,050 docs -> tokenize()", '"Promise.all()" ->', "  [promise, all, ...]",
      "BM25Okapi -> IDF"]),
    (2, ORANGE, ORANGE_BG, "USER CODE INPUT", "buggy JS submitted",
     ["for (var i=0; i<3;", "     i++) {", "  setTimeout(() =>", "    log(i), 100);", "}"]),
    (3, GOLD, GOLD_BG, "AST EXTRACT", "ast_preprocessor.py",
     ["Parses code ->", "detects pattern ->", 'query = "setTimeout', '  var closure async"']),
    (4, BLUE, BLUE_BG, "TOKENIZE QUERY", "same pipeline as Step 1",
     ["tokenize(query) ->", "[settimeout, var,", " closure, async]"]),
    (5, TEAL, TEAL_BG, "SCORE EVERY DOC", "index.get_scores(tokens)",
     ['"async": df=340', "IDF ~= 1.62", "TF=2  |D|=48", "score ~= 2.38"]),
    (6, ORANGE, ORANGE_BG, "RANK & FILTER", "sort, drop zero, dedupe",
     ["Sort scores, desc.", "Drop score == 0", 'Dedupe by title']),
    (7, GOLD, GOLD_BG, "RETURN TOP-3", "highest-scoring docs",
     ['"Promise.all()"  4.71', '"Closures loop"  3.95', '"setTimeout"     3.20']),
    (8, BLUE, BLUE_BG, "FEED INTO PROMPT", "grounds the LLM fix",
     ["Top-3 docs ->", "context before code", "-> Qwen2.5-Coder"]),
]

cols, rows = 4, 2
grid_left, grid_right = 0.03, 0.97
grid_top, grid_bottom = 0.775, 0.03
col_gap, row_gap = 0.018, 0.05
card_w = (grid_right - grid_left - col_gap * (cols - 1)) / cols
card_h = (grid_top - grid_bottom - row_gap * (rows - 1)) / rows

for i, (num, edge, bg, title, sub, lines) in enumerate(STEPS):
    r, c = divmod(i, cols)
    x0 = grid_left + c * (card_w + col_gap)
    y0 = grid_top - (r + 1) * card_h - r * row_gap
    ax = fig.add_axes([x0, y0, card_w, card_h])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 9.7, boxstyle="round,pad=0.05,rounding_size=0.35",
                                  facecolor=bg, edgecolor=edge, linewidth=1.8))

    ax.add_patch(plt.Circle((2.0, 8.4), 1.15, facecolor=edge, edgecolor="white", linewidth=2.2, zorder=3))
    ax.text(2.0, 8.4, str(num), ha="center", va="center", fontsize=26, fontweight="bold", color="white", zorder=4)

    ax.text(3.7, 8.8, title, ha="left", va="center", fontsize=17, fontweight="bold", color=edge)
    ax.text(3.7, 7.55, sub, ha="left", va="center", fontsize=13.5, color=MUTED, style="italic")

    line_txt = "\n".join(lines)
    ax.text(0.9, 6.6, line_txt, ha="left", va="top", fontsize=15, fontfamily="monospace",
            color=INK, linespacing=1.85)

    # Arrow to next step (skip after last card in a row-wrap that isn't sequential visually,
    # but keep simple right-pointing arrows between horizontally adjacent cards)
    if c < cols - 1:
        arrow_ax = fig.add_axes([x0 + card_w, y0, col_gap, card_h])
        arrow_ax.set_xlim(0, 1); arrow_ax.set_ylim(0, 1); arrow_ax.axis("off")
        arrow_ax.annotate("", xy=(0.95, 0.5), xytext=(0.05, 0.5),
                           arrowprops=dict(arrowstyle="-|>", color="#AAB0B8", lw=2.2))
    elif r < rows - 1:
        arrow_ax = fig.add_axes([grid_left, y0 - row_gap, grid_right - grid_left, row_gap])
        arrow_ax.set_xlim(0, 1); arrow_ax.set_ylim(0, 1); arrow_ax.axis("off")
        arrow_ax.annotate("", xy=(0.02, 0.15), xytext=(0.98, 0.85),
                           arrowprops=dict(arrowstyle="-|>", color="#AAB0B8", lw=2.2,
                                            connectionstyle="arc3,rad=-0.3"))

fig.savefig(os.path.join(OUTPUT_DIR, "slide_bm25_explained.png"), dpi=200, facecolor="white")
print("Saved: slide_bm25_explained.png")
