FROM vllm/vllm-openai:latest

# Set environment variables
ENV MODEL_NAME="Qwen/Qwen3-4B-Thinking-2507"
ENV VLLM_LOGGING_LEVEL="INFO"

# Create model cache directory
RUN mkdir -p /root/.cache/huggingface

# Expose vLLM API port
EXPOSE 8000

# Override the entrypoint and use vllm serve directly
ENTRYPOINT []
CMD ["/bin/sh", "-c", "\
    vllm serve ${MODEL_NAME} \
    --max-num-batched-tokens 50000 \
    --max-model-len 50000 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --host 0.0.0.0 \
    --port 8000\
    "]
