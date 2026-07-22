#!/usr/bin/env python3
"""Slide 20: Why use a static race detector at all (vs. LLM-only)?"""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Design Decision", "Why Use a Static Race Detector?")

fig.text(0.06, 0.775, "Existing tools sit at two extremes — neither is enough on its own:",
          fontsize=13.5, color="#444", ha="left")

# two extremes
card_w, card_h = 0.40, 0.30
y0 = 0.44

xb = 0.06
ax.add_patch(plt.Rectangle((xb, y0), card_w, card_h, facecolor=CARD_BG,
                            edgecolor=BASELINE, linewidth=2.5, transform=ax.transAxes, zorder=2))
fig.text(xb + card_w/2, y0 + card_h - 0.04, "Rule-based only", fontsize=14, fontweight="bold",
          color=BASELINE, ha="center", va="top")
fig.text(xb + card_w/2, y0 + card_h - 0.10, "(ESLint, ThreadSanitizer)", fontsize=10.5,
          color=MUTED, ha="center", va="top", style="italic")
fig.text(xb + card_w/2, y0 + card_h - 0.16, "Finds bugs at a precise line —\nbut cannot generate a fix.\nRigid: only known patterns,\nno generalization.",
          fontsize=11, color="#444", ha="center", va="top", linespacing=1.5)

xa = 0.54
ax.add_patch(plt.Rectangle((xa, y0), card_w, card_h, facecolor=CARD_BG,
                            edgecolor=GPT, linewidth=2.5, transform=ax.transAxes, zorder=2))
fig.text(xa + card_w/2, y0 + card_h - 0.04, "LLM-only", fontsize=14, fontweight="bold",
          color=GPT, ha="center", va="top")
fig.text(xa + card_w/2, y0 + card_h - 0.10, "(GPT-3.5-turbo, PCWMs)", fontsize=10.5,
          color=MUTED, ha="center", va="top", style="italic")
fig.text(xa + card_w/2, y0 + card_h - 0.16, "Can reason about code —\nbut misses the exact buggy\nline and needs 7B–32B\nparameters for accuracy.",
          fontsize=11, color="#444", ha="center", va="top", linespacing=1.5)

# arrow down to ThreadLearn resolution
ax.annotate("", xy=(0.5, 0.365), xytext=(0.5, 0.41),
            xycoords="figure fraction", textcoords="figure fraction",
            arrowprops=dict(arrowstyle="-|>", color=MUTED, linewidth=2.5))

# resolution card
ax.add_patch(plt.Rectangle((0.06, 0.15), 0.88, 0.20, facecolor=CARD_BG,
                            edgecolor=OURS, linewidth=2.5, transform=ax.transAxes, zorder=2))
fig.text(0.5, 0.325, "ThreadLearn: detector narrows what the LLM must infer", fontsize=14.5,
          fontweight="bold", color=OURS, ha="center")
fig.text(0.5, 0.285, "race_detector.py outputs {pattern_id, line_range, description} in O(n) time — this\n"
          "structured signal is injected into the prompt as grounding context, so the fine-tuned\n"
          "1.5B model doesn't need to re-derive what the detector already knows.",
          fontsize=11, color="#444", ha="center", va="top", linespacing=1.5)

fig.text(0.06, 0.10, "G1: rule-based detectors find bugs but can't fix them  ·  G2: LLM-only ignores structural signals, needs large models",
          fontsize=9.5, color=MUTED, ha="left", style="italic")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_20_why_race_detector.png"))
print("Saved: slide_20_why_race_detector.png")
