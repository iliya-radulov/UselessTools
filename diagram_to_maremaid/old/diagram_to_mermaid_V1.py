import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import json
import os
import webbrowser
import math
from datetime import datetime

class DiagramApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Diagram to Mermaid Converter")
        self.root.geometry("1200x700")
        
        # Variables for drawing
        self.shapes = []
        self.current_shape = None
        self.start_x = None
        self.start_y = None
        self.selected_shape = None
        self.drag_data = {"x": 0, "y": 0}
        self.next_id = 1
        
        # Shape types
        self.shape_type = tk.StringVar(value="rectangle")
        self.shape_color = tk.StringVar(value="#3498db")
        self.shape_text = tk.StringVar()
        
        # Mode: "select" or "draw"
        self.mode = tk.StringVar(value="draw")
        
        # Setup UI
        self.setup_ui()
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_shape_double_click)
        self.canvas.bind("<Delete>", lambda e: self.delete_selected())
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Toolbar
        left_panel = ttk.Frame(main_frame, width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Scrollable toolbar
        toolbar_canvas = tk.Canvas(left_panel, highlightthickness=0)
        toolbar_scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=toolbar_canvas.yview)
        toolbar_frame = ttk.Frame(toolbar_canvas)
        
        toolbar_canvas.configure(yscrollcommand=toolbar_scrollbar.set)
        toolbar_canvas.pack(side="left", fill="both", expand=True)
        toolbar_scrollbar.pack(side="right", fill="y")
        
        toolbar_canvas.create_window((0, 0), window=toolbar_frame, anchor="nw", width=200)
        toolbar_frame.bind("<Configure>", lambda e: toolbar_canvas.configure(scrollregion=toolbar_canvas.bbox("all")))
        
        # Mode selection
        mode_frame = ttk.LabelFrame(toolbar_frame, text="Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(
            mode_frame,
            text="🖱 Select/Move",
            variable=self.mode,
            value="select"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="✏️ Draw Shapes",
            variable=self.mode,
            value="draw"
        ).pack(anchor=tk.W, pady=2)
        
        # Shape selection (only available in draw mode)
        shape_frame = ttk.LabelFrame(toolbar_frame, text="Shapes", padding=10)
        shape_frame.pack(fill=tk.X, pady=(0, 10))
        
        shapes = [
            ("▭ Rectangle", "rectangle"),
            ("○ Circle", "circle"),
            ("⬭ Ellipse", "ellipse"),
            ("▢ Square", "square"),
            ("◇ Diamond", "diamond"),
            ("━ Line", "line"),
            ("➜ Arrow", "arrow"),
            ("A Text", "text")
        ]
        
        self.shape_buttons = []
        for text, value in shapes:
            rb = ttk.Radiobutton(
                shape_frame, 
                text=text, 
                variable=self.shape_type, 
                value=value
            )
            rb.pack(anchor=tk.W, pady=1)
            self.shape_buttons.append(rb)
        
        # Color picker
        color_frame = ttk.LabelFrame(toolbar_frame, text="Colors", padding=10)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        colors = [
            ("Blue", "#3498db"),
            ("Red", "#e74c3c"),
            ("Green", "#2ecc71"),
            ("Yellow", "#f1c40f"),
            ("Orange", "#e67e22"),
            ("Purple", "#9b59b6"),
            ("Pink", "#e91e63"),
            ("Teal", "#1abc9c"),
            ("Black", "#2c3e50")
        ]
        
        color_grid = ttk.Frame(color_frame)
        color_grid.pack()
        
        row = 0
        col = 0
        for text, color in colors:
            btn = tk.Button(
                color_grid,
                bg=color,
                width=4,
                height=1,
                relief=tk.RAISED,
                command=lambda c=color: self.shape_color.set(c)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # Text input
        text_frame = ttk.LabelFrame(toolbar_frame, text="Text (for shapes)", padding=10)
        text_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(text_frame, textvariable=self.shape_text, width=20).pack(fill=tk.X)
        
        # Actions
        action_frame = ttk.LabelFrame(toolbar_frame, text="Actions", padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="🗑 Clear All", command=self.clear_canvas).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="❌ Delete Selected", command=self.delete_selected).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🔄 Generate Mermaid", command=self.generate_mermaid).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="💾 Export JSON", command=self.export_json).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="📂 Import JSON", command=self.import_json).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="📋 Copy Code", command=self.copy_code).pack(fill=tk.X, pady=2)
        
        # Canvas - Center
        canvas_frame = ttk.LabelFrame(main_frame, text="Diagram Canvas", padding=5)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            width=600,
            height=500,
            cursor="cross"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add grid
        self.draw_grid()
        
        # Right panel - Mermaid code
        right_panel = ttk.Frame(main_frame, width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        mermaid_frame = ttk.LabelFrame(right_panel, text="Mermaid Code", padding=5)
        mermaid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Buttons for mermaid
        mermaid_buttons = ttk.Frame(mermaid_frame)
        mermaid_buttons.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(mermaid_buttons, text="📋 Copy Code", command=self.copy_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(mermaid_buttons, text="👁 Preview", command=self.preview_mermaid).pack(side=tk.LEFT, padx=2)
        ttk.Button(mermaid_buttons, text="💾 Save .md", command=self.save_markdown).pack(side=tk.LEFT, padx=2)
        
        self.mermaid_text = scrolledtext.ScrolledText(
            mermaid_frame,
            wrap=tk.WORD,
            height=20,
            font=("Consolas", 10)
        )
        self.mermaid_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready - Select 'Draw' mode to add shapes, 'Select' mode to move/delete", 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def draw_grid(self):
        """Draw a subtle grid on the canvas"""
        for i in range(0, 1000, 20):
            self.canvas.create_line(i, 0, i, 800, fill="#e0e0e0", tags="grid")
            self.canvas.create_line(0, i, 1000, i, fill="#e0e0e0", tags="grid")
        # Bring grid to back
        self.canvas.tag_lower("grid")
        
    def on_canvas_click(self, event):
        # Check if we're in select mode
        if self.mode.get() == "select":
            # Try to select a shape
            item = self.canvas.find_closest(event.x, event.y)
            if item:
                # Find which shape this item belongs to (match by actual
                # canvas item id only — shape_data["id"] is just a display
                # counter and can coincidentally equal an unrelated canvas
                # item's id, e.g. a grid line's)
                for shape_data in self.shapes:
                    if any(part == item[0] for part in shape_data["parts"]):
                        self.selected_shape = shape_data
                        self.drag_data["x"] = event.x
                        self.drag_data["y"] = event.y
                        self.highlight_shape(shape_data)
                        self.status_bar.config(text=f"Selected: {shape_data['type']} (ID: {shape_data['id']})")
                        # Change cursor to indicate selection
                        self.canvas.config(cursor="hand2")
                        return
            # Click on empty space - deselect
            self.selected_shape = None
            self.clear_highlight()
            self.canvas.config(cursor="arrow")
            self.status_bar.config(text="Deselected")
            return
        
        # Draw mode - check if clicking on existing shape to select it (for convenience)
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            for shape_data in self.shapes:
                if any(part == item[0] for part in shape_data["parts"]):
                    # Allow selection even in draw mode for convenience
                    self.selected_shape = shape_data
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
                    self.highlight_shape(shape_data)
                    self.status_bar.config(text=f"Selected: {shape_data['type']} (Click on canvas to deselect)")
                    return
        
        # Start drawing new shape
        self.start_x = event.x
        self.start_y = event.y
        self.current_shape = None
        # Deselect any previously selected shape
        self.selected_shape = None
        self.clear_highlight()
        
    def on_canvas_drag(self, event):
        if self.selected_shape:
            # Move selected shape
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # Move all parts of the shape
            for part in self.selected_shape["parts"]:
                self.canvas.move(part, dx, dy)
            
            # Update coordinates
            self.selected_shape["x1"] += dx
            self.selected_shape["y1"] += dy
            self.selected_shape["x2"] += dx
            self.selected_shape["y2"] += dy
            
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            return
            
        # Only draw in draw mode
        if self.mode.get() != "draw":
            return
            
        if self.start_x is None or self.start_y is None:
            return
            
        # Preview shape while dragging
        if self.current_shape:
            # Remove preview
            for part in self.current_shape["parts"]:
                self.canvas.delete(part)
            self.shapes.remove(self.current_shape)
        
        # Create preview shape
        shape_type = self.shape_type.get()
        color = self.shape_color.get()
        text = self.shape_text.get()
        
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        shape = self.create_shape(shape_type, x1, y1, x2, y2, color, text, preview=True)
        if shape:
            self.current_shape = shape
            self.shapes.append(shape)
    
    def on_canvas_release(self, event):
        if self.selected_shape:
            self.selected_shape = None
            self.status_bar.config(text="Shape moved")
            return
            
        if self.start_x is None or self.start_y is None:
            return
        
        # Only finalize in draw mode
        if self.mode.get() != "draw":
            self.start_x = None
            self.start_y = None
            return
            
        # Finalize shape
        if self.current_shape:
            # Remove preview flag and finalize
            self.current_shape["preview"] = False
            self.current_shape = None
            self.status_bar.config(text=f"Added: {self.shape_type.get()}")
            self.generate_mermaid()
        else:
            # Create final shape
            shape_type = self.shape_type.get()
            color = self.shape_color.get()
            text = self.shape_text.get()
            
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            
            # If click without drag or too small, create a default size
            if abs(x2 - x1) < 10 and abs(y2 - y1) < 10:
                if shape_type == "text":
                    x2, y2 = x1 + 100, y1 + 30
                else:
                    x2, y2 = x1 + 80, y1 + 60
            
            shape = self.create_shape(shape_type, x1, y1, x2, y2, color, text)
            if shape:
                self.shapes.append(shape)
                self.status_bar.config(text=f"Added: {shape_type}")
                self.generate_mermaid()
        
        self.start_x = None
        self.start_y = None
        self.current_shape = None
        
        # Clear text after adding (except for text shapes)
        if self.shape_type.get() != "text":
            self.shape_text.set("")
    
    def highlight_shape(self, shape_data):
        """Highlight selected shape"""
        self.clear_highlight()
        for part in shape_data["parts"]:
            if self.canvas.type(part) != "text":
                self.canvas.itemconfig(part, width=3)
                self.canvas.itemconfig(part, outline="#e74c3c")
            else:
                # Highlight text with a background
                self.canvas.itemconfig(part, fill="#e74c3c")
    
    def clear_highlight(self):
        """Clear all highlights"""
        for shape in self.shapes:
            for part in shape["parts"]:
                if self.canvas.type(part) != "text":
                    self.canvas.itemconfig(part, width=2)
                    self.canvas.itemconfig(part, outline=shape["color"])
                else:
                    self.canvas.itemconfig(part, fill=shape["color"])
    
    def create_shape(self, shape_type, x1, y1, x2, y2, color, text="", preview=False):
        """Create a shape on the canvas and return its data"""
        # Lines and arrows are directional — (x1,y1) must stay the true drag
        # start and (x2,y2) the true drag end, or the arrowhead ends up
        # pointing the wrong way. Only bounding-box shapes get their
        # coordinates sorted.
        if shape_type not in ("line", "arrow"):
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
        shape_data = {
            "id": self.next_id,
            "type": shape_type,
            "color": color,
            "text": text,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "preview": preview,
            "parts": []
        }
        self.next_id += 1
        
        # Calculate center and dimensions
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        
        # Create fill color (lighter version)
        fill_color = self.lighten_color(color) if not preview else "#ecf0f1"
        
        if shape_type == "rectangle":
            id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2, fill=fill_color)
            shape_data["parts"].append(id)
            if text:
                id_text = self.canvas.create_text(cx, cy, text=text, font=("Arial", 10))
                shape_data["parts"].append(id_text)
                
        elif shape_type == "square":
            size = max(w, h)
            id = self.canvas.create_rectangle(x1, y1, x1 + size, y1 + size, outline=color, width=2, fill=fill_color)
            shape_data["parts"].append(id)
            if text:
                id_text = self.canvas.create_text(x1 + size/2, y1 + size/2, text=text, font=("Arial", 10))
                shape_data["parts"].append(id_text)
                
        elif shape_type == "circle":
            r = max(w, h) / 2
            id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2, fill=fill_color)
            shape_data["parts"].append(id)
            if text:
                id_text = self.canvas.create_text(cx, cy, text=text, font=("Arial", 10))
                shape_data["parts"].append(id_text)
                
        elif shape_type == "ellipse":
            id = self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=2, fill=fill_color)
            shape_data["parts"].append(id)
            if text:
                id_text = self.canvas.create_text(cx, cy, text=text, font=("Arial", 10))
                shape_data["parts"].append(id_text)
                
        elif shape_type == "diamond":
            points = [
                cx, y1,
                x2, cy,
                cx, y2,
                x1, cy
            ]
            id = self.canvas.create_polygon(points, outline=color, width=2, fill=fill_color)
            shape_data["parts"].append(id)
            if text:
                id_text = self.canvas.create_text(cx, cy, text=text, font=("Arial", 10))
                shape_data["parts"].append(id_text)
                
        elif shape_type == "line":
            id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
            shape_data["parts"].append(id)
            
        elif shape_type == "arrow":
            # Calculate arrow
            angle = math.atan2(y2 - y1, x2 - x1)
            arrow_len = 12
            arrow_angle = math.pi / 6
            
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            
            id1 = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
            shape_data["parts"].append(id1)
            id2 = self.canvas.create_polygon(x2, y2, x3, y3, x4, y4, fill=color)
            shape_data["parts"].append(id2)
            
        elif shape_type == "text":
            id = self.canvas.create_text(x1, y1, text=text or "Text", font=("Arial", 12), fill=color)
            shape_data["parts"].append(id)
            # Store text position
            shape_data["x1"] = x1
            shape_data["y1"] = y1
            shape_data["x2"] = x1 + 50
            shape_data["y2"] = y1 + 20
        
        return shape_data if shape_data["parts"] else None
    
    def lighten_color(self, color):
        """Create a lighter version of a color for fill"""
        color_map = {
            "#3498db": "#d6eaf8",
            "#e74c3c": "#fadbd8",
            "#2ecc71": "#d5f5e3",
            "#f1c40f": "#fef9e7",
            "#e67e22": "#fdebd0",
            "#9b59b6": "#ebdef0",
            "#e91e63": "#fce4ec",
            "#1abc9c": "#d1f2eb",
            "#2c3e50": "#d5d8dc"
        }
        return color_map.get(color, "#ecf0f1")
    
    def on_shape_double_click(self, event):
        """Double click on shape to edit text"""
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            # Check if we clicked on a text item
            for shape_data in self.shapes:
                if any(part == item[0] for part in shape_data["parts"]):
                    if shape_data["type"] in ["rectangle", "circle", "ellipse", "square", "diamond", "text"]:
                        new_text = simpledialog.askstring("Edit Text", "Enter new text:", initialvalue=shape_data.get("text", ""))
                        if new_text is not None:
                            shape_data["text"] = new_text
                            # Update text on canvas
                            for part in shape_data["parts"]:
                                if self.canvas.type(part) == "text":
                                    self.canvas.itemconfig(part, text=new_text)
                            self.generate_mermaid()
                    break
    
    def clear_canvas(self):
        if messagebox.askyesno("Clear", "Clear all shapes?"):
            self.canvas.delete("all")
            self.draw_grid()
            self.shapes = []
            self.next_id = 1
            self.selected_shape = None
            self.mermaid_text.delete(1.0, tk.END)
            self.status_bar.config(text="Canvas cleared")
    
    def delete_selected(self):
        if self.selected_shape:
            for part in self.selected_shape["parts"]:
                self.canvas.delete(part)
            self.shapes.remove(self.selected_shape)
            deleted_id = self.selected_shape["id"]
            self.selected_shape = None
            self.clear_highlight()
            self.generate_mermaid()
            self.status_bar.config(text=f"Shape {deleted_id} deleted")
            self.canvas.config(cursor="arrow")
        else:
            messagebox.showinfo("No Selection", 
                "Please select a shape first:\n"
                "1. Switch to 'Select' mode\n"
                "2. Click on a shape to select it\n"
                "3. Press Delete key or click Delete Selected")
    
    def find_node_at_point(self, px, py, node_shapes, node_ids, tolerance=15, max_snap_dist=60):
        """Return the Mermaid node id whose shape sits under/near (px, py).

        First tries an actual bounding-box hit (with a small tolerance, since
        clicking exactly on a shape's edge with a mouse is hard). Falls back
        to "nearest shape center" so an arrow endpoint dropped a little off
        target still connects to the shape you meant.
        """
        # 1) direct hit (with tolerance) on a shape's bounding box
        for shape, node_id in zip(node_shapes, node_ids):
            x1, y1, x2, y2 = shape["x1"], shape["y1"], shape["x2"], shape["y2"]
            if (x1 - tolerance) <= px <= (x2 + tolerance) and (y1 - tolerance) <= py <= (y2 + tolerance):
                return node_id

        # 2) fall back to nearest shape center, within a reasonable distance
        best_id, best_dist = None, float("inf")
        for shape, node_id in zip(node_shapes, node_ids):
            cx = (shape["x1"] + shape["x2"]) / 2
            cy = (shape["y1"] + shape["y2"]) / 2
            dist = math.hypot(px - cx, py - cy)
            if dist < best_dist:
                best_dist, best_id = dist, node_id
        if best_id is not None and best_dist <= max_snap_dist:
            return best_id
        return None

    def generate_mermaid(self):
        """Generate Mermaid code from shapes"""
        # Remove preview shapes
        shapes = [s for s in self.shapes if not s.get("preview", False)]

        if not shapes:
            self.mermaid_text.delete(1.0, tk.END)
            self.mermaid_text.insert(1.0, "# No shapes to convert\n# Draw shapes on the canvas to generate Mermaid code")
            return

        # Lines/arrows are CONNECTORS, not diagram nodes — keep them separate
        node_shapes = [s for s in shapes if s["type"] not in ("line", "arrow")]
        connector_shapes = [s for s in shapes if s["type"] in ("line", "arrow")]

        if not node_shapes:
            self.mermaid_text.delete(1.0, tk.END)
            self.mermaid_text.insert(1.0, "# No shapes to convert\n# Draw a box/circle/etc. (not just arrows) to generate Mermaid code")
            return

        # Build Mermaid code
        mermaid_code = "```mermaid\ngraph TD\n"
        mermaid_code += "    %% Auto-generated diagram\n"

        # Create nodes
        node_ids = []
        for i, shape in enumerate(node_shapes):
            shape_type = shape["type"]
            text = shape.get("text") or f"Node{i+1}"
            node_id = f"N{i+1}"

            # Sanitize text for Mermaid
            text = text.replace('"', "'").replace('\n', ' ')

            if shape_type in ["rectangle", "square"]:
                mermaid_code += f"    {node_id}[\"{text}\"]\n"
            elif shape_type in ["circle", "ellipse"]:
                mermaid_code += f"    {node_id}(\"{text}\")\n"
            elif shape_type == "diamond":
                mermaid_code += f"    {node_id}{{\"{text}\"}}\n"
            else:  # text
                mermaid_code += f"    {node_id}[\"{text}\"]\n"

            node_ids.append(node_id)

        # Connections come from where you actually drew arrows/lines,
        # matched to whichever node shape sits at each endpoint.
        edges = []
        skipped = 0
        for shape in connector_shapes:
            start_id = self.find_node_at_point(shape["x1"], shape["y1"], node_shapes, node_ids)
            end_id = self.find_node_at_point(shape["x2"], shape["y2"], node_shapes, node_ids)
            if start_id and end_id and start_id != end_id:
                arrow_syntax = "-->" if shape["type"] == "arrow" else "---"
                edges.append(f"    {start_id} {arrow_syntax} {end_id}\n")
            else:
                skipped += 1

        if edges:
            mermaid_code += "\n    %% Connections\n"
            mermaid_code += "".join(edges)

        mermaid_code += "```"

        self.mermaid_text.delete(1.0, tk.END)
        self.mermaid_text.insert(1.0, mermaid_code)

        status = f"Mermaid code generated ({len(node_ids)} nodes, {len(edges)} connections)"
        if skipped:
            status += f" — {skipped} arrow/line(s) not touching two shapes were skipped"
        self.status_bar.config(text=status)
    
    def copy_code(self):
        code = self.mermaid_text.get(1.0, tk.END).strip()
        if code and "No shapes" not in code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status_bar.config(text="Code copied to clipboard!")
        else:
            messagebox.showinfo("No Code", "Generate Mermaid code first by drawing shapes")
    
    def preview_mermaid(self):
        """Open Mermaid code in browser"""
        code = self.mermaid_text.get(1.0, tk.END).strip()
        if code and "No shapes" not in code and code != "# No shapes to convert":
            # Open in browser using Mermaid live editor
            import urllib.parse
            # Just the mermaid code without the ``` markers
            mermaid_code = code.replace("```mermaid\n", "").replace("```", "").strip()
            encoded = urllib.parse.quote(mermaid_code)
            url = f"https://mermaid.live/edit#pako:{encoded}"
            webbrowser.open(url)
            self.status_bar.config(text="Opening Mermaid preview in browser...")
        else:
            messagebox.showinfo("No Code", "Generate Mermaid code first by drawing shapes")
    
    def save_markdown(self):
        """Save diagram as markdown file with Mermaid code"""
        code = self.mermaid_text.get(1.0, tk.END).strip()
        if code and "No shapes" not in code:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("# Diagram\n\n")
                    f.write(code)
                    f.write("\n\n---\n*Generated by Diagram to Mermaid Converter*")
                self.status_bar.config(text=f"Saved to {file_path}")
        else:
            messagebox.showinfo("No Code", "Generate Mermaid code first by drawing shapes")
    
    def export_json(self):
        """Export shapes as JSON"""
        if not self.shapes:
            messagebox.showinfo("No Shapes", "Draw some shapes first!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            # Export shape data (skip preview shapes)
            export_data = []
            for shape in self.shapes:
                if not shape.get("preview", False):
                    export_data.append({
                        "type": shape["type"],
                        "color": shape["color"],
                        "text": shape.get("text", ""),
                        "x1": shape["x1"],
                        "y1": shape["y1"],
                        "x2": shape["x2"],
                        "y2": shape["y2"]
                    })
            
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            self.status_bar.config(text=f"Exported {len(export_data)} shapes to {file_path}")
    
    def import_json(self):
        """Import shapes from JSON"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r") as f:
                    import_data = json.load(f)
                
                # Clear current canvas
                self.canvas.delete("all")
                self.draw_grid()
                self.shapes = []
                self.next_id = 1
                self.selected_shape = None
                
                # Import shapes
                imported = 0
                for data in import_data:
                    shape = self.create_shape(
                        data["type"],
                        data["x1"], data["y1"],
                        data["x2"], data["y2"],
                        data["color"],
                        data.get("text", "")
                    )
                    if shape:
                        self.shapes.append(shape)
                        imported += 1
                
                self.generate_mermaid()
                self.status_bar.config(text=f"Imported {imported} shapes from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")

def main():
    root = tk.Tk()
    app = DiagramApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    
