from mobilenetv2 import QuantMobileNetV2
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from torch import nn, optim
import torch

def load_data_step(
    batch_size: int,
) -> tuple[DataLoader, DataLoader]:
    """Load the data for the vision on the edge.
    
    Args:
        batch_size: The batch size to use for the data loaders.

    Returns:
        A tuple of train and test data loaders.
    """
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])
    train_dataset = datasets.MNIST(root='data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root='data', train=False, download=True, transform=transform)

    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    return train_dataloader, test_dataloader



def train_step(
    device: str,
    train_dataloader: DataLoader,
    lr: float,
    num_epochs: int,
    bit_w: int = 8,
    bit_a: int = 8,
) -> nn.Module:
    """Train the quantised MobileNetV2 model."""

    # MNIST has 10 classes
    model = QuantMobileNetV2(
        num_classes=10,
        bit_w=bit_w,
        bit_a=bit_a,
    ).to(device)

    loss_fn = nn.CrossEntropyLoss()
    optimiser = optim.Adam(model.parameters(), lr=lr)

    model.train()

    for epoch in range(num_epochs):
        for batch_idx, (raw_inputs, raw_labels) in enumerate(train_dataloader):
            inputs, labels = raw_inputs.to(device), raw_labels.to(device)

            optimiser.zero_grad()

            outputs = model(inputs)
            loss = loss_fn(outputs, labels)

            loss.backward()
            optimiser.step()

            if batch_idx % 100 == 0:
                print(
                    f"Epoch [{epoch + 1}/{num_epochs}], "
                    f"Batch [{batch_idx}/{len(train_dataloader)}], "
                    f"Loss: {loss.item():.4f}"
                )

    return model


if __name__ == "__main__":
    train_dataloader, test_dataloader = load_data_step(batch_size=16)
    model = train_step(device="cpu", train_dataloader=train_dataloader, lr=0.001, num_epochs=1)
    torch.save(model.state_dict(), "quantised_mobilenetv2.pth")
    print(model)