"""
Image Preprocessing Pipeline.
High-accuracy preprocessing with EXIF orientation auto-correction,
aspect-ratio preserving letterboxing, and color space standardization.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple, Union
import numpy as np
from PIL import Image, ImageOps

from config import config


def resize_with_aspect_ratio(
    img: Image.Image,
    target_size: Tuple[int, int] = (224, 224),
    bg_color: Tuple[int, int, int] = (245, 245, 245),
) -> Image.Image:
    """
    Resizes image preserving authentic aspect ratio using high-quality Lanczos resampling.
    Pads the remaining canvas borders with a neutral background color (letterboxing).
    Prevents physical shapes (tall bottles, cylindrical cans, flat boxes) from being squashed.
    """
    target_w, target_h = target_size
    img_w, img_h = img.size

    # Compute scaling factor to fit within target bounding box
    scale = min(target_w / img_w, target_h / img_h)
    new_w = max(1, int(img_w * scale))
    new_h = max(1, int(img_h * scale))

    # High-quality antialiasing resample
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Place resized image onto center of target canvas
    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized_img, (offset_x, offset_y))
    return canvas


def preprocess_image(
    image_input: Union[bytes, io.BytesIO, str, Path, Image.Image],
    target_size: Tuple[int, int] = config.image_target_size,
) -> np.ndarray:
    """
    Complete preprocessing pipeline:
    1. Decodes raw image bytes / stream / path.
    2. Auto-corrects EXIF orientation (crucial for iPhone & Android portrait photos).
    3. Converts color space to 3-channel RGB.
    4. Resizes with aspect-ratio preservation (letterboxing).
    5. Normalizes pixel values to [0.0, 1.0] float32.
    6. Expands batch dimension to (1, height, width, 3).
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.BytesIO):
        img = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        img = image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # 1. Correct smartphone camera orientation via EXIF tag
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # 2. Ensure standard 3-channel RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 3. Aspect-ratio preserving letterboxing (prevents object distortion)
    img_letterboxed = resize_with_aspect_ratio(img, target_size=target_size)

    # 4. Convert to float32 numpy array and normalize to [0, 1]
    img_array = np.array(img_letterboxed, dtype=np.float32) / 255.0

    # 5. Expand batch dimension: (H, W, C) -> (1, H, W, C)
    batch_array = np.expand_dims(img_array, axis=0)
    return batch_array
