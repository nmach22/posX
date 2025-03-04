import os
import pytest
from fastapi.testclient import TestClient

from app.runner.setup import setup

os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="module")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)
