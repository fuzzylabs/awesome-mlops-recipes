"""Helpers for exposing the project logbook to MLflow runs."""


def get_logbook():
    """Read the local LOGBOOK and return its contents as a string.

    Returns:
        str: Markdown contents of `LOGBOOK.md`.
    """
    with open("LOGBOOK.md", "r") as file:
        logbook = file.read()

    return logbook
