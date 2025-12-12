"""Entrypoint for running the vision on the edge training pipeline."""

import argparse
from pipelines.training_pipeline import training_pipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the training pipeline."""
    parser = argparse.ArgumentParser(description="Run the ZenML training pipeline.")
    parser.add_argument("--num-epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate.")
    return parser.parse_args()


def main() -> None:
    """Run the ZenML pipeline end-to-end."""
    args = parse_args()

    training_pipeline(
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )

if __name__ == "__main__":
    main()