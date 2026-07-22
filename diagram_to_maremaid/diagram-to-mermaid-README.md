# 🖊️ Diagram to Mermaid Converter

A desktop app (Tkinter) for drawing a diagram by hand — boxes, circles, diamonds, arrows — and converting it into ready-to-use [Mermaid](https://mermaid.js.org/) code.

## What it does

1. Draw shapes on the canvas: rectangles, squares, circles, ellipses, diamonds, or plain text labels.
2. Connect them with arrows or lines.
3. Click **Generate Mermaid** — it reads your actual layout and produces a `graph TD` Mermaid diagram, with your connections and colors preserved.
4. Export as a `.md` file, copy the code, or preview it live in the browser.

## Modes

| Mode | What it lets you do |
|---|---|
| ✏️ Draw Shapes | Click and drag to place a new shape. Clicking an existing shape selects it (for quick edits) without starting a new one. |
| 🖱 Select/Move | Click a shape to select it, drag to move it, press **Delete** (or the Delete Selected button) to remove it. Click empty space to deselect. |

## Toolbar

- **Shapes** — pick what the next drag will draw.
- **Colors** — click a swatch to set the active color for new shapes; the selected one gets a dark ring around it.
- **Text** — type a label before drawing a shape (or double-click an existing shape to edit its label afterward).
- **Actions** — clear the canvas, delete the selected shape, generate/copy Mermaid code, export/import the diagram as JSON (so you can save and reopen your work).

## How shapes become Mermaid code

- Rectangles/squares → `["label"]`, circles/ellipses → `("label")`, diamonds → `{"label"}`.
- Each node gets an explicit `style` line using the color you picked, with the text color automatically chosen (black or white) for legibility — so the diagram looks right whether you're pasting it into a light or dark-themed viewer.
- **Arrows and lines are connectors, not nodes.** Each one is matched to whichever shape sits at its start and end point (with a bit of tolerance, so you don't have to pixel-perfectly touch the edge) and becomes a `-->` (arrow) or `---` (line) edge between those two nodes. A connector not touching two shapes is skipped, and the status bar tells you if that happened.
- Arrow direction is preserved exactly as drawn — dragging from B to A produces `B --> A`, not the reverse.

## Exporting

- **📋 Copy Code** — copies the Mermaid block to your clipboard.
- **👁 Preview** — opens the diagram in the Mermaid Live Editor in your browser.
- **💾 Save .md** — writes a Markdown file with a `# Diagram` heading and the fenced ```` ```mermaid ```` code block, ready to drop into a README or wiki page.
- **💾 Export JSON / 📂 Import JSON** — saves the raw shape data (positions, types, colors, text) so you can reopen and keep editing a diagram later, separate from the generated Mermaid code.
