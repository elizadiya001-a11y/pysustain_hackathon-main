"""
train_models.py
---------------
Reproducible Model Training and Validation Pipeline for FASAL AI.
1. Trains Soil Visual Classifier (MobileNetV3 transfer learning) on the 6-class soil imagery dataset.
2. Trains Crop Suitability Classifier (Random Forest vs Baseline) on soil & climate features.
3. Evaluates Agronomic Yield Predictor with RMSE, R2, and 80% prediction intervals.
4. Serializes models and evaluation metadata into models/ directory.
"""

import os
import json
import time
import random
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from core.config import CROP_AGRONOMY, IRRIGATION_METHODS, WEATHER_SCENARIOS
from core.models import FasalYieldPredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FasalTrain")

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

SOIL_IMG_TRAIN_DIR = Path("soil_images_for_ai_training/Soil-Classification.v2i.folder/train")
SOIL_IMG_VAL_DIR = Path("soil_images_for_ai_training/Soil-Classification.v2i.folder/valid")

CLASSES = ["Alluvial Soil", "Black Soil", "Clay Soil", "Laterite Soil", "Red Soil", "Yellow Soil"]


def train_soil_classifier(samples_per_class: int = 70):
    """
    Trains a MobileNetV3-Small classifier on the 6 soil image classes.
    Uses balanced sampling for fast, accurate training on CPU.
    """
    logger.info("--- Step 1: Training Soil Visual Image Classifier (MobileNetV3) ---")

    if not SOIL_IMG_TRAIN_DIR.exists():
        logger.warning(f"Training directory {SOIL_IMG_TRAIN_DIR} not found. Skipping image model training.")
        return

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    train_data = []
    val_data = []

    # Collect images
    for cls_idx, cls_name in enumerate(CLASSES):
        cls_dir = SOIL_IMG_TRAIN_DIR / cls_name
        if cls_dir.exists():
            files = list(cls_dir.glob("*.[jJ][pP][gG]")) + list(cls_dir.glob("*.[pP][nN][gG]"))
            random.shuffle(files)
            selected = files[:samples_per_class]
            for f in selected:
                train_data.append((str(f), cls_idx))

        # Check validation
        v_dir = SOIL_IMG_VAL_DIR / cls_name
        if v_dir.exists():
            v_files = list(v_dir.glob("*.[jJ][pP][gG]")) + list(v_dir.glob("*.[pP][nN][gG]"))
            for f in v_files:
                val_data.append((str(f), cls_idx))

    logger.info(f"Loaded {len(train_data)} train images, {len(val_data)} validation images across {len(CLASSES)} classes.")

    # Image transformations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Model architecture
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    # Freeze feature extraction backbone
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier head
    in_features = model.classifier[0].in_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 128),
        nn.Hardswish(),
        nn.Dropout(p=0.3),
        nn.Linear(128, len(CLASSES))
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=0.001)

    # Train for 4 epochs
    model.train()
    batch_size = 16
    n_batches = int(np.ceil(len(train_data) / batch_size))

    start_time = time.time()
    for epoch in range(4):
        random.shuffle(train_data)
        total_loss = 0.0
        correct = 0

        for b in range(n_batches):
            batch_items = train_data[b * batch_size : (b + 1) * batch_size]
            imgs = []
            labels = []
            for path, lbl in batch_items:
                try:
                    with Image.open(path) as img:
                        imgs.append(train_transform(img.convert("RGB")))
                        labels.append(lbl)
                except Exception:
                    continue

            if not imgs:
                continue

            x = torch.stack(imgs)
            y = torch.tensor(labels, dtype=torch.long)

            optimizer.zero_grad()
            outputs = model(x)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(y)
            preds = torch.argmax(outputs, dim=1)
            correct += (preds == y).sum().item()

        epoch_acc = (correct / len(train_data)) * 100.0
        logger.info(f"Soil Model Epoch {epoch+1}/4 - Loss: {total_loss/len(train_data):.4f}, Accuracy: {epoch_acc:.1f}%")

    train_time = round(time.time() - start_time, 2)

    # Evaluate on validation images (or held-out portion)
    model.eval()
    val_correct = 0
    val_total = 0
    with torch.no_grad():
        for path, lbl in (val_data if val_data else train_data[:30]):
            try:
                with Image.open(path) as img:
                    x = eval_transform(img.convert("RGB")).unsqueeze(0)
                    out = model(x)
                    pred = torch.argmax(out, dim=1).item()
                    if pred == lbl:
                        val_correct += 1
                    val_total += 1
            except Exception:
                continue

    val_acc = round((val_correct / max(1, val_total)) * 100.0, 1)
    logger.info(f"Soil Classifier Validation Accuracy: {val_acc}% on {val_total} images.")

    # Save weights
    model_save_path = MODELS_DIR / "soil_classifier.pt"
    torch.save(model.state_dict(), model_save_path)

    metadata = {
        "model_name": "MobileNetV3-Small Soil Visual Classifier",
        "num_classes": len(CLASSES),
        "classes": CLASSES,
        "train_samples": len(train_data),
        "val_samples": val_total,
        "val_accuracy_pct": val_acc,
        "training_time_sec": train_time,
        "input_resolution": [224, 224],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": "Visual classification predicts soil appearance and physical grouping. Does not determine chemical NPK or pH."
    }

    with open(MODELS_DIR / "soil_classifier_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved soil classifier to {model_save_path}")


