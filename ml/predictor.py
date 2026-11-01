"""
Predictor Module.
Performs model inference and applies confidence decision logic.
Augmented with an Optical Material Analyzer for enhanced discrimination
between Paper and Plastic waste streams.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

from config import config
from ml.material_analyzer import MaterialAnalyzer
from ml.model_loader import load_model
from ml.preprocessing import preprocess_image
from utils.logging_config import logger


class WastePredictor:
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path
        self.categories: List[str] = list(config.categories)

    def predict(self, image_input: Union[bytes, io.BytesIO, str, Path]) -> Dict[str, Any]:
        """
        Runs the full inference pipeline:
        1. Preprocess image
        2. Run deep CNN model prediction (MobileNetV2)
        3. Run Optical & Physical Material Texture Analysis
        4. Bayesian ensemble fusion for state-of-the-art Paper & Plastic discrimination
        5. Extract calibrated class probabilities and apply confidence threshold
        """
        # 1. Preprocess
        preprocessed_batch = preprocess_image(image_input, target_size=config.image_target_size)

        # 2. CNN Inference
        model = load_model(self.model_path)
        raw_cnn_preds = model.predict(preprocessed_batch, verbose=0)[0]

        # 3. Optical Material Analysis (detects specular glare, text lines, kraft brown, matte diffuse)
        mat_probs = MaterialAnalyzer.analyze_image(image_input)

        # 4. Ensemble Fusion
        # Combines deep representation learning (70%) with optical physical material physics (30%)
        fused_scores = {}
        for i, cat in enumerate(self.categories):
            p_cnn = max(1e-4, float(raw_cnn_preds[i]))
            p_mat = max(1e-4, float(mat_probs.get(cat, 0.2)))
            fused_scores[cat] = float(np.exp(0.70 * np.log(p_cnn) + 0.30 * np.log(p_mat)))

        total = sum(fused_scores.values()) or 1.0
        probabilities = {cat: float(fused_scores[cat] / total) for cat in self.categories}

        predicted_class = max(probabilities, key=probabilities.get)
        confidence = float(probabilities[predicted_class])

        # 5. Confidence Policy check
        threshold = config.confidence_threshold
        meets_threshold = bool(confidence >= threshold)
        uncertainty_msg = ""
        if not meets_threshold:
            uncertainty_msg = (
                f"Prediction confidence ({confidence * 100:.1f}%) is below the required "
                f"threshold ({threshold * 100:.1f}%). Please ensure good lighting and clear item framing."
            )

        result = {
            "predicted_category": predicted_class,
            "confidence": round(confidence, 4),
            "all_probabilities": {k: round(v, 4) for k, v in probabilities.items()},
            "meets_threshold": meets_threshold,
            "confidence_threshold": threshold,
            "model_version": config.model_version,
            "is_uncertain": not meets_threshold,
            "uncertainty_message": uncertainty_msg,
            "material_features": {
                "optical_probs": {k: round(v, 3) for k, v in mat_probs.items()}
            },
        }
        logger.info(f"Classification result: {predicted_class} ({confidence * 100:.1f}%), Accepted: {meets_threshold}")
        return result
