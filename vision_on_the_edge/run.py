"""Entrypoint for running the vision on the edge training pipeline."""

import argparse
from functools import partial
from typing import Any, Dict

import optuna
import mlflow

from pipelines.training_pipeline import training_pipeline
from zenml.client import Client
import os

# load the experiment tracker configured in your active stack
tracker = Client().active_stack.experiment_tracker

os.environ["MLFLOW_TRACKING_USERNAME"] = tracker.config.tracking_username
os.environ["MLFLOW_TRACKING_PASSWORD"] = tracker.config.tracking_password



def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the training pipeline.

    Returns:
        Parsed CLI arguments.
    """
    parser = argparse.ArgumentParser(description="Run the ZenML training pipeline.")
    parser.add_argument("--num-epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate.")
    parser.add_argument("--bit-w", type=int, default=8, help="Quantisation bit width for weights.")
    parser.add_argument("--bit-a", type=int, default=8, help="Quantisation bit width for activations.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu", help="Device to train on.")
    parser.add_argument(
        "--optuna-trials",
        type=int,
        default=0,
        help="Number of Optuna trials to run. Set to 0 to skip hyperparameter search.",
    )
    parser.add_argument(
        "--alpha-latency",
        type=float,
        default=0.05,
        help="Penalty weight per millisecond of latency when computing the Optuna score.",
    )
    parser.add_argument(
        "--beta-size",
        type=float,
        default=0.2,
        help="Penalty weight per MB of model size when computing the Optuna score.",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default="artifacts/edge",
        help="Directory to write exported TFLite artifacts.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="fashion_mnist_tiny_cnn",
        help="Base name for exported model artifacts.",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip exporting the model to TFLite.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy a TFLite Micro model via PlatformIO after evaluation.",
    )
    parser.add_argument(
        "--platformio-project-dir",
        type=str,
        default=None,
        help="Path to the PlatformIO project used for ESP32 deployment.",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Build the PlatformIO project without uploading to the device.",
    )
    return parser.parse_args()


def run_single_training(args: argparse.Namespace, bit_w: int, bit_a: int) -> Dict[str, Any]:
    """Run the pipeline once and return metrics.

    Args:
        args: Parsed CLI arguments.
        bit_w: Bit width for weight quantization.
        bit_a: Bit width for activation quantization.

    Returns:
        A dictionary of metrics produced by the pipeline run.

    Raises:
        RuntimeError: If metrics cannot be retrieved from the pipeline run.
    """
    run_result = training_pipeline(
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        bit_w=bit_w,
        bit_a=bit_a,
        device=args.device,
        export_tflite=not args.no_export,
        export_dir=args.export_dir,
        model_name=args.model_name,
        deploy=args.deploy,
        platformio_project_dir=args.platformio_project_dir,
        upload=not args.no_upload,
    )

    # ZenML can return a PipelineRunView instead of direct outputs; try to read the evaluation artifact.
    if isinstance(run_result, dict):
        return run_result

    try:
        steps = getattr(run_result, "steps", None)
        if isinstance(steps, dict) and "evaluate_step" in steps:
            eval_step = steps["evaluate_step"]
            output = getattr(eval_step, "output", None)
            if output is not None:
                if hasattr(output, "read"):
                    return output.read()
                if hasattr(output, "load"):
                    return output.load()
    except Exception as exc:
        raise RuntimeError(f"Failed to retrieve metrics from pipeline run: {exc}") from exc

    raise RuntimeError(f"Could not retrieve metrics; got object of type {type(run_result)}")


def objective(trial: optuna.Trial, args: argparse.Namespace) -> float:
    """Optuna objective to search bit widths.

    Args:
        trial: Optuna trial instance.
        args: Parsed CLI arguments.

    Returns:
        Objective score combining accuracy, latency, and model size.
    """
    bit_w = trial.suggest_categorical("bit_w", [2, 4, 6, 8])
    bit_a = trial.suggest_categorical("bit_a", [2, 4, 6, 8])

    with mlflow.start_run(run_name=f"optuna-trial-{trial.number}", nested=True):
        metrics = run_single_training(args=args, bit_w=bit_w, bit_a=bit_a)
        accuracy = float(metrics.get("overall_accuracy", 0.0))
        latency = float(metrics.get("latency_ms", 0.0))
        size_mb = float(metrics.get("model_size_mb", 0.0))
        score = accuracy - args.alpha_latency * latency - args.beta_size * size_mb

        mlflow.log_params(
            {
                "trial_number": trial.number,
                "bit_w": bit_w,
                "bit_a": bit_a,
                "num_epochs": args.num_epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "device": args.device,
                "alpha_latency": args.alpha_latency,
                "beta_size": args.beta_size,
            }
        )
        mlflow.log_metrics(
            {
                "overall_accuracy": accuracy,
                "latency_ms": latency,
                "model_size_mb": size_mb,
                "score": score,
            }
        )

        return score


def main() -> None:
    """Run the ZenML pipeline end-to-end.

    Returns:
        None.
    """
    args = parse_args()

    mlflow.set_tracking_uri(tracker.config.tracking_uri)
    mlflow.set_experiment("vision-on-the-edge")

    if args.optuna_trials > 0:
        study = optuna.create_study(direction="maximize")
        study.optimize(partial(objective, args=args), n_trials=args.optuna_trials)

        print(f"Best trial score: {study.best_trial.value:.2f}")
        print(f"Best params: {study.best_trial.params}")
    else:
        with mlflow.start_run(run_name="single-run"):
            metrics = run_single_training(args=args, bit_w=args.bit_w, bit_a=args.bit_a)
            accuracy = float(metrics.get("overall_accuracy", 0.0))
            latency = float(metrics.get("latency_ms", 0.0))
            size_mb = float(metrics.get("model_size_mb", 0.0))
            score = accuracy - args.alpha_latency * latency - args.beta_size * size_mb

            mlflow.log_params(
                {
                    "bit_w": args.bit_w,
                    "bit_a": args.bit_a,
                    "num_epochs": args.num_epochs,
                    "batch_size": args.batch_size,
                    "learning_rate": args.learning_rate,
                    "device": args.device,
                    "alpha_latency": args.alpha_latency,
                    "beta_size": args.beta_size,
                }
            )
            mlflow.log_metrics(
                {
                    "overall_accuracy": accuracy,
                    "latency_ms": latency,
                    "model_size_mb": size_mb,
                    "score": score,
                }
            )

            print(f"Metrics: {metrics}")
            print(f"Score (accuracy - alpha*latency - beta*size): {score:.2f}")


if __name__ == "__main__":
    main()
