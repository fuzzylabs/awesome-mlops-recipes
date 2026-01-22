"""Fallback Interpreter shim for platforms without ai_edge_litert wheels."""


try:
    from tensorflow.lite import Interpreter as _TfLiteInterpreter
except Exception:
    try:
        from tensorflow.lite.python.interpreter import Interpreter as _TfLiteInterpreter
    except Exception as exc:  # pragma: no cover - depends on local TF install
        raise ImportError(
            "TensorFlow Lite Interpreter is unavailable. Install TensorFlow to use "
            "the ai_edge_litert compatibility shim."
        ) from exc


class Interpreter(_TfLiteInterpreter):
    """Drop-in alias used by onnx2tf when ai_edge_litert is missing."""

