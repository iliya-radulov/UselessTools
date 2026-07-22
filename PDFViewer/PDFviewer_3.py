import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from pdfjs_viewer import PDFViewerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader")
        self.resize(1024, 768)
        
        self.viewer = PDFViewerWidget()
        self.viewer.load_pdf("your_document.pdf")
        
        # Connect signals
        self.viewer.pdf_loaded.connect(lambda meta: print(f"Loaded: {meta['filename']}"))
        
        self.setCentralWidget(self.viewer)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())