"""
Modelos SQLAlchemy para las tablas RUC y DNI
"""
from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class RUC(Base):
    """Tabla de Registros Únicos de Contribuyente (RUC) - Personas Jurídicas y Naturales"""
    __tablename__ = "ruc"

    numero_documento = Column(String(11), primary_key=True, index=True)
    nombre = Column(String(500), nullable=False)
    estado = Column(String(50), nullable=True)
    condicion = Column(String(50), nullable=True)
    ubigeo = Column(String(6), nullable=True)
    via_tipo = Column(String(50), nullable=True)
    via_nombre = Column(String(200), nullable=True)
    zona_codigo = Column(String(50), nullable=True)
    zona_tipo = Column(String(50), nullable=True)
    numero = Column(String(20), nullable=True)
    interior = Column(String(20), nullable=True)
    lote = Column(String(20), nullable=True)
    departamento = Column(String(100), nullable=True)
    manzana = Column(String(20), nullable=True)
    kilometro = Column(String(20), nullable=True)
    direccion = Column(String(500), nullable=True)  # Calculado: via_tipo + via_nombre + numero
    distrito = Column(String(100), nullable=True)  # Por ahora vacío
    provincia = Column(String(100), nullable=True)  # Por ahora vacío

    # Índices adicionales para búsquedas rápidas
    __table_args__ = (
        Index("idx_ruc_nombre", "nombre"),
        Index("idx_ruc_estado", "estado"),
    )

    def to_dict(self) -> dict:
        """Convierte el registro a diccionario"""
        return {
            "numeroDocumento": self.numero_documento,
            "tipoDocumento": "6",  # 6 = RUC de empresa
            "nombre": self.nombre,
            "estado": self.estado or "",
            "condicion": self.condicion or "",
            "ubigeo": self.ubigeo or "",
            "viaTipo": self.via_tipo or "",
            "viaNombre": self.via_nombre or "",
            "zonaCodigo": self.zona_codigo or "",
            "zonaTipo": self.zona_tipo or "",
            "numero": self.numero or "",
            "interior": self.interior or "",
            "lote": self.lote or "",
            "dpto": self.departamento or "-",
            "manzana": self.manzana or "-",
            "kilometro": self.kilometro or "-",
            "departamento": self.departamento or "",
            "distrito": self.distrito or "",
            "provincia": self.provincia or "",
            "direccion": self.direccion or "",
        }


class DNI(Base):
    """Tabla de Documento Nacional de Identidad (DNI) - Personas Naturales extraído de RUC"""
    __tablename__ = "dni"

    numero_documento = Column(String(8), primary_key=True, index=True)
    nombre = Column(String(500), nullable=False)
    apellido_paterno = Column(String(200), nullable=False)
    apellido_materno = Column(String(200), nullable=True)
    nombres = Column(String(300), nullable=True)
    direccion = Column(String(500), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_dni_nombre", "nombre"),
        Index("idx_dni_apellido_paterno", "apellido_paterno"),
    )

    def to_dict(self) -> dict:
        """Convierte el registro a diccionario"""
        return {
            "numeroDocumento": self.numero_documento,
            "tipoDocumento": "1",  # 1 = DNI
            "nombre": self.nombre,
            "apellidoPaterno": self.apellido_paterno,
            "apellidoMaterno": self.apellido_materno or "",
            "nombres": self.nombres or "",
            "estado": "",
            "condicion": "",
            "ubigeo": "",
            "viaTipo": "",
            "viaNombre": "",
            "zonaCodigo": "",
            "zonaTipo": "",
            "numero": "",
            "interior": "",
            "lote": "",
            "dpto": "-",
            "manzana": "-",
            "kilometro": "-",
            "departamento": "",
            "distrito": "",
            "provincia": "",
            "direccion": "",
        }


class Tenant(Base):
    """Empresa/tienda dentro del SaaS."""
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(Base):
    """Cliente registrado por una tienda/tenant."""
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    document_type = Column(String(3), nullable=False)
    document_number = Column(String(11), nullable=False)
    nombre = Column(String(500), nullable=False)
    apellido_paterno = Column(String(200), nullable=True)
    apellido_materno = Column(String(200), nullable=True)
    nombres = Column(String(300), nullable=True)
    direccion = Column(String(500), nullable=True)
    source = Column(String(50), nullable=False, default="manual")
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_type",
            "document_number",
            name="uq_customer_tenant_document",
        ),
        Index("idx_customer_tenant_nombre", "tenant_id", "nombre"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenantId": self.tenant_id,
            "documentType": self.document_type,
            "documentNumber": self.document_number,
            "nombre": self.nombre,
            "apellidoPaterno": self.apellido_paterno or "",
            "apellidoMaterno": self.apellido_materno or "",
            "nombres": self.nombres or "",
            "direccion": self.direccion or "",
            "source": self.source,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class IdentityQueryLog(Base):
    """Historial de consultas de identidad por tenant."""
    __tablename__ = "identity_query_logs"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    document_type = Column(String(3), nullable=False)
    document_number = Column(String(11), nullable=False, index=True)
    result_status = Column(String(20), nullable=False)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AuditLog(Base):
    """Auditoria de cambios sensibles."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    entity_id = Column(String(64), nullable=True)
    old_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

