"""
Rutas/Endpoints de la API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4

from app.database import get_db
from app.models import DNI, RUC, Customer, IdentityQueryLog
from app.schemas import DNIManualCreate, DNIResponse, RUCResponse, HealthResponse, ErrorResponse, CustomerCreate, CustomerResponse, IdentityQueryLogResponse
from app.validators import validar_dni, validar_ruc
from app.cache import cache
from app.scraper import buscar_dni_eldni
from app.security import APIClient, require_roles


router = APIRouter(prefix="/api/v1", tags=["consultas"])


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    """Health check de la API (endpoint alternativo)"""
    return HealthResponse(
        status="ok",
        message="API Consulta DNI/RUC funcionando."
    )


@router.get("/dni/{numero}", response_model=DNIResponse)
async def consultar_dni(
    numero: str,
    db: Session = Depends(get_db)
) -> DNIResponse:
    """
    Consulta informacion de un DNI peruano

    - **numero**: DNI de 8 digitos

    Returns:
        - 200: Datos encontrados
        - 404: DNI no existe en el padron
        - 422: Validacion fallida
    """
    # Validar DNI
    valido, error = validar_dni(numero)
    if not valido:
        raise HTTPException(status_code=422, detail={"error": error})

    # Buscar en cache
    cache_key = cache.build_dni_key(numero)
    cached = cache.get(cache_key)
    if cached:
        return DNIResponse(**cached)

    # Buscar en BD
    registro = db.query(DNI).filter(DNI.numero_documento == numero).first()

    if registro:
        respuesta = DNIResponse(**registro.to_dict())
        cache.set(cache_key, respuesta.dict())
        return respuesta

    resultado = await buscar_dni_eldni(numero)

    if resultado is None:
        error_msg = f"El DNI {numero} no existe en el padr\u00f3n."
        raise HTTPException(status_code=404, detail={"error": error_msg})

    try:
        db.add(DNI(**resultado))
        db.commit()
    except SQLAlchemyError:
        db.rollback()

    respuesta = DNIResponse(
        numeroDocumento=resultado["numero_documento"],
        tipoDocumento="1",
        nombre=resultado["nombre"],
        apellidoPaterno=resultado["apellido_paterno"],
        apellidoMaterno=resultado["apellido_materno"],
        nombres=resultado["nombres"],
    )

    cache.set(cache_key, respuesta.dict())

    return respuesta


@router.post("/dni/manual", response_model=DNIResponse)
async def guardar_dni_manual(
    payload: DNIManualCreate,
    api_client: APIClient = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db)
) -> DNIResponse:
    """
    Registra o actualiza manualmente un DNI en la base local (solo SuperAdmin).
    NOTA: Para registro en POS, utilizar POST /api/v1/customers.
    """
    dni = payload.numeroDocumento.strip()
    apellido_paterno = " ".join(payload.apellidoPaterno.strip().split()).upper()
    apellido_materno = " ".join(payload.apellidoMaterno.strip().split()).upper() if payload.apellidoMaterno else ""
    nombres = " ".join(payload.nombres.strip().split()).upper()
    direccion = payload.direccion.strip()
    # Validar DNI
    valido, error = validar_dni(dni)
    if not valido:
        raise HTTPException(status_code=422, detail={"error": error})
    # Buscar duplicados
    registro = db.query(DNI).filter(DNI.numero_documento == dni, DNI.deleted_at == None).first()
    if registro:
        # Actualizar
        registro.apellido_paterno = apellido_paterno
        registro.apellido_materno = apellido_materno
        registro.nombres = nombres
        registro.nombre = f"{apellido_paterno} {apellido_materno} {nombres}".strip()
        registro.direccion = direccion
        db.commit()
    else:
        nuevo = DNI(
            numero_documento=dni,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            nombres=nombres,
            nombre=f"{apellido_paterno} {apellido_materno} {nombres}".strip(),
            direccion=direccion
        )
        db.add(nuevo)
        db.commit()
        registro = nuevo
    return DNIResponse(**registro.to_dict())


@router.get("/ruc/{numero}", response_model=RUCResponse)
async def consultar_ruc(
    numero: str,
    db: Session = Depends(get_db)
) -> RUCResponse:
    """
    Consulta informacion de un RUC peruano

    - **numero**: RUC de 11 digitos

    Returns:
        - 200: Datos encontrados
        - 404: RUC no existe en el padron
        - 422: Validacion fallida
    """
    # Validar RUC
    valido, error = validar_ruc(numero)
    if not valido:
        raise HTTPException(status_code=422, detail={"error": error})

    # Buscar en cache
    cache_key = cache.build_ruc_key(numero)
    cached = cache.get(cache_key)
    if cached:
        return RUCResponse(**cached)

    # Buscar en BD
    registro = db.query(RUC).filter(RUC.numero_documento == numero).first()

    if not registro:
        error_msg = f"El RUC {numero} no existe en el padr\u00f3n."
        raise HTTPException(status_code=404, detail={"error": error_msg})

    # Convertir a respuesta
    respuesta = RUCResponse(**registro.to_dict())

    # Guardar en cache
    cache.set(cache_key, respuesta.dict())

    return respuesta


@router.post("/customers", response_model=CustomerResponse)
async def crear_cliente_manual(
    payload: CustomerCreate,
    api_client: APIClient = Depends(require_roles("admin", "operator")),
    db: Session = Depends(get_db)
) -> CustomerResponse:
    """
    Registrar cliente manual para un tenant (flujo POS).
    """
    # Validar documento
    if payload.documentType == "DNI":
        valido, error = validar_dni(payload.documentNumber)
        if not valido:
            raise HTTPException(status_code=422, detail={"error": error})
    elif payload.documentType == "RUC":
        valido, error = validar_ruc(payload.documentNumber)
        if not valido:
            raise HTTPException(status_code=422, detail={"error": error})
    else:
        raise HTTPException(status_code=422, detail={"error": "Tipo de documento inválido"})
    # Buscar duplicados
    existe = db.query(Customer).filter(
        Customer.tenant_id == api_client.role,  # Suponiendo role=tenant_id
        Customer.document_type == payload.documentType,
        Customer.document_number == payload.documentNumber,
        Customer.deleted_at == None
    ).first()
    if existe:
        raise HTTPException(status_code=409, detail={"error": "Cliente ya existe para este tenant"})
    cliente = Customer(
        id=str(uuid4()),
        tenant_id=api_client.role,
        document_type=payload.documentType,
        document_number=payload.documentNumber,
        nombre=payload.nombre,
        apellido_paterno=payload.apellidoPaterno,
        apellido_materno=payload.apellidoMaterno,
        nombres=payload.nombres,
        direccion=payload.direccion,
        source="manual",
        created_by=api_client.role
    )
    db.add(cliente)
    db.commit()
    return CustomerResponse(**cliente.to_dict())


@router.get("/consultas", response_model=list[IdentityQueryLogResponse])
async def historial_consultas(
    api_client: APIClient = Depends(require_roles("admin", "operator")),
    db: Session = Depends(get_db)
) -> list[IdentityQueryLogResponse]:
    """
    Devuelve el historial de consultas de identidad del tenant.
    """
    logs = db.query(IdentityQueryLog).filter(IdentityQueryLog.tenant_id == api_client.role).order_by(IdentityQueryLog.created_at.desc()).limit(100).all()
    return [IdentityQueryLogResponse(
        id=str(l.id),
        tenantId=l.tenant_id,
        documentType=l.document_type,
        documentNumber=l.document_number,
        resultStatus=l.result_status,
        source=l.source,
        createdAt=l.created_at.isoformat() if l.created_at else None
    ) for l in logs]
