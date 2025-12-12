"""Model definitions for the vision on the edge."""

import torch.nn as nn
from torchvision import models


def mobilenet_v2() -> nn.Module:
    """Create a MobileNetV2 backbone configured for MNIST classification.

    Returns:
        A MobileNetV2 model adapted to produce 10-class outputs.
    """
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 10) # Swap MobileNet's classifier for a 10-class head.

    return model


def resnet18() -> nn.Module:
    """Create a ResNet18 backbone configured for MNIST classification.

    Returns:
        A ResNet18 model with a 10-class fully connected head.
    """
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, 10)

    return model
