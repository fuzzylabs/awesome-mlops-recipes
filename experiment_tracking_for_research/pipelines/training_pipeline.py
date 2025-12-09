"""ZenML pipeline wiring data loading, training, and evaluation steps."""

from zenml import pipeline

from steps.data_loader import load_data_step
from steps.evaluate import evaluate_step
from steps.training import train_step


@pipeline
def training_pipeline(
    data_dir: str = "./data",
    num_epochs: int = 10,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    seed: int = 42,
):
    """Run the training workflow end-to-end."""
    train_features, train_labels, test_features, test_labels = load_data_step(
        data_dir=data_dir
    )
    model, metrics = train_step(
        train_features=train_features,
        train_labels=train_labels,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        seed=seed,
    )
    _ = evaluate_step(
        model=model,
        test_features=test_features,
        test_labels=test_labels,
        batch_size=batch_size,
    )
    return metrics
