#!/usr/bin/env python3
"""Slide 21: Race Condition Detector — accurate detail (replaces old Canva slide with wrong '10 patterns'/'Babel' claims)."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _slide_style import OURS, GPT, FT, BASELINE, INK, MUTED, CARD_BG, SLIDE_W, SLIDE_H, apply_rc, title_block, footer

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
apply_rc()

fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

title_block(fig, "Architecture — Verified Against race_detector.py", "Race Condition Detector (Static Analysis)")

fig.text(0.06, 0.815, "detectRaceConditions(code, language)  ->  regex-based pattern scan  ->  18 detectors total (14 JS + 4 Python)",
          fontsize=11.5, color="#444", ha="left", family="monospace")

# JS column
xj, y0j = 0.06, 0.16
col_w = 0.42
ax.add_patch(plt.Rectangle((xj, y0j), col_w, 0.58, facecolor=CARD_BG, edgecolor=OURS, linewidth=2, transform=ax.transAxes, zorder=2))
ax.add_patch(plt.Rectangle((xj, y0j + 0.58 - 0.055), col_w, 0.055, facecolor=OURS, transform=ax.transAxes, zorder=3))
fig.text(xj + col_w/2, y0j + 0.58 - 0.03, "JAVASCRIPT — 14 patterns", fontsize=12.5, fontweight="bold", color="white", ha="center", va="center")

js_patterns = [
    "closure_loop_var", "shared_var_settimeout", "promise_no_await",
    "concurrent_write_array", "counter_no_atomic", "unhandled_rejection",
    "double_callback", "zalgo", "context_loss_this", "callback_hell",
    "resource_exhaustion", "sequential_awaits", "buffer_leak", "sync_io_blocking",
]
for i, p in enumerate(js_patterns):
    y = y0j + 0.58 - 0.10 - i * 0.033
    fig.text(xj + 0.03, y, f"{i+1}.", fontsize=8.5, color=MUTED, ha="left", va="top")
    fig.text(xj + 0.06, y, p, fontsize=8.5, color=INK, ha="left", va="top", family="monospace")

# Python column
xp = 0.52
ax.add_patch(plt.Rectangle((xp, y0j), col_w, 0.58, facecolor=CARD_BG, edgecolor=BASELINE, linewidth=2, transform=ax.transAxes, zorder=2))
ax.add_patch(plt.Rectangle((xp, y0j + 0.58 - 0.055), col_w, 0.055, facecolor=BASELINE, transform=ax.transAxes, zorder=3))
fig.text(xp + col_w/2, y0j + 0.58 - 0.03, "PYTHON — 4 patterns", fontsize=12.5, fontweight="bold", color="white", ha="center", va="center")

py_patterns = ["global_var_thread", "shared_list_no_lock", "missing_join", "singleton_lazy_init"]
for i, p in enumerate(py_patterns):
    y = y0j + 0.58 - 0.10 - i * 0.033
    fig.text(xp + 0.03, y, f"{i+1}.", fontsize=8.5, color=MUTED, ha="left", va="top")
    fig.text(xp + 0.06, y, p, fontsize=8.5, color=INK, ha="left", va="top", family="monospace")

fig.text(xp + 0.03, y0j + 0.58 - 0.10 - 4 * 0.033 - 0.02,
          "Paper highlights 5 of the 14\nJS patterns as core (Table 2:\nDirect detector support) —\nsee Sect. 4.2.",
          fontsize=8.5, color=MUTED, ha="left", va="top", style="italic", linespacing=1.4)

footer(fig)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_21_race_detector_detail.png"))
print("Saved: slide_21_race_detector_detail.png")
