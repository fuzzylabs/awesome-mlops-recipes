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
    """Load Fashion-MNIST data and return train/test data loaders.

    Args:
        batch_size: Batch size to use for the data loaders.

    Returns:
        A tuple of train and test data loaders.
    """
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.2860], std=[0.3530]),
        ]
    )
    train_dataset = datasets.FashionMNIST(
        root="data", train=True, download=True, transform=transform
    )
    test_dataset = datasets.FashionMNIST(
        root="data", train=False, download=True, transform=transform
    )

    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    return train_dataloader, test_dataloader
