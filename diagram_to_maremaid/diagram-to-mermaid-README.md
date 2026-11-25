# 🖊️ Diagram to Mermaid Converter

A desktop app (Tkinter) for drawing a diagram by hand — boxes, circles, diamonds, arrows — and converting it into ready-to-use [Mermaid](https://mermaid.js.org/) code.

## What it does

1. Draw shapes on the canvas: rectangles, squares, circles, ellipses, diamonds, or plain text labels.
2. Connect them with arrows or lines.
3. Click **Generate Mermaid** (the code also updates after every change) — it reads your actual layout and produces a Mermaid flowchart, with your connections, labels and colors preserved.
4. Export as a `.md` file, copy the code, or preview it live in the browser.

## Modes

| Mode | What it lets you do |
|---|---|
| ✏️ Draw Shapes | Click and drag to place a new shape. With a box/circle/diamond tool, clicking an existing shape selects it instead of starting a new one. With the arrow, line and text tools a click always draws — so you can start an arrow on a shape and put text on top of one. |
| 🖱 Select/Move | Click a shape to select it, drag to move it — arrows and lines attached to it move along. Press **Delete** / **Backspace** (or the Delete Selected button) to remove it. Click empty space to deselect. |

## Toolbar

- **Shapes** — pick what the next drag will draw.
- **Colors** — click a swatch to set the active color for new shapes; the selected one gets a dark ring around it.
- **Text** — type a label before drawing a shape (or double-click an existing shape to edit its label afterward).
- **Actions** — clear the canvas, delete the selected shape, generate/copy Mermaid code, export/import the diagram as JSON (so you can save and reopen your work).

## How shapes become Mermaid code

- Rectangles/squares → `["label"]`, circles → `(("label"))`, ellipses → `(["label"])`, diamonds → `{"label"}`.
- Each node gets an explicit `style` line matching the canvas: light fill, a border in the color you picked, and dark text — so the diagram looks the same whether you paste it into a light or dark-themed viewer.
- **Text** placed inside a shape that has no label becomes that shape's label. Text placed on or next to an arrow/line becomes the label of that connection (`A -->|"yes"| B`). Any other text becomes a borderless note.
- The direction is chosen from your drawing: mostly horizontal arrows give `graph LR`, mostly vertical ones `graph TD`.
- Quotes and line breaks in labels are escaped, so they can't break the Mermaid code.
- **Arrows and lines are connectors, not nodes.** Each one is matched to whichever shape sits at its start and end point (with a bit of tolerance, so you don't have to pixel-perfectly touch the edge) and becomes a `-->` (arrow) or `---` (line) edge between those two nodes. A connector not touching two shapes is skipped, and the status bar tells you if that happened.
- Arrow direction is preserved exactly as drawn — dragging from B to A produces `B --> A`, not the reverse.

## Exporting

- **📋 Copy Code** — copies the Mermaid block to your clipboard.
- **👁 Preview** — opens the diagram in the Mermaid Live Editor in your browser (the link carries the diagram in the editor's compressed `#pako:` format).
- **💾 Save .md** — writes a Markdown file with a `# Diagram` heading and the fenced ```` ```mermaid ```` code block, ready to drop into a README or wiki page.
- **💾 Export JSON / 📂 Import JSON** — saves the raw shape data (positions, types, colors, text) so you can reopen and keep editing a diagram later, separate from the generated Mermaid code.

## Changes (November 2026)

- Arrows and lines can now start on top of a shape (before, that click selected the shape and the drag moved it).
- Text can be placed on a shape and becomes its label; text on an arrow becomes the edge label.
- Moving a shape moves its attached arrows and regenerates the code.
- Fixed crashes when selecting/deselecting arrows and lines (`unknown option "-outline"`).
- Squares, circles and free text now use their real drawn size when matching arrow ends.
- Preview link fixed (it was not in the format Mermaid Live understands).
- Node colors match the canvas; direction (TD/LR) follows the drawing; labels are escaped.
- Backspace deletes the selected shape (macOS).
