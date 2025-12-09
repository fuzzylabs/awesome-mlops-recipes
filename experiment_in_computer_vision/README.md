# Experiment In Computer Vision

This recipe gives you a runnable example of frictionless experiment tracking for computer‑vision research, ready to adapt to your own models and datasets.

**Cook Time**: ~1 Hour

## 🥗 Ingredients

- **Data Versioning**: DVC
- **Experiment Tracking**: MLFlow
- **Pipeline Orchestrator**: ZenML
- **Code Verisoning**: Git

## 🗄️ Project Structure

## 🚀 Quick Start

### 1. Start MLFlow

```bash
mlflow server --app-name basic-auth --backend-store-uri sqlite:///mlflow.db --port 5000
```

### 2. Set up DVC & Version Our Data

THe dataset we are using in this recipe is the [Simpsons-MNIST](https://github.com/alvarobartt/simpsons-mnist). You can use whatever dataset you want.

If you are sticking with [Simpsons-MNIST](https://github.com/alvarobartt/simpsons-mnist), there are two dataset which you will find, grayscale and rgb.

```bash

```

### 3. Start ZenML

### 3. Make some changes

### 4. Reproduce the run

Update code:

```python
"""Data loading step for the ZenML pipeline."""

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from zenml import step
from zenml.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


def _load_split(data_dir: str, split: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a dataset split (train/test) from disk."""
    images = []
    labels = []
    label_map: dict[str, int] = {}

    split_path = Path(data_dir) / split
    if not split_path.exists():
        raise ValueError(f"Split directory not found: {split_path}")

    characters = sorted([d for d in split_path.iterdir() if d.is_dir()])

    for idx, character_dir in enumerate(characters):
        label_map[character_dir.name] = idx
        image_files = [
            f for f in character_dir.iterdir() if f.name.endswith((".png", ".jpg"))
        ]
        for file in image_files:
            img = Image.open(file).convert("RGB")
            img = img.resize((28, 28), Image.LANCZOS)
            transform = transforms.Compose(
                [
                    transforms.ToTensor(),
                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                ]
            )
            images.append(transform(img))
            labels.append(label_map[character_dir.name])

    if not images:
        raise ValueError(f"No images found under {split_path}")

    X = torch.stack(images).numpy()
    y = torch.tensor(labels, dtype=torch.long).numpy()
    return X, y


@step(enable_cache=False)
def load_data_step(
    data_dir: str = "./data",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load train and test splits; fallback to dummy data if needed."""
    try:
        train_features, train_labels = _load_split(data_dir, "train")
        test_features, test_labels = _load_split(data_dir, "test")
        logger.info("Loaded %s train samples and %s test samples", len(train_labels), len(test_labels))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falling back to dummy data: %s", exc)
        train_features = torch.randn(1000, 3, 28, 28).numpy()
        train_labels = torch.randint(0, 10, (1000,)).numpy()
        test_features = torch.randn(200, 3, 28, 28).numpy()
        test_labels = torch.randint(0, 10, (200,)).numpy()

    return train_features, train_labels, test_features, test_labels
```