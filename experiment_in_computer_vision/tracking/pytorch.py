"""PyTorch-related MLflow logging helpers."""

import mlflow


def log_model_architecture(model):
    """Log the string representation of a PyTorch model to MLflow.

    Args:
        model (torch.nn.Module): Model to serialize via `str(model)`.
    """
    mlflow.log_text(str(model), "model_architecture.txt")
