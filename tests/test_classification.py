"""
Unit tests for Waste Classification Service and Preprocessing.
"""

import io
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

from config import config
from ml.preprocessing import preprocess_image
from services.classification_service import ClassificationService
from services.recommendation_service import RecommendationService


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Creates a simple in-memory 180x180 PNG test image."""
    img = Image.new("RGB", (180, 180), color=(50, 150, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_preprocessing(sample_image_bytes):
    batch = preprocess_image(sample_image_bytes, target_size=(180, 180))
    assert isinstance(batch, np.ndarray)
    assert batch.shape == (1, 180, 180, 3)
    assert batch.dtype == np.float32
    assert 0.0 <= batch.min() <= batch.max() <= 1.0


def test_classification_service_predict(sample_image_bytes):
    service = ClassificationService()
    result = service.classify_image("test_bottle.png", sample_image_bytes)

    assert result["status"] in ("success", "low_confidence")
    assert result["predicted_category"] in config.categories
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["model_version"] == config.model_version
    assert result["image_hash"] is not None
    assert "recommendation" in result
    assert result["recommendation"]["bin_type"] != ""


def test_invalid_image_extension():
    service = ClassificationService()
    result = service.classify_image("document.pdf", b"fake-pdf-content")
    assert result["status"] == "validation_failed"
    assert "unsupported file extension" in result["error_message"].lower()


def test_corrupted_image():
    service = ClassificationService()
    result = service.classify_image("corrupt.png", b"not-a-valid-png-stream")
    assert result["status"] == "validation_failed"
    assert "corrupted or invalid" in result["error_message"].lower()


def test_qr_code_detection_on_image():
    import qrcode
    qr = qrcode.make("https://smartwaste.org/bottle-123")
    buf = io.BytesIO()
    qr.save(buf, format="PNG")

    service = ClassificationService()
    result = service.classify_image("qr_bottle.png", buf.getvalue())
    assert result["qr_code_detected"] is True
    assert "https://smartwaste.org/bottle-123" in result["qr_code_content"]


def test_recommendation_service_categories():
    rec_service = RecommendationService()
    for cat in config.categories:
        rec = rec_service.get_recommendation(cat, is_accepted=True)
        assert rec["category"] == cat
        assert len(rec["preparation_steps"]) > 0
        assert len(rec["contamination_warnings"]) > 0

    # Low-confidence fallback
    fallback = rec_service.get_recommendation("Plastic", is_accepted=False)
    assert fallback["status"] == "low_confidence_fallback"
