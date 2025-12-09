"""Evaluation step for the ZenML pipeline using the test split."""

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from zenml import step
from zenml.client import Client
from zenml.logger import get_logger
import mlflow

logger = get_logger(__name__)


def _experiment_tracker_name() -> str | None:
    try:
        tracker = Client().active_stack.experiment_tracker
        return tracker.name if tracker else None
    except Exception:
        return None


@step(enable_cache=False, experiment_tracker=_experiment_tracker_name())
def evaluate_step(
    model: torch.nn.Module,
    test_features: np.ndarray,
    test_labels: np.ndarray,
    batch_size: int = 64,
) -> dict[str, float]:
    """Evaluate the trained model on the held-out test set."""
    model.eval()
    X_tensor = torch.from_numpy(test_features)
    y_tensor = torch.from_numpy(test_labels).long()

    test_loader = DataLoader(
        TensorDataset(X_tensor, y_tensor), batch_size=batch_size, shuffle=False
    )

    criterion = torch.nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, targets in test_loader:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()

    test_loss = total_loss / len(test_loader.dataset)
    test_accuracy = correct / total if total else 0.0

    mlflow.log_metric("test_loss", test_loss)
    mlflow.log_metric("test_accuracy", test_accuracy)

    logger.info("Test Loss: %.4f Test Acc: %.4f", test_loss, test_accuracy)

    return {"test_loss": test_loss, "test_accuracy": test_accuracy}
