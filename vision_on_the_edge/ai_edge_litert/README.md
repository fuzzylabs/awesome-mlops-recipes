# What is this?

This folder provides a small compatibility shim for `ai_edge_litert`.

`onnx2tf` tries to import `ai_edge_litert.Interpreter` on startup. That
package only ships Linux wheels, so the import fails on macOS. This shim
defines the same `Interpreter` name by re-exporting TensorFlow Lite’s
interpreter instead. In other words:

- On macOS, `onnx2tf` imports this shim and continues using TensorFlow Lite.
- On Linux, you can install the real `ai_edge_litert` package and ignore this.

No model logic changes here; it is just a thin import bridge so conversion
doesn’t crash on platforms without `ai_edge_litert` wheels.

`onnx2tf` uses this interpreter during conversion only to run small inference
checks/validations. The shim provides a TensorFlow Lite-backed interpreter
so those checks still work on macOS.

If you are on linux feel free to install `ai_edge_litert` by doing:
```bash
uv add ai-edge-litert
```

And remove the shim.