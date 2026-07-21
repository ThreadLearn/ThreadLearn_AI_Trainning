#!/usr/bin/env python3
"""Slide 4: Dataset composition — donut charts + stat cards."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
title_block(fig, "Data", "Dataset Composition")

ax1 = fig.add_axes([0.06, 0.12, 0.40, 0.62])
ax2 = fig.add_axes([0.54, 0.12, 0.40, 0.62])

# Fine-tuning dataset
labels1 = ["Synthetic\n(332)", "Generated\n(560)"]
sizes1 = [332, 560]
w1, t1, at1 = ax1.pie(sizes1, labels=labels1, colors=[FT, OURS], autopct="%1.0f%%",
                       startangle=90, pctdistance=0.75,
                       wedgeprops=dict(width=0.42, edgecolor="white"), textprops={"fontsize": 12})
for a in at1: a.set_fontweight("bold"); a.set_color("white")
ax1.text(0, 0, "892", ha="center", va="center", fontsize=24, fontweight="bold", color=INK)
ax1.set_title("Fine-Tuning Examples", fontsize=15, pad=14)

# Knowledge base
labels2 = ["Patterns\n(1,418)", "Race-cond.\n(352)", "Anti-patterns\n(280)"]
sizes2 = [1418, 352, 280]
w2, t2, at2 = ax2.pie(sizes2, labels=labels2, colors=[GPT, OURS, BASELINE], autopct="%1.0f%%",
                       startangle=90, pctdistance=0.75,
                       wedgeprops=dict(width=0.42, edgecolor="white"), textprops={"fontsize": 12})
for a in at2: a.set_fontweight("bold"); a.set_color("white")
ax2.text(0, 0, "2,050", ha="center", va="center", fontsize=22, fontweight="bold", color=INK)
ax2.set_title("Knowledge Base Documents", fontsize=15, pad=14)

fig.text(0.5, 0.06, "30-case real-world benchmark drawn from independent production GitHub issues",
          fontsize=13, color=MUTED, ha="center", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_04_dataset.png"))
print("Saved: slide_04_dataset.png")
