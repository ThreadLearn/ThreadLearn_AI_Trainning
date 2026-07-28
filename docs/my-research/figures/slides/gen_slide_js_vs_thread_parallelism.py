#!/usr/bin/env python3
"""Slide: JavaScript "song song" (event loop / libuv) vs Java/C++ "song song"
thật (OS threads) — 2 card so sánh + mini timeline diagram mỗi bên + bảng tóm tắt.
Same visual style as gen_slide_keyword_mechanism.py / gen_slide_bm25.py.
Nội dung khớp phần đã thêm vào script_thuyet_trinh_slide13-25.md (Slide 13)."""

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

fig = plt.figure(figsize=(19.2, 10.8))  # 16:9
fig.patch.set_facecolor("white")

# ── Title ──────────────────────────────────────────────────────
fig.text(0.5, 0.99, 'JavaScript "Parallelism" vs. Java/C++ — What\'s Really Different?',
          ha="center", va="top", fontsize=37, fontweight="bold", color=INK)
fig.text(0.5, 0.945, "Both are called parallelism, but the execution mechanism underneath is completely different",
          ha="center", va="top", fontsize=18.5, color=MUTED)

card_top, card_bottom = 0.895, 0.20
card_gap = 0.03
card_w = (0.97 - 0.03 - card_gap) / 2
card_h = card_top - card_bottom


def draw_box(ax, cx, cy, w, h, face, edge, text, fs, lw=1.6, textcolor=None):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.03,rounding_size=0.1",
                                 facecolor=face, edgecolor=edge, linewidth=lw))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=textcolor or INK,
            fontfamily="monospace", linespacing=1.35, fontweight="bold")


# ============================= CARD LEFT: Java/C++ =============================
ax = fig.add_axes([0.03, card_bottom, card_w, card_h])
ax.set_xlim(0, 10); ax.set_ylim(0, 24); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 23.7, boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=ORANGE_BG, edgecolor=ORANGE, linewidth=2.6))

ax.add_patch(plt.Circle((1.75, 22.7), 1.25, facecolor=ORANGE, edgecolor="white", linewidth=2.6, zorder=3))
ax.text(1.75, 22.7, "1", ha="center", va="center", fontsize=30, fontweight="bold", color="white", zorder=4)
ax.text(3.5, 23.15, "JAVA / C++", ha="left", va="center", fontsize=22, fontweight="bold", color=ORANGE)
ax.text(3.5, 22.1, "multiple real OS threads, running concurrently on the CPU", ha="left", va="center",
        fontsize=15.5, color=MUTED, style="italic")

# Mini diagram: 3 thread lanes chạy song song thật, có điểm giao cắt (race) khi cùng ghi 1 biến
lane_y = [19.6, 17.7, 15.8]
lane_labels = ["Thread A", "Thread B", "Thread C"]
for ly, lbl in zip(lane_y, lane_labels):
    ax.plot([1.0, 8.6], [ly, ly], color=ORANGE, lw=2.4, solid_capstyle="round", zorder=1)
    ax.add_patch(plt.Circle((1.0, ly), 0.22, facecolor=ORANGE, edgecolor="white", linewidth=1.4, zorder=3))
    ax.text(0.55, ly, lbl.split()[1], ha="center", va="center", fontsize=10, fontweight="bold",
            color="white", zorder=4)
    ax.text(1.35, ly + 0.55, lbl, ha="left", va="center", fontsize=12, color=ORANGE, fontweight="bold")

# Shared memory box + race point
ax.add_patch(FancyBboxPatch((4.05, 16.5), 1.9, 4.0, boxstyle="round,pad=0.03,rounding_size=0.12",
                             facecolor="white", edgecolor="#D8DCE2", linewidth=1.4))
ax.text(5.0, 18.5, "SHARED\nMEMORY\n(counter)", ha="center", va="center", fontsize=10.5,
        fontfamily="monospace", fontweight="bold", color=INK, linespacing=1.4)
for ly in lane_y:
    ax.annotate("", xy=(5.0, 18.5), xytext=(5.0, ly),
                arrowprops=dict(arrowstyle="-", color="#C7452F", lw=1.6, linestyle=(0, (2, 2))))
