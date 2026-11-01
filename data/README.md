# Data Directory Overview

This directory stores the local SQLite database and dataset partitions for the Smart Waste Classification System.

## Directory Structure

```
data/
|-- waste_classification.db       # Primary SQLite application database
|-- dataset/                      # Multiclass training, validation, and test images
|   |-- train/
|   |   |-- Plastic/
|   |   |-- Paper/
|   |   |-- Organic/
|   |   |-- Metal/
|   |   |-- Glass/
|   |-- val/
|   |   |-- Plastic/ ...
|   |-- test/
|   |   |-- Plastic/ ...
```

## Dataset Specifications

- **Classes**: Exactly 5 authoritative waste classes:
  1. `Plastic` (e.g. bottles, jugs, containers)
  2. `Paper` (e.g. clean paper, cardboard, newsprint)
  3. `Organic` (e.g. fruit scraps, vegetable peels, leaves)
  4. `Metal` (e.g. aluminum cans, tin food cans)
  5. `Glass` (e.g. jars, beverage bottles)
- **Image Resolution**: Scaled uniformly to `180 x 180` pixels, 3-channel RGB.
- **Normalization**: Pixel values normalized to `[0.0, 1.0]`.

## Ingesting External Datasets (e.g. TrashNet)

To train on external real-world benchmarks like TrashNet:
1. Download TrashNet or Kaggle Waste Dataset images.
2. Map categories to the 5 supported classes: Plastic, Paper, Organic, Metal, Glass.
3. Place images into `data/dataset/train/<Category>/` and `data/dataset/val/<Category>/`.
4. Run:
   ```bash
   python training/train_model.py
   python training/evaluate_model.py
   ```
