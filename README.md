# API_RUC_DNI - Identity & Customer Service (SaaS POS)

API REST para consultar información de DNI y RUC peruanos, optimizada para integrarse como microservicio de identidad en un SaaS POS multi-tenant.

## 🚀 Inicio Rápido

### 1. Requisitos
- **PostgreSQL 12+** (Obligatorio, con soporte para Timezones).
- **Redis 5+** (Obligatorio en Producción para Caché y Rate Limiting global).

### 2. Instalar Dependencias

```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar Base de Datos y Redis

```powershell
# Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE sunat_db;"
```

### 4. Variables de Entorno (.env)

Edita el archivo `.env`:
```env
DB_PASSWORD=tu_contraseña_de_postgres_aqui
REDIS_ENABLED=1
# Rate Limiting debe ser configurado a nivel de API Gateway o usando librerías como slowapi apoyadas en Redis
```

### 5. Ejecutar la API

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 📚 **Swagger / OpenAPI**: http://localhost:8000/api/v1/docs

## 🏗 Arquitectura SaaS y Multi-Tenant

Esta API está diseñada para soportar un ecosistema SaaS (Puntos de Venta):
1. **SSOT (Single Source of Truth)**: La tabla `DNI` y `RUC` actúan como registros maestros. No deben ser editadas por los tenants.
2. **Aislamiento de Clientes (Tenants)**: La tabla `customers` almacena la información de los clientes específica de cada tienda (tenant).
3. **Roles y Permisos**: La API valida `APIClient` para distinguir peticiones de `admin`, `operator` o `superadmin`.

## 📡 Endpoints Principales

### 1. Consultar Identidad Oficial (Caché + Padrón + Scraping)
```http
GET /api/v1/dni/{numero}
GET /api/v1/ruc/{numero}
```
*Si un DNI no está en BD local, consulta asíncronamente a fuentes externas (ej. eldni.com) sin bloquear el Event Loop.*

### 2. Guardar Cliente Manual (Flujo POS)
Cuando un DNI no existe, el POS debe registrar el cliente en su propia base de datos, NO en el padrón global.
```http
POST /api/v1/customers
```
```json
{
  "documentType": "DNI",
  "documentNumber": "12345678",
  "nombre": "JUAN PEREZ",
  "nombres": "JUAN",
  "apellidoPaterno": "PEREZ",
  "direccion": "Av. Principal 123"
}
```

### 3. Forzar Corrección de Padrón (Solo SuperAdmin)
```http
POST /api/v1/dni/manual
```
*Uso exclusivo de administración interna para corregir registros oficiales.*

### 4. Auditoría de Consultas
```http
GET /api/v1/consultas
```

## 🛠 Cambios Recientes (Auditoría Técnica Aplicada)
- **Timezones**: Todos los campos `DateTime` usan zona horaria (`timezone=True`) para evitar desfases.
- **Relaciones BD**: Se establecieron `ForeignKey` hacia la tabla `tenants`.
- **Rendimiento**: Se aisló `BeautifulSoup` usando `asyncio.to_thread` para mantener la concurrencia alta.
- **Seguridad**: El Rate Limiting en memoria fue removido. Para entornos multi-worker (SaaS), usar Redis o NGINX.
- **Flujo**: Restricción del endpoint manual de DNI a `superadmin` para evitar corrupción de datos.

## 📋 Validaciones de Dominio
- **DNI**: 8 dígitos numéricos exactos.
- **RUC**: 11 dígitos, prefijos válidos (10, 15, 17, 20) y validación de Módulo 11 (SUNAT).

## 🆘 Solución de Problemas
- **Problemas con Redis**: Asegúrate de tener Redis en ejecución (`docker run -d -p 6379:6379 redis:latest`). La API funcionará sin él, pero perderás caché.
- **Problemas de Timezone (Postgres)**: La API guarda en UTC (`datetime.now(timezone.utc)`). Tu cliente de base de datos convertirá automáticamente a tu zona horaria local.


