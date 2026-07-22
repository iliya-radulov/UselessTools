# 🧵 String Art Pro — Real Size Export

Turns a photo into a circular pin-and-thread pattern, sized for real-world printing, with a step-by-step build sheet included.

## What it does

1. Upload a photo.
2. It's converted to grayscale, then a greedy algorithm picks a path of straight lines between pins around a circle, chosen so the pattern of "thread" approximates the darker areas of the image.
3. Export a print-ready PDF sized to your exact hoop diameter (not squeezed onto a fixed A4 page), plus a text file — both listing the full pin-by-pin sequence so you can physically string it.

## Controls

| Control | What it does |
|---|---|
| Preview canvas px | On-screen preview resolution only — doesn't affect the export |
| Pins | Number of pins around the circle (max 500) |
| Lines | How many thread segments to draw — more = finer detail, longer to compute |
| Thread width | Visual thickness of each line |
| Contrast / Sharpness | Pre-processing applied to the photo before the path is calculated |
| Remove background | Makes near-white areas transparent |
| Show pin numbers | Toggle the numbered labels around the circle |
| Diameter (cm) | Physical size of your hoop/board |
| DPI | Print resolution — combined with diameter, sets the export pixel size |

**Render** / **Apply filters** recompute the pattern from your current settings. Because the algorithm is deterministic, the same settings always produce the same pattern.

## Exporting

- **📄 Export PDF (Real Size)** — a PDF with the artwork at true physical size (page sized to your diameter, not cropped to A4), followed by extra pages listing the ordered pin sequence to follow when stringing.
- **🧾 Path as text** — the same pin sequence as a plain `.txt` file, handy to keep open on a phone or tablet while working.
- **🖨️ Print preview** — opens the current on-screen preview in a print dialog.

## How the pattern is generated

A "residual" (error-map) greedy algorithm:
- Starts by marking how much "darkness" each pixel of the photo needs.
- At each step, checks every valid pin (skipping near-neighbors and already-used connections) and picks whichever line removes the most remaining darkness.
- Subtracts that line's contribution from the map before the next step, so thread spreads across the whole image instead of piling onto one dark region.

If a result looks too sparse, try increasing **Lines** — this algorithm generally needs a higher line count than a naive random one to fully resolve an image, since darkness gets "used up" as lines are added.
