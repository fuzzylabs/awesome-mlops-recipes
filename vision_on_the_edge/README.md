# 👀 Vision On The Edge

This recipe gives you a concrete, reusable starting point for any project where a vision model needs to live out in the wild.

**Cook Time:** ~30 minutes (depends heavily on your GPU; running this on a CPU will be very slow)

## 🥗 Ingredients

- **Hyperparameter optimisation framework**: [Optuna](https://optuna.org/)
- **Deep learning framework**: [Pytorch](https://github.com/pytorch/pytorch)
- **Quantisation aware training**: [Brevitas](https://xilinx.github.io/brevitas/v0.12.1/)
- **Experiment tracking**: [MLflow](https://mlflow.org/)
- **Pipeline orchestrator**: [ZenML](https://www.zenml.io/)

## 🗄️ Project Structure

```
.                   # This recipe
├── run.py          # Entry point; runs Optuna search or single run
├── pipelines/      # ZenML pipeline wiring
├── steps/          # Data, train, eval steps
├── mobilenetv2.py  # Quantiseable MobileNetV2
└── data/           # MNIST cache (downloaded on first run)
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
