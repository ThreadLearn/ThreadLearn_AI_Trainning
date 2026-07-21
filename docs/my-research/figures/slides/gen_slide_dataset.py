#!/usr/bin/env python3
"""Slide chart 4: Dataset composition — donut chart, fine-tuning pairs + KB breakdown."""
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

fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))

# --- Left: fine-tuning dataset composition ---
labels1 = ["Synthetic\n(handcrafted, 332)", "Generated\n(template-expanded, 560)"]
sizes1 = [332, 560]
colors1 = ["#E9C46A", "#E76F51"]
wedges, texts, autotexts = axes[0].pie(
    sizes1, labels=labels1, colors=colors1, autopct="%1.1f%%",
    startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.42, edgecolor="white"),
    textprops={"fontsize": 11},
)
for at in autotexts:
    at.set_fontweight("bold")
    at.set_color("white")
axes[0].set_title("Fine-Tuning Dataset\n(892 examples)", pad=12)
axes[0].text(0, 0, "892", ha="center", va="center", fontsize=22, fontweight="bold", color="#333")

# --- Right: knowledge base composition ---
labels2 = ["Patterns\n(1,418)", "Race-conditions\n(352)", "Anti-patterns\n(280)"]
sizes2 = [1418, 352, 280]
colors2 = ["#2A9D8F", "#E76F51", "#B0BEC5"]
wedges2, texts2, autotexts2 = axes[1].pie(
    sizes2, labels=labels2, colors=colors2, autopct="%1.1f%%",
    startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.42, edgecolor="white"),
    textprops={"fontsize": 11},
)
for at in autotexts2:
    at.set_fontweight("bold")
    at.set_color("white")
axes[1].set_title("Knowledge Base\n(2,050 documents)", pad=12)
axes[1].text(0, 0, "2,050", ha="center", va="center", fontsize=20, fontweight="bold", color="#333")

fig.suptitle("Dataset Composition", fontsize=17, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "slide_dataset_composition.png"))
print("Saved: slide_dataset_composition.png")
