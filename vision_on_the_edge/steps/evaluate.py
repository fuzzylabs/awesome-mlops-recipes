"""Evaluation step."""

from zenml import step
from zenml.logger import get_logger
import torch
from torch import nn
from torch.utils.data import DataLoader

logger = get_logger(__name__)


@step(enable_cache=False)
def evaluate_step(
    model: nn.Module,
    test_dataloader: DataLoader,
    device: str,
):
    """Evaluate the model on test data.

    Args:
        model: The trained neural network model.
        test_dataloader: DataLoader for test data.
        device: Device to evaluate on ('auto', 'cpu', 'cuda', 'mps').

    Returns:
        Dictionary containing evaluation metrics.
    """
    # Setup device
    model.to(device)
    model.eval()

    # Initialise metrics
    correct = 0
    total = 0

    logger.info("Starting model evaluation...")
    logger.info(f"Test samples: {len(test_dataloader.dataset)}")  # type: ignore

    with torch.no_grad():
        for raw_inputs, raw_labels in test_dataloader:
            inputs, labels = raw_inputs.to(device), raw_labels.to(device)

            # Forward pass
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)

            # Overall accuracy
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # Calculate overall accuracy
    overall_accuracy = 100 * correct / total

    # Create evaluation results
    results = {
        "overall_accuracy": overall_accuracy,
    }

    return results