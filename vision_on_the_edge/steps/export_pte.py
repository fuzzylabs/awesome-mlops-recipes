"""Export a trained model to ExecuTorch .pte format."""

from pathlib import Path

import torch
from zenml import step

from tiny_cnn import QuantTinyCNN


@step(enable_cache=False)
def export_pte_step(
    state_dict: dict[str, torch.Tensor],
    bit_w: int,
    bit_a: int,
    export_dir: str = "artifacts/edge",
    model_name: str = "fashion_mnist_tiny_cnn",
) -> str:
    """Export a trained model to an ExecuTorch .pte file.

    Args:
        state_dict: Trained model weights.
        bit_w: Weight quantisation bits used for reconstruction.
        bit_a: Activation quantisation bits used for reconstruction.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.

    Returns:
        Path to the exported ExecuTorch program.
    """
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    pte_path = export_path / f"{model_name}.pte"

    model = QuantTinyCNN(num_classes=10, bit_w=bit_w, bit_a=bit_a)
    model.load_state_dict(state_dict)
    model.eval()

    try:
        from executorch.exir import to_edge_transform_and_lower
        from executorch.backends.xnnpack.partition.xnnpack_partitioner import (
            XnnpackPartitioner,
        )
        from brevitas.graph.calibrate import quantization_status_manager
    except ImportError as exc:
        raise RuntimeError(
            "ExecuTorch is not installed. Install it first (see https://github.com/pytorch/executorch)."
        ) from exc

    example_input = torch.randn(1, 1, 28, 28)
    with quantization_status_manager(
        model,
        disable_act_quant=True,
        disable_weight_quant=True,
        disable_bias_quant=True,
    ):
        exported_program = torch.export.export(model, (example_input,))

    program = to_edge_transform_and_lower(
        exported_program,
        partitioner=[XnnpackPartitioner()],
    ).to_executorch()

    pte_path.write_bytes(program.buffer)
    return str(pte_path)
