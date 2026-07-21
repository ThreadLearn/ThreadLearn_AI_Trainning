#!/usr/bin/env python3
"""Slide chart 5: PASS/PARTIAL/FAIL stacked bar — 6 configurations (counts out of 30)."""
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
    "Base (no pipe)",
    "GPT-3.5 (no pipe)",
    "Fine-tuned (no pipe)",
    "Base + pipeline",
    "GPT-3.5 + pipeline",
    "ThreadLearn + pipeline",
]
passc    = [6, 7, 8, 8, 9, 14]
partialc = [24, 23, 22, 20, 21, 16]
failc    = [0, 0, 0, 2, 0, 0]

y = np.arange(len(configs))

fig, ax = plt.subplots(figsize=(9.5, 5.5))

b1 = ax.barh(y, passc, color="#2A9D8F", label="Pass", edgecolor="white", height=0.6, zorder=3)
b2 = ax.barh(y, partialc, left=passc, color="#E9C46A", label="Partial", edgecolor="white", height=0.6, zorder=3)
left2 = [p + q for p, q in zip(passc, partialc)]
b3 = ax.barh(y, failc, left=left2, color="#E76F51", label="Fail", edgecolor="white", height=0.6, zorder=3)

for i, (p, pa, f) in enumerate(zip(passc, partialc, failc)):
    ax.text(p/2, i, str(p), ha="center", va="center", fontsize=10.5, fontweight="bold", color="white")
    ax.text(p + pa/2, i, str(pa), ha="center", va="center", fontsize=10.5, fontweight="bold", color="#553")
    if f > 0:
        ax.text(p + pa + f/2, i, str(f), ha="center", va="center", fontsize=10.5, fontweight="bold", color="white")

ax.set_yticks(y)
ax.set_yticklabels(configs, fontsize=12)
ax.set_xlabel("Number of cases (out of 30)")
ax.set_xlim(0, 32)
ax.set_title("PASS / PARTIAL / FAIL Breakdown by Configuration", pad=14)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=11.5, frameon=True)

fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "slide_pass_breakdown.png"))
print("Saved: slide_pass_breakdown.png")
