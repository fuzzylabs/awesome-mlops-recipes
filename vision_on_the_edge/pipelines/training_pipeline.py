"""Training pipeline."""

from dataclasses import dataclass

import torch
from steps.convert_int8_tflite import convert_int8_tflite_step
from steps.data_loader import load_data_step
from steps.deploy_platformio import deploy_platformio_step
from steps.evaluate import evaluate_step
from steps.export_tflite import export_saved_model_step
from steps.training import train_step
from zenml import pipeline
from zenml.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for training pipeline.

    Args:
        bit_w: Bit width for weight quantisation.
        bit_a: Bit width for activation quantisation.
        device: Device to train on ('auto', 'cpu', 'cuda').
        num_epochs: Number of epochs to train for.
        batch_size: Batch size for training.
        learning_rate: Learning rate for the optimizer.
    """

    bit_w: int
    bit_a: int
    device: str = "auto"
    num_epochs: int = 10
    batch_size: int = 64
    learning_rate: float = 0.001


@dataclass
class ExportConfig:
    """Configuration for model export and deployment.

    Args:
        export_tflite: Whether to export the model to TFLite.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.
        deploy: Whether to deploy via PlatformIO.
        platformio_project_dir: PlatformIO project directory path.
        upload: Whether to upload firmware after building.
    """

    export_tflite: bool = True
    export_dir: str = "artifacts/edge"
    model_name: str = "fashion_mnist_tiny_cnn"
    deploy: bool = False
    platformio_project_dir: str | None = None
    upload: bool = True


@pipeline  # type: ignore[untyped-decorator]
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
    platformio_project_dir: str | None = None,
    upload: bool = True,
) -> dict[str, float]:
    """Run the training workflow end-to-end.

    Args:
        bit_w: Bit width for weight quantisation.
        bit_a: Bit width for activation quantisation.
        device: Device to train on ('auto', 'cpu', 'cuda').
        num_epochs: Number of epochs to train for.
        batch_size: Batch size for training.
        learning_rate: Learning rate for the optimizer.
        export_tflite: Whether to export the model to TFLite.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.
        deploy: Whether to deploy via PlatformIO.
        platformio_project_dir: PlatformIO project directory path.
        upload: Whether to upload firmware after building.

    Returns:
        Metrics dictionary from the evaluation step.
    """
    if device == "auto":  # No mps support with Brevitas
        device = "cuda" if torch.cuda.is_available() else "cpu"

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
        saved_model_dir = export_saved_model_step(
            state_dict=state_dict,
            bit_w=bit_w,
            bit_a=bit_a,
            export_dir=export_dir,
            model_name=model_name,
        )
        exported_model_path = convert_int8_tflite_step(
            saved_model_dir=saved_model_dir,
            export_dir=export_dir,
            model_name=model_name,
        )

    if deploy:
        if not platformio_project_dir:
            raise ValueError("Deployment requires platformio_project_dir.")
        if not exported_model_path:
            raise ValueError("Deployment requires export_tflite=True.")
        deploy_platformio_step(
            tflite_model_path=exported_model_path,
            platformio_project_dir=platformio_project_dir,
            upload=upload,
        )

    return dict(metrics)