ax.text(5.0, 15.05, "3 CPU cores write the SAME variable\nAT THE SAME TIME -> needs a LOCK/mutex", ha="center", va="top",
        fontsize=11.8, color="#C7452F", fontweight="bold", linespacing=1.4)

steps_left = [
    ("1", "N REAL THREADS", "The OS spawns N threads; a multi-core\nCPU runs them TRULY AT ONCE\n(hardware-level concurrency)."),
    ("2", "SHARED MEMORY", "Multiple threads can read/write the\nsame memory at the exact same\nmoment -> concurrent-access race."),
    ("3", "LOCKS REQUIRED", "Developers must manage mutexes,\nsemaphores, atomics themselves —\nmissing a lock is the #1 race cause."),
]
y = 12.55
for num, head, body in steps_left:
    ax.add_patch(plt.Circle((1.4, y), 0.62, facecolor=ORANGE, edgecolor="white", linewidth=2.2, zorder=3))
    ax.text(1.4, y, num, ha="center", va="center", fontsize=16, fontweight="bold", color="white", zorder=4)
    ax.text(2.6, y + 0.4, head, ha="left", va="center", fontsize=16, fontweight="bold", color=ORANGE)
    ax.text(2.6, y - 0.55, body, ha="left", va="top", fontsize=13, color=INK, linespacing=1.45)
    y -= 3.55

ax.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                             facecolor=ORANGE, edgecolor=ORANGE, linewidth=1.5, alpha=0.15))
ax.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                             facecolor="none", edgecolor=ORANGE, linewidth=2.2))
ax.text(5.0, 1.18, "KEY: race = real concurrent memory access\nbetween OS threads running on multiple cores.",
        ha="center", va="center", fontsize=14, color=ORANGE, fontweight="bold", linespacing=1.5)

# ============================= CARD RIGHT: JavaScript/Node.js =============================
ax2 = fig.add_axes([0.03 + card_w + card_gap, card_bottom, card_w, card_h])
ax2.set_xlim(0, 10); ax2.set_ylim(0, 24); ax2.axis("off")
ax2.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 23.7, boxstyle="round,pad=0.05,rounding_size=0.2",
                              facecolor=TEAL_BG, edgecolor=TEAL, linewidth=2.6))

ax2.add_patch(plt.Circle((1.75, 22.7), 1.25, facecolor=TEAL, edgecolor="white", linewidth=2.6, zorder=3))
ax2.text(1.75, 22.7, "2", ha="center", va="center", fontsize=30, fontweight="bold", color="white", zorder=4)
ax2.text(3.5, 23.15, "JAVASCRIPT / NODE.JS", ha="left", va="center", fontsize=22, fontweight="bold", color=TEAL)
ax2.text(3.5, 22.1, "a single thread, interleaved through the event loop", ha="left", va="center",
         fontsize=15.5, color=MUTED, style="italic")

# Mini diagram: 1 lane duy nhất, các block A/B/C xen kẽ theo thời gian (không chồng lấn)
ax2.plot([1.0, 8.6], [18.6, 18.6], color=TEAL, lw=2.4, solid_capstyle="round", zorder=1)
ax2.add_patch(plt.Circle((1.0, 18.6), 0.22, facecolor=TEAL, edgecolor="white", linewidth=1.4, zorder=3))
ax2.text(0.55, 18.6, "T", ha="center", va="center", fontsize=10, fontweight="bold", color="white", zorder=4)
ax2.text(1.35, 19.35, "Main / JS Thread (only one)", ha="left", va="center", fontsize=12, color=TEAL, fontweight="bold")

blocks = [("A", 1.9), ("B", 3.3), ("A", 4.7), ("C", 6.1), ("B", 7.5)]
for lbl, x in blocks:
    ax2.add_patch(FancyBboxPatch((x - 0.5, 18.05), 1.0, 1.1, boxstyle="round,pad=0.02,rounding_size=0.08",
                                  facecolor="white", edgecolor=TEAL, linewidth=1.6, zorder=2))
    ax2.text(x, 18.6, lbl, ha="center", va="center", fontsize=13, fontweight="bold", color=TEAL, zorder=3)
