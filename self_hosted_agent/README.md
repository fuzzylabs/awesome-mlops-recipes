# Self Hosted Agent

The self hosted agent recipe create a PR review agent

regions https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-regions.html

leaderboard https://huggingface.co/spaces/gorilla-llm/berkeley-function-calling-leaderboard

## Ingredients

- Agent Orchestration Framework: pydantic AI
- Model Serving: vLLM
- Agent Evaluation: Pydantic Eval
- Observability: Pydantic Logfire
- Prompt Versioning: MLFlow

## Structure
```
```

- src contains the agent source code
- evals contains eval suite
- llm contains the dockerfile for a vllm server, you can set the model you want to use there
- prompt versioning, helper script to register a new promp and update a new prompt version


## Getting Started

### MLFlow For Prompt Versioning
We will need to configure these first which.

```bash
MLFLOW_S3_BUCKET=""
MLFLOW_S3_ROLE_ARN=""
MLFLOW_DB_ENDPOINT=""
MLFLOW_DB_NAME=""
MLFLOW_DB_USERNAME=""
MLFLOW_DB_PASSWORD=""
```

1. Set up mlflow, run the helping sh script to isntall after setting the above value.

### Hosting a vLLM server For Our Agent

### Step 1: Choosing A Model and Build a vLLM server With It

You can configure which model you would like to use in the Dockerfile and various vllm parmaters.

Then, run the build and push script to build a vllm server docker image, make sure you are using a terminal that is already autheticated with aws already.

update the ecr repo name inside the buold and push script

```bash
./build-and-push.sh
```
This will automatica build and push to your ECR.

### Step 2: 

## Prompt Versioning

To create a new prompt on the mlflow prompt registry, lets portforward mlflow:

```bash
kubectl port-forward svc/mlflow 5000:5000 -n mlflow
```

Then, run new to create a new prompt

Run update to create a new version

