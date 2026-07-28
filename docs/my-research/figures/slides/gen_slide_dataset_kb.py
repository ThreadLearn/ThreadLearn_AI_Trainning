#!/usr/bin/env python3
"""Slide: Knowledge Base composition — donut chart + source note.
2,050 documents: 1,418 patterns + 352 race-conditions + 280 anti-patterns.
Sources: MDN (99), lib docs (50), curated (151), context-permutation (1,750)."""

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

fig = plt.figure(figsize=(10, 10.8))
gs = GridSpec(2, 1, figure=fig, height_ratios=[2.0, 3.5], hspace=0.35)

ax_chart = fig.add_subplot(gs[0])
ax_text = fig.add_subplot(gs[1])
ax_text.axis("off")

# ── TOP: Donut chart ──────────────────────────────────────────────
labels = ["Patterns\n(1,418)", "Race-conditions\n(352)", "Anti-patterns\n(280)"]
sizes = [1418, 352, 280]
colors = ["#2A9D8F", "#E76F51", "#B0BEC5"]
wedges, texts, autotexts = ax_chart.pie(
    sizes, labels=labels, colors=colors, autopct="%1.1f%%",
    startangle=90, pctdistance=0.78, wedgeprops=dict(width=0.40, edgecolor="white"),
    textprops={"fontsize": 12},
)
for at in autotexts:
    at.set_fontweight("bold")
    at.set_color("white")
ax_chart.text(0, 0, "2,050", ha="center", va="center", fontsize=28, fontweight="bold", color="#333")
ax_chart.set_title("Knowledge Base — 2,050 Documents", pad=14, fontsize=16, fontweight="bold")

# ── BOTTOM: Compact provenance ───────────────────────────────────
note = (
    "DATA SOURCE & CREATION METHOD:\n"
    + "─" * 56 + "\n" +
    "  MDN Web Docs (99)             Official JS concurrency API:\n"
    "                                Promise, async/await, Worker, Atomics\n"
    "\n"
    "  Concurrency-library docs (50)  RxJS, p-limit, async-mutex, Bluebird\n"
    "\n"
    "  Curated patterns (151)         Hand-written detection signatures &\n"
    "                                fix templates by authors (esprima AST)\n"
    "\n"
    "  Context-permutation (1,750)    Automated re-phrasing of API descriptions\n"
    "                                with synonymous terms — expands all 3\n"
    "                                groups without label noise\n"
    "\n"
    "  3 GROUPS   Patterns = API how-to  |  Race-conditions = bug docs\n"
    "             Anti-patterns = what NOT to do\n"
    "\n"
    "Storage: ai2/knowledge-base/     Retrieval: BM25 (k1=1.5, b=0.75) → top-3"
)

ax_text.text(
    0.02, 0.98, note, transform=ax_text.transAxes,
    fontsize=9.5, fontfamily="monospace", color="#444",
    va="top", ha="left", linespacing=1.5,
    bbox=dict(boxstyle="round,pad=0.8", facecolor="#FAFAFA", edgecolor="#CCC", linewidth=0.8),
)

fig.savefig(os.path.join(OUTPUT_DIR, "slide_dataset_kb.png"), dpi=200)
print("Saved: slide_dataset_kb.png")
