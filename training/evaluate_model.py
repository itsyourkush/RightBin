"""
Model Evaluation and Metrics Reporting Script.
Evaluates the trained CNN on the held-out test split,
computes precision, recall, f1-score, generates a confusion matrix,
and outputs authoritative model metadata.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import numpy as np

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"
os.environ["KERAS_HOME"] = "/tmp/keras_home"
Path("/tmp/keras_home").mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow import keras

from config import config
from training.prepare_dataset import DATASET_DIR
from utils.logging_config import logger
from utils.time_utils import to_iso_string


def evaluate_model() -> None:
    test_dir = DATASET_DIR / "test"
    model_path = config.model_path

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Train the model first.")

    logger.info(f"Loading trained model from {model_path}...")
    model = keras.models.load_model(str(model_path))

    class_names = list(config.categories)

    # Load test dataset
    test_ds = keras.utils.image_dataset_from_directory(
        test_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=class_names,
        image_size=config.image_target_size,
        batch_size=16,
        shuffle=False,
    )
    test_ds = test_ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y))

    y_true_indices = []
    y_pred_indices = []

    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true_indices.extend(np.argmax(labels.numpy(), axis=1))
        y_pred_indices.extend(np.argmax(preds, axis=1))

    y_true = np.array(y_true_indices)
    y_pred = np.array(y_pred_indices)

    # Calculate overall accuracy
    test_acc = float(np.mean(y_true == y_pred))
    logger.info(f"Test Set Accuracy: {test_acc * 100:.2f}%")

    # Classification report
    report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    logger.info("Classification Report:\n" + classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    # Plot Confusion Matrix
    plt.figure(figsize=(7, 6))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Greens)
    plt.title("Confusion Matrix - Waste Classifier")
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    # Annotate matrix cells
    thresh = cm.max() / 2.0 if cm.max() > 0 else 1
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j,
                i,
                format(cm[i, j], "d"),
                horizontalalignment="center",
                color="white" if cm[i, j] > thresh else "black",
                fontweight="bold",
            )

    plt.ylabel("True Class")
    plt.xlabel("Predicted Class")
    plt.tight_layout()

    cm_path = config.model_path.parent / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close()
    logger.info(f"Confusion matrix plot saved to: {cm_path}")

    # Save model metadata
    metadata = {
        "model_version": config.model_version,
        "evaluated_at": to_iso_string(),
        "input_shape": [config.image_target_size[0], config.image_target_size[1], 3],
        "categories": class_names,
        "overall_test_accuracy": round(test_acc, 4),
        "confidence_threshold": config.confidence_threshold,
        "per_class_metrics": {
            cat: {
                "precision": round(report[cat]["precision"], 4),
                "recall": round(report[cat]["recall"], 4),
                "f1_score": round(report[cat]["f1-score"], 4),
                "support": report[cat]["support"],
            }
            for cat in class_names
            if cat in report
        },
        "dataset_splits": {
            "source": "Balanced Multiclass Waste Dataset (Synthesized and Verified Classes)",
            "categories": class_names,
        },
    }

    metadata_path = config.model_path.parent / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model metadata saved to: {metadata_path}")


if __name__ == "__main__":
    evaluate_model()
