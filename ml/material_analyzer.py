"""
Optical & Physical Material Texture Analyzer.
Extracts distinctive optical, colorimetric, and surface reflectance features
to discriminate between Paper, Plastic, Metal, Glass, and Organic waste items.

Key Discriminators:
- Paper: High diffuse matte reflectance, low specular highlights, horizontal text/rule lines,
  fibrous texture entropy, kraft brown or matte white color space.
- Plastic: Strong localized specular glare / gloss hotspots, cylindrical highlight streaks,
  translucency/refraction contours, synthetic vibrant color accents, smooth polymer surface.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Tuple, Union
import numpy as np
from PIL import Image, ImageFilter, ImageOps


class MaterialAnalyzer:
    """
    Analyzes visual and optical properties of waste items to generate
    calibrated material likelihood priors.
    """

    @staticmethod
    def analyze_image(
        image_input: Union[bytes, io.BytesIO, str, Path, Image.Image, np.ndarray]
    ) -> Dict[str, float]:
        """
        Extracts material signatures and returns normalized likelihood scores
        for ['Plastic', 'Paper', 'Organic', 'Metal', 'Glass'].
        """
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, io.BytesIO):
            pil_img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            pil_img = image_input
        elif isinstance(image_input, np.ndarray):
            # If batch array (1, H, W, 3) or (H, W, 3) in [0, 1]
            arr = image_input.squeeze()
            if arr.max() <= 1.0:
                arr = (arr * 255.0).astype(np.uint8)
            pil_img = Image.fromarray(arr)
        else:
            return {"Plastic": 0.2, "Paper": 0.2, "Organic": 0.2, "Metal": 0.2, "Glass": 0.2}

        # Normalize image orientation and resize for fast analysis
        try:
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception:
            pass
        pil_img = pil_img.convert("RGB").resize((160, 160), Image.Resampling.BILINEAR)
        img_np = np.array(pil_img, dtype=np.float32)

        # Convert to Grayscale
        gray = 0.299 * img_np[:, :, 0] + 0.587 * img_np[:, :, 1] + 0.114 * img_np[:, :, 2]

        # ── 1. Specular Glare & Highlight Analysis (Plastic vs Paper) ───────────
        # Plastic, metal, and glass produce intense, localized specular glare (pixels > 238)
        # with sharp drop-offs. Diffuse paper or bright background is flat without high edge gradients.
        gy, gx = np.gradient(gray)
        gradient_mag = np.sqrt(gx**2 + gy**2)

        raw_bright = gray > 238
        raw_bright_ratio = float(np.mean(raw_bright))

        # A true specular hotspot is localized (< 35% of frame) AND has steep boundary drop-off
        if raw_bright_ratio < 0.35:
            specular_pixels = raw_bright & (gradient_mag > 15.0)
            specular_ratio = float(np.mean(specular_pixels))
            high_gradient_at_glare = float(np.mean(gradient_mag[specular_pixels])) if np.any(specular_pixels) else 0.0
        else:
            # High-key diffuse white scene (paper sheet or clean uniform background)
            specular_ratio = 0.005
            high_gradient_at_glare = 0.0

        # Cylindrical Specular Streak: Plastic bottles/cups often have a vertical highlight stripe
        # Compute vertical vs horizontal gradient asymmetry
        v_streak_score = float(np.mean(np.abs(gx)) / (np.mean(np.abs(gy)) + 1e-5))

        # ── 2. Text Line & Ruled Pattern Detection (Paper Signature) ───────────
        # Documents, newspapers, receipts, lined notebook paper, and corrugated cardboard
        # exhibit dense, periodic horizontal line edges.
        horiz_edges = np.abs(gy)
        horiz_projection = np.mean(horiz_edges, axis=1)  # 1D line along rows
        # High variance in row-wise horizontal edge projection signifies lines of text or ruling
        text_line_score = float(np.std(horiz_projection))

        # ── 3. Colorimetry & Chroma Analysis ────────────────────────────────────
        r, g, b = img_np[:, :, 0], img_np[:, :, 1], img_np[:, :, 2]
        mean_r, mean_g, mean_b = float(np.mean(r)), float(np.mean(g)), float(np.mean(b))

        # Cardboard / Kraft paper brown profile (Warm R > G > B with moderate saturation)
        is_kraft_brown = (mean_r > 130) and (mean_g > 95) and (mean_b < mean_r - 25) and (mean_r > mean_g + 15)

        # High-key matte white (Notebook paper, printer paper, receipts)
        # Uniform high brightness across R, G, B without high specular glare
        color_spread = max(abs(mean_r - mean_g), abs(mean_g - mean_b), abs(mean_r - mean_b))
        is_matte_white = (mean_r > 195) and (mean_g > 195) and (mean_b > 190) and (color_spread < 20) and (specular_ratio < 0.02)

        # PET / Plastic bottle tint (Light blue / cyan tint or high synthetic saturation)
        is_pet_cyan = (mean_b > mean_r + 15) and (mean_g > mean_r + 10) and (mean_b > 160)

        # Highly saturated synthetic polymer dye (caps, wrappers, shampoo containers)
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        saturation = np.where(max_c > 0, (max_c - min_c) / (max_c + 1e-5), 0.0)
        mean_sat = float(np.mean(saturation))

        # ── 4. Compute Prior Likelihood Scores ──────────────────────────────────
        paper_score = 1.0
        plastic_score = 1.0
        metal_score = 1.0
        glass_score = 1.0
        organic_score = 1.0

        # Paper Evidence:
        if is_kraft_brown:
            paper_score += 3.0  # Strong cardboard / kraft paper indicator
        if is_matte_white:
            paper_score += 2.6  # Strong office / notebook / receipt paper indicator
        if text_line_score > 1.2:
            paper_score += min(3.0, (text_line_score - 1.0) * 0.8)

        # If matte and diffuse (little to no specular glare), paper is favored over plastic
        if specular_ratio < 0.015 and not is_pet_cyan:
            paper_score += 1.2
            plastic_score *= 0.85

        # Plastic Evidence:
        # High specular glare with steep boundary gradient is hallmark of smooth plastic/film
        if specular_ratio > 0.012 and high_gradient_at_glare > 15.0:
            plastic_score += min(3.0, specular_ratio * 40.0)
            metal_score += min(1.5, specular_ratio * 15.0)
            paper_score *= 0.7  # Paper rarely has high-contrast specular hotspots

        if v_streak_score > 1.35 and specular_ratio > 0.008:
            plastic_score += 1.8  # Cylindrical bottle/cup highlight streak
            glass_score += 1.2

        if is_pet_cyan:
            plastic_score += 2.5  # Translucent light blue PET water bottle tint
            glass_score += 1.0
            paper_score *= 0.65

        if mean_sat > 0.40 and specular_ratio > 0.008:
            plastic_score += 1.6  # Glossy brightly colored plastic packaging / caps

        # Normalize to probability distribution
        raw_scores = np.array([plastic_score, paper_score, organic_score, metal_score, glass_score], dtype=np.float32)
        exp_scores = np.exp(raw_scores - np.max(raw_scores))
        probs = exp_scores / np.sum(exp_scores)

        categories = ["Plastic", "Paper", "Organic", "Metal", "Glass"]
        return {cat: float(probs[i]) for i, cat in enumerate(categories)}
