#!/usr/bin/env python3
"""Figure 1: Ablation bar chart — 6 configurations on 30-case benchmark."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
OUR_COLOR      = "#E76F51"
GPT_COLOR      = "#2A9D8F"
FT_COLOR       = "#E9C46A"

configs = [
    "Base\n(no pipe)",
    "GPT-3.5\n(no pipe)",
    "ThreadLearn\n(no pipe)",
    "Base\n+pipeline",
    "GPT-3.5\n+pipeline",
    "ThreadLearn\n+pipeline",
]
scores  = [60.0, 61.7, 63.3, 60.0, 65.0, 73.3]
colors  = [BASELINE_COLOR, GPT_COLOR, FT_COLOR, BASELINE_COLOR, GPT_COLOR, OUR_COLOR]
hatches = ["", "", "", "///", "///", "///"]

fig, ax = plt.subplots(figsize=(7.2, 4.8))

x = np.arange(len(configs))
bars = ax.bar(x, scores, width=0.55, color=colors, hatch=hatches,
              edgecolor="white", linewidth=0.8, zorder=3)

# Value labels — above each bar
for bar, s in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{s:.1f}%",
            ha="center", va="bottom", fontsize=9, color="#222", fontweight="bold")

# Baseline reference line
ax.axhline(60.0, color="#9E9E9E", linestyle="--", linewidth=1.0, alpha=0.7, zorder=0)
ax.text(-0.5, 60.3, "baseline 60%", fontsize=7, color="#999", va="bottom", ha="left")

ax.set_xticks(x)
ax.set_xticklabels(configs, fontsize=9)
ax.set_ylabel("Score (%)", labelpad=6)
ax.set_ylim(54, 82)
ax.set_title("Ablation: Score by Configuration on 30-Case Real-World Benchmark", pad=10)

# Legend BELOW the axes — never overlaps bars
legend_elements = [
    mpatches.Patch(facecolor=BASELINE_COLOR,                      label="Base (Qwen2.5-Coder-1.5B)"),
    mpatches.Patch(facecolor=GPT_COLOR,                           label="GPT-3.5-turbo"),
    mpatches.Patch(facecolor=FT_COLOR,                            label="ThreadLearn (fine-tuned, no pipe)"),
    mpatches.Patch(facecolor=OUR_COLOR,                           label="ThreadLearn + pipeline (ours)"),
    mpatches.Patch(facecolor="#eee", edgecolor="#888", hatch="///", label="Hatched = with pipeline"),
]
ax.legend(handles=legend_elements,
          loc="upper center",
          bbox_to_anchor=(0.5, -0.18),   # below x-axis
          ncol=3,
          fontsize=8,
          frameon=True,
          edgecolor="#ccc")

fig.subplots_adjust(bottom=0.22)
fig.savefig(os.path.join(OUTPUT_DIR, "fig_ablation.pdf"))
fig.savefig(os.path.join(OUTPUT_DIR, "fig_ablation.png"), dpi=300)
print("Saved: fig_ablation.pdf / fig_ablation.png")
