"""Training pipeline."""

from zenml import pipeline

from steps.data_loader import load_data_step
from steps.evaluate import evaluate_step
from steps.training import train_step
import torch
from zenml.logger import get_logger

logger = get_logger(__name__)


@pipeline
def training_pipeline(
    device: str = "auto",
    num_epochs: int = 10,
    batch_size: int = 64,
    learning_rate: float = 0.001,
):
    """Run the training workflow end-to-end."""
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    logger.info(f"Using device: {device}")

    train_dataloader, test_dataloader = load_data_step(
        batch_size=batch_size,
    )
    
    model = train_step(
        device=device,
        train_dataloader=train_dataloader,
        lr=learning_rate,
        num_epochs=num_epochs,
    )

    metrics = evaluate_step(
        model=model,
        test_dataloader=test_dataloader,
        device=device,
    )

    return metrics
