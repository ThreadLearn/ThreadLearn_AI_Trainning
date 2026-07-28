#!/usr/bin/env python3
"""Slide chart 4: Dataset composition — donut chart, fine-tuning pairs + KB breakdown.
Compact source & method notes only."""

import matplotlib.pyplot as plt
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 12,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

fig, axes = plt.subplots(1, 2, figsize=(12.5, 7.5))

# ── Left: fine-tuning dataset composition ──────────────────────────
labels1 = ["Synthetic\n(handcrafted, 332)", "Generated\n(template-expanded, 560)"]
sizes1 = [332, 560]
colors1 = ["#E9C46A", "#E76F51"]
axes[0].pie(
    sizes1, labels=labels1, colors=colors1, autopct="%1.1f%%",
    startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.42, edgecolor="white"),
    textprops={"fontsize": 10},
)
for at in axes[0].texts[-2:]:
    at.set_fontweight("bold")
    at.set_color("white")
axes[0].set_title("Fine-Tuning Dataset\n(892 examples)", pad=12, fontsize=13, fontweight="bold")
axes[0].text(0, 0, "892", ha="center", va="center", fontsize=22, fontweight="bold", color="#333")

left_note = (
    "SOURCE & METHOD:\n"
    "  Synthetic (332): handcrafted by authors\n"
    "  (ai1_01_dataset_collector.py + edge-case\n"
    "  generator). 14 concurrency categories.\n"
    "  Generated (560): generate_pairs() template\n"
    "  engine — 30 domains × 20 generators.\n"
    "  Deterministic, no LLM labels."
)
axes[0].text(
    0.0, -0.48, left_note, transform=axes[0].transAxes,
    fontsize=8, fontfamily="monospace", color="#555",
    va="top", ha="left",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#FAFAFA", edgecolor="#CCC", linewidth=0.8),
)

# ── Right: knowledge base composition ──────────────────────────────
labels2 = ["Patterns\n(1,418)", "Race-conditions\n(352)", "Anti-patterns\n(280)"]
sizes2 = [1418, 352, 280]
colors2 = ["#2A9D8F", "#E76F51", "#B0BEC5"]
axes[1].pie(
    sizes2, labels=labels2, colors=colors2, autopct="%1.1f%%",
    startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.42, edgecolor="white"),
    textprops={"fontsize": 10},
)
for at in axes[1].texts[-3:]:
    at.set_fontweight("bold")
    at.set_color("white")
axes[1].set_title("Knowledge Base\n(2,050 documents)", pad=12, fontsize=13, fontweight="bold")
axes[1].text(0, 0, "2,050", ha="center", va="center", fontsize=20, fontweight="bold", color="#333")

right_note = (
    "SOURCE & METHOD:\n"
    "  4 sources: MDN Web Docs (99), concurrency-\n"
    "  library docs (50), hand-written patterns (151),\n"
    "  context-permutation synthetic (1,750).\n"
    "  3 groups: Patterns (API how-to),\n"
    "  Race-conditions (bug docs),\n"
    "  Anti-patterns (what to avoid).\n"
    "  Retrieved via BM25 (k1=1.5, b=0.75)."
)
axes[1].text(
    0.0, -0.48, right_note, transform=axes[1].transAxes,
    fontsize=8, fontfamily="monospace", color="#555",
    va="top", ha="left",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#FAFAFA", edgecolor="#CCC", linewidth=0.8),
)

fig.suptitle("Dataset Composition", fontsize=17, fontweight="bold", y=1.03)
fig.subplots_adjust(bottom=0.28, top=0.90, wspace=0.35)
fig.savefig(os.path.join(OUTPUT_DIR, "slide_dataset_composition.png"))
print("Saved: slide_dataset_composition.png")
