"""Ray Serve proxy that forwards OpenAI-compatible requests to vLLM."""

import os

import httpx
from ray import serve
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://qwen3.vllm.svc.cluster.local:8000")


@serve.deployment(ray_actor_options={"num_cpus": 1})
class VLLMProxy:
    """Forward requests to a vLLM server behind Ray Serve."""

    def __init__(self) -> None:
        """Initialise the proxy client.

        Returns:
            None.
        """
        self.base_url = VLLM_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120)

    async def __call__(self, request: Request) -> Response:
        """Handle incoming requests and forward to vLLM.

        Args:
            request: Incoming HTTP request.

        Returns:
            The proxied HTTP response.
        """
        if request.url.path == "/health":
            return JSONResponse({"status": "ok"})

        target_url = f"{self.base_url}{request.url.path}"
        body = await request.body()
        headers = {"content-type": request.headers.get("content-type", "application/json")}
        upstream = await self.client.request(
            request.method,
            target_url,
            content=body,
            headers=headers,
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers={"content-type": upstream.headers.get("content-type", "application/json")},
        )


app = VLLMProxy.bind()  # type: ignore[attr-defined]
