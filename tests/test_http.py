"""HTTP-level integration tests."""

import tempfile
import unittest

import httpx

from app.database import Base, get_db
from app.main import app
from tests.test_support import build_async_db_override, build_test_engine


class BackendHttpTestCase(unittest.IsolatedAsyncioTestCase):
    """HTTP-level tests using httpx ASGI transport and dependency overrides."""

    async def asyncSetUp(self):
        """Create an isolated app database and async HTTP client."""

        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.engine, self.session_local = build_test_engine(
            self.temp_dir.name,
            "http-test.db",
        )
        Base.metadata.create_all(bind=self.engine)
        app.dependency_overrides[get_db] = build_async_db_override(self.session_local)
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(
            transport=self.transport,
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        """Dispose the client and restore global dependency overrides."""

        await self.client.aclose()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    async def register_user(
        self,
        username: str,
        email: str,
        password: str = "secret123",
    ):
        """Register a user over HTTP."""

        return await self.client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )

    async def login_user(self, username: str, password: str = "secret123"):
        """Log in a user over HTTP."""

        return await self.client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )

    async def test_http_health_and_root_routes(self):
        """The app should expose root and health routes."""

        root_response = await self.client.get("/")
        health_response = await self.client.get("/health")

        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(root_response.json(), {"message": "Finance backend is running"})
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json(), {"status": "ok"})
        self.assertIn("X-Request-ID", health_response.headers)

    async def test_http_auth_and_login_flow(self):
        """Register and log in over HTTP."""

        register_response = await self.register_user("admin1", "admin1@example.com")
        login_response = await self.login_user("admin1")

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.json()["role"], "admin")
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["token_type"], "bearer")
