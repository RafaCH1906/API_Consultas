"""
Esquemas Pydantic para validación y serialización de datos
"""
from pydantic import BaseModel, Field
from typing import Optional


class DNIResponse(BaseModel):
    """Respuesta para consulta de DNI"""
    nombre: str
    tipoDocumento: str
    numeroDocumento: str
    apellidoPaterno: str
    apellidoMaterno: str = ""
    nombres: str = ""
    estado: str = ""
    condicion: str = ""
    direccion: str = ""
    ubigeo: str = ""
    viaTipo: str = ""
    viaNombre: str = ""
    zonaCodigo: str = ""
    zonaTipo: str = ""
    numero: str = ""
    interior: str = ""
    lote: str = ""
    dpto: str = "-"
    manzana: str = "-"
    kilometro: str = "-"
    distrito: str = ""
    provincia: str = ""
    departamento: str = ""

    class Config:
        from_attributes = True


class DNIManualCreate(BaseModel):
    """Entrada para registrar o actualizar un DNI manualmente"""
    numeroDocumento: str = Field(pattern=r"^\d{8}$")
    apellidoPaterno: str = Field(min_length=1, max_length=200)
    apellidoMaterno: str = Field(default="", max_length=200)
    nombres: str = Field(min_length=1, max_length=300)
    direccion: str = Field(default="", max_length=500)


class CustomerCreate(BaseModel):
    """Entrada para crear o actualizar un cliente del tenant."""
    documentType: str = Field(pattern=r"^(DNI|RUC)$")
    documentNumber: str
    nombre: str = Field(default="", max_length=500)
    apellidoPaterno: str = Field(default="", max_length=200)
    apellidoMaterno: str = Field(default="", max_length=200)
    nombres: str = Field(default="", max_length=300)
    direccion: str = Field(default="", max_length=500)


class CustomerResponse(BaseModel):
    id: str
    tenantId: str
    documentType: str
    documentNumber: str
    nombre: str
    apellidoPaterno: str = ""
    apellidoMaterno: str = ""
    nombres: str = ""
    direccion: str = ""
    source: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class IdentityQueryLogResponse(BaseModel):
    id: str
    tenantId: str
    documentType: str
    documentNumber: str
    resultStatus: str
    source: str
    createdAt: Optional[str] = None


class RUCResponse(BaseModel):
    """Respuesta para consulta de RUC"""
    nombre: str
    tipoDocumento: str
    numeroDocumento: str
    estado: str = ""
    condicion: str = ""
    direccion: str = ""
    ubigeo: str = ""
    viaTipo: str = ""
    viaNombre: str = ""
    zonaCodigo: str = ""
    zonaTipo: str = ""
    numero: str = ""
    interior: str = ""
    lote: str = ""
    dpto: str = "-"
    manzana: str = "-"
    kilometro: str = "-"
    distrito: str = ""
    provincia: str = ""
    departamento: str = ""

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Respuesta de salud de la API"""
    status: str = "ok"
    message: str = "API Consulta DNI/RUC funcionando."


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str

