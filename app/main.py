"""
Aplicación principal FastAPI lista para SaaS POS
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import time
from collections import defaultdict
import os

from app.config import get_settings
from app.database import init_db
from app.routes import router


# Configuración
settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title="API Consulta DNI/RUC",
    description="API para consultar datos de DNI y RUC peruanos del padrón de SUNAT",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS restrictivo (leer de entorno o settings)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "https://tudominio.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(router)

# Endpoint raíz para health check (debe estar después de incluir routers)
@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raíz para health check"""
    return {
        "status": "ok",
        "message": "API Consulta DNI/RUC funcionando."
    }


# Middleware de logging estructurado
@app.middleware("http")
async def log_requests(request: Request, call_next):
    from time import time
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    print(f"[LOG] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s - IP: {request.client.host}")
    return response


# Middleware de rate limiting simple por IP
class SimpleRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # {ip: [timestamps]}

    async def dispatch(self, request: StarletteRequest, call_next):
        ip = request.client.host
        now = time.time()
        window = self.requests[ip]
        # Eliminar timestamps fuera de ventana
        window = [t for t in window if now - t < self.window_seconds]
        window.append(now)
        self.requests[ip] = window
        if len(window) > self.max_requests:
            return PlainTextResponse(
                "Rate limit exceeded. Intenta nuevamente en unos segundos.",
                status_code=HTTP_429_TOO_MANY_REQUESTS
            )
        return await call_next(request)

app.add_middleware(SimpleRateLimiter, max_requests=60, window_seconds=60)


# Manejadores de errores personalizados
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador personalizado para excepciones HTTP"""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    # Para otros casos, devolver mensaje de error genérico
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador personalizado para errores de validación"""
    errors = exc.errors()
    if errors:
        error_msg = f"Error de validación: {errors[0]['msg']}"
        return JSONResponse(
            status_code=422,
            content={"error": error_msg}
        )

    return JSONResponse(
        status_code=422,
        content={"error": "Error de validación"}
    )


# Inicializar BD
@app.on_event("startup")
def startup_event():
    """Evento de arranque: inicializar BD"""
    try:
        init_db()
        print("Base de datos inicializada")
    except Exception as e:
        print(f"Advertencia: No se pudo inicializar la base de datos: {e}")
        print("La API continuará funcionando, pero requiere BD para consultas")


# Ejemplo de endpoint de métricas Prometheus (opcional, requiere librería extra)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass  # Si no está instalado, ignora


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
