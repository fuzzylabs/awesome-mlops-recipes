"""Compatibility shim for onnx2tf's optional ai_edge_litert dependency."""

from .interpreter import Interpreter

__all__ = ["Interpreter"]
