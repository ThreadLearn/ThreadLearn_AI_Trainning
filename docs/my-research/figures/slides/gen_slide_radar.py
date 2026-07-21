#!/usr/bin/env python3
"""Slide chart 2: Radar — 3 models across 10 benchmark categories."""
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

categories = [
    "Race\nCond.", "Double\nCallback", "Unhandled\nRejection",
    "Resource\nExhaustion", "Event Loop\nBlocking", "Sequential\nAwaits",
    "Zalgo", "Context\nLoss", "Callback\nHell", "Stream\nLeak",
]
base_scores = [50, 50, 50, 63, 67, 67, 50, 75, 100, 100]
gpt_scores  = [50, 63, 70, 63, 67, 83, 50, 75,  50, 100]
tl_scores   = [70, 50, 90, 75, 67, 100, 50, 75, 100,  50]

N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

def close(vals):
    return vals + vals[:1]

fig, ax = plt.subplots(figsize=(8.5, 8.5), subplot_kw=dict(polar=True))

ax.plot(angles, close(base_scores), color="#B0BEC5", linewidth=2, label="Base + pipeline")
ax.fill(angles, close(base_scores), color="#B0BEC5", alpha=0.10)

ax.plot(angles, close(gpt_scores), color="#2A9D8F", linewidth=2, label="GPT-3.5 + pipeline")
ax.fill(angles, close(gpt_scores), color="#2A9D8F", alpha=0.10)

ax.plot(angles, close(tl_scores), color="#E76F51", linewidth=2.5, label="ThreadLearn + pipeline (ours)")
ax.fill(angles, close(tl_scores), color="#E76F51", alpha=0.18)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10.5)
ax.set_ylim(0, 100)
ax.set_yticks([25, 50, 75, 100])
ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=8.5, color="#888")
ax.set_title("Per-Category Score Comparison", pad=28)

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=10.5, frameon=True)

fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "slide_radar_categories.png"))
print("Saved: slide_radar_categories.png")
