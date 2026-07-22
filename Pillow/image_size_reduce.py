from PIL import Image
from pathlib import Path

input_dir = Path("/Users/r/Pictures/in_photos")
output_dir = Path("/Users/r/Pictures/out_photos")
output_dir.mkdir(exist_ok=True)

max_size = (1600, 1600)  # change to whatever fits your upload limit
allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

for img_path in input_dir.iterdir():
    if img_path.suffix.lower() not in allowed_ext:
        continue

    try:
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            img.thumbnail(max_size)  # keeps aspect ratio

            out_path = output_dir / f"{img_path.stem}.jpg"
            img.save(out_path, "JPEG", quality=85, optimize=True)
            print(f"Saved: {out_path}")
    except Exception as e:
        print(f"Skipped {img_path.name}: {e}")