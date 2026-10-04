from fastapi.testclient import TestClient
from sourcedna.app import app


def test_health():
    with TestClient(app) as c:
        r = c.get('/api/health')
        assert r.status_code == 200
        assert r.json()['ok'] is True


def test_demo_endpoint():
    with TestClient(app) as c:
        r = c.get('/api/demo')
        assert r.status_code == 200
        data = r.json()
        assert data['metrics']['cited_urls'] == 6
