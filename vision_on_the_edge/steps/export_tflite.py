"""Export a trained model to a SavedModel directory."""

import logging
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path

import torch
from tiny_cnn import QuantTinyCNN
from zenml import step

logger = logging.getLogger(__name__)


def _fold_constant_ops(onnx_path: Path, output_path: Path) -> Path | None:
    """Fold constant operations in an ONNX graph.

    Args:
        onnx_path: Path to the input ONNX model.
        output_path: Path to write the folded ONNX model.

    Returns:
        Path to the folded model, or None if no changes were made.
    """
    try:
        import numpy as np
        import onnx
        from onnx import numpy_helper
    except Exception:
        return None

    model = onnx.load(str(onnx_path))
    graph = model.graph
    initializer_map = {
        initializer.name: numpy_helper.to_array(initializer)
        for initializer in graph.initializer
    }

    def set_initializer(name: str, value: np.ndarray) -> None:
        for initializer in list(graph.initializer):
            if initializer.name == name:
                graph.initializer.remove(initializer)
        graph.initializer.append(numpy_helper.from_array(value, name))
        initializer_map[name] = value

    def cast_like(value: np.ndarray, reference: np.ndarray) -> np.ndarray:
        if value.dtype == reference.dtype:
            return value
        return value.astype(reference.dtype)

    changed = False
    progress = True
    while progress:
        progress = False
        for node in list(graph.node):
            if node.op_type == "Constant":
                attr = next(
                    (
                        attribute
                        for attribute in node.attribute
                        if attribute.name == "value"
                    ),
                    None,
                )
                if attr is None:
                    continue
                value = numpy_helper.to_array(attr.t)
                set_initializer(node.output[0], value)
                graph.node.remove(node)
                changed = True
                progress = True
                continue

            if node.op_type == "Cast":
                if len(node.input) != 1 or node.input[0] not in initializer_map:
                    continue
                to_type = next(
                    (
                        attribute
                        for attribute in node.attribute
                        if attribute.name == "to"
                    ),
                    None,
                )
                if to_type is None:
                    continue
                np_dtype = onnx.helper.tensor_dtype_to_np_dtype(to_type.i)
                if np_dtype is None:
                    continue
                value = initializer_map[node.input[0]].astype(np_dtype)
                set_initializer(node.output[0], value)
                graph.node.remove(node)
                changed = True
                progress = True
                continue

            if any(input_name not in initializer_map for input_name in node.input):
                continue

            inputs = [initializer_map[input_name] for input_name in node.input]
            result = None
            if node.op_type == "Mul" and len(inputs) == 2:
                result = cast_like(inputs[0] * inputs[1], inputs[0])
            elif node.op_type == "Add" and len(inputs) == 2:
                result = cast_like(inputs[0] + inputs[1], inputs[0])
            elif node.op_type == "Sub" and len(inputs) == 2:
                result = cast_like(inputs[0] - inputs[1], inputs[0])
            elif node.op_type == "Div" and len(inputs) == 2:
                result = cast_like(inputs[0] / inputs[1], inputs[0])
            elif node.op_type == "Abs" and len(inputs) == 1:
                result = cast_like(np.abs(inputs[0]), inputs[0])
            elif node.op_type == "Round" and len(inputs) == 1:
                result = cast_like(np.round(inputs[0]), inputs[0])
            elif node.op_type == "Greater" and len(inputs) == 2:
                result = np.greater(inputs[0], inputs[1])
            elif node.op_type == "Less" and len(inputs) == 2:
                result = np.less(inputs[0], inputs[1])
            elif node.op_type == "GreaterOrEqual" and len(inputs) == 2:
                result = np.greater_equal(inputs[0], inputs[1])
            elif node.op_type == "Where" and len(inputs) == 3:
                result = cast_like(np.where(inputs[0], inputs[1], inputs[2]), inputs[1])
            elif node.op_type == "Clip":
                if len(inputs) == 2:
                    result = np.maximum(inputs[0], inputs[1])
                elif len(inputs) == 3:
                    result = np.clip(inputs[0], inputs[1], inputs[2])
            elif node.op_type == "ReduceMax":
                keepdims_attr = next(
                    (
                        attribute
                        for attribute in node.attribute
                        if attribute.name == "keepdims"
                    ),
                    None,
                )
                keepdims = bool(keepdims_attr.i) if keepdims_attr is not None else True
                axes = None
                if len(inputs) >= 2:
                    axes = tuple(int(x) for x in inputs[1].flatten())
                else:
                    axes_attr = next(
                        (
                            attribute
                            for attribute in node.attribute
                            if attribute.name == "axes"
                        ),
                        None,
                    )
                    if axes_attr is not None:
                        axes = tuple(axes_attr.ints)
                result = np.max(inputs[0], axis=axes, keepdims=keepdims)
            elif node.op_type == "Reshape" and len(inputs) == 2:
                allowzero_attr = next(
                    (
                        attribute
                        for attribute in node.attribute
                        if attribute.name == "allowzero"
                    ),
                    None,
                )
                allowzero = (
                    bool(allowzero_attr.i) if allowzero_attr is not None else False
                )
                shape = [int(x) for x in inputs[1].flatten()]
                if not allowzero:
                    shape = [
                        inputs[0].shape[idx] if dim == 0 else dim
                        for idx, dim in enumerate(shape)
                    ]
                result = np.reshape(inputs[0], shape)

            if result is None:
                continue

            set_initializer(node.output[0], result)
            graph.node.remove(node)
            changed = True
            progress = True

    if not changed:
        return None

    onnx.save(model, str(output_path))
    return output_path


