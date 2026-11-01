import shutil
from pathlib import Path
from PIL import Image, ImageDraw

def process_logo():
    src = Path("/Users/kushagrakantrai9hmail.com/.gemini/antigravity/brain/5c2af742-adb7-46c6-8678-b356a6621bcb/rightbin_app_logo_1793537109315.jpg")
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(src).convert("RGBA")

    # 1. Save full-res master logo
    master_path = assets_dir / "rightbin_logo.png"
    img.save(master_path, "PNG")

    # 2. Generate smooth 512x512 squircle app icon
    size = 512
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Rounded corners mask with gentle antialiasing
    scale = 4
    mask = Image.new("L", (size * scale, size * scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size * scale, size * scale], radius=110 * scale, fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)

    app_icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    app_icon.paste(resized, (0, 0), mask=mask)
    
    app_icon_path = assets_dir / "app_icon.png"
    app_icon.save(app_icon_path, "PNG")

    # 3. Save as logo.png
    logo_path = assets_dir / "logo.png"
    app_icon.save(logo_path, "PNG")

    # 4. Save 64x64 favicon
    favicon_path = assets_dir / "favicon.png"
    app_icon.resize((64, 64), Image.Resampling.LANCZOS).save(favicon_path, "PNG")

    print(f"Master logo: {master_path}")
    print(f"App icon: {app_icon_path}")
    print(f"Logo: {logo_path}")
    print(f"Favicon: {favicon_path}")

if __name__ == "__main__":
    process_logo()
