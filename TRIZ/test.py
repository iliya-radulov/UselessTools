# convert epub to PDF
import subprocess
from pathlib import Path

# Define the folder path
folder_path = Path("/pelevin-epub")

# Find and convert all epub files
for epub_file in folder_path.glob("*.epub"):
    # Create the output PDF file name
    pdf_file = epub_file.with_suffix(".pdf")
    
    # Run the Calibre ebook-convert tool
    try:
        subprocess.run(["ebook-convert", str(epub_file), str(pdf_file)], check=True)
        print(f"Converted: {epub_file.name}")
    except FileNotFoundError:
        print("Error: Calibre 'ebook-convert' tool is not installed on this system.")
        break
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {epub_file.name}: {e}")