@step(enable_cache=False)  # type: ignore[untyped-decorator]
def export_saved_model_step(
    state_dict: dict[str, torch.Tensor],
    bit_w: int,
    bit_a: int,
    export_dir: str = "artifacts/edge",
    model_name: str = "fashion_mnist_tiny_cnn",
) -> str:
    """Export a trained model to a SavedModel directory.

    Args:
        state_dict: Trained model weights.
        bit_w: Weight quantisation bits used for reconstruction.
        bit_a: Activation quantisation bits used for reconstruction.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.

    Returns:
        Path to the exported SavedModel directory.
    """
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    onnx_path = export_path / f"{model_name}.onnx"
    saved_model_dir = export_path / f"{model_name}_saved_model"
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
        opset_version=18,
    )

    onnx_path_for_conversion = onnx_path
    try:
        import onnx
        from onnxsim import simplify

        onnx_model = onnx.load(str(onnx_path))
        simplified_model, check = simplify(
            onnx_model, input_shapes={"input": [1, 1, 28, 28]}
        )
        if check:
            simplified_path = export_path / f"{model_name}_simplified.onnx"
            onnx.save(simplified_model, str(simplified_path))
            onnx_path_for_conversion = simplified_path
    except Exception as exc:
        logger.warning(
            "ONNX simplification failed; continuing with original graph. %s", exc
        )

    folded_path = _fold_constant_ops(
        onnx_path_for_conversion, export_path / f"{model_name}_folded.onnx"
    )
    if folded_path is not None:
        onnx_path_for_conversion = folded_path

    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(project_root), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    onnx2tf_command = [
        "onnx2tf",
        "-i",
        str(onnx_path_for_conversion),
        "-o",
        str(saved_model_dir),
    ]
    if shutil.which("onnxsim") is None:
        onnx2tf_command.append("--not_use_onnxsim")

    def run_onnx2tf(command: list[str]) -> None:
        """Run onnx2tf and retry with auto-generated params on failure.

        Args:
            command: Command list to execute.

        Returns:
            None.
        """
        try:
            subprocess.run(  # nosec B603
                command,
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError:
            auto_json = saved_model_dir / f"{model_name}_auto.json"
            if auto_json.is_file():
                subprocess.run(  # nosec B603
                    command + ["--param_replacement_file", str(auto_json)],
                    check=True,
                    env=env,
                )
            else:
                raise

    try:
        run_onnx2tf(onnx2tf_command)
    except subprocess.CalledProcessError:
        run_onnx2tf(onnx2tf_command + ["--disable_strict_mode"])

    return str(saved_model_dir)
