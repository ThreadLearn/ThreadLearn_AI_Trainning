#!/usr/bin/env python3
"""Slide 11: Static detector — 5 pattern deep-dive."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Core Contribution", "Static Race Detector — 5 Patterns")

patterns = [
    ("closure_loop_var", "var captured by reference\nin loop callbacks", "var i → let i", OURS),
    ("shared_var_settimeout", "shared variable modified\ninside setTimeout", "scoped var / atomic op", FT),
    ("promise_no_await", "Promise created but\nnot awaited", "await / .catch()", GPT),
    ("concurrent_write_array", "array mutated from\nconcurrent callbacks", "mutex / atomic update", BASELINE),
    ("counter_no_atomic", "non-atomic counter\nincrement", "mutex / queue", OURS),
]

y0 = 0.72
row_h = 0.115
for i, (name, desc, fix, color) in enumerate(patterns):
    y = y0 - i * row_h
    ax.add_patch(plt.Rectangle((0.06, y), 0.88, row_h - 0.02, facecolor=CARD_BG,
                                edgecolor=color, linewidth=1.8, transform=ax.transAxes, zorder=2))
    fig.text(0.09, y + (row_h-0.02)/2 + 0.012, name, fontsize=13.5, fontweight="bold",
              color=color, ha="left", va="center", family="monospace")
    fig.text(0.34, y + (row_h-0.02)/2 + 0.012, desc, fontsize=11, color="#444",
              ha="left", va="center", linespacing=1.3)
    fig.text(0.66, y + (row_h-0.02)/2 + 0.012, "→ " + fix, fontsize=11.5, fontweight="bold",
              color=INK, ha="left", va="center")

fig.text(0.5, 0.08, "Detector output narrows what the LLM must infer — pattern_id + line_range as structured context",
          fontsize=12.5, color=OURS, ha="center", style="italic", fontweight="bold")

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_11_detector_patterns.png"))
print("Saved: slide_11_detector_patterns.png")
