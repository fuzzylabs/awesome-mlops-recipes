# 👀 Vision On The Edge

This recipe gives you a concrete, reusable starting point for any project where a vision model needs to live out in the wild.

**Cook Time:** ~30 minutes (depends heavily on your GPU; running this on a CPU will be very slow)

## 🥗 Ingredients

- **Hyperparameter optimisation framework**: [Optuna](https://optuna.org/)
- **Deep learning framework**: [Pytorch](https://github.com/pytorch/pytorch)
- **Quantisation aware training**: [Brevitas](https://xilinx.github.io/brevitas/v0.12.1/)
- **Experiment tracking**: [MLflow](https://mlflow.org/)
- **Pipeline orchestrator**: [ZenML](https://www.zenml.io/) with local orchestrator
- **Model conversion**: ONNX → onnx2tf → TensorFlow SavedModel → TFLite (int8)
- **Deployment**: [PlatformIO](https://platformio.org/)

## 🗄️ Project Structure

```
.                     # This recipe
├── run.py            # Entry point; runs Optuna search or single run
├── pipelines/        # ZenML pipeline wiring
├── steps/            # Data, train, eval, export, deploy steps
├── tiny_cnn.py       # Quantiseable tiny CNN for Fashion-MNIST
├── platformio_esp32/ # PlatformIO project for ESP32-S3 deployment
└── data/             # Fashion-MNIST cache (downloaded on first run)
```

## ✅ Prerequisites

- Python 3.12 with `uv` and `make`

## 🚀 Quick Start

### 1. Install dependencies and activate the venv

```bash
uv sync --extra tflite-export
source .venv/bin/activate
```

### 2. Start MLflow

```bash
export MLFLOW_FLASK_SERVER_SECRET_KEY="my-secret-key"
mlflow server --app-name basic-auth --backend-store-uri sqlite:///mlflow.db --port 5000
```

### 3. Configure ZenML

```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # Required on macOS
zenml login --local
```

Register the MLflow experiment tracker:

```bash
zenml experiment-tracker register mlflow_experiment_tracker \
    --flavor=mlflow \
    --tracking_uri=http://localhost:5000 \
    --tracking_username="admin" \
    --tracking_password="password1234"
```

Create and activate the stack:

```bash
zenml stack register vision-on-the-edge \
    -e mlflow_experiment_tracker \
    -a default \
    -o default \
    --set
```

### 4. Run the pipeline

Train the model and export to TFLite:

```bash
python run.py \
    --export-dir artifacts/edge \
    --model-name fashion_mnist_tiny_cnn
```

> Make sure the `tflite-export` dependency group is installed locally since the pipeline runs in the local orchestrator.

## 🔁 Optuna Hyperparameter Search

Run Optuna to search hyperparameters (export/deploy is skipped during search):

```bash
python run.py --optuna-trials 10
```

Pick the best trial from Optuna output or MLflow, then run a single training with those parameters:

```bash
python run.py \
    --bit-w 4 \
    --bit-a 4 \
    --export-dir artifacts/edge \
    --model-name fashion_mnist_tiny_cnn
```

## 📦 ESP32 Deployment (Optional)

> Note: PlatformIO requires Linux (or a Linux container/CI), because the tensorflow/tflite-micro
> package in the PIO registry doesn’t have a build for darwin_arm64 (Apple Silicon), so installs
> fail during `platformio run` on macOS.

To deploy the TFLite model to an ESP32 via PlatformIO:

```bash
python run.py \
    --bit-w 4 \
    --bit-a 4 \
    --export-dir artifacts/edge \
    --model-name fashion_mnist_tiny_cnn \
    --deploy \
    --platformio-project-dir platformio_esp32
```

### Configuring the ESP32

- **Board target:** Update the `board = ...` line in `platformio_esp32/platformio.ini`.
- **Device connection:** Plug the ESP32-S3 into your laptop via USB before running `--deploy`. If PlatformIO cannot auto-detect the port, set `upload_port` in `platformio_esp32/platformio.ini`.
- **Input source:** `platformio_esp32/src/main.cpp` currently fills the input with a default value and runs one inference; replace that block with your real input capture (camera, sensor, serial, etc).

## 🧩 Why ONNX conversion needs constant folding

When exporting from Brevitas (QAT), Conv weights are often represented as a small ONNX subgraph
(fake-quant ops like `Mul`, `Where`, `Clip`, etc.) instead of a single constant tensor.
`onnx2tf` only transposes Conv weights when they are constants. If weights stay as a computed
tensor, TensorFlow receives them in ONNX layout (`[out, in, kH, kW]`) and fails with a shape
mismatch (e.g. “input depth 32 is not a multiple of filter depth 3”).

To fix this, the export step runs a light **constant-folding** pass that evaluates any
fully-constant subgraphs and replaces them with a single initialiser. That makes the Conv
weights look like constants again so `onnx2tf` can transpose them correctly.

This issue is specific to quantisation/fake-quant flows (like Brevitas). A plain PyTorch model
usually exports Conv weights as constants and does not require this extra folding step.

## 🛠️ CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--num-epochs` | 3 | Number of training epochs |
| `--batch-size` | 16 | Training batch size |
| `--learning-rate` | 0.001 | Learning rate |
| `--bit-w` | 8 | Weight quantisation bit width |
| `--bit-a` | 8 | Activation quantisation bit width |
| `--device` | cpu | Device to train on (auto/cpu/cuda) |
| `--optuna-trials` | 0 | Number of Optuna trials (0 = skip search) |
| `--export-dir` | artifacts/edge | Directory for TFLite artifacts |
| `--model-name` | fashion_mnist_tiny_cnn | Base name for exported model |
| `--no-export` | - | Skip TFLite export |
| `--deploy` | - | Deploy to ESP32 via PlatformIO |
| `--platformio-project-dir` | - | Path to PlatformIO project |
| `--no-upload` | - | Build without uploading to device |
