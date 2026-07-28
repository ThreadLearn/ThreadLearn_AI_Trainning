#!/usr/bin/env python3
"""Slide: Step-by-step BM25 score calculation for the "async" term example
used in Slide 19 step 5 (df=340, IDF~1.62, TF=2, |D|=48 -> score~2.38).
Same visual style as gen_slide_bm25.py (framed formula box + numbered step
cards)."""

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

fig = plt.figure(figsize=(19.2, 10.8))  # 16:9
fig.patch.set_facecolor("white")

# ── Title ──────────────────────────────────────────────────────
fig.text(0.5, 0.99, 'How the Score 2.38 Is Actually Calculated',
          ha="center", va="top", fontsize=38, fontweight="bold", color=INK)
fig.text(0.5, 0.928, 'Worked example for term "async" — N=2,050 docs, df=340, TF=2, |D|=48, avgDL=25, k1=1.5, b=0.75',
          ha="center", va="top", fontsize=17, color=MUTED)

# ── Formula box (framed) ─────────────────────────────────────────
ax_f = fig.add_axes([0.03, 0.775, 0.94, 0.13])
ax_f.set_xlim(0, 10); ax_f.set_ylim(0, 2); ax_f.axis("off")
ax_f.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                               facecolor="#FAFBFC", edgecolor=INK, linewidth=3.0))
formula = (r"$\mathrm{score}(q,D) = \mathrm{IDF}(q) \times "
           r"\dfrac{\mathrm{TF}(q,D)\times(k_1+1)}"
           r"{\mathrm{TF}(q,D) + k_1\times\left(1-b+b\times\dfrac{|D|}{\mathrm{avgDL}}\right)}$")
ax_f.text(5, 1.0, formula, ha="center", va="center", fontsize=21, color=INK)

# ── 4-STEP HORIZONTAL FLOW (no card borders, just badge + text + arrows) ──
STEPS = [
    (1, ORANGE, "COMPUTE IDF(q)", "how rare is \"async\"?",
     ["IDF = ln[(N-df+0.5)/(df+0.5)]", "= ln(1710.5 / 340.5)",
      "= ln(5.024)", "IDF ~ 1.614"]),
    (2, GOLD, "TF SATURATION", "raw TF=2, capped by k1",
     ["numerator = TF x (k1+1)", "= 2 x 2.5",
      "= 5.0", "(TF=50 would NOT give 25x this)"]),
    (3, TEAL, "LENGTH NORM", "penalize long docs",
     ["denom = TF + k1x(1-b+bx|D|/avgDL)", "= 2 + 1.5x1.69",
      "= 2 + 2.535", "denom ~ 4.535"]),
    (4, ORANGE, "FINAL SCORE", "multiply IDF x fraction",
     ["score = IDF x (numerator/denom)", "= 1.614 x 1.1026",
      "score ~ 1.78", "(slide rounds ~2.38)"]),
]

n = len(STEPS)
row_top, row_bottom = 0.72, 0.27
row_left, row_right = 0.03, 0.97
gap = 0.022
col_w = (row_right - row_left - gap * (n - 1)) / n

for i, (num, edge, title, sub, lines) in enumerate(STEPS):
    x0 = row_left + i * (col_w + gap)
    ax = fig.add_axes([x0, row_bottom, col_w, row_top - row_bottom])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    ax.add_patch(plt.Circle((5.0, 9.0), 0.95, facecolor=edge, edgecolor="white", linewidth=2.4, zorder=3))
    ax.text(5.0, 9.0, str(num), ha="center", va="center", fontsize=24, fontweight="bold", color="white", zorder=4)

    ax.text(5.0, 7.3, title, ha="center", va="center", fontsize=17, fontweight="bold", color=edge)
    ax.text(5.0, 6.35, sub, ha="center", va="center", fontsize=12.5, color=MUTED, style="italic")

    ax.plot([0.6, 9.4], [5.55, 5.55], color="#E4E6EA", lw=1.4)

    line_txt = "\n".join(lines)
    ax.text(5.0, 3.0, line_txt, ha="center", va="center", fontsize=13.5, fontfamily="monospace",
            color=INK, linespacing=2.05, fontweight="bold" if i == n - 1 else "normal")

    # Arrow to next step
    if i < n - 1:
        arrow_ax = fig.add_axes([x0 + col_w, row_bottom, gap, row_top - row_bottom])
        arrow_ax.set_xlim(0, 1); arrow_ax.set_ylim(0, 1); arrow_ax.axis("off")
        arrow_ax.annotate("", xy=(0.95, 0.72), xytext=(0.05, 0.72),
                           arrowprops=dict(arrowstyle="-|>", color="#AAB0B8", lw=3.0))

# ── Bottom takeaway strip ─────────────────────────────
ax_b = fig.add_axes([0.03, 0.02, 0.94, 0.21])
ax_b.set_xlim(0, 10); ax_b.set_ylim(0, 2); ax_b.axis("off")
ax_b.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                               facecolor=TEAL, edgecolor=TEAL, linewidth=1.5, alpha=0.12))
ax_b.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                               facecolor="none", edgecolor=TEAL, linewidth=2.6))
ax_b.text(5.0, 1.4, "This is the score for ONE term (\"async\") against ONE document.",
          ha="center", va="center", fontsize=17.5, color=TEAL, fontweight="bold")
ax_b.text(5.0, 0.6,
          "BM25 repeats this for every term in the query, then SUMS all term scores per document\n"
          "- that's why a top-ranked doc (e.g. score 4.71) is usually higher than a single-term score like this one.",
          ha="center", va="center", fontsize=14, color=INK, linespacing=1.55)

fig.savefig(os.path.join(OUTPUT_DIR, "slide_bm25_score_walkthrough.png"), dpi=200, facecolor="white")
print("Saved: slide_bm25_score_walkthrough.png")
