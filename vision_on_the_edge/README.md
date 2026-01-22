# 👀 Vision On The Edge

This recipe gives you a concrete, reusable starting point for any project where a vision model needs to live out in the wild.

**Cook Time:** ~30 minutes (depends heavily on your GPU; running this on a CPU will be very slow)

## 🥗 Ingredients

- **Hyperparameter optimisation framework**: [Optuna](https://optuna.org/)
- **Deep learning framework**: [Pytorch](https://github.com/pytorch/pytorch)
- **Quantisation aware training**: [Brevitas](https://xilinx.github.io/brevitas/v0.12.1/)
- **Experiment tracking**: [MLflow](https://mlflow.org/)
- **Pipeline orchestrator**: [ZenML](https://www.zenml.io/)
- **Model conversion**: ONNX, onnx2tf, TensorFlow Lite
- **Deployment**: [PlatformIO](https://platformio.org/)

## 🗄️ Project Structure

```
.                   # This recipe
├── run.py          # Entry point; runs Optuna search or single run
├── pipelines/      # ZenML pipeline wiring
├── steps/          # Data, train, eval, export, deploy steps
├── tiny_cnn.py     # Quantiseable tiny CNN for Fashion-MNIST
├── platformio_esp32/ # PlatformIO project for ESP32-S3 deployment
└── data/           # Fashion-MNIST cache (downloaded on first run)
```

## ✅ Prerequisites

- Python 3.12 with `uv` and `make`

## 🚀 Quick Start

1) Install deps and activate the venv

```bash
uv sync
source .venv/bin/activate
```

2) Start MLflow

```bash
# The basic auth app requires a secret key for CSRF protection.
export MLFLOW_FLASK_SERVER_SECRET_KEY="my-secret-key"
mlflow server --app-name basic-auth --backend-store-uri sqlite:///mlflow.db --port 5000
```

3) Point ZenML at MLflow

```bash
source .venv/bin/activate
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES # This is requried if you are on a Mac
zenml login --local
```

```bash
zenml experiment-tracker register mlflow_experiment_tracker \
    --flavor=mlflow \
    --tracking_uri=http://localhost:5000 \
    --tracking_username="admin" --tracking_password="password1234"

zenml stack register \
    -e mlflow_experiment_tracker experiment-computer-vision \
    -a default \
    -o default \
    --set
```

4) Run an experiment

```bash
python run.py --optuna-trials 10
```
The above commands will carry out 10 optuna trails based on objective defined in [run.py](run.py#83)

> Note: Optuna can also run a full grid search, which tries every possible combination of your parameters instead of sampling them randomly.

## 📦 Export + Deploy (Optional)

The pipeline exports a fully-quantized .pte model by default. Deployment to ESP32 via PlatformIO is optional and controlled by `--deploy`.

```bash
python run.py \
  --export-dir artifacts/edge \
  --model-name fashion_mnist_tiny_cnn \
  --deploy \
  --platformio-project-dir vision_on_the_edge/platformio_esp32
```

To skip export entirely:

```bash
python run.py --no-export
```

## 🔁 Optuna → Export → Deploy Flow

1) **Optimise with Optuna**  
Run Optuna to search hyperparameters; each trial runs the ZenML pipeline through evaluation only (no export/deploy).

```bash
python run.py --optuna-trials 10
```

2) **Pick the best trial**  
Use the Optuna output/MLflow to choose the best `bit_w`, `bit_a`, and other parameters.

3) **Export and deploy the chosen configuration**  
Run a single training with those parameters to export the .pte model and (optionally) deploy it to the ESP32.

```bash
python run.py \
  --bit-w 4 \
  --bit-a 4 \
  --export-dir artifacts/edge \
  --model-name fashion_mnist_tiny_cnn \
  --deploy \
  --platformio-project-dir vision_on_the_edge/platformio_esp32
```

When running Optuna (`--optuna-trials > 0`), export and deployment are skipped by design. Use the single-run path above for export/deployment of your chosen configuration.

### Configuring the ESP32 board and input source

- Board target: update the `board = ...` line in `vision_on_the_edge/platformio_esp32/platformio.ini`.
- Device connection: plug the ESP32-S3 into your laptop via USB before running `--deploy`. If PlatformIO cannot auto-detect the port, set `upload_port` in `vision_on_the_edge/platformio_esp32/platformio.ini`.
- Input source: `vision_on_the_edge/platformio_esp32/src/main.cpp` currently fills the input with a default value and runs one inference; replace that block with your real input capture (camera, sensor, serial, etc).
