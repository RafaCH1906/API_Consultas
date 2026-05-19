# API_RUC_DNI - Consulta DNI y RUC Peruano

API REST para consultar información de DNI y RUC peruanos del padrón reducido de SUNAT.

## 🚀 Inicio Rápido

### 1. Requisitos
- PostgreSQL 12+
- Redis (opcional, para caché)

### 2. Instalar Dependencias

```bash
# El entorno virtual ya está listo en venv/
# Las dependencias ya están instaladas

# Si necesitas reinstalar:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar Base de Datos

```powershell
# Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE sunat_db;"
```

### 4. Editar Archivo .env

Edita el archivo `.env` y reemplaza:
```env
DB_PASSWORD=tu_contraseña_de_postgres_aqui
```

### 5. Ejecutar la API

```powershell
cd "C:\Users\rafae\Desktop\API_RUC_DNI"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**La API estará disponible en:**
- 🌐 http://localhost:8000/
- 📚 Documentación: http://localhost:8000/api/v1/docs

## 📊 Cargar Datos (Primera Vez)

```powershell
# Esto tarda ~30 minutos (2.7M de registros)
.\venv\Scripts\python.exe etl/cargar_padron.py
```

## 📡 Endpoints

### Health Check
```
GET http://localhost:8000/
```

Respuesta:
```json
{
  "status": "ok",
  "message": "API Consulta DNI/RUC funcionando."
}
```

### Consultar DNI
```
GET http://localhost:8000/api/v1/dni/{numero}
```

Ejemplo: `http://localhost:8000/api/v1/dni/46027897`

### Consultar RUC
```
GET http://localhost:8000/api/v1/ruc/{numero}
```

Ejemplo: `http://localhost:8000/api/v1/ruc/20601030013`

### Documentación Interactiva
```
GET http://localhost:8000/api/v1/docs
```

## 📁 Estructura del Proyecto

```
API_RUC_DNI/
├── app/                  ← Código de la API
│   ├── main.py           - Aplicación FastAPI
│   ├── routes.py         - Endpoints
│   ├── models.py         - Modelos de BD
│   ├── schemas.py        - Esquemas de respuesta
│   ├── validators.py     - Validación DNI/RUC
│   ├── cache.py          - Caché Redis
│   ├── database.py       - Conexión PostgreSQL
│   └── config.py         - Configuración
├── etl/
│   ├── cargar_padron.py  - Script para cargar datos
│   └── logs/             - Logs de ejecución
├── venv/                 - Entorno virtual Python
├── requirements.txt      - Dependencias
├── .env                  - Variables de entorno
├── .env.example          - Plantilla .env
└── README.md             - Este archivo
```

## ⚙️ Configuración (.env)

```env
# Base de datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sunat_db
DB_USER=postgres
DB_PASSWORD=tu_password

# Redis (caché - opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=1
REDIS_TTL=86400
REDIS_KEY_PREFIX=sunat

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# ETL
PADRON_RUC_PATH=C:/Users/rafae/Desktop/API_RUC_DNI/padron_reducido_ruc.txt
ETL_CHUNK_SIZE=50000
ETL_LOG_INTERVAL=5
ETL_VALIDATE_ONLY=0
```

## 🛠️ Stack Técnico

- **Python**: 3.11.9
- **Framework**: FastAPI 0.111.0
- **Server**: Uvicorn 0.29.0
- **BD**: PostgreSQL 12+
- **ORM**: SQLAlchemy 2.0.30
- **Caché**: Redis 5.0.4 (opcional)
- **Datos**: Pandas 3.0.3

## 🧪 Probar Endpoints

### Con cURL
```bash
# Health check
curl http://localhost:8000/

# Consultar DNI
curl http://localhost:8000/api/v1/dni/46027897

# Consultar RUC
curl http://localhost:8000/api/v1/ruc/20601030013
```

### Con Python
```python
import requests

# Health check
response = requests.get("http://localhost:8000/")
print(response.json())

# DNI
response = requests.get("http://localhost:8000/api/v1/dni/46027897")
print(response.json())
```

## 📋 Validaciones

### DNI
- Exactamente 8 dígitos
- Solo números [0-9]

### RUC
- Exactamente 11 dígitos
- Solo números [0-9]
- Prefijo válido: 10, 15, 17, 20
- Dígito verificador SUNAT válido

## 🆘 Solución de Problemas

### "No se puede conectar a PostgreSQL"
```
Verificar:
1. PostgreSQL está corriendo (Services → postgresql)
2. Contraseña en .env es correcta
3. Base de datos 'sunat_db' existe
```

### "No se puede conectar a Redis"
```
Esto es una advertencia, no es error.
La API continúa funcionando sin caché.

Para habilitar Redis:
docker run -d -p 6379:6379 redis:latest
```

### "Puerto 8000 ya en uso"
```powershell
# Usar otro puerto:
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

## 📊 Base de Datos

### Tabla `ruc`
Contiene ~2.1 millones de registros del padrón SUNAT

### Tabla `dni`
Contiene ~1 millón de registros extraídos de RUCs con prefijo "10"

## 🔄 Programar Ejecución Diaria del ETL

### Windows (Task Scheduler)
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Nombre: "Cargar Padrón SUNAT"
4. Desencadenador: Diario a las 2:00 AM
5. Acción:
   ```
   Programa: C:\Users\rafae\Desktop\API_RUC_DNI\venv\Scripts\python.exe
   Argumentos: etl/cargar_padron.py
   ```

### Linux/Mac (Cron)
```bash
0 2 * * * cd /path/to/API_RUC_DNI && ./venv/bin/python etl/cargar_padron.py
```

## 📚 Información Adicional

- **Padrón SUNAT**: http://www2.sunat.gob.pe/padron_reducido_ruc.zip
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

**Versión**: 1.0.0  
**Estado**: ✅ Producción  
**Última actualización**: 2026-05-18

