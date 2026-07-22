import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import os

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Reader")
        self.root.geometry("900x700")
        
        self.current_page = 0
        self.total_pages = 0
        self.doc = None
        self.zoom = 1.0
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame with buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(top_frame, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        
        self.page_label = tk.Label(top_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        tk.Button(top_frame, text="◀ Previous", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        # Canvas for PDF display
        self.canvas = tk.Canvas(self.root, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
            
        try:
            self.doc = fitz.open(file_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.zoom = 1.0
            self.show_page()
            self.update_page_label()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open PDF: {e}")
            
    def show_page(self):
        if not self.doc:
            return
            
        page = self.doc[self.current_page]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_image = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
    def update_page_label(self):
        self.page_label.config(text=f"Page: {self.current_page + 1}/{self.total_pages}")
        
    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()
            self.update_page_label()
            
    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page()
            self.update_page_label()
            
    def zoom_in(self):
        self.zoom *= 1.2
        self.show_page()
        
    def zoom_out(self):
        self.zoom *= 0.8
        self.show_page()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewer(root)
    root.mainloop()