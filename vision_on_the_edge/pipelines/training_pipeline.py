"""Training pipeline."""

from typing import Optional

from zenml import pipeline

from steps.data_loader import load_data_step
from steps.evaluate import evaluate_step
from steps.export_pte import export_pte_step
from steps.training import train_step
from steps.deploy_platformio import deploy_platformio_step
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
    export_tflite: bool = True,
    export_dir: str = "artifacts/edge",
    model_name: str = "fashion_mnist_tiny_cnn",
    deploy: bool = False,
    platformio_project_dir: Optional[str] = None,
    upload: bool = True,
):
    """Run the training workflow end-to-end.

    Args:
        bit_w: Bit width for weight quantization.
        bit_a: Bit width for activation quantization.
        device: Device to train on ('auto', 'cpu', 'cuda').
        num_epochs: Number of epochs to train for.
        batch_size: Batch size for training.
        learning_rate: Learning rate for the optimizer.

    Returns:
        Metrics dictionary from the evaluation step.
    """
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

    exported_model_path = None
    if export_tflite:
        exported_model_path = export_pte_step(
            state_dict=state_dict,
            bit_w=bit_w,
            bit_a=bit_a,
            export_dir=export_dir,
            model_name=model_name,
        )

    if deploy:
        if not platformio_project_dir:
            raise ValueError("Deployment requires platformio_project_dir.")
        if not exported_model_path:
            raise ValueError("Deployment requires export_tflite=True.")
        deploy_platformio_step(
            pte_model_path=exported_model_path,
            platformio_project_dir=platformio_project_dir,
            upload=upload,
        )

    return metrics
