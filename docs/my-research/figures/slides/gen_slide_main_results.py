#!/usr/bin/env python3
"""Slide chart 1: Main Results — horizontal bar, 6 configs, score %."""
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 13,
    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.2,
    "axes.grid.axis": "x",
})

configs = [
    "ThreadLearn + pipeline",
    "GPT-3.5-turbo + pipeline",
    "Base + pipeline",
    "Fine-tuned only (no pipe)",
    "GPT-3.5-turbo (no pipe)",
    "Base (no pipe)",
][::-1]
scores = [73.3, 65.0, 60.0, 63.3, 61.7, 60.0][::-1]
colors = ["#E76F51", "#2A9D8F", "#B0BEC5", "#E9C46A", "#2A9D8F", "#B0BEC5"][::-1]

fig, ax = plt.subplots(figsize=(9.5, 5.2))
y = np.arange(len(configs))
bars = ax.barh(y, scores, color=colors, edgecolor="white", height=0.62, zorder=3)

for bar, s in zip(bars, scores):
    ax.text(bar.get_width() + 1.0, bar.get_y() + bar.get_height() / 2,
            f"{s:.1f}%", va="center", ha="left", fontsize=12, fontweight="bold", color="#222")

ax.set_yticks(y)
ax.set_yticklabels(configs, fontsize=12)
ax.set_xlabel("Score on 30-case real-world benchmark (%)")
ax.set_xlim(0, 88)
ax.set_title("ThreadLearn vs. Baselines — Main Results", pad=14)
ax.axvline(60.0, color="#999", linestyle="--", linewidth=1, alpha=0.6, zorder=0)

fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "slide_main_results.png"))
print("Saved: slide_main_results.png")
