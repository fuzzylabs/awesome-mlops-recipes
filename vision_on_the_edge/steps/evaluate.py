"""Evaluation step."""

import time

from zenml import step
from zenml.logger import get_logger
import torch
from torch.utils.data import DataLoader
from tiny_cnn import QuantTinyCNN


logger = get_logger(__name__)


@step(enable_cache=False)
def evaluate_step(
    state_dict: dict[str, torch.Tensor],
    test_dataloader: DataLoader,
    device: str,
    bit_w: int,
    bit_a: int,
) -> dict[str, float]:
    """Evaluate the model on test data.

    Args:
        state_dict: The trained model weights.
        test_dataloader: DataLoader for test data.
        device: Device to evaluate on ('auto', 'cpu', 'cuda').
        bit_w: Weight quantization bits used for reconstruction.
        bit_a: Activation quantization bits used for reconstruction.

    Returns:
        Dictionary containing evaluation metrics.
    """
    # Rebuild and setup device
    model = QuantTinyCNN(num_classes=10, bit_w=bit_w, bit_a=bit_a)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # Initialise metrics
    correct = 0
    total = 0
    latency_sum = 0.0
    latency_samples = 0
    latency_batches_to_measure = 5

    logger.info("Starting model evaluation...")
    logger.info(f"Test samples: {len(test_dataloader.dataset)}")  # type: ignore

    with torch.no_grad():
        for raw_inputs, raw_labels in test_dataloader:
            inputs, labels = raw_inputs.to(device), raw_labels.to(device)

            # Forward pass
            start = time.time()
            outputs = model(inputs)
            end = time.time()
            _, predicted = torch.max(outputs, 1)

            # Overall accuracy
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            # Collect latency sample on a few batches
            if latency_samples < latency_batches_to_measure:
                latency_sum += end - start
                latency_samples += 1

    # Calculate overall accuracy
    overall_accuracy = 100 * correct / total
    avg_latency_ms = (latency_sum / latency_samples) * 1000 if latency_samples else 0.0
    param_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_bytes = sum(b.numel() * b.element_size() for b in model.buffers())
    model_size_mb = (param_bytes + buffer_bytes) / (1024 * 1024)

    # Create evaluation results
    results = {
        "overall_accuracy": overall_accuracy,
        "latency_ms": avg_latency_ms,
        "model_size_mb": model_size_mb,
    }

    return results
