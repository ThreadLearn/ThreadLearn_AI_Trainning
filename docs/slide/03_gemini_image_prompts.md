# Gemini Image Prompts — Slide Visuals

Câu lệnh vẽ ảnh cho từng slide, gửi Gemini. Cùng 1 style base (đơn giản, flat, ít màu) áp cho toàn bộ 9 slide để đồng bộ bộ deck. Đã viết chi tiết layout/vị trí/kích thước để Gemini không tự bịa bố cục.

## Style base (giữ nguyên, chèn đầu mỗi prompt)

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.
```

---

## Slide 1 — Title

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — hero graphic for the title slide, centered in the frame:
- On the LEFT half: a vertical stack of 4-5 small gray rounded
  rectangles of varying width (like abstract lines of code, no letters
  inside them, just blank bars), stacked like a code editor snippet.
- Crossing diagonally OVER the code stack: two orange arrows forming
  an X shape, thin stroke, arrowheads visible on both ends — this
  represents two operations colliding (a race condition).
- On the RIGHT side, slightly below and overlapping the bottom-right
  corner of the code stack: a teal green shield icon (rounded shield
  outline) with a simple white checkmark inside it — representing
  "verified / fixed by AI".
- Nothing else in the frame. Plenty of white space above, below, and
  to the sides of this cluster so title text can be placed around it.
```

---

## Slide 2 — Problem Statement

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — a left-vs-right comparison diagram, split down the
middle by an invisible vertical center line:
- LEFT side (gray): 3 short horizontal parallel "lane" bars stacked
  vertically, evenly spaced, each lane with a tiny closed padlock icon
  centered on it — representing traditional multi-threading with locks.
  All in neutral gray #7A7A7A.
- RIGHT side (navy blue): one single circular arrow forming a loop
  (like a circular arrow chasing its own tail, clockwise), with 3 tiny
  small dots (representing code blocks / tasks) placed at different
  points along the circle's orbit, as if orbiting the loop. All in
  navy blue #2C3E93.
- Small orange warning triangle (thin outline, exclamation mark
  removed, just the empty triangle shape) placed just outside the
  navy circular loop on its right edge — implying a hidden bug near
  the event loop.
- Both sides same visual weight and size, aligned on the same
  horizontal center line, clear gap between them.
```

---

## Slide 3 — NodeCB Related Work

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — a flat donut chart (ring shape, not filled circle, with
a white hole in the center) positioned left-of-center, made of exactly
3 arc segments with small visible gaps between each segment:
- Largest arc segment (~65% of the ring) in orange #F2994A.
- Second arc segment (~30% of the ring) in navy blue #2C3E93.
- Smallest thin arc segment (~5% of the ring) in teal green #2FA88A.
Segments arranged clockwise starting from the top (12 o'clock position):
orange first, then navy, then the small teal sliver.
To the right of the donut chart: a simple magnifying glass icon (thin
circle with a short diagonal handle) in neutral gray #7A7A7A, roughly
the same height as the donut chart, floating with clear white space
between it and the chart — representing empirical research/study.
```

---

## Slide 4 — PCWMs Related Work

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — centered single icon cluster:
- Center: one rounded-square icon in navy blue #2C3E93 that visually
  blends a simple brain outline (rounded lobed shape) on its left half
  with a simple gear outline (circle with 6 small teeth) on its right
  half, merged into one symmetric icon — representing an AI "world
  model" that reasons like a simulated tool.
- A thin dashed orange arrow curves out from the right side of this
  icon, loops around clockwise, and points back into the left side of
  the same icon — a self-referencing loop, NOT pointing to anything
  external — representing self-simulation instead of calling an
  outside tool.
- Small, faint gray wrench icon positioned in the upper-right corner
  of the frame, far from the main icon, with a thin diagonal gray line
  struck through it (crossed-out) — representing "no external tool
  needed". Keep this element small and secondary, not competing with
  the main center icon.
```

---

## Slide 5 — Research Gap

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — classic 3-circle Venn diagram, all 3 circles the same
size, arranged so each pair overlaps but all three overlap only in one
small shared region in the middle:
- Left circle: outline and semi-flat fill in neutral gray #7A7A7A.
- Right circle: outline and semi-flat fill in teal green #2FA88A.
- Top circle (positioned above and between the other two, overlapping
  both): outline and semi-flat fill in navy blue #2C3E93.
- Use flat semi-transparent-looking overlap tones only through simple
  flat color blending in the overlap zones (no real transparency
  needed, just distinct flat overlap colors), keeping it clean and
  vector-like.
- In the exact center where all three circles would overlap, instead
  leave that small triangular zone completely empty/white, outlined
  with a thin dashed orange #F2994A border — representing a gap that
  no existing circle (approach) covers.
- No text, no labels, no icons inside any circle — just the shapes.
```

