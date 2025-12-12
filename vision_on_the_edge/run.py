"""Entrypoint for running the vision on the edge training pipeline."""

import argparse
from functools import partial
from typing import Any, Dict

import optuna

from pipelines.training_pipeline import training_pipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the training pipeline."""
    parser = argparse.ArgumentParser(description="Run the ZenML training pipeline.")
    parser.add_argument("--num-epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate.")
    parser.add_argument("--bit-w", type=int, default=8, help="Quantisation bit width for weights.")
    parser.add_argument("--bit-a", type=int, default=8, help="Quantisation bit width for activations.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="cpu", help="Device to train on.")
    parser.add_argument(
        "--optuna-trials",
        type=int,
        default=0,
        help="Number of Optuna trials to run. Set to 0 to skip hyperparameter search.",
    )
    return parser.parse_args()


def run_single_training(args: argparse.Namespace, bit_w: int, bit_a: int) -> Dict[str, Any]:
    """Run the pipeline once and return metrics."""
    metrics = training_pipeline(
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        bit_w=bit_w,
        bit_a=bit_a,
        device=args.device,
    )

    if not isinstance(metrics, dict):
        raise RuntimeError("Expected metrics dictionary from training pipeline.")

    return metrics


def objective(trial: optuna.Trial, args: argparse.Namespace) -> float:
    """Optuna objective to search bit widths."""
    bit_w = trial.suggest_categorical("bit_w", [2, 4, 6, 8])
    bit_a = trial.suggest_categorical("bit_a", [2, 4, 6, 8])

    metrics = run_single_training(args=args, bit_w=bit_w, bit_a=bit_a)
    return float(metrics.get("overall_accuracy", 0.0))


def main() -> None:
    """Run the ZenML pipeline end-to-end."""
    args = parse_args()

    if args.optuna_trials > 0:
        study = optuna.create_study(direction="maximize")
        study.optimize(partial(objective, args=args), n_trials=args.optuna_trials)

        print(f"Best trial accuracy: {study.best_trial.value:.2f}")
        print(f"Best params: {study.best_trial.params}")
    else:
        metrics = run_single_training(args=args, bit_w=args.bit_w, bit_a=args.bit_a)
        print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()
