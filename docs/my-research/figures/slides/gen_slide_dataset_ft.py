#!/usr/bin/env python3
"""Slide: Fine-Tuning Dataset composition — donut chart + source note.
332 handcrafted (37.2%) + 560 template-generated (62.8%) = 892 examples."""

import matplotlib.pyplot as plt
import os
from matplotlib.gridspec import GridSpec

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 12,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": None,
})

fig = plt.figure(figsize=(10, 9.2))
gs = GridSpec(2, 1, figure=fig, height_ratios=[2.0, 3.0], hspace=0.35)

ax_chart = fig.add_subplot(gs[0])
ax_text = fig.add_subplot(gs[1])
ax_text.axis("off")

# ── Donut chart ─────────────────────────────────────────────────
labels = ["Synthetic\n(handcrafted, 332)", "Generated\n(template-expanded, 560)"]
sizes = [332, 560]
colors = ["#E9C46A", "#E76F51"]
wedges, texts, autotexts = ax_chart.pie(
    sizes, labels=labels, colors=colors, autopct="%1.1f%%",
    startangle=90, pctdistance=0.78, wedgeprops=dict(width=0.40, edgecolor="white"),
    textprops={"fontsize": 12},
)
for at in autotexts:
    at.set_fontweight("bold")
    at.set_color("white")
ax_chart.text(0, 0, "892", ha="center", va="center", fontsize=28, fontweight="bold", color="#333")
ax_chart.set_title("Fine-Tuning Dataset — 892 Examples", pad=18, fontsize=16, fontweight="bold")

# ── Compact provenance note ──────────────────────────────────────
note = (
    "DATA SOURCE & CREATION METHOD:\n"
    + "─" * 48 + "\n" +
    "  Synthetic (332)   Handcrafted bug/fix pairs by authors\n"
    "                    (ai1_01_dataset_collector.py + edge-case\n"
    "                    generator). 14 concurrency categories:\n"
    "                    callback→async, Promise.all, worker_threads,\n"
    "                    race-condition fix, AbortController, etc.\n"
    "\n"
    "  Generated (560)   Deterministic template engine\n"
    "                    generate_pairs(): 30 domain entities\n"
    "                    (User, Order, Payment, ...) × 20 pattern\n"
    "                    generators. No LLM labels — all correct\n"
    "                    by construction."
)

ax_text.text(
    0.02, 0.98, note, transform=ax_text.transAxes,
    fontsize=9.5, fontfamily="monospace", color="#444",
    va="top", ha="left", linespacing=1.5,
    bbox=dict(boxstyle="round,pad=0.8", facecolor="#FAFAFA", edgecolor="#CCC", linewidth=0.8),
)

fig.savefig(os.path.join(OUTPUT_DIR, "slide_dataset_ft.png"), dpi=200)
print("Saved: slide_dataset_ft.png")
