"""
src/image_analysis.py
---------------------
Visual soil classification and computer vision pipeline for FASAL AI.
Uses PyTorch MobileNetV3 trained on Indian soil classes with strict agronomic disclaimers.
"""

import os
import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np

logger = logging.getLogger("FasalImageAnalysis")

MODELS_DIR = Path("models")
WEIGHTS_PATH = MODELS_DIR / "soil_classifier.pt"
METADATA_PATH = MODELS_DIR / "soil_classifier_metadata.json"

CLASSES = ["Alluvial Soil", "Black Soil", "Clay Soil", "Laterite Soil", "Red Soil", "Yellow Soil"]

_model_instance = None


def get_soil_model() -> Optional[nn.Module]:
    """Loads and caches the trained PyTorch MobileNetV3 soil classifier."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if not WEIGHTS_PATH.exists():
        logger.warning(f"Soil model weights not found at {WEIGHTS_PATH}")
        return None

    try:
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[0].in_features
        model.classifier = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.3),
            nn.Linear(128, len(CLASSES))
        )
        state_dict = torch.load(WEIGHTS_PATH, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()
        _model_instance = model
        logger.info("Loaded trained MobileNetV3 soil classifier.")
        return _model_instance
    except Exception as e:
        logger.error(f"Failed to load soil model: {e}")
        return None


def get_image_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])


def analyze_soil_image(image_input: Union[str, bytes, Image.Image]) -> Dict[str, Any]:
    """
    Classifies a soil photograph and returns predicted soil type, confidence,
    visual color features, and clear scientific disclaimers.
    """
    # 1. Load image
    img = None
    try:
        if isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        else:
            return {"success": False, "error": "Unsupported image format"}
    except Exception as e:
        return {"success": False, "error": f"Could not decode image: {e}"}

    # 2. Extract visual color and brightness metrics
    np_img = np.array(img.resize((100, 100)))
    r_mean = float(np.mean(np_img[:, :, 0]))
    g_mean = float(np.mean(np_img[:, :, 1]))
    b_mean = float(np.mean(np_img[:, :, 2]))
    brightness = float(np.mean(np_img))

    # 3. Model Inference
    model = get_soil_model()
    if model is None:
        return {
            "success": False,
            "error": "Image classifier model weights not available.",
            "disclaimer": "Visual classification is currently offline."
        }

    transform = get_image_transform()
    x = transform(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).numpy()

    top_idx = int(np.argmax(probs))
    top_class = CLASSES[top_idx]
    top_confidence = round(float(probs[top_idx]) * 100.0, 1)

    prob_dict = {CLASSES[i]: round(float(probs[i]) * 100.0, 1) for i in range(len(CLASSES))}
    sorted_probs = sorted(prob_dict.items(), key=lambda item: item[1], reverse=True)

    # Agronomic descriptions for visual types
    SOIL_TRAITS = {
        "Alluvial Soil": {"drainage": "Moderate to High", "workability": "Good", "typical_texture": "Loam to Sandy Loam"},
        "Black Soil": {"drainage": "Slow / High Water Retention", "workability": "Heavy / Sticky", "typical_texture": "Clay / Black Cotton"},
        "Clay Soil": {"drainage": "Low / High Plasticity", "workability": "Tough when dry", "typical_texture": "Clay Loam"},
        "Laterite Soil": {"drainage": "Very Fast / Low Retentivity", "workability": "Gritty", "typical_texture": "Porous Sandy Loam"},
        "Red Soil": {"drainage": "Fast / Leached", "workability": "Friable", "typical_texture": "Sandy Clay Loam"},
        "Yellow Soil": {"drainage": "Moderate", "workability": "Medium", "typical_texture": "Silt Loam"}
    }

    traits = SOIL_TRAITS.get(top_class, {"drainage": "Medium", "workability": "Medium", "typical_texture": "Loam"})

    return {
        "success": True,
        "predicted_soil_group": top_class,
        "confidence_pct": top_confidence,
        "class_probabilities": sorted_probs,
        "visual_features": {
            "mean_rgb": [round(r_mean, 1), round(g_mean, 1), round(b_mean, 1)],
            "brightness_index": round(brightness, 1),
            "estimated_drainage": traits["drainage"],
            "physical_workability": traits["workability"],
            "typical_texture": traits["typical_texture"]
        },
        "disclaimer": (
            "IMPORTANT: Visual classification estimates physical soil group and surface color texture. "
            "RGB photography CANNOT reveal chemical NPK or pH. Always confirm with an accredited soil test card."
        )
    }

