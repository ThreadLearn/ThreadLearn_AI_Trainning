"""Shared style constants for ThreadLearn slide deck — matches figure_base palette."""
import matplotlib.pyplot as plt

# Palette — identical to gen_fig_ablation.py / gen_fig_category.py
BASELINE  = "#B0BEC5"
OURS      = "#E76F51"
GPT       = "#2A9D8F"
FT        = "#E9C46A"
INK       = "#222222"
MUTED     = "#888888"
BG        = "#FFFFFF"
CARD_BG   = "#FAFAFA"

SLIDE_W, SLIDE_H = 13.333, 7.5  # 16:9 @ matching Canva/PowerPoint inches

def apply_rc():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
        "font.size": 15,
        "axes.titlesize": 22,
        "axes.titleweight": "bold",
        "axes.labelsize": 15,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
    })

def title_block(fig, kicker, title, y_kicker=0.965, y_title=0.925):
    """Small orange kicker label + big bold title, consistent across slides."""
    fig.text(0.06, y_kicker, kicker.upper(), fontsize=13, fontweight="bold",
              color=OURS, ha="left", va="top", family="sans-serif")
    fig.text(0.06, y_title, title, fontsize=27, fontweight="bold",
              color=INK, ha="left", va="top", family="sans-serif")

def footer(fig, text="ThreadLearn — RAG-Augmented Fine-Tuned LLM for JS Concurrency Bugs"):
    fig.text(0.06, 0.025, text, fontsize=10, color=MUTED, ha="left", va="bottom")
    fig.text(0.94, 0.025, "●", fontsize=10, color=OURS, ha="right", va="bottom")