ax2.text(5.0, 16.75, "A, B, C interleave over time on the SAME thread\n(each await/callback is an event-loop handoff point)",
         ha="center", va="top", fontsize=11.8, color=TEAL, fontweight="bold", linespacing=1.4)

steps_right = [
    ("1", "ONE SINGLE THREAD", "JS code always runs on exactly one\nthread — no two JS lines ever run\nAT THE SAME TIME on the CPU."),
    ("2", "LIBUV DOES THE HEAVY LIFTING", "Event loop + hidden thread pool\nhandle blocking I/O; network I/O\nuses non-blocking kernel calls."),
    ("3", "BUGS FROM WRONG ORDERING", "Not concurrent access — callbacks\ninterleave in the WRONG order\nbetween two awaits (atomicity bug)."),
]
y = 12.55
for num, head, body in steps_right:
    ax2.add_patch(plt.Circle((1.4, y), 0.62, facecolor=TEAL, edgecolor="white", linewidth=2.2, zorder=3))
    ax2.text(1.4, y, num, ha="center", va="center", fontsize=16, fontweight="bold", color="white", zorder=4)
    ax2.text(2.6, y + 0.4, head, ha="left", va="center", fontsize=16, fontweight="bold", color=TEAL)
    ax2.text(2.6, y - 0.55, body, ha="left", va="top", fontsize=13, color=INK, linespacing=1.45)
    y -= 3.55

ax2.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                              facecolor=TEAL, edgecolor=TEAL, linewidth=1.5, alpha=0.15))
ax2.add_patch(FancyBboxPatch((0.6, 0.4), 8.8, 1.55, boxstyle="round,pad=0.04,rounding_size=0.12",
                              facecolor="none", edgecolor=TEAL, linewidth=2.2))
ax2.text(5.0, 1.18, "KEY: race = wrong-order interleaving on one\nthread — no two instructions truly run at once.",
         ha="center", va="center", fontsize=14, color=TEAL, fontweight="bold", linespacing=1.5)

# ── Bottom compact comparison strip ─────────────────────────────
ax_b = fig.add_axes([0.03, 0.02, 0.94, 0.155])
ax_b.set_xlim(0, 10); ax_b.set_ylim(0, 2); ax_b.axis("off")
ax_b.add_patch(FancyBboxPatch((0.05, 0.05), 9.9, 1.9, boxstyle="round,pad=0.05,rounding_size=0.15",
                               facecolor="#FAFBFC", edgecolor=INK, linewidth=2.6))
rows = [
    ("Execution unit", "N real OS threads", "1 JS thread + hidden libuv pool"),
    ("\"Parallelism\" mechanism", "Multi-core CPU runs at once", "Event loop interleaves tasks"),
    ("Root cause of races", "Concurrent memory access", "Wrong-order callback interleaving"),
    ("Tool to avoid bugs", "Lock / mutex / semaphore", "Keep blocks atomic between awaits"),
]
col_x = [1.7, 4.7, 7.9]
headers = ["Criteria", "Java / C++", "JavaScript / Node.js"]
for cx, h in zip(col_x, headers):
    ax_b.text(cx, 1.7, h, ha="center", va="center", fontsize=14.5, fontweight="bold", color=MUTED)
row_y = [1.33, 0.97, 0.61, 0.25]
for ry, (crit, left, right) in zip(row_y, rows):
    ax_b.text(col_x[0], ry, crit, ha="center", va="center", fontsize=13, color=INK, fontweight="bold")
    ax_b.text(col_x[1], ry, left, ha="center", va="center", fontsize=13, color=ORANGE)
    ax_b.text(col_x[2], ry, right, ha="center", va="center", fontsize=13, color=TEAL)

fig.savefig(os.path.join(OUTPUT_DIR, "slide_js_vs_thread_parallelism.png"), dpi=200, facecolor="white")
print("Saved: slide_js_vs_thread_parallelism.png")
