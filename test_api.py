#!/usr/bin/env python3
"""Simple script to test the FastAPI server standalone."""

import asyncio

import uvicorn


async def main():
    """Run FastAPI server for testing."""
    config = uvicorn.Config(
        "src.api.main:app",
        host="0.0.0.0",
        port=8081,
        log_level="info",
        reload=True,  # Enable auto-reload for development
    )
    server = uvicorn.Server(config)
    print("🚀 FastAPI server starting on http://localhost:8081")
    print("📚 API docs: http://localhost:8081/docs")
    print("🔍 Health check: http://localhost:8081/health")
    print("\nPress Ctrl+C to stop")
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
