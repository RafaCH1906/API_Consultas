"""
Script ETL para cargar el padrón reducido de RUC de SUNAT
Procesamiento en chunks, validación y carga en PostgreSQL
"""
import os
import sys
import time
import logging
import zipfile
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sqlalchemy import text, Index
from sqlalchemy.orm import Session

# Agregar el directorio padre al path para poder importar app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import engine, SessionLocal
from app.models import Base, RUC, DNI
from app.validators import (
    validar_ruc,
    extraer_dni_de_ruc,
    parsear_nombre
)


# Configuración
settings = get_settings()

# Crear carpeta de logs si no existe
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Nombre del archivo de log rotativo (por fecha)
LOG_FILENAME = LOGS_DIR / f"etl_{datetime.now().strftime('%Y%m%d')}.log"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def descargar_padron() -> str:
    """
    Descargar padrón reducido de SUNAT si no existe localmente

    URL: http://www2.sunat.gob.pe/padron_reducido_ruc.zip
    Reintentos: 3 con backoff fijo de 5 segundos

    Returns:
        Ruta del archivo TXT extraído
    """
    padron_path = Path(settings.PADRON_RUC_PATH)

    # Si el archivo TXT ya existe localmente, usarlo directamente
    if padron_path.exists():
        logger.info(f"Usando archivo local: {padron_path}")
        return str(padron_path)

    # Si no existe, intentar descargar
    zip_url = "http://www2.sunat.gob.pe/padron_reducido_ruc.zip"
    zip_path = padron_path.parent / "padron_reducido_ruc.zip"

    logger.info(f"Descargando padrón desde: {zip_url}")

    reintentos = 3
    backoff = 5  # segundos

    for intento in range(reintentos):
        try:
            response = requests.get(zip_url, timeout=30)
            response.raise_for_status()

            # Guardar ZIP
            with open(zip_path, "wb") as f:
                f.write(response.content)

            logger.info(f"ZIP descargado correctamente ({zip_path.stat().st_size} bytes)")

            # Descomprimir
            logger.info("Descomprimiendo archivo...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(padron_path.parent)

            logger.info(f"Archivo extraído a: {padron_path}")

            # Eliminar ZIP
            zip_path.unlink()

            return str(padron_path)

        except Exception as e:
            intento_num = intento + 1
            logger.warning(f"Intento {intento_num}/{reintentos} falló: {e}")

            if intento_num < reintentos:
                logger.info(f"Esperando {backoff} segundos antes de reintentar...")
                time.sleep(backoff)
            else:
                logger.error(f"No se pudo descargar el padrón después de {reintentos} intentos")
                raise

    return str(padron_path)


def procesar_padron():
    """
    Procesa el padrón reducido de SUNAT:

    1. Obtener ruta del archivo
    2. Preparar tablas (CREATE IF NOT EXISTS + TRUNCATE)
    3. Leer en chunks
    4. Validar y cargar datos
    5. Crear índices
    6. Generar reporte
    """
    inicio_total = time.time()

    logger.info("="*60)
    logger.info("Iniciando carga de padrón de SUNAT")
    logger.info("="*60)

    # Obtener archivo
    try:
        padron_path = descargar_padron()
    except Exception as e:
        logger.error(f"Error al obtener el padrón: {e}")
        return

    # Verificar que el archivo existe
    if not Path(padron_path).exists():
        logger.error(f"Archivo no encontrado: {padron_path}")
        return

    logger.info(f"Archivo a procesar: {padron_path}")

    # Preparar tablas
    logger.info("Preparando tablas...")
    try:
        Base.metadata.create_all(bind=engine)

        # Truncate tablas
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE ruc CASCADE"))
            conn.execute(text("TRUNCATE TABLE dni CASCADE"))

        logger.info("Tablas preparadas")
    except Exception as e:
        logger.error(f"Error al preparar tablas: {e}")
        return

    # Procesar archivo en chunks
    db = SessionLocal()
    try:
        total_leidas = 0
        total_ruc_insertadas = 0
        total_dni_insertadas = 0
        total_descartadas = 0
        numero_lote = 0

        # Leer padrón en chunks
        # Encoding: ISO-8859-1, Separador: pipe "|"
        chunk_size = settings.ETL_CHUNK_SIZE

        for chunk in pd.read_csv(
            padron_path,
            sep='|',
            encoding='ISO-8859-1',
            dtype=str,
            chunksize=chunk_size,
            skiprows=1  # Omitir cabecera
        ):
            numero_lote += 1
            inicio_lote = time.time()

            filas_chunk = len(chunk)
            total_leidas += filas_chunk

            ruc_validos = []
            dni_validos = []
            descartadas_lote = 0

            # Procesar cada fila
            for idx, row in chunk.iterrows():
                try:
                    # Extraer número de documento
                    numero_documento = str(row[0]).strip() if pd.notna(row[0]) else ""

                    # Validaciones básicas
                    if not numero_documento or len(numero_documento) != 11:
                        descartadas_lote += 1
                        continue

                    if not numero_documento.isdigit():
                        descartadas_lote += 1
                        continue

                    # Validar prefijo
                    prefijo = numero_documento[:2]
                    if prefijo not in ["10", "15", "17", "20"]:
                        descartadas_lote += 1
                        continue

                    # Validar dígito verificador
                    valido, error = validar_ruc(numero_documento)
                    if not valido:
                        descartadas_lote += 1
                        continue

                    # Extraer datos de la fila
                    nombre = str(row[1]).strip() if pd.notna(row[1]) else ""
                    estado = str(row[2]).strip() if pd.notna(row[2]) else None
                    condicion = str(row[3]).strip() if pd.notna(row[3]) else None
                    ubigeo = str(row[4]).strip() if pd.notna(row[4]) else None
                    via_tipo = str(row[5]).strip() if pd.notna(row[5]) else None
                    via_nombre = str(row[6]).strip() if pd.notna(row[6]) else None
                    zona_codigo = str(row[7]).strip() if pd.notna(row[7]) else None
                    zona_tipo = str(row[8]).strip() if pd.notna(row[8]) else None
                    numero = str(row[9]).strip() if pd.notna(row[9]) else None
                    interior = str(row[10]).strip() if pd.notna(row[10]) else None
                    lote = str(row[11]).strip() if pd.notna(row[11]) else None
                    departamento = str(row[12]).strip() if pd.notna(row[12]) else None
                    manzana = str(row[13]).strip() if pd.notna(row[13]) else None
                    kilometro = str(row[14]).strip() if pd.notna(row[14]) else None

                    # Reemplazar valores "-" por None
                    estado = None if estado == "-" else estado
                    condicion = None if condicion == "-" else condicion
                    ubigeo = None if ubigeo == "-" else ubigeo
                    via_tipo = None if via_tipo == "-" else via_tipo
                    via_nombre = None if via_nombre == "-" else via_nombre
                    zona_codigo = None if zona_codigo == "-" else zona_codigo
                    zona_tipo = None if zona_tipo == "-" else zona_tipo
                    numero = None if numero == "-" else numero
                    interior = None if interior == "-" else interior
                    lote = None if lote == "-" else lote
                    departamento = None if departamento == "-" else departamento
                    manzana = None if manzana == "-" else manzana
                    kilometro = None if kilometro == "-" else kilometro

                    # Calcular dirección
                    direccion_partes = []
                    if via_tipo:
                        direccion_partes.append(via_tipo)
                    if via_nombre:
                        direccion_partes.append(via_nombre)
                    if numero:
                        direccion_partes.append(f"NRO. {numero}")

                    direccion = " ".join(direccion_partes) if direccion_partes else None

                    # Crear registro RUC
                    ruc_record = RUC(
                        numero_documento=numero_documento,
                        nombre=nombre,
                        estado=estado,
                        condicion=condicion,
                        ubigeo=ubigeo,
                        via_tipo=via_tipo,
                        via_nombre=via_nombre,
                        zona_codigo=zona_codigo,
                        zona_tipo=zona_tipo,
                        numero=numero,
                        interior=interior,
                        lote=lote,
                        departamento=departamento,
                        manzana=manzana,
                        kilometro=kilometro,
                        direccion=direccion,
                        distrito="",
                        provincia=""
                    )
                    ruc_validos.append(ruc_record)

                    # Si es persona natural (prefijo 10), crear DNI
                    if prefijo == "10":
                        dni = extraer_dni_de_ruc(numero_documento)
                        apellido_paterno, apellido_materno, nombres = parsear_nombre(nombre)

                        dni_record = DNI(
                            numero_documento=dni,
                            nombre=nombre,
                            apellido_paterno=apellido_paterno,
                            apellido_materno=apellido_materno,
                            nombres=nombres,
                            estado=estado,
                            condicion=condicion,
                            ubigeo=ubigeo,
                            via_tipo=via_tipo,
                            via_nombre=via_nombre,
                            zona_codigo=zona_codigo,
                            zona_tipo=zona_tipo,
                            numero=numero,
                            interior=interior,
                            lote=lote,
                            departamento=departamento,
                            manzana=manzana,
                            kilometro=kilometro,
                            direccion=direccion,
                            distrito="",
                            provincia=""
                        )
                        dni_validos.append(dni_record)

                except Exception as e:
                    logger.warning(f"Error procesando fila {idx}: {e}")
                    descartadas_lote += 1
                    continue

            # Insertar en lote
            if not settings.ETL_VALIDATE_ONLY:
                try:
                    if ruc_validos:
                        db.bulk_save_objects(ruc_validos)
                    if dni_validos:
                        db.bulk_save_objects(dni_validos)
                    db.commit()

                    total_ruc_insertadas += len(ruc_validos)
                    total_dni_insertadas += len(dni_validos)
                    total_descartadas += descartadas_lote

                except Exception as e:
                    logger.error(f"Error insertando lote {numero_lote}: {e}")
                    db.rollback()
                    continue
            else:
                total_ruc_insertadas += len(ruc_validos)
                total_dni_insertadas += len(dni_validos)
                total_descartadas += descartadas_lote

            # Reporte de progreso
            duracion_lote = time.time() - inicio_lote
            if numero_lote % settings.ETL_LOG_INTERVAL == 0:
                logger.info(
                    f"Lote {numero_lote}: "
                    f"leídas={filas_chunk}, "
                    f"válidas={len(ruc_validos)}, "
                    f"descartadas={descartadas_lote}, "
                    f"tiempo={duracion_lote:.2f}s"
                )

        # Crear índices
        logger.info("Creando índices...")
        try:
            with engine.begin() as conn:
                # Índices para RUC
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_ruc_nombre ON ruc(nombre)"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_ruc_estado ON ruc(estado)"
                ))

                # Índices para DNI
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_dni_nombre ON dni(nombre)"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_dni_apellido_paterno ON dni(apellido_paterno)"
                ))
            logger.info("Índices creados")
        except Exception as e:
            logger.warning(f"Error creando índices: {e}")

        # Reporte final
        duracion_total = time.time() - inicio_total

        logger.info("="*60)
        logger.info("CARGA COMPLETADA")
        logger.info("="*60)
        logger.info(f"Total leídas: {total_leidas:,}")
        logger.info(f"Total RUC insertadas: {total_ruc_insertadas:,}")
        logger.info(f"Total DNI insertadas: {total_dni_insertadas:,}")
        logger.info(f"Total descartadas: {total_descartadas:,}")
        logger.info(f"Duración total: {duracion_total:.2f}s")
        logger.info(f"Tiempo promedio por lote: {duracion_total/numero_lote:.2f}s")

        if settings.ETL_VALIDATE_ONLY:
            logger.info("\n⚠️  MODO VALIDACIÓN: No se insertaron datos en la BD")

        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error procesando padrón: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        procesar_padron()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

