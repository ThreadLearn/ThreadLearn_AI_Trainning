#!/usr/bin/env python3
"""Slide chart 3: Pipeline gain per model — before/after grouped bar."""
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
    "axes.grid.axis": "y",
})

models = ["Base\n(Qwen2.5-1.5B)", "GPT-3.5-turbo", "ThreadLearn\n(fine-tuned)"]
no_pipe = [60.0, 61.7, 63.3]
with_pipe = [60.0, 65.0, 73.3]
gains = [w - n for w, n in zip(with_pipe, no_pipe)]

x = np.arange(len(models))
width = 0.32

fig, ax = plt.subplots(figsize=(8.5, 5.5))

b1 = ax.bar(x - width/2, no_pipe, width, color="#B0BEC5", label="No pipeline", edgecolor="white", zorder=3)
b2 = ax.bar(x + width/2, with_pipe, width, color="#E76F51", label="+ Pipeline", edgecolor="white", zorder=3)

for bar, s in zip(b1, no_pipe):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{s:.1f}%",
            ha="center", va="bottom", fontsize=10.5, color="#555")
for bar, s in zip(b2, with_pipe):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{s:.1f}%",
            ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#222")

# gain annotations
for i, g in enumerate(gains):
    label = f"+{g:.1f} pp" if g > 0 else "±0 pp"
    color = "#c0392b" if g > 0 else "#888"
    ax.annotate(label, xy=(x[i] + width/2, with_pipe[i] + 6),
                ha="center", fontsize=11, fontweight="bold", color=color)

ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=12)
ax.set_ylabel("Score (%)")
ax.set_ylim(0, 92)
ax.set_title("Pipeline Impact by Model — Fine-Tuning Is a Prerequisite", pad=14)
ax.legend(loc="upper left", fontsize=11, frameon=True)

fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "slide_pipeline_gain.png"))
print("Saved: slide_pipeline_gain.png")
