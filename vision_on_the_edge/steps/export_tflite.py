"""Export a trained model to TFLite for microcontroller deployment."""

from __future__ import annotations

from pathlib import Path
import subprocess

import numpy as np
import torch
from torchvision import datasets, transforms
from zenml import step

from tiny_cnn import QuantTinyCNN


def _representative_dataset(num_samples: int = 200):
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.2860], std=[0.3530]),
        ]
    )
    dataset = datasets.FashionMNIST(
        root="data", train=True, download=True, transform=transform
    )
    for idx in range(min(num_samples, len(dataset))):
        image, _ = dataset[idx]
        image = image.unsqueeze(0).permute(0, 2, 3, 1).numpy().astype(np.float32)
        yield [image]


@step(enable_cache=False)
def export_tflite_step(
    state_dict: dict[str, torch.Tensor],
    bit_w: int,
    bit_a: int,
    export_dir: str = "artifacts/edge",
    model_name: str = "fashion_mnist_tiny_cnn",
) -> str:
    """Export a trained model to a TFLite file.

    Args:
        state_dict: Trained model weights.
        bit_w: Weight quantisation bits used for reconstruction.
        bit_a: Activation quantisation bits used for reconstruction.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.

    Returns:
        Path to the exported TFLite model.
    """
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    onnx_path = export_path / f"{model_name}.onnx"
    saved_model_dir = export_path / f"{model_name}_saved_model"
    tflite_path = export_path / f"{model_name}.tflite"

    model = QuantTinyCNN(num_classes=10, bit_w=bit_w, bit_a=bit_a)
    model.load_state_dict(state_dict)
    model.eval()

    dummy_input = torch.zeros(1, 1, 28, 28, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input"],
        output_names=["logits"],
        opset_version=13,
    )

    subprocess.run(
        ["onnx2tf", "-i", str(onnx_path), "-o", str(saved_model_dir)],
        check=True,
    )

    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = _representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    tflite_model = converter.convert()

    tflite_path.write_bytes(tflite_model)
    return str(tflite_path)
