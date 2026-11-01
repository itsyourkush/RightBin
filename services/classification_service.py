"""
Waste Classification Service.
Coordinates image validation, model prediction, fine-grained sub-type identification,
location-based area limit enforcement (1 to 2 scans per particular area; otherwise discarded),
and recommendation retrieval.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from config import config
from ml.model_loader import ModelNotFoundError, is_model_available
from ml.predictor import WastePredictor
from repositories.scan_repository import ScanRepository
from services.recommendation_service import RecommendationService
from utils.location_utils import extract_exif_gps
from utils.logging_config import logger
from utils.security import compute_image_hash
from utils.validators import validate_image_file


class ClassificationService:
    def __init__(self, model_path: Optional[Path] = None, db_path: Optional[str] = None):
        self.model_path = model_path if model_path is not None else config.model_path
        self.db_path = db_path
        self.predictor = WastePredictor(self.model_path)
        self.recommendation_service = RecommendationService()
        self.scan_repo = ScanRepository(db_path)

    def classify_image(
        self,
        file_name: str,
        image_bytes: bytes,
        user_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        area_name: Optional[str] = None,
        location_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates the uploaded image, checks model readiness, runs CNN inference,
        identifies specific waste sub-types, applies area-based fraud rules (1 to 2 scans per area,
        otherwise discarded), and returns actionable recommendations.
        """
        effective_area = (area_name or location_name or "").strip()

        # 1. Image validation
        is_valid, err_msg = validate_image_file(file_name, len(image_bytes), image_bytes)
        if not is_valid:
            logger.warning(f"Image validation failed for '{file_name}': {err_msg}")
            return {
                "status": "validation_failed",
                "error_message": err_msg,
                "prediction_accepted": False,
                "is_discarded": False,
                "predicted_category": None,
                "sub_category": None,
                "subtype_details": {},
                "confidence": 0.0,
                "image_hash": None,
                "model_version": config.model_version,
                "latitude": latitude,
                "longitude": longitude,
                "area_name": effective_area or "Unspecified Area",
                "location_name": effective_area or "Unspecified Area",
                "rejection_reason": err_msg,
                "recommendation": self.recommendation_service.get_recommendation("", is_accepted=False),
            }

        # 2. Compute image hash for duplicate audit
        img_hash = compute_image_hash(image_bytes)

        # 3. EXIF GPS extraction from camera image (accurate hardware GPS)
        exif_coords = extract_exif_gps(image_bytes)
        if exif_coords:
            latitude, longitude = exif_coords
            effective_area = f"Photo Camera GPS ({latitude:.4f}, {longitude:.4f})"
            logger.info(f"Extracted camera EXIF GPS coordinates: {latitude}, {longitude}")

        # 4. Location-based area limit enforcement (1 to 2 scans per particular area)
        scans_in_area = 0
        is_discarded = False
        if user_id is not None and (latitude is not None or effective_area):
            scans_in_area = self.scan_repo.count_accepted_scans_in_area(
                user_id=user_id,
                latitude=latitude,
                longitude=longitude,
                location_name=effective_area,
                proximity_meters=config.area_proximity_threshold_meters,
            )
            # If user has already completed 2 or more scans in this area, scan is DISCARDED
            if scans_in_area >= config.max_scans_per_area:
                is_discarded = True
                logger.warning(
                    f"User {user_id} exceeded area limit ({scans_in_area}/{config.max_scans_per_area}) "
                    f"in area '{effective_area}'. Scan will be discarded."
                )

        # 5. Detect any embedded packaging QR code / barcode
        qr_content = ""
        try:
            import cv2
            import numpy as np
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_cv is not None:
                detector = cv2.QRCodeDetector()
                decoded, _, _ = detector.detectAndDecode(img_cv)
                if decoded:
                    qr_content = decoded.strip()
                    logger.info(f"QR code detected on image: '{qr_content}'")
        except Exception as e:
            logger.debug(f"QR detection pass skipped: {e}")

        # 6. Model availability check
        if not is_model_available(self.model_path):
            setup_msg = (
                "CNN model artifact not found. Please train the model by running:\n"
                "python training/train_model.py"
            )
            logger.error(setup_msg)
            return {
                "status": "model_unavailable",
                "error_message": setup_msg,
                "prediction_accepted": False,
                "is_discarded": False,
                "predicted_category": None,
                "sub_category": None,
                "subtype_details": {},
                "confidence": 0.0,
                "image_hash": img_hash,
                "model_version": config.model_version,
                "latitude": latitude,
                "longitude": longitude,
                "area_name": effective_area or "Unspecified Area",
                "location_name": effective_area or "Unspecified Area",
                "rejection_reason": setup_msg,
                "recommendation": self.recommendation_service.get_recommendation("", is_accepted=False),
            }

        # 7. CNN Inference
        try:
            prediction = self.predictor.predict(image_bytes)
        except Exception as e:
            logger.error(f"Inference error during classification: {e}")
            return {
                "status": "inference_error",
                "error_message": f"Inference failed: {str(e)}",
                "prediction_accepted": False,
                "is_discarded": False,
                "predicted_category": None,
                "sub_category": None,
                "subtype_details": {},
                "confidence": 0.0,
                "image_hash": img_hash,
                "model_version": config.model_version,
                "latitude": latitude,
                "longitude": longitude,
                "area_name": effective_area or "Unspecified Area",
                "location_name": effective_area or "Unspecified Area",
                "rejection_reason": f"Inference error: {str(e)}",
                "recommendation": self.recommendation_service.get_recommendation("", is_accepted=False),
            }

        predicted_category = prediction["predicted_category"]
        confidence = prediction["confidence"]
        meets_threshold = prediction["meets_threshold"]

        # 8. Specific Subtype Identification
        subtype_info = self.recommendation_service.identify_subtype(
            category=predicted_category,
            image_bytes=image_bytes,
            qr_content=qr_content,
        )

        # 9. Area Limit & Discard Decision
        rejection_reason = ""
        if is_discarded:
            prediction_accepted = False
            status = "discarded"
            rejection_reason = (
                f"Scan Discarded: Exceeded the allowed limit of 1 to 2 scans for this particular area "
                f"({scans_in_area}/{config.max_scans_per_area} used in '{effective_area or 'this area'}'). "
                f"To prevent duplicate reward farming, scans beyond {config.max_scans_per_area} in the same area are discarded. "
                "Please move to a different area or zone to scan recyclable items!"
            )
        elif not meets_threshold:
            prediction_accepted = False
            status = "low_confidence"
            rejection_reason = prediction.get("uncertainty_message", "Confidence below threshold.")
        else:
            prediction_accepted = True
            status = "success"

        # 10. Disposal & Recycling Recommendation
        recommendation = self.recommendation_service.get_recommendation(
            predicted_category,
            is_accepted=prediction_accepted,
            subtype_info=subtype_info,
        )

        return {
            "status": status,
            "predicted_category": predicted_category,
            "sub_category": subtype_info["subtype_name"],
            "subtype_details": subtype_info,
            "confidence": confidence,
            "all_probabilities": prediction["all_probabilities"],
            "prediction_accepted": prediction_accepted,
            "is_discarded": is_discarded,
            "rejection_reason": rejection_reason,
            "image_hash": img_hash,
            "model_version": config.model_version,
            "latitude": latitude,
            "longitude": longitude,
            "area_name": effective_area or "Unspecified Area",
            "location_name": effective_area or "Unspecified Area",
            "scans_in_area": scans_in_area,
            "max_scans_per_area": config.max_scans_per_area,
            "location_limit_exceeded": is_discarded,  # backwards compatibility
            "qr_code_detected": bool(qr_content),
            "qr_code_content": qr_content,
            "uncertainty_message": prediction.get("uncertainty_message", ""),
            "recommendation": recommendation,
            "error_message": "",
        }
