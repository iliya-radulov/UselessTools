# 🧵 String Art Pro — Real Size Export

Turns a photo into a circular pin-and-thread pattern, sized for real-world printing, with a step-by-step build sheet included.

## What it does

1. Upload a photo.
2. An algorithm picks a path of straight thread lines between pins around a circle, chosen so the pattern approximates the photo's dark/light areas.
3. Export a print-ready PDF sized to your exact hoop diameter (not squeezed onto a fixed A4 page), plus a text file — both listing the full pin-by-pin sequence so you can physically string it.

A design note on orientation: the app fits the **photo to the canvas** (crops/scales your image into the circle), rather than fitting the canvas to the photo's aspect ratio — the more common approach elsewhere. That's an intentional choice for this project, not an oversight, so a portrait or landscape photo will be center-cropped to a square before it's mapped onto the circular pin layout.

## Controls

| Control | What it does |
|---|---|
| Preview canvas px | On-screen preview resolution only — doesn't affect the export or the computed pattern |
| Pins | Number of pins around the circle (max 500) |
| Lines | The *maximum* number of thread segments to draw — the algorithm may stop earlier on its own (see below) |
| Thread width | Visual thickness of each line |
| Contrast / Sharpness | Pre-processing applied to the photo before the path is calculated |
| Remove background | Makes near-white areas transparent |
| Show pin numbers | Toggle the numbered labels around the circle |
| Diameter (cm) | Physical size of your hoop/board |
| DPI | Print resolution — combined with diameter, sets the export pixel size |

**Render** / **Apply filters** recompute the pattern from your current settings. The algorithm is deterministic — the same settings always produce the same pattern.

## Exporting

- **📄 Export PDF (Real Size)** — a PDF with the artwork at true physical size (page sized to your diameter, not cropped to A4), followed by extra pages listing the ordered pin sequence to follow when stringing.
- **🧾 Path as text** — the same pin sequence as a plain `.txt` file, handy to keep open on a phone or tablet while working.
- **🖨️ Print preview** — opens the current on-screen preview in a print dialog.

## How the pattern is generated

The current algorithm:

- Maintains a **simulated rendering** of the artwork (starts blank) alongside a **target** derived from the photo (how dark each pixel should end up).
- For every candidate pin-to-pin line, traces its exact pixel coverage using **Xiaolin Wu's anti-aliased line algorithm**, and scores it by how much it would reduce total *squared error* between the simulation and the target — not just "how dark are the pixels it crosses."
- Picks whichever candidate improves the picture the most, adds it, updates the simulation, and repeats.
- **Stops itself early** once no remaining line would improve the picture further, rather than forcing out however many lines the slider asked for. The status bar and both exports report however many lines actually got used.
- Runs the search on a fixed internal resolution independent of your preview size or export DPI, so pattern quality and generation time stay predictable no matter what you're eventually printing to. Larger settings (many pins, many lines) run in chunks with a live progress readout so the browser tab never freezes.

If a result looks too sparse, try raising the **Lines** cap — the squared-error model will use more of them if there's still room to improve, and stop on its own once there isn't.

## Credits

The pattern algorithm evolved through a few iterations, each borrowing ideas from existing open-source string art projects:

- **[grvlbit/stringart](https://github.com/grvlbit/stringart/blob/main/stringart/stringart.py)** — the move from a fixed per-line sample count to exact pixel-accurate line tracing (originally via Bresenham's algorithm), plus the idea of caching each pin-pair's traced path since a full search revisits most pairs many times over a run.
- **[kaspar98/StringArt](https://github.com/kaspar98/StringArt)** — the core scoring model currently in use: a simulated rendering scored against the target photo by squared-error improvement, anti-aliased line tracing (Xiaolin Wu's algorithm), and the natural early-stopping rule (halt once no candidate line improves the picture).

No code was copied directly from either project — both were read for their approach and reimplemented independently in JavaScript for this app's architecture (canvas-based, resolution-independent pattern computation, physical-size PDF export).

## Version history

| Version | What changed |
|---|---|
| v1 | Initial working app: upload, draw preview, PDF export, adjustable pins/lines/diameter/DPI. |
| v2 | Fixed PDF export (page now matches real diameter instead of being cropped to A4, no more DOM-screenshot/blank-page bug), fixed pin numbers rendering inside the circle, added the exported pin-sequence text/PDF pages, first pass at a residual-based (subtract-until-satisfied) greedy algorithm. |
| v3 | Replaced fixed-sample line scoring with exact Bresenham pixel tracing plus per-pin-pair caching, decoupled pattern computation from preview/export resolution, made generation async/chunked with a progress readout so large settings don't freeze the tab. |
| v4 *(current)* | Replaced the residual model with proper simulated-render + squared-error scoring, switched line tracing to anti-aliased Wu's algorithm, added natural early-stopping. |
