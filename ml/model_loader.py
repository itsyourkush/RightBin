"""
Model Loader Module.
Loads the Keras CNN model once per application lifecycle with thread-safe caching.
Provides graceful fallbacks and actionable error messages when models are missing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import threading

os.environ.setdefault("KERAS_HOME", "/tmp/keras_home")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
Path("/tmp/keras_home").mkdir(parents=True, exist_ok=True)
Path("/tmp/matplotlib_cache").mkdir(parents=True, exist_ok=True)

import tensorflow as tf
from tensorflow import keras

from config import config
from utils.logging_config import logger

_model_lock = threading.Lock()
_cached_model: Optional[keras.Model] = None


class ModelNotFoundError(Exception):
    """Raised when the trained CNN model artifact cannot be found on disk."""
    pass


def load_model(model_path: Optional[Path] = None, force_reload: bool = False) -> keras.Model:
    """
    Loads and returns the trained TensorFlow/Keras CNN model.
    Caches the model in memory to prevent repeated disk I/O.
    """
    global _cached_model

    target_path = model_path if model_path is not None else config.model_path

    if _cached_model is not None and not force_reload:
        return _cached_model

    with _model_lock:
        if _cached_model is not None and not force_reload:
            return _cached_model

        if not target_path.exists():
            error_msg = (
                f"Model artifact not found at '{target_path}'.\n"
                f"Please train the model first by running:\n"
                f"    python training/train_model.py\n"
                f"or download the pre-trained weights into ml/artifacts/."
            )
            logger.error(error_msg)
            raise ModelNotFoundError(error_msg)

        logger.info(f"Loading trained CNN model from {target_path}...")
        try:
            model = keras.models.load_model(str(target_path))
            _cached_model = model
            logger.info("CNN model loaded and cached successfully.")
            return _cached_model
        except Exception as e:
            logger.error(f"Failed to load CNN model from {target_path}: {e}")
            raise


def is_model_available(model_path: Optional[Path] = None) -> bool:
    """Checks whether the model artifact exists on disk."""
    target_path = model_path if model_path is not None else config.model_path
    return target_path.exists()
