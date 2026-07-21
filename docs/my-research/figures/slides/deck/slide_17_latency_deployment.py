#!/usr/bin/env python3
"""Slide 17: Latency & deployment context."""
import matplotlib.pyplot as plt
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
title_block(fig, "Deployment", "Latency & Where ThreadLearn Fits")

ax = fig.add_axes([0.08, 0.20, 0.42, 0.55])
labels = ["GPT-3.5-turbo\n(API)", "ThreadLearn\n(T4 GPU)"]
vals = [1.8, 26]
colors = [GPT, OURS]
bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor="white", zorder=3)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8, f"~{v}s",
            ha="center", fontsize=14, fontweight="bold", color=INK)
ax.set_ylabel("Latency per case (s)")
ax.set_ylim(0, 32)
ax.grid(axis="y", alpha=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# right side: deployment cards
cards = [
    ("Fits", "Offline code review, CI pipelines,\nIDE-assisted repair workflows.", OURS),
    ("Doesn't fit", "Real-time production monitoring\nrequiring sub-second response.", BASELINE),
    ("Privacy advantage", "Runs entirely on-premise — no\nsource code sent to external APIs\n(GDPR/HIPAA compliance).", GPT),
]
y0 = 0.68
for i, (head, body, color) in enumerate(cards):
    y = y0 - i * 0.19
    fig.add_artist(plt.Rectangle((0.56, y), 0.38, 0.15, transform=fig.transFigure,
                    facecolor="#FAFAFA", edgecolor=color, linewidth=2))
    fig.text(0.585, y + 0.12, head, fontsize=13.5, fontweight="bold", color=color)
    fig.text(0.585, y + 0.085, body, fontsize=10.5, color="#444", va="top", linespacing=1.4)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_17_latency_deployment.png"))
print("Saved: slide_17_latency_deployment.png")
