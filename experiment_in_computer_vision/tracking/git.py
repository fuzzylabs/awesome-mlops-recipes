"""Utilities for capturing Git metadata as MLflow artifacts."""

import os
import subprocess
import tempfile

import mlflow

from zenml.logger import get_logger

logger = get_logger(__name__)


def _get_git_info():
    """Collect the current Git diff and most recent commit message.

    Returns:
        tuple[str | None, str]: Path to the temporary diff file (if available)
        and the latest commit message.
    """
    try:
        # Get the most recent commit message
        commit_message = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            universal_newlines=True
        ).strip()

        # Create a temporary file to store the diff
        with tempfile.NamedTemporaryFile(delete=False, suffix='.diff') as temp_file:
            diff_file_path = temp_file.name

        # Trick to get the diff for previously untracked files
        subprocess.run(
            ["git", "add", "-N", "."],
            check=True,
        )

        # Get the diff between current state and most recent commit
        diff_output = subprocess.check_output(
            ["git", "diff", "HEAD"],
            universal_newlines=True
        )

        # Write the diff to the temporary file
        with open(diff_file_path, 'w') as f:
            f.write(diff_output)

        return diff_file_path, commit_message
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git information: {e}")
        return None, "No git information available"
    except Exception as e:
        logger.error(f"Unexpected error getting git information: {e}")
        return None, "No git information available"


def log_git_info() -> None:
    """Log the current Git diff and commit message to the active MLflow run."""
    diff_file_path, commit_message = _get_git_info()
    _log_git_info(commit_message, diff_file_path)


def _log_git_info(commit_message, diff_file_path):
    """Persist Git metadata to MLflow and clean up temporary files.

    Args:
        commit_message (str): Commit message to log.
        diff_file_path (str | None): Path to the temporary diff file, if one
            was created.
    """
    # Log git information
    if diff_file_path:
        mlflow.log_artifact(diff_file_path, "git_info")
        logger.info(f"Logged git diff as artifact")
        # Clean up the temporary file
        try:
            os.remove(diff_file_path)
        except Exception as e:
            logger.warning(f"Warning: Could not remove temporary diff file: {e}")
    mlflow.log_text(commit_message, "git_commit_message.txt")
    logger.info(f"Logged most recent commit message: {commit_message}")


def log_model_architecture(model):
    """Log the model architecture to MLflow and return current Git metadata.

    Args:
        model (torch.nn.Module): Model whose architecture representation is logged.

    Returns:
        tuple[str | None, str]: Path to the temporary diff file (if available)
        and the latest commit message.
    """
    mlflow.log_text(str(model), "model_architecture.txt")
    return _get_git_info()
