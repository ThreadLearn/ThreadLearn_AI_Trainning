#!/usr/bin/env python3
"""Figure 2: Per-category grouped bar chart — 3 models with pipeline."""
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "grid.linestyle": "-",
    "axes.grid.axis": "y",
})

BASELINE_COLOR = "#B0BEC5"
GPT_COLOR      = "#2A9D8F"
OUR_COLOR      = "#E76F51"

categories = [
    "Race\nCond.", "Double\nCallback", "Unhandled\nRejection",
    "Resource\nExhaustion", "Event Loop\nBlocking", "Sequential\nAwaits",
    "Zalgo", "Context\nLoss", "Callback\nHell", "Stream\nLeak",
]
cases = [5, 4, 5, 4, 3, 3, 2, 2, 1, 1]

base_scores = [50, 50, 50, 63, 67, 67, 50, 75, 100, 100]
gpt_scores  = [50, 63, 70, 63, 67, 83, 50, 75,  50, 100]
tl_scores   = [70, 50, 90, 75, 67, 100, 50, 75, 100,  50]

# Wide + tall figure — room for labels above bars AND n= below
fig, ax = plt.subplots(figsize=(10.0, 5.0))

x = np.arange(len(categories))
width = 0.22

b1 = ax.bar(x - width, base_scores, width, color=BASELINE_COLOR,
            label="Base + pipeline", edgecolor="white", linewidth=0.5, zorder=3)
b2 = ax.bar(x,          gpt_scores,  width, color=GPT_COLOR,
            label="GPT-3.5 + pipeline", edgecolor="white", linewidth=0.5, zorder=3)
b3 = ax.bar(x + width,  tl_scores,   width, color=OUR_COLOR,
            label="ThreadLearn + pipeline (ours)", edgecolor="white", linewidth=0.5, zorder=3)

# Value labels — only on ThreadLearn bars to avoid clutter
for bar, s in zip(b3, tl_scores):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2.0,
            f"{s}%",
            ha="center", va="bottom", fontsize=7.5,
            color="#c0392b", fontweight="bold")

# n= case count annotations — in a separate text row below x-tick labels
# Using ax.annotate with clip_on=False so they appear outside plot area
for i, n in enumerate(cases):
    ax.annotate(f"n={n}",
                xy=(x[i], 0),
                xytext=(x[i], -16),
                textcoords=("data", "data"),
                ha="center", va="top",
                fontsize=7, color="#888",
                annotation_clip=False)

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=8.5)
ax.set_ylabel("Score (%)", labelpad=6)
ax.set_ylim(0, 120)
ax.set_title("Per-Category Scores with BM25+AST Pipeline (30-Case Benchmark)", pad=10)

# Legend BELOW axes
ax.legend(loc="upper center",
          bbox_to_anchor=(0.5, -0.28),
          ncol=3,
          fontsize=9,
          frameon=True,
          edgecolor="#ccc")

# 100% reference line
ax.axhline(100, color="#9E9E9E", linestyle="--", linewidth=0.8, alpha=0.5, zorder=0)

fig.subplots_adjust(bottom=0.28)
fig.savefig(os.path.join(OUTPUT_DIR, "fig_category.pdf"))
fig.savefig(os.path.join(OUTPUT_DIR, "fig_category.png"), dpi=300)
print("Saved: fig_category.pdf / fig_category.png")