---

## Slide 6 — Our Contribution

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — a horizontal row of exactly 5 icon "cards", evenly
spaced with equal gaps, all the same size, vertically centered on the
same baseline. Each card is a rounded-square outline (thin stroke,
white fill inside) containing one simple centered icon:
1. (leftmost) Teal green #2FA88A shield outline with a simple
   checkmark inside — "verified detector".
2. Navy blue #2C3E93 small rounded rectangle with a simplified chip
   circuit pattern (a few short perpendicular lines at the corners) —
   "fine-tuned model".
3. (center) Neutral gray #7A7A7A stack of 2-3 flat rounded rectangles
   layered like books/documents — "knowledge base".
4. Orange #F2994A puzzle-piece outline (single jigsaw piece shape) —
   "per-issue fixing".
5. (rightmost) Navy blue #2C3E93 clipboard outline with 2-3 small
   checkmarks inside it in a vertical list — "real-world evaluation".
Keep every icon the same visual size and stroke weight so the row
looks balanced and uniform. No text anywhere.
```

---

## Slide 7 — AI Workflow / Pipeline

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — a horizontal flowchart of exactly 6 rounded rectangle
boxes, all the same size, arranged left to right in a single row,
evenly spaced, connected by thin navy blue arrows pointing rightward
between each consecutive box. Each box outline is thin, fill is very
light/white, with ONE simple centered icon per box, colored as follows:
1. (leftmost, gray #7A7A7A icon) small rounded rectangle with 2 thin
   horizontal lines inside — representing raw input code.
2. (navy #2C3E93 icon) magnifying glass — representing the detector
   scanning for issues.
3. (teal #2FA88A icon) a small key shape combined with a search
   magnifier outline — representing keyword extraction.
4. (orange #F2994A icon) a small stacked-cylinder database icon —
   representing knowledge retrieval.
5. (navy #2C3E93 icon) a funnel shape merging two small arrows into
   one — representing combining code and retrieved docs into a prompt.
6. (teal #2FA88A icon) a small 4-pointed sparkle/star shape —
   representing the AI generating the fix.
After box 6, one final small green #2FA88A checkmark circle icon
sits outside the last box, connected by one more thin arrow —
representing the final output. All 6 boxes must be equal width and
height, aligned on the same horizontal center line, arrows same length.
```

---

## Slide 8 — Why These Techniques

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — a simple flat balance scale icon, centered in the frame,
in navy blue #2C3E93: a vertical center post with a small triangular
base at the bottom, a horizontal beam balanced on top of the post, and
two thin strings hanging down from each end of the beam holding a
small flat circular pan on each side.
- On the LEFT pan: a small teal green #2FA88A feather icon (simple
  curved feather outline) resting on it — representing lightweight
  design.
- On the RIGHT pan: a small orange #F2994A gear icon (circle with 6
  teeth) resting on it — representing efficiency/performance.
- The beam sits perfectly level/horizontal (not tilted), implying a
  deliberate balanced tradeoff. Nothing else in the frame besides the
  scale itself. No text.
```

---

## Slide 9 — References

```
Style: flat minimal vector illustration for a tech presentation slide.
Clean geometric shapes, soft rounded corners (8-12px radius look),
thin consistent stroke weight (2-3px), no gradients, no drop shadows,
no photorealism, no 3D, no text/letters/numbers anywhere in the image.
Flat solid fills only. Generous white negative space — icons/shapes
should occupy roughly the center 60% of the frame, leaving margin on
all sides for slide text to be overlaid later outside the image area.
Color palette — use ONLY these colors:
  - Navy blue #2C3E93 (primary)
  - Teal green #2FA88A (secondary / positive)
  - Orange #F2994A (accent / warning / highlight)
  - Neutral gray #7A7A7A (muted / inactive)
  - White #FFFFFF (background, fully white, no texture)
16:9 landscape aspect ratio, centered composition, balanced symmetry.

Composition — two simple open-book icons placed side by side, evenly
spaced, same size, resting on the same horizontal baseline:
- LEFT book: outline in navy blue #2C3E93, drawn as a simple open-book
  silhouette (two curved page shapes meeting at a center spine line).
  A small triangular bookmark ribbon in orange #F2994A hangs from the
  top edge of the spine, overlapping slightly onto the right page.
- RIGHT book: outline in neutral gray #7A7A7A, same open-book shape.
  A small triangular bookmark ribbon in teal green #2FA88A hangs from
  its spine the same way.
Both books tilted slightly outward from each other (like a shallow V),
symmetric composition, plenty of white space around and between them.
No text, no lines suggesting printed words inside the pages — pages
are blank flat shapes.
```
