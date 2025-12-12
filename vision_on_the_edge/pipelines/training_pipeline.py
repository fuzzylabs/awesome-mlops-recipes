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
    bit_w: int,
    bit_a: int,
    device: str = "auto",
    num_epochs: int = 10,
    batch_size: int = 64,
    learning_rate: float = 0.001,
):
    """Run the training workflow end-to-end."""
    if device == "auto": # No mps support with Brevitas
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    logger.info(f"Using device: {device}")

    train_dataloader, test_dataloader = load_data_step(
        batch_size=batch_size,
    )
    
    state_dict = train_step(
        device=device,
        train_dataloader=train_dataloader,
        lr=learning_rate,
        num_epochs=num_epochs,
        bit_w=bit_w,
        bit_a=bit_a,
    )

    metrics = evaluate_step(
        state_dict=state_dict,
        test_dataloader=test_dataloader,
        device=device,
        bit_w=bit_w,
        bit_a=bit_a,
    )

    return metrics
