from dataclasses import dataclass
from hmac import compare_digest
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import get_settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
jwt_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class APIClient:
    role: str
    tenant_id: str | None = None
    user_id: str | None = None


def _split_keys(raw_keys: str) -> list[str]:
    return [key.strip() for key in raw_keys.split(",") if key.strip()]


def _key_matches(api_key: str, configured_keys: list[str]) -> bool:
    return any(compare_digest(api_key, configured_key) for configured_key in configured_keys)


def _resolve_role(api_key: str) -> str | None:
    settings = get_settings()
    role_keys = {
        "admin": _split_keys(settings.ADMIN_API_KEYS),
        "operator": _split_keys(settings.OPERATOR_API_KEYS),
        "reader": _split_keys(settings.READONLY_API_KEYS),
    }

    for role, keys in role_keys.items():
        if _key_matches(api_key, keys):
            return role

    return None


SECRET_KEY = get_settings().JWT_SECRET if hasattr(get_settings(), 'JWT_SECRET') else "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_api_client(
    api_key: str | None = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Security(jwt_bearer)
) -> APIClient:
    settings = get_settings()
    # Primero, API Key
    if api_key:
        role_keys = {
            "admin": _split_keys(settings.ADMIN_API_KEYS),
            "operator": _split_keys(settings.OPERATOR_API_KEYS),
            "reader": _split_keys(settings.READONLY_API_KEYS),
        }
        for role, keys in role_keys.items():
            if _key_matches(api_key, keys):
                return APIClient(role=role, tenant_id=role)
    # Luego, JWT
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload and "role" in payload:
            return APIClient(role=payload["role"], tenant_id=payload.get("tenant_id"), user_id=payload.get("user_id"))
    raise HTTPException(status_code=401, detail={"error": "No autorizado"})

def require_roles(*allowed_roles: str):
    async def dependency(
        client: APIClient = Security(get_current_api_client),
    ) -> APIClient:
        if client.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={"error": "No tienes permisos para realizar esta operaci\u00f3n."},
            )

        return client

    return dependency
