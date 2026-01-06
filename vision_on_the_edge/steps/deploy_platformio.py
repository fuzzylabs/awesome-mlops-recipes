"""Deploy a TFLite Micro model to ESP32 via PlatformIO."""

from __future__ import annotations

import subprocess
from pathlib import Path

from zenml import step


def _write_c_array(data: bytes, array_name: str, out_cc: Path, out_h: Path) -> None:
    hex_bytes = ", ".join(f"0x{b:02x}" for b in data)
    out_cc.write_text(
        "\n".join(
            [
                '#include "model_data.h"',
                "",
                f"const unsigned char {array_name}[] = {{",
                f"  {hex_bytes}",
                "};",
                f"const unsigned int {array_name}_len = {len(data)};",
                "",
            ]
        ),
        encoding="ascii",
    )
    out_h.write_text(
        "\n".join(
            [
                "#pragma once",
                "",
                f"extern const unsigned char {array_name}[];",
                f"extern const unsigned int {array_name}_len;",
                "",
            ]
        ),
        encoding="ascii",
    )


@step(enable_cache=False)
def deploy_platformio_step(
    tflite_model_path: str,
    platformio_project_dir: str,
    upload: bool = True,
) -> str:
    """Package a TFLite model into a PlatformIO project and upload it.

    Args:
        tflite_model_path: Path to a TFLite model file.
        platformio_project_dir: PlatformIO project directory with a src/ folder.
        upload: Whether to upload the firmware after building.

    Returns:
        Status message.
    """
    project_dir = Path(platformio_project_dir)
    src_dir = project_dir / "src"
    if not src_dir.is_dir():
        raise ValueError(f"PlatformIO src directory not found: {src_dir}")

    model_path = Path(tflite_model_path)
    if not model_path.is_file():
        raise ValueError(f"TFLite model not found: {model_path}")

    model_data = model_path.read_bytes()
    model_cc_path = src_dir / "model_data.cc"
    model_h_path = src_dir / "model_data.h"
    _write_c_array(model_data, "g_model", model_cc_path, model_h_path)

    command = ["platformio", "run"]
    if upload:
        command += ["-t", "upload"]
    subprocess.run(command, cwd=project_dir, check=True)

    return f"Deployed {model_path.name} via PlatformIO"
