"""
CNN Training Script for Smart Waste Classification.
Implements MobileNetV2 transfer learning with data augmentation,
two-stage fine-tuning, callbacks, and training curve generation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Configure temp caches for sandbox safety
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"
os.environ["KERAS_HOME"] = "/tmp/keras_home"
Path("/tmp/keras_home").mkdir(parents=True, exist_ok=True)
Path("/tmp/matplotlib_cache").mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from config import config
from training.prepare_dataset import DATASET_DIR, prepare_dataset
from utils.logging_config import logger


def build_mobilenet_model(input_shape=(224, 224, 3), num_classes=5) -> tuple[keras.Model, keras.Model]:
    """
    Constructs the 5-class Waste Classifier using MobileNetV2 transfer learning.
    Architecture:
    Input (scaled to [0, 1]) ->
    Data Augmentation (Flip, Rotation, Zoom, Translation) ->
    Rescaling(scale=2.0, offset=-1.0) to [-1, 1] ->
    MobileNetV2 Base (pre-trained on ImageNet) ->
    GlobalAveragePooling2D ->
    BatchNormalization ->
    Dense(128, relu) ->
    Dropout(0.3) ->
    Dense(num_classes, softmax)
    """
    inputs = layers.Input(shape=input_shape, name="waste_image_input")

    # Data augmentation layers (active only during training)
    x = layers.RandomFlip("horizontal", name="aug_flip")(inputs)
    x = layers.RandomRotation(0.08, fill_mode="nearest", name="aug_rot")(x)
    x = layers.RandomZoom(0.08, fill_mode="nearest", name="aug_zoom")(x)
    x = layers.RandomTranslation(0.05, 0.05, fill_mode="nearest", name="aug_trans")(x)

    # Scale [0, 1] to [-1, 1] for MobileNetV2
    x = layers.Rescaling(scale=2.0, offset=-1.0, name="mobilenet_rescaling")(x)

    # Pre-trained MobileNetV2 backbone
    base_model = keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.BatchNormalization(name="bn_gap")(x)
    x = layers.Dense(128, activation="relu", name="dense_features")(x)
    x = layers.Dropout(0.3, name="dropout_regularization")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="classification_output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="waste_classifier_mobilenetv2")
    return model, base_model


def train_model(epochs_stage1: int = 8, epochs_stage2: int = 5, batch_size: int = 16) -> None:
    """Trains the CNN on prepared dataset and saves artifacts."""
    train_dir = DATASET_DIR / "train"
    val_dir = DATASET_DIR / "val"

    if not train_dir.exists() or not list(train_dir.glob("*/*.png")):
        logger.info("Training dataset not found. Generating initial dataset...")
        prepare_dataset()

    class_names = list(config.categories)
    logger.info(f"Target classes ({len(class_names)}): {class_names}")

    # Load datasets
    train_ds = keras.utils.image_dataset_from_directory(
        train_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=class_names,
        image_size=config.image_target_size,
        batch_size=batch_size,
        shuffle=True,
        seed=42,
    )

    val_ds = keras.utils.image_dataset_from_directory(
        val_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=class_names,
        image_size=config.image_target_size,
        batch_size=batch_size,
        shuffle=False,
    )

    # Normalize inputs to [0.0, 1.0] matching runtime preprocessing
    train_ds = train_ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y))
    val_ds = val_ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y))

    # Prefetch for performance
    train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)

    model, base_model = build_mobilenet_model(
        input_shape=(config.image_target_size[0], config.image_target_size[1], 3),
        num_classes=len(class_names),
    )

    save_path = config.model_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # --- STAGE 1: Train Classification Head (Backbone Frozen) ---
    logger.info("Stage 1: Training classifier head with frozen MobileNetV2 backbone...")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    callbacks_stage1 = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ModelCheckpoint(filepath=str(save_path), monitor="val_accuracy", save_best_only=True),
    ]

    history_stage1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_stage1,
        callbacks=callbacks_stage1,
        verbose=1,
    )

    # --- STAGE 2: Fine-Tuning Top Layers ---
    logger.info("Stage 2: Unfreezing top 25 layers of MobileNetV2 for fine-tuning...")
    base_model.trainable = True
    for layer in base_model.layers[:-25]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_stage2 = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ModelCheckpoint(filepath=str(save_path), monitor="val_accuracy", save_best_only=True),
    ]

    history_stage2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_stage2,
        callbacks=callbacks_stage2,
        verbose=1,
    )

    # Save final model
    model.save(str(save_path))
    logger.info(f"Model saved successfully to: {save_path}")

    # Combine histories for plotting
    acc = history_stage1.history.get("accuracy", []) + history_stage2.history.get("accuracy", [])
    val_acc = history_stage1.history.get("val_accuracy", []) + history_stage2.history.get("val_accuracy", [])
    loss = history_stage1.history.get("loss", []) + history_stage2.history.get("loss", [])
    val_loss = history_stage1.history.get("val_loss", []) + history_stage2.history.get("val_loss", [])

    # Generate training curves plot
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(acc, label="Train Accuracy", color="#2E7D32")
    plt.plot(val_acc, label="Val Accuracy", color="#1565C0")
    plt.axvline(x=len(history_stage1.history.get("accuracy", [])) - 0.5, color="gray", linestyle="--", label="Fine-tuning")
    plt.title("Model Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.subplot(1, 2, 2)
    plt.plot(loss, label="Train Loss", color="#C62828")
    plt.plot(val_loss, label="Val Loss", color="#E65100")
    plt.axvline(x=len(history_stage1.history.get("loss", [])) - 0.5, color="gray", linestyle="--", label="Fine-tuning")
    plt.title("Model Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    chart_path = config.model_path.parent / "training_history.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    logger.info(f"Training history curves saved to: {chart_path}")


if __name__ == "__main__":
    train_model(epochs_stage1=8, epochs_stage2=5)
