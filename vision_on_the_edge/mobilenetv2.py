"""Quantiseable MobileNetV2 model using Brevitas."""

import torch
import torch.nn as nn
import brevitas.nn as qnn
from brevitas.quant import Int8WeightPerTensorFloat, Int8ActPerTensorFloat # This is just the type of quantiser (scaled int, per tensor, etc). We can still use the same quantiser for different bit widths.
from torchvision.models._utils import _make_divisible


class QuantConvBNReLU(nn.Sequential):
    """Quantised Convolutional Block with Batch Normalisation and ReLU."""

    def __init__(self, in_c: int, out_c: int, stride: int, bit_w: int, bit_a: int) -> None:
        """Initialise the quantised convolutional block.

        Args:
            in_c: Input channels.
            out_c: Output channels.
            stride: Stride of the convolution.
            bit_w: Weight quantisation bits used for reconstruction.
            bit_a: Activation quantisation bits used for reconstruction.
        """
        super().__init__(
            qnn.QuantConv2d(
                in_channels=in_c,
                out_channels=out_c,
                kernel_size=3,
                stride=stride,
                padding=1,
                bias=False,
                weight_quant=Int8WeightPerTensorFloat,
                weight_bit_width=bit_w,
            ),
            nn.BatchNorm2d(out_c),
            qnn.QuantReLU(
                act_quant=Int8ActPerTensorFloat,
                bit_width=bit_a,
            ),
        )


class QuantInvertedResidual(nn.Module):
    """Quantised Inverted Residual Block."""

    def __init__(self, in_c: int, out_c: int, stride: int, expand_ratio: int, bit_w: int, bit_a: int) -> None:
        """Initialise the quantised inverted residual block.

        Args:
            in_c: Input channels.
            out_c: Output channels.
            stride: Stride of the convolution.
            expand_ratio: Expansion ratio of the residual block.
            bit_w: Weight quantisation bits used for reconstruction.
            bit_a: Activation quantisation bits used for reconstruction.
        """
        super().__init__()
        hidden_dim = int(round(in_c * expand_ratio))
        self.use_res = stride == 1 and in_c == out_c

        layers = []
        if expand_ratio != 1:
            # pointwise
            layers.extend(
                [
                    qnn.QuantConv2d(
                        in_c,
                        hidden_dim,
                        kernel_size=1,
                        stride=1,
                        padding=0,
                        bias=False,
                        weight_quant=Int8WeightPerTensorFloat,
                        weight_bit_width=bit_w,
                    ),
                    nn.BatchNorm2d(hidden_dim),
                    qnn.QuantReLU(
                        act_quant=Int8ActPerTensorFloat,
                        bit_width=bit_a,
                    ),
                ]
            )

        # depthwise
        layers.extend(
            [
                qnn.QuantConv2d(
                    hidden_dim,
                    hidden_dim,
                    kernel_size=3,
                    stride=stride,
                    padding=1,
                    groups=hidden_dim,
                    bias=False,
                    weight_quant=Int8WeightPerTensorFloat,
                    weight_bit_width=bit_w,
                ),
                nn.BatchNorm2d(hidden_dim),
                qnn.QuantReLU(
                    act_quant=Int8ActPerTensorFloat,
                    bit_width=bit_a,
                ),
            ]
        )

        # pointwise linear
        layers.extend(
            [
                qnn.QuantConv2d(
                    hidden_dim,
                    out_c,
                    kernel_size=1,
                    stride=1,
                    padding=0,
                    bias=False,
                    weight_quant=Int8WeightPerTensorFloat,
                    weight_bit_width=bit_w,
                ),
                nn.BatchNorm2d(out_c),
            ]
        )

        self.conv = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run the forward pass through the inverted residual block.

        Args:
            x: Input tensor.

        Returns:
            Output tensor after applying the block.
        """
        out = self.conv(x)
        if self.use_res:
            return x + out
        return out


class QuantMobileNetV2(nn.Module):
    """Quantised MobileNetV2 model."""

    def __init__(
        self,
        num_classes=1000,
        width_mult=1.0,
        bit_w=8,
        bit_a=8,
        round_nearest=8,
        dropout=0.2,
    ) -> None:
        """Initialise the quantised MobileNetV2 model.

        Args:
            num_classes: Number of classes.
            width_mult: Width multiplier.
            bit_w: Weight quantisation bits used for reconstruction.
            bit_a: Activation quantisation bits used for reconstruction.
            round_nearest: Round nearest.
            dropout: Dropout rate.
        """
        super().__init__()

        input_channel = 32
        last_channel = 1280

        # MobileNetV2 config: t, c, n, s
        inverted_residual_setting = [
            [1, 16, 1, 1],
            [6, 24, 2, 2],
            [6, 32, 3, 2],
            [6, 64, 4, 2],
            [6, 96, 3, 1],
            [6, 160, 3, 2],
            [6, 320, 1, 1],
        ]

        input_channel = _make_divisible(input_channel * width_mult, round_nearest)
        last_channel = _make_divisible(last_channel * max(1.0, width_mult), round_nearest)

        features = []

        # first conv: stride 2
        features.append(QuantConvBNReLU(3, input_channel, stride=2, bit_w=bit_w, bit_a=bit_a))

        # inverted residual blocks
        for t, c, n, s in inverted_residual_setting:
            output_channel = _make_divisible(c * width_mult, round_nearest)
            for i in range(n):
                stride = s if i == 0 else 1
                features.append(
                    QuantInvertedResidual(
                        input_channel,
                        output_channel,
                        stride=stride,
                        expand_ratio=t,
                        bit_w=bit_w,
                        bit_a=bit_a,
                    )
                )
                input_channel = output_channel

        # last conv
        features.append(
            QuantConvBNReLU(
                input_channel,
                last_channel,
                stride=1,
                bit_w=bit_w,
                bit_a=bit_a,
            )
        )

        self.features = nn.Sequential(*features)

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(p=dropout)
        self.classifier = qnn.QuantLinear(
            last_channel,
            num_classes,
            weight_quant=Int8WeightPerTensorFloat,
            weight_bit_width=bit_w,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the MobileNetV2 model.

        Args:
            x: Input tensor.

        Returns:
            Output logits tensor.
        """
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.classifier(x)
        return x
