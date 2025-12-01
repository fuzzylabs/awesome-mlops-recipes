"""FastAPI server for PR review agent."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

from agent import initialise_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Load the agent on startup
    app.state.pr_review_agent, app.state.prompt_version = initialise_agent()
    yield
    # Clean up resources on shutdown
    app.state.pr_review_agent = None
    app.state.prompt_version = None


app = FastAPI(title="PR Review Agent", version="1.0.0", lifespan=lifespan)


class ReviewRequest(BaseModel):
    """Request body for PR review."""
    pr_title: str


class ReviewResponse(BaseModel):
    """Response for PR review."""
    review: str
    status: str = "completed"


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "PR Review Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "review": "/review (POST)",
            "prompt_version": "/prompt_version (GET)"
        }
    }


@app.get("/prompt_version")
async def prompt_version():
    """Prompt endpoint."""
    return {
        "prompt_version": app.state.prompt_version
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pr-review-agent"
    }


@app.post("/review", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest):
    """
    Review a pull request based on its title.
    
    Args:
        request: ReviewRequest containing the PR title
        
    Returns:
        ReviewResponse with the agent's review
    """
    try:
        # Get the agent from app state
        agent = app.state.pr_review_agent
        
        # Run the agent with the PR title (use await in async context!)
        result = await agent.run(
            f"Review the pull request titled \"{request.pr_title}\""
        )
        
        return ReviewResponse(
            review=result.output,
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to review PR: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