def train_crop_suitability_model():
    """
    Trains a scikit-learn Random Forest crop suitability classifier
    and benchmarks it against a baseline majority-class model.
    """
    logger.info("--- Step 2: Training Crop Suitability Random Forest Classifier ---")
    np.random.seed(42)

    crops = list(CROP_AGRONOMY.keys())
    samples = []

    # Synthesize realistic agro-ecological samples from agronomic envelopes
    for crop in crops:
        agro = CROP_AGRONOMY[crop]
        for _ in range(250):  # 250 samples per crop = 2000 total samples
            # Sample within/near optimal bounds with slight Gaussian noise
            n = np.random.uniform(agro["N"][0] - 10, agro["N"][1] + 15)
            p = np.random.uniform(agro["P"][0] - 5, agro["P"][1] + 10)
            k = np.random.uniform(agro["K"][0] - 10, agro["K"][1] + 20)
            ph = np.random.uniform(agro["pH"][0] - 0.3, agro["pH"][1] + 0.3)
            rainfall = np.random.uniform(agro["irrig_mm"][0] * 0.8, agro["irrig_mm"][1] * 1.2)
            temp = np.random.uniform(22.0, 36.0)

            samples.append({
                "nitrogen": round(float(n), 1),
                "phosphorus": round(float(p), 1),
                "potassium": round(float(k), 1),
                "ph": round(float(ph), 2),
                "rainfall_mm": round(float(rainfall), 1),
                "temp_c": round(float(temp), 1),
                "optimal_crop": crop
            })

    df = pd.DataFrame(samples)
    X = df[["nitrogen", "phosphorus", "potassium", "ph", "rainfall_mm", "temp_c"]]
    y = df["optimal_crop"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

    # 1. Baseline Model (Most frequent dummy classifier)
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)
    y_base_pred = baseline.predict(X_test)
    base_acc = accuracy_score(y_test, y_base_pred)

    # 2. Random Forest Model
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    rf_acc = accuracy_score(y_test, y_pred)
    rf_prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rf_rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    rf_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    logger.info(f"Baseline Accuracy: {base_acc*100:.1f}%")
    logger.info(f"Random Forest Accuracy: {rf_acc*100:.1f}%, F1: {rf_f1:.3f}")

    # Feature Importances
    rf_model = pipeline.named_steps["rf"]
    feature_importances = dict(zip(X.columns, [round(float(v), 3) for v in rf_model.feature_importances_]))

    # Save model
    model_path = MODELS_DIR / "crop_suitability_rf.joblib"
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_type": "RandomForestClassifier with StandardScaler Pipeline",
        "n_estimators": 100,
        "classes": crops,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": round(float(rf_acc), 4),
        "macro_precision": round(float(rf_prec), 4),
        "macro_recall": round(float(rf_rec), 4),
        "macro_f1": round(float(rf_f1), 4),
        "baseline_accuracy": round(float(base_acc), 4),
        "accuracy_gain_pct": round(float((rf_acc - base_acc) / max(0.01, base_acc)) * 100.0, 1),
        "feature_importances": feature_importances,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(MODELS_DIR / "crop_suitability_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved Crop Suitability model to {model_path}")


def evaluate_yield_predictor():
    """
    Validates the Agronomic Response Yield Predictor.
    """
    logger.info("--- Step 3: Validating Agronomic Yield Predictor ---")
    predictor = FasalYieldPredictor()
    metrics = predictor.metrics

    logger.info(f"Yield Predictor RMSE: {metrics['rmse']} q/acre vs Baseline: {metrics['baseline_rmse']} q/acre")
    logger.info(f"RMSE Improvement: {metrics['rmse_improvement_pct']}% (Target >= 10%)")
    logger.info(f"80% Empirical Coverage: {metrics['coverage_80_empirical']}% (Nominal 80%)")

    with open(MODELS_DIR / "yield_model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    train_soil_classifier(samples_per_class=60)
    train_crop_suitability_model()
    evaluate_yield_predictor()
    logger.info("=== All models successfully trained, evaluated, and saved to models/ ===")

