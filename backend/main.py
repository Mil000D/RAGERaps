"""
RAGERaps - AI Rap Battle Web Application
Main application entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.router import api_router
from app.agents.rapper_agent import initialize_rapper_agent

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    Args:
        app: FastAPI application
    """

    # Initialize the rapper agent with MCP tools
    try:
        print("Initializing rapper agent with MCP tools...")
        await initialize_rapper_agent()
        print("Rapper agent initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize rapper agent with MCP tools: {str(e)}")
        print("The application will continue, but search functionality may be limited.")

    yield

    # Cleanup resources if needed


# Create FastAPI app
app = FastAPI(
    title="RAGERaps API",
    description="""
    # RAGERaps API Documentation

    RAGERaps is an AI-powered rap battle application that generates verses in different rap styles.

    ## Features

    * Create rap battles between AI rappers
    * Generate verses in various rap styles
    * Judge battles automatically or manually
    * Track battle progress and results

    ## Authentication

    Currently, the API does not require authentication.

    ## Rate Limiting

    Please be mindful of rate limits when generating verses, as the process is resource-intensive.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": 1, "persistAuthorization": True},
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to RAGERaps API", "status": "online"}


# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
