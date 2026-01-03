#!/usr/bin/env python3
"""Test FastAPI endpoints."""

import asyncio
import sys

import httpx
import uvicorn


class TestableServer:
    """Wrapper to run and test the server."""

    def __init__(self):
        """Initialize server."""
        self.config = uvicorn.Config(
            "src.api.main:app",
            host="127.0.0.1",
            port=8081,
            log_level="error",  # Quiet mode for testing
        )
        self.server = uvicorn.Server(self.config)

    async def start(self):
        """Start server in background."""
        asyncio.create_task(self.server.serve())
        # Wait for server to be ready
        await asyncio.sleep(2)

    async def stop(self):
        """Stop server."""
        self.server.should_exit = True


async def test_endpoints():
    """Test all FastAPI endpoints."""
    server = TestableServer()

    try:
        print("🚀 Starting FastAPI server...")
        await server.start()

        async with httpx.AsyncClient(base_url="http://127.0.0.1:8081", timeout=5.0) as client:
            # Test root endpoint
            print("\n📍 Testing GET /")
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Response: {data}")

            # Test health endpoint
            print("\n📍 Testing GET /health")
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Response: {data}")
            assert data["status"] == "healthy"
            assert data["service"] == "btcbot-api"

            # Test readiness endpoint
            print("\n📍 Testing GET /health/ready")
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Response: {data}")
            assert data["status"] == "ready"

            # Test liveness endpoint
            print("\n📍 Testing GET /health/live")
            response = await client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Response: {data}")
            assert data["status"] == "alive"

            # Test OpenAPI docs endpoint
            print("\n📍 Testing GET /docs (OpenAPI UI)")
            response = await client.get("/docs")
            assert response.status_code == 200
            print(f"   ✅ Status: {response.status_code}")
            print("   ✅ OpenAPI docs available")

            # Test OpenAPI JSON
            print("\n📍 Testing GET /openapi.json")
            response = await client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ API Title: {data.get('info', {}).get('title')}")
            print(f"   ✅ API Version: {data.get('info', {}).get('version')}")

        print("\n" + "=" * 50)
        print("✨ All endpoints passed! ✨")
        print("=" * 50)
        print("\nYou can access the API at:")
        print("  📚 Swagger UI:  http://localhost:8081/docs")
        print("  📖 ReDoc:       http://localhost:8081/redoc")
        print("  🏥 Health:      http://localhost:8081/health")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        print("\n🛑 Stopping server...")
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(test_endpoints())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(1)
