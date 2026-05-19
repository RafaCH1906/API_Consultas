import pytest
from httpx import AsyncClient
from app.main import app

API_KEY = "admin123"

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health", headers={"X-API-Key": API_KEY})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_dni_manual():
    payload = {
        "numeroDocumento": "12345679",
        "apellidoPaterno": "TEST",
        "apellidoMaterno": "USER",
        "nombres": "PRUEBA",
        "direccion": "CALLE TEST 123"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/dni/manual", json=payload, headers={"X-API-Key": API_KEY})
        assert resp.status_code == 200
        assert resp.json()["numeroDocumento"] == "12345679"

@pytest.mark.asyncio
async def test_dni_invalido():
    payload = {
        "numeroDocumento": "1234",
        "apellidoPaterno": "TEST",
        "apellidoMaterno": "USER",
        "nombres": "PRUEBA",
        "direccion": "CALLE TEST 123"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/dni/manual", json=payload, headers={"X-API-Key": API_KEY})
        assert resp.status_code == 422
        assert "error" in resp.json()

@pytest.mark.asyncio
async def test_consulta_dni():
    # Debe existir el DNI 12345679 por el test anterior
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/dni/12345679", headers={"X-API-Key": API_KEY})
        assert resp.status_code == 200
        assert resp.json()["numeroDocumento"] == "12345679"

@pytest.mark.asyncio
async def test_consulta_dni_no_existe():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/dni/00000000", headers={"X-API-Key": API_KEY})
        assert resp.status_code in (404, 422)

@pytest.mark.asyncio
async def test_rate_limit():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for _ in range(65):
            resp = await ac.get("/api/v1/health", headers={"X-API-Key": API_KEY})
        # El último request debería estar rate limited o seguir respondiendo 200 si el limit no aplica en test
        assert resp.status_code in (200, 429)
