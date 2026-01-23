"""Deploy a TFLite Micro model to ESP32 via PlatformIO."""

import shutil
import subprocess  # nosec B404
from pathlib import Path

from zenml import step


def _write_c_array(data: bytes, array_name: str, out_cc: Path, out_h: Path) -> None:
    """Write binary data into C array source and header files.

    Args:
        data: Binary payload to embed.
        array_name: C array symbol name.
        out_cc: Output path for the C++ source file.
        out_h: Output path for the header file.

    Returns:
        None.
    """
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


@step(enable_cache=False)  # type: ignore[untyped-decorator]
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
    candidates = [project_dir]
    if not project_dir.is_absolute():
        base_dir = Path(__file__).resolve().parents[1]
        repo_root = base_dir.parent
        candidates.extend([base_dir / project_dir, repo_root / project_dir])
        if project_dir.parts and project_dir.parts[0] == base_dir.name:
            candidates.append(base_dir / Path(*project_dir.parts[1:]))
    for candidate in candidates:
        if candidate.is_dir():
            project_dir = candidate
            break

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

    platformio_bin = shutil.which("platformio")
    if not platformio_bin:
        raise FileNotFoundError("platformio executable not found on PATH")
    command = [platformio_bin, "run"]
    if upload:
        command += ["-t", "upload"]
    subprocess.run(command, cwd=project_dir, check=True)  # nosec B603

    return f"Deployed {model_path.name} via PlatformIO"
