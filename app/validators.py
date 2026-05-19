"""
Validadores para DNI y RUC
"""
from typing import Tuple


def validar_dni(dni: str) -> Tuple[bool, str]:
    """
    Valida un número de DNI peruano

    Reglas:
    - Longitud exacta: 8 dígitos
    - Solo números [0-9]

    Returns:
        (válido, mensaje_error)
    """
    # Longitud
    if len(dni) != 8:
        return False, f"El DNI debe tener exactamente 8 dígitos, se recibieron {len(dni)}."

    # Solo dígitos
    if not dni.isdigit():
        return False, "El DNI solo debe contener números [0-9]."

    return True, ""


def validar_ruc(ruc: str) -> Tuple[bool, str]:
    """
    Valida un número de RUC peruano

    Reglas:
    - Longitud exacta: 11 dígitos
    - Solo números [0-9]
    - Prefijo válido: 10, 15, 17 o 20
    - Dígito verificador SUNAT válido (solo para prefijos válidos)

    Returns:
        (válido, mensaje_error)
    """
    # Longitud
    if len(ruc) != 11:
        return False, f"El RUC debe tener exactamente 11 dígitos, se recibieron {len(ruc)}."

    # Solo dígitos
    if not ruc.isdigit():
        return False, "El RUC solo debe contener números [0-9]."

    # Prefijo válido
    prefijo = ruc[:2]
    if prefijo not in ["10", "15", "17", "20"]:
        return False, "El RUC no tiene un prefijo válido (10, 15, 17 o 20)."

    # Validar dígito verificador SUNAT
    factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(ruc[i]) * factores[i] for i in range(10))
    residuo = suma % 11
    digito = 11 - residuo

    # Ajustar si es 10 o 11
    if digito == 10:
        digito = 0
    elif digito == 11:
        digito = 1

    # Comparar con el dígito verificador recibido
    if int(ruc[10]) != digito:
        return False, "El RUC tiene un dígito verificador inválido."

    return True, ""


def extraer_dni_de_ruc(ruc: str) -> str:
    """
    Extrae el DNI de un RUC de persona natural (prefijo 10)

    Estructura RUC:
    10 + DNI(8 dígitos) + dígito_verificador
    ^^ = posición 0-1
       ^^^^^^^^ = posición 2-9 (el DNI)
                ^ = posición 10 (verificador)

    Args:
        ruc: String de 11 dígitos

    Returns:
        String de 8 dígitos (el DNI)
    """
    return ruc[2:10]


def parsear_nombre(nombre_completo: str) -> Tuple[str, str, str]:
    """
    Parsea el nombre completo en componentes

    Estructura esperada: APELLIDO_PATERNO APELLIDO_MATERNO NOMBRES...

    Args:
        nombre_completo: Nombre completo del registro

    Returns:
        (apellido_paterno, apellido_materno, nombres)
    """
    partes = nombre_completo.strip().split()

    if not partes:
        return "", "", ""

    apellido_paterno = partes[0] if len(partes) > 0 else ""
    apellido_materno = partes[1] if len(partes) > 1 else ""
    nombres = " ".join(partes[2:]) if len(partes) > 2 else ""

    return apellido_paterno, apellido_materno, nombres

