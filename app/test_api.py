import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Base, engine
from app.config import get_settings

get_settings.cache_clear()

# Usaremos las keys que sabemos que están en el .env
ADMIN_KEY = "admin123"
SUPERADMIN_KEY = "superadmin123"
INVALID_KEY = "invalid-key"

@pytest.fixture(autouse=True)
def setup_db():
    """
    Se ejecuta antes de cada test. Asegura que las tablas estén creadas.
    En un entorno CI/CD real, se apuntaría a una SQLite en memoria o una DB PostgreSQL de test.
    """
    Base.metadata.create_all(bind=engine)
    yield


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_auth_missing():
    """Prueba que el acceso sin API Key a rutas protegidas devuelva 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/consultas")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid():
    """Prueba que el acceso con API Key inválida devuelva 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/consultas", headers={"X-API-Key": INVALID_KEY})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_consulta_ruc_invalid_format():
    """Prueba formato de RUC inválido (no numérico / longitud incorrecta)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/ruc/1234")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_consulta_dni_invalid_format():
    """Prueba formato de DNI inválido"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/dni/123")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_customers_manual_success():
    """Prueba la creación exitosa de un cliente manual en el tenant (SaaS flow)"""
    payload = {
        "documentType": "DNI",
        "documentNumber": "99998888",
        "nombre": "CLIENTE SAAS",
        "apellidoPaterno": "CLIENTE",
        "apellidoMaterno": "SAAS",
        "nombres": "PRUEBA"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/customers", json=payload, headers={"X-API-Key": ADMIN_KEY})
        # 200 si lo crea nuevo, 409 si ya corrió el test antes sin dropear DB
        assert resp.status_code in (200, 409)
        if resp.status_code == 200:
            assert resp.json()["documentNumber"] == "99998888"


@pytest.mark.asyncio
async def test_customers_manual_duplicate():
    """Prueba que no se puedan crear clientes duplicados en el mismo tenant"""
    payload = {
        "documentType": "DNI",
        "documentNumber": "77776666",
        "nombre": "DUPLICADO TEST"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primera inserción
        await ac.post("/api/v1/customers", json=payload, headers={"X-API-Key": ADMIN_KEY})
        # Segunda inserción (debe dar 409)
        resp2 = await ac.post("/api/v1/customers", json=payload, headers={"X-API-Key": ADMIN_KEY})
        assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_dni_manual_admin_forbidden():
    """Prueba que un admin normal no pueda insertar DNIs en el padrón maestro"""
    payload = {
        "numeroDocumento": "11112222",
        "apellidoPaterno": "MASTER",
        "nombres": "TEST"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/dni/manual", json=payload, headers={"X-API-Key": ADMIN_KEY})
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dni_manual_superadmin_success():
    """Prueba que un superadmin sí pueda insertar DNIs en el padrón maestro"""
    payload = {
        "numeroDocumento": "11112222",
        "apellidoPaterno": "MASTER",
        "apellidoMaterno": "TEST",
        "nombres": "SUPERADMIN",
        "direccion": "OFICINA CENTRAL"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/dni/manual", json=payload, headers={"X-API-Key": SUPERADMIN_KEY})
        assert resp.status_code == 200
        assert resp.json()["numeroDocumento"] == "11112222"


@pytest.mark.asyncio
async def test_consultas_history():
    """Prueba la obtención del historial de consultas"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/consultas", headers={"X-API-Key": ADMIN_KEY})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

