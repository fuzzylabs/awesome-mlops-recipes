"""Quantised tiny CNN for Fashion-MNIST using Brevitas."""

import brevitas.nn as qnn
from brevitas.quant import Int8ActPerTensorFloat, Int8WeightPerTensorFloat
import torch
from torch import nn


class QuantTinyCNN(nn.Module):  # type: ignore[misc]
    """Small quantised CNN suitable for microcontroller-class targets."""

    def __init__(self, num_classes: int, bit_w: int, bit_a: int) -> None:
        """Initialise the tiny CNN.

        Args:
            num_classes: Number of output classes.
            bit_w: Weight quantisation bit width.
            bit_a: Activation quantisation bit width.
        """
        super().__init__()
        self.features = nn.Sequential(
            qnn.QuantConv2d(
                in_channels=1,
                out_channels=16,
                kernel_size=3,
                padding=1,
                bias=False,
                weight_quant=Int8WeightPerTensorFloat,
                weight_bit_width=bit_w,
            ),
            nn.BatchNorm2d(16),
            qnn.QuantReLU(act_quant=Int8ActPerTensorFloat, bit_width=bit_a),
            nn.MaxPool2d(2),
            qnn.QuantConv2d(
                in_channels=16,
                out_channels=32,
                kernel_size=3,
                padding=1,
                bias=False,
                weight_quant=Int8WeightPerTensorFloat,
                weight_bit_width=bit_w,
            ),
            nn.BatchNorm2d(32),
            qnn.QuantReLU(act_quant=Int8ActPerTensorFloat, bit_width=bit_a),
            nn.MaxPool2d(2),
            qnn.QuantConv2d(
                in_channels=32,
                out_channels=64,
                kernel_size=3,
                padding=1,
                bias=False,
                weight_quant=Int8WeightPerTensorFloat,
                weight_bit_width=bit_w,
            ),
            nn.BatchNorm2d(64),
            qnn.QuantReLU(act_quant=Int8ActPerTensorFloat, bit_width=bit_a),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = qnn.QuantLinear(
            in_features=64,
            out_features=num_classes,
            weight_quant=Int8WeightPerTensorFloat,
            weight_bit_width=bit_w,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run a forward pass through the network.

        Args:
            x: Input tensor batch.

        Returns:
            Output logits tensor.
        """
        x = self.features(x)
        x = self.pool(x)
        x = x.flatten(1)
        return self.classifier(x)
