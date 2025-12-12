"""Quantisation helper functions."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import torch
from torch import nn
from torchao.quantization import (
    Float8DynamicActivationFloat8WeightConfig,
    Float8WeightOnlyConfig,
    Int4WeightOnlyConfig,
    Int8DynamicActivationInt8WeightConfig,
    Int8WeightOnlyConfig,
    quantize_,
)

from model import mobilenet_v2


def load_model(model_path: str) -> nn.Module:
    """Load a MobileNetV2 checkpoint."""
    model = mobilenet_v2()
    state_dict = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state_dict)
    return model


QuantConfigName = Literal[
    "int4_weight_only",
    "int8_weight_only",
    "int8_dynamic",
    "float8_weight_only",
    "float8_dynamic",
]


_CONFIGS: dict[QuantConfigName, nn.Module] = {
    "int4_weight_only": Int4WeightOnlyConfig(),
    "int8_weight_only": Int8WeightOnlyConfig(),
    "int8_dynamic": Int8DynamicActivationInt8WeightConfig(),
    "float8_weight_only": Float8WeightOnlyConfig(),
    "float8_dynamic": Float8DynamicActivationFloat8WeightConfig(),
}


def quantise_model(
    model: nn.Module,
    config_name: QuantConfigName,
    device: str | torch.device = "cpu",
) -> nn.Module:
    """Apply torchao quantisation in-place and return the model."""
    model.to(device)
    config = _CONFIGS[config_name]
    quantize_(model, config=config)
    model.eval()
    return model


def save_quantised(model: nn.Module, output_path: str | Path) -> None:
    """Save the quantised model weights."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)



if __name__ == "__main__":
    model = load_model("checkpoint.pt")  # or "entire_model.pt" if it’s a state_dict
    qmodel = quantise_model(model, config_name="int8_weight_only", device="cpu")
    save_quantised(qmodel, "quantised/int8_weight_only.pt")