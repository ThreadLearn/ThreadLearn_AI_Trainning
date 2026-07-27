#!/usr/bin/env python3
"""Slide: Keyword Extraction — 3 case walkthrough (3a/3b/3c), same visual style
as gen_slide_bm25.py (colored cards, framed header, number badges).
Real code/output from server/server/rag_pipeline.py + training/modules/ast_preprocessor.py."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": None,
})

INK = "#1a1a2e"
MUTED = "#5b6472"
TEAL = "#2A9D8F"; TEAL_BG = "#E4F3F1"
ORANGE = "#E76F51"; ORANGE_BG = "#FCE9E4"
BLUE = "#5B6EA8"; BLUE_BG = "#E7EAF4"

fig = plt.figure(figsize=(19.2, 10.8))  # 16:9
fig.patch.set_facecolor("white")

# ── Title ──────────────────────────────────────────────────────
fig.text(0.5, 0.988, "Keyword Extraction: 3 Priority Tiers, 3 Different Queries",
          ha="center", va="top", fontsize=33, fontweight="bold", color=INK)
fig.text(0.5, 0.943, "Sequential fallback with early return — not parallel."
                     " Each tier hands BM25 a completely different kind of query.",
          ha="center", va="top", fontsize=15.5, color=MUTED)

# ── Framed control-flow box ──────────────────────────────────────
ax_f = fig.add_axes([0.03, 0.775, 0.94, 0.145])
ax_f.set_xlim(0, 10); ax_f.set_ylim(0, 2); ax_f.axis("off")
ax_f.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor="#FAFBFC", edgecolor=INK, linewidth=3.0))
code = (
    "semantic = _semantic_keywords(code)          # 3a — regex, always tried first\n"
    "if semantic: return semantic                  # STOP here if matched\n"
    "if _HAS_AST:\n"
    "    kw = _ast_extract_keywords(code)           # 3b — only if 3a empty\n"
    "    if kw.strip(): return kw                   # STOP here if matched\n"
    "return tokenize(code)[:20]                     # 3c — only if 3a AND 3b empty"
)
ax_f.text(5, 1.0, code, ha="center", va="center", fontsize=12.8, fontfamily="monospace", color=INK,
          linespacing=1.5)

# ── 3 CASE CARDS ───────────────────────────────────────────────
CASES = [
    ("A", TEAL, TEAL_BG, "3a MATCHES — STOPS IMMEDIATELY", "regex hard-coded label",
     [
         "async function loadDashboard(userId) {",
         "  const profile = await fetch(...)",
         "  const orders  = await fetch(...)",
         "  return { profile, orders };",
         "}",
     ],
     'query = "sequential await Promise.all\n         parallel concurrent"',
     "Fixed concept label — no code words\nat all (no \"profile\", \"userId\", \"fetch\").\n3b and 3c never run."),
    ("B", ORANGE, ORANGE_BG, "3a EMPTY -> 3b RUNS (AST)", "esprima real parse",
     [
         "class InventoryManager {",
         "  syncWarehouse(items) {",
         "    return items.reduce(",
         "      (acc,x) => acc.merge(x),",
         "      this.baseStock);",
         "  }",
         "}",
     ],
     'query = "InventoryManager syncWarehouse\n         items reduce acc x merge\n         baseStock"',
     "Real identifiers, original casing kept\n(CamelCase intact). Code-specific\nvocabulary, not a fixed label."),
    ("C", BLUE, BLUE_BG, "3a & 3b EMPTY -> 3c RUNS", "plain regex tokenize",
     [
         "# same code as Case B, but",
         "# esprima import/parse fails",
         "class InventoryManager {",
         "  syncWarehouse(items) { ... }",
         "}",
     ],
     'query = "inventory manager sync\n         warehouse items reduce acc\n         merge base stock"',
     "Same identifiers as Case B, but split\non CamelCase/snake_case — different\ntokenizer, different STOPWORDS set."),
]

card_top, card_bottom = 0.745, 0.045
card_gap = 0.025
card_w = (0.97 - 0.03 - card_gap * 2) / 3
card_h = card_top - card_bottom

for i, (letter, edge, bg, title, sub, code_lines, query_str, note) in enumerate(CASES):
    x0 = 0.03 + i * (card_w + card_gap)
    ax = fig.add_axes([x0, card_bottom, card_w, card_h])
    ax.set_xlim(0, 10); ax.set_ylim(0, 20); ax.axis("off")

    ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 19.7, boxstyle="round,pad=0.05,rounding_size=0.25",
                                  facecolor=bg, edgecolor=edge, linewidth=2.2))

    # Badge circle with letter
    ax.add_patch(plt.Circle((1.7, 18.6), 1.2, facecolor=edge, edgecolor="white", linewidth=2.4, zorder=3))
    ax.text(1.7, 18.6, letter, ha="center", va="center", fontsize=28, fontweight="bold", color="white", zorder=4)

    ax.text(3.35, 19.05, "CASE " + letter, ha="left", va="center", fontsize=15, color=MUTED, fontweight="bold")
    ax.text(3.35, 18.05, title, ha="left", va="center", fontsize=14, fontweight="bold", color=edge)
    ax.text(0.9, 16.95, sub, ha="left", va="center", fontsize=12.5, color=MUTED, style="italic")

    # Code box
    ax.add_patch(FancyBboxPatch((0.6, 11.5), 8.8, 5.15, boxstyle="round,pad=0.04,rounding_size=0.15",
                                  facecolor="white", edgecolor="#D8DCE2", linewidth=1.2))
    code_txt = "\n".join(code_lines)
    ax.text(1.0, 14.1, code_txt, ha="left", va="center", fontsize=11.8, fontfamily="monospace",
            color=INK, linespacing=1.5)

    # Arrow down
    ax.annotate("", xy=(5, 10.6), xytext=(5, 11.4),
                arrowprops=dict(arrowstyle="-|>", color=edge, lw=2.8))

    # Query result box (highlighted)
    ax.add_patch(FancyBboxPatch((0.6, 7.2), 8.8, 3.15, boxstyle="round,pad=0.04,rounding_size=0.15",
                                  facecolor=edge, edgecolor=edge, linewidth=1.5, alpha=0.12))
    ax.add_patch(FancyBboxPatch((0.6, 7.2), 8.8, 3.15, boxstyle="round,pad=0.04,rounding_size=0.15",
                                  facecolor="none", edgecolor=edge, linewidth=2.2))
    ax.text(5.0, 8.75, query_str, ha="center", va="center", fontsize=12.5, fontfamily="monospace",
            fontweight="bold", color=edge, linespacing=1.45)

    ax.text(0.9, 5.35, "BM25 RECEIVES:", ha="left", va="top", fontsize=11.5, fontweight="bold", color=MUTED)
    ax.text(0.9, 4.35, note, ha="left", va="top", fontsize=12, color=INK, linespacing=1.55)

# ── Bottom summary strip ─────────────────────────────────────────
fig.text(0.5, 0.015, "3a -> concept label for known bug patterns   |   "
                      "3b/3c -> real code vocabulary for everything else",
         ha="center", va="bottom", fontsize=14, color=MUTED, style="italic")

fig.savefig(os.path.join(OUTPUT_DIR, "slide_keyword_extraction_cases.png"), dpi=200, facecolor="white")
print("Saved: slide_keyword_extraction_cases.png")
