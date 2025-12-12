"""Data loading for the vision on the edge."""

from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step(enable_cache=False)
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
