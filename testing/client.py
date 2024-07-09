from httpx import ASGITransport, AsyncClient
from main import app

base_url = "http://localhost:8000/"
transport = ASGITransport(app=app)


def async_client():
    return AsyncClient(transport=transport, base_url=base_url)
