"""Convert a SavedModel to int8 TFLite."""

import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

from zenml import step


@step(enable_cache=False)  # type: ignore[untyped-decorator]
def convert_int8_tflite_step(
    saved_model_dir: str,
    export_dir: str = "artifacts/edge",
    model_name: str = "fashion_mnist_tiny_cnn",
    num_samples: int = 10,
) -> str:
    """Convert a SavedModel directory to an int8 TFLite model.

    The conversion needs to be run in a separate subporcess
    otherwise will deadlock and stuck.

    Args:
        saved_model_dir: Path to the SavedModel directory.
        export_dir: Directory to write exported artifacts.
        model_name: Base name for exported artifacts.
        num_samples: Representative dataset sample count.

    Returns:
        Path to the exported int8 TFLite model.
    """
    saved_model_path = Path(saved_model_dir)
    if not saved_model_path.is_dir():
        raise ValueError(f"SavedModel directory not found: {saved_model_path}")

    output_path = Path(export_dir) / f"{model_name}.tflite"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Converting {saved_model_path} to int8 TFLite...")

    # spellchecker:off
    int8_script = """
import sys
from pathlib import Path
import numpy as np
import tensorflow as tf

saved_model_dir = Path(sys.argv[1])
output_path = Path(sys.argv[2])
num_samples = int(sys.argv[3])

def representative_dataset():
    rng = np.random.default_rng(0)
    for _ in range(num_samples):
        yield [rng.random((1, 28, 28, 1), dtype=np.float32)]

converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
tflite_model = converter.convert()
output_path.write_bytes(tflite_model)
print(f"Saved int8 TFLite to {output_path}")
"""
    # spellchecker:on
    conversion_timeout_seconds = 600
    env = os.environ.copy()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as script_file:
        script_file.write(int8_script)
        script_path = script_file.name
    try:
        subprocess.run(  # nosec B603
            [
                sys.executable,
                script_path,
                str(saved_model_path),
                str(output_path),
                str(num_samples),
            ],
            check=True,
            env=env,
            timeout=conversion_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Int8 conversion timed out after {conversion_timeout_seconds} seconds."
        ) from exc
    finally:
        os.unlink(script_path)

    return str(output_path)
