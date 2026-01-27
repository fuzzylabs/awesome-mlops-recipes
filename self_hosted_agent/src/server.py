"""FastAPI server for PR review agent."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from agent import initialise_agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Args:
        app: FastAPI application instance.

    Returns:
        AsyncContextManager[None]: Async context manager for lifespan handling.
    """
    # Load the agent on startup
    app.state.pr_review_agent, app.state.prompt_version = initialise_agent()
    yield
    # Clean up resources on shutdown
    app.state.pr_review_agent = None
    app.state.prompt_version = None


app = FastAPI(title="PR Review Agent", version="1.0.0", lifespan=lifespan)


class ReviewRequest(BaseModel):  # type: ignore[misc]
    """Request body for PR review.

    Args:
        pr_title: Title of the pull request.
    """

    pr_title: str


class ReviewResponse(BaseModel):  # type: ignore[misc]
    """Response for PR review.

    Args:
        review: Generated review text.
        status: Review status string.
    """

    review: str
    status: str = "completed"


@app.get("/")  # type: ignore[untyped-decorator]
async def root() -> dict[str, object]:
    """Return basic service metadata.

    Returns:
        dict[str, object]: Metadata payload for the service.
    """
    return {
        "service": "PR Review Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "review": "/review (POST)",
            "prompt_version": "/prompt_version (GET)",
        },
    }


@app.get("/prompt_version")  # type: ignore[untyped-decorator]
async def prompt_version() -> dict[str, str | int]:
    """Return the active prompt version.

    Returns:
        dict[str, str | int]: Prompt version payload.
    """
    return {"prompt_version": app.state.prompt_version}


@app.get("/health")  # type: ignore[untyped-decorator]
async def health() -> dict[str, str]:
    """Report service health.

    Returns:
        dict[str, str]: Health status payload.
    """
    return {"status": "healthy", "service": "pr-review-agent"}


@app.post("/review", response_model=ReviewResponse)  # type: ignore[untyped-decorator]
async def review_pr(request: ReviewRequest) -> ReviewResponse:
    """Review a pull request based on its title.

    Args:
        request: ReviewRequest containing the PR title.

    Returns:
        ReviewResponse: Response with the agent's review.
    """
    try:
        # Get the agent from app state
        agent = app.state.pr_review_agent

        # Run the agent with the PR title (use await in async context!)
        result = await agent.run(f'Review the pull request titled "{request.pr_title}"')

        return ReviewResponse(review=result.output, status="completed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to review PR: {str(e)}")


if __name__ == "__main__":
    host = os.getenv("PR_REVIEW_HOST", "127.0.0.1")
    port = int(os.getenv("PR_REVIEW_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
