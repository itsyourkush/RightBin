"""
RightBin - Official Logo and App Icon Generator
Renders a modern, high-definition, 512x512 app icon & logo for 'RightBin':
- "Wet or Dry, Always Right." theme
- Verification checkmark fused with dual-stream smart bin and recycling infinity loop
- 4 color-coded waste segregation nodes (Green=Organic/Wet, Blue=Dry/Recyclable, Amber=Metal, Cyan=E-Waste)
- AI Vision scanner brackets in neon cyan
- "RIGHTBIN" typography badge
- Glossy 3D glassmorphic finish & squircle silhouette
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 512
PADDING = 40
ICON_SIZE = SIZE - PADDING * 2

def create_rounded_mask(size, radius):
    """Creates a high-precision anti-aliased rounded rectangle mask."""
    scale = 4
    mask = Image.new("L", (size[0] * scale, size[1] * scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0] * scale, size[1] * scale], radius=radius * scale, fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)

def generate_rightbin_logo():
    output_dir = Path(__file__).resolve().parent.parent / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Base canvas (RGBA with transparency for shadow)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # 2. Ambient drop shadow behind squircle
    shadow_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_box = [PADDING + 6, PADDING + 18, SIZE - PADDING - 6, SIZE - PADDING + 28]
    shadow_draw.rounded_rectangle(shadow_box, radius=96, fill=(2, 35, 25, 175))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=22))
    canvas.alpha_composite(shadow_img)

    # 3. Squircle body with rich multi-stop gradient
    body = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    body_draw = ImageDraw.Draw(body)

    for y in range(ICON_SIZE):
        for x in range(ICON_SIZE):
            diag = (x * 0.75 + y * 1.25) / (ICON_SIZE * 2.0)
            dx = (x - ICON_SIZE * 0.48) / (ICON_SIZE * 0.5)
            dy = (y - ICON_SIZE * 0.28) / (ICON_SIZE * 0.5)
            rad = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy))

            # Blend from deep forest jade (0x04, 0x43, 0x32) to vivid emerald (0x10, 0xB9, 0x81) to cyan
            r = int(4 * (1 - diag) + 16 * diag + 30 * (rad ** 2))
            g = int(67 * (1 - diag) + 185 * diag + 65 * (rad ** 2))
            b = int(50 * (1 - diag) + 140 * diag + 85 * (rad ** 2))

            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            body_draw.point((x, y), fill=(r, g, b, 255))

    squircle_mask = create_rounded_mask((ICON_SIZE, ICON_SIZE), radius=92)
    body.putalpha(squircle_mask)

    # 4. Tech Grid & Radar Pulse overlay
    tech_overlay = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    tech_draw = ImageDraw.Draw(tech_overlay)
    cx, cy = ICON_SIZE // 2, ICON_SIZE // 2 - 24  # Shift center slightly up for bottom badge

    # Radar rings
    for r_ring in [55, 105, 155]:
        tech_draw.ellipse(
            [cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring],
            outline=(255, 255, 255, 26),
            width=2,
        )

    # Diagonal tech ticks
    for angle_deg in range(0, 360, 45):
        rad = math.radians(angle_deg)
        x1 = cx + math.cos(rad) * 145
        y1 = cy + math.sin(rad) * 145
        x2 = cx + math.cos(rad) * 160
        y2 = cy + math.sin(rad) * 160
        tech_draw.line([(x1, y1), (x2, y2)], fill=(6, 214, 160, 120), width=3)

    body.alpha_composite(tech_overlay)

    # 5. AI Vision Scanner Brackets in 4 corners
    emblem = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    emblem_draw = ImageDraw.Draw(emblem)

    b_pad = 58
    b_len = 34
    b_w = 6
    b_color = (0, 245, 212, 235)  # Neon Cyan-Teal

    # Top-Left Bracket
    emblem_draw.line([(b_pad, b_pad), (b_pad + b_len, b_pad)], fill=b_color, width=b_w)
    emblem_draw.line([(b_pad, b_pad), (b_pad, b_pad + b_len)], fill=b_color, width=b_w)
    # Top-Right Bracket
    emblem_draw.line([(ICON_SIZE - b_pad, b_pad), (ICON_SIZE - b_pad - b_len, b_pad)], fill=b_color, width=b_w)
    emblem_draw.line([(ICON_SIZE - b_pad, b_pad), (ICON_SIZE - b_pad, b_pad + b_len)], fill=b_color, width=b_w)
    # Bottom-Left Bracket
    emblem_draw.line([(b_pad, ICON_SIZE - b_pad - 60), (b_pad + b_len, ICON_SIZE - b_pad - 60)], fill=b_color, width=b_w)
    emblem_draw.line([(b_pad, ICON_SIZE - b_pad - 60), (b_pad, ICON_SIZE - b_pad - 60 - b_len)], fill=b_color, width=b_w)
    # Bottom-Right Bracket
    emblem_draw.line([(ICON_SIZE - b_pad, ICON_SIZE - b_pad - 60), (ICON_SIZE - b_pad - b_len, ICON_SIZE - b_pad - 60)], fill=b_color, width=b_w)
    emblem_draw.line([(ICON_SIZE - b_pad, ICON_SIZE - b_pad - 60), (ICON_SIZE - b_pad, ICON_SIZE - b_pad - 60 - b_len)], fill=b_color, width=b_w)

    # 6. Central RightBin Emblem: White Glowing Circular Plaque
    plaque_r = 85
    emblem_draw.ellipse(
        [cx - plaque_r, cy - plaque_r, cx + plaque_r, cy + plaque_r],
        fill=(255, 255, 255, 245),
        outline=(16, 185, 129, 255),
        width=5,
    )

    # 7. Draw the "Right" Verification Green Checkmark ✓
    chk_start = (cx - 40, cy - 5)
    chk_mid = (cx - 10, cy + 28)
    chk_end = (cx + 42, cy - 32)

    emblem_draw.line([chk_start, chk_mid], fill=(4, 120, 87, 255), width=18)
    emblem_draw.line([chk_mid, chk_end], fill=(4, 120, 87, 255), width=18)
    emblem_draw.line([chk_start, chk_mid], fill=(16, 185, 129, 255), width=12)
    emblem_draw.line([chk_mid, chk_end], fill=(16, 185, 129, 255), width=12)

    emblem_draw.line([(cx - 38, cy - 5), (cx - 10, cy + 25)], fill=(240, 253, 244, 255), width=4)
    emblem_draw.line([(cx - 10, cy + 25), (cx + 40, cy - 30)], fill=(240, 253, 244, 255), width=4)

    emblem_draw.ellipse([chk_start[0] - 6, chk_start[1] - 6, chk_start[0] + 6, chk_start[1] + 6], fill=(16, 185, 129, 255))
    emblem_draw.ellipse([chk_end[0] - 6, chk_end[1] - 6, chk_end[0] + 6, chk_end[1] + 6], fill=(16, 185, 129, 255))

    # 8. 4 Color-Coded Segregation Nodes (Green=Wet, Blue=Dry, Yellow=Metal, Cyan=E-Waste)
    orbit_r = 112
    nodes = [
        (215, (16, 185, 129, 255), "Wet"),     # Green
        (325, (2, 132, 199, 255), "Dry"),      # Blue
        (85,  (245, 158, 11, 255), "Metal"),   # Gold/Yellow
        (145, (6, 182, 212, 255), "E-Waste"),  # Cyan
    ]

    for angle_deg, color, _ in nodes:
        rad = math.radians(angle_deg)
        nx = cx + math.cos(rad) * orbit_r
        ny = cy + math.sin(rad) * orbit_r

        emblem_draw.ellipse([nx - 15, ny - 15, nx + 15, ny + 15], fill=(255, 255, 255, 220))
        emblem_draw.ellipse([nx - 11, ny - 11, nx + 11, ny + 11], fill=color)
        emblem_draw.ellipse([nx - 4, ny - 6, nx + 3, ny + 1], fill=(255, 255, 255, 230))

    glow = emblem.filter(ImageFilter.GaussianBlur(radius=6))
    body.alpha_composite(glow)
    body.alpha_composite(emblem)

    # 9. Bottom "RIGHTBIN" Brand Pill Badge
    pill_img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    pill_draw = ImageDraw.Draw(pill_img)

    pill_w = 260
    pill_h = 52
    pill_x0 = (ICON_SIZE - pill_w) // 2
    pill_y0 = ICON_SIZE - 78
    pill_box = [pill_x0, pill_y0, pill_x0 + pill_w, pill_y0 + pill_h]

    pill_draw.rounded_rectangle(pill_box, radius=24, fill=(6, 44, 32, 240), outline=(52, 211, 153, 230), width=3)

    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 22)
    except Exception:
        font = ImageFont.load_default()

    brand_text = "RIGHTBIN"
    bbox = pill_draw.textbbox((0, 0), brand_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = pill_x0 + (pill_w - tw) // 2
    ty = pill_y0 + (pill_h - th) // 2 - 2

    pill_draw.text((tx, ty + 1), brand_text, font=font, fill=(0, 0, 0, 140))
    pill_draw.text((tx, ty), brand_text, font=font, fill=(255, 255, 255, 255))

    body.alpha_composite(pill_img)

    # 10. Glassmorphism Top-Rim Gloss Sheen
    gloss = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    gloss_draw = ImageDraw.Draw(gloss)
    gloss_draw.ellipse(
        [-ICON_SIZE * 0.2, -ICON_SIZE * 0.45, ICON_SIZE * 1.2, ICON_SIZE * 0.55],
        fill=(255, 255, 255, 45),
    )
    gloss.putalpha(squircle_mask)
    body.alpha_composite(gloss)

    # 11. Subtle Rim Stroke
    rim = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    rim_draw = ImageDraw.Draw(rim)
    rim_draw.rounded_rectangle(
        [1, 1, ICON_SIZE - 2, ICON_SIZE - 2],
        radius=92,
        outline=(255, 255, 255, 95),
        width=3,
    )
    body.alpha_composite(rim)

    # 12. Composite squircle onto shadow canvas
    canvas.alpha_composite(body, (PADDING, PADDING))

    # 13. Save logo and icons
    icon_path_png = output_dir / "app_icon.png"
    canvas.save(icon_path_png, "PNG")

    logo_path = output_dir / "logo.png"
    canvas.save(logo_path, "PNG")

    favicon_path = output_dir / "favicon.png"
    canvas.resize((64, 64), Image.Resampling.LANCZOS).save(favicon_path, "PNG")

    print(f"Generated RightBin App Icon: {icon_path_png}")
    print(f"Updated Logo: {logo_path}")
    print(f"Generated Favicon: {favicon_path}")

if __name__ == "__main__":
    generate_rightbin_logo()
