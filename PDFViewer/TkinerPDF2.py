from tkinter import Tk
from TkPdfWidget import PdfReader

tk = Tk()
tk.title("PDF Reader")
tk.geometry("800x600")

# Create PDF reader widget
reader = PdfReader(tk, width=700, height=550, fp="your_document.pdf")
reader.pack()

tk.mainloop()