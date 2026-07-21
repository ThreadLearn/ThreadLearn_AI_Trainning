#!/usr/bin/env python3
"""Slide 7: Per-category radar comparison."""
import matplotlib.pyplot as plt
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
title_block(fig, "Results", "Per-Category Performance")

ax = fig.add_axes([0.24, 0.08, 0.55, 0.78], polar=True)

categories = [
    "Race\nCond.", "Double\nCallback", "Unhandled\nRejection",
    "Resource\nExhaustion", "Event Loop\nBlocking", "Sequential\nAwaits",
    "Zalgo", "Context\nLoss", "Callback\nHell", "Stream\nLeak",
]
base_scores = [50, 50, 50, 63, 67, 67, 50, 75, 100, 100]
gpt_scores  = [50, 63, 70, 63, 67, 83, 50, 75,  50, 100]
tl_scores   = [70, 50, 90, 75, 67, 100, 50, 75, 100,  50]

N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]
def close(v): return v + v[:1]

ax.plot(angles, close(base_scores), color=BASELINE, linewidth=2, label="Base + pipeline")
ax.fill(angles, close(base_scores), color=BASELINE, alpha=0.10)
ax.plot(angles, close(gpt_scores), color=GPT, linewidth=2, label="GPT-3.5 + pipeline")
ax.fill(angles, close(gpt_scores), color=GPT, alpha=0.10)
ax.plot(angles, close(tl_scores), color=OURS, linewidth=2.5, label="ThreadLearn (ours)")
ax.fill(angles, close(tl_scores), color=OURS, alpha=0.18)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10.5)
ax.set_ylim(0, 100)
ax.set_yticks([25, 50, 75, 100])
ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color=MUTED)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=1, fontsize=11, frameon=True)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_07_radar.png"))
print("Saved: slide_07_radar.png")
