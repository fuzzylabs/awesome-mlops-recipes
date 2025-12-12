"""Training step."""

from zenml import step
from zenml.logger import get_logger
from torch import nn, optim
from torch.utils.data import DataLoader
import torch
from mobilenetv2 import QuantMobileNetV2
from zenml.integrations.constants import PYTORCH

logger = get_logger(__name__)


@step(enable_cache=False)
def train_step(
    device: str,
    train_dataloader: DataLoader,
    lr: float,
    num_epochs: int,
    bit_w: int,
    bit_a: int,
) -> dict[str, torch.Tensor]:
    """Train the model and return its state dict."""

    model = QuantMobileNetV2(num_classes=10, bit_w=bit_w, bit_a=bit_a).to(device)

    loss_fn = nn.CrossEntropyLoss()
    optimiser = optim.Adam(model.parameters(), lr=lr)

    model.train()

    for epoch in range(num_epochs):
        for batch_idx, (raw_inputs, raw_labels) in enumerate(train_dataloader):
            inputs, labels = raw_inputs.to(device), raw_labels.to(device)

            # Zero gradients
            optimiser.zero_grad()

            # Forward pass
            outputs = model(inputs)
            loss = loss_fn(outputs, labels)

            # Backward pass and optimize
            loss.backward()
            optimiser.step()

            # Log progress every 100 batches
            if batch_idx % 100 == 0:
                logger.info(
                    f"Epoch [{epoch + 1}/{num_epochs}], "
                    f"Batch [{batch_idx}/{len(train_dataloader)}], "
                    f"Loss: {loss.item():.4f}"
                )

    # Move to CPU before returning to avoid device-specific serialization issues
    model = model.cpu()
    return model.state_dict()
