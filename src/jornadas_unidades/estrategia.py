"""Programación de las jornadas de una unidad móvil."""

import math
from typing import List, Tuple

# (inicio, fin, pacientes_alto_riesgo); inicio y fin en minutos.
Jornada = tuple[int, int, int]


def hay_cruce(jornadas: list[Jornada]) -> bool:
    """Indica si alguna pareja de jornadas se cruza.

    Args:
        jornadas: jornadas a revisar.

    Returns:
        True si dos jornadas se cruzan; False en caso contrario.
    """
    if len(jornadas) <= 1:
        return False

    # Ordenar por hora de inicio para verificar solapamientos en O(k log k)
    jornadas_ordenadas = sorted(jornadas, key=lambda j: (j[0], j[1]))
    max_fin = jornadas_ordenadas[0][1]

    for i in range(1, len(jornadas_ordenadas)):
        inicio_actual, fin_actual, _ = jornadas_ordenadas[i]
        # Cruce si el inicio es estrictamente menor al fin previo (intervalo abierto)
        if inicio_actual < max_fin:
            return True
        if fin_actual > max_fin:
            max_fin = fin_actual

    return False


def seleccionar_jornadas(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige las jornadas que atiende la unidad, sin cruces.

    Args:
        solicitudes: solicitudes del mes de una subregión.

    Returns:
        Las jornadas elegidas, ordenadas por hora de inicio. Optimiza el
        criterio que el equipo declaró en el README.
    """
    if not solicitudes:
        return []

    # Estrategia voraz: ordenar por hora de fin ascendente (earliest finish time)
    # En caso de empate en hora de fin, priorizar la de inicio más tardío (-j[0])
    ordenadas = sorted(solicitudes, key=lambda j: (j[1], -j[0]))

    elegidas: list[Jornada] = [ordenadas[0]]
    ultimo_fin = ordenadas[0][1]

    for j in ordenadas[1:]:
        if j[0] >= ultimo_fin:
            elegidas.append(j)
            ultimo_fin = j[1]

    # Devolver ordenadas por hora de inicio
    return sorted(elegidas, key=lambda j: (j[0], j[1]))


def seleccionar_jornadas_con_conteo(solicitudes: list[Jornada]) -> tuple[list[Jornada], int]:
    """Ejecuta la estrategia voraz contando las operaciones elementales.

    Args:
        solicitudes: lista de solicitudes del mes.

    Returns:
        Tupla con las jornadas elegidas y el número total de operaciones elementales.
    """
    n = len(solicitudes)
    if n == 0:
        return [], 0

    operaciones = 0

    if n > 1:
        operaciones += int(n * math.ceil(math.log2(n)))

    ordenadas = sorted(solicitudes, key=lambda j: (j[1], -j[0]))

    elegidas: list[Jornada] = [ordenadas[0]]
    ultimo_fin = ordenadas[0][1]

    for j in ordenadas[1:]:
        operaciones += 1  # Comparación de compatibilidad j[0] >= ultimo_fin
        if j[0] >= ultimo_fin:
            elegidas.append(j)
            ultimo_fin = j[1]

    k = len(elegidas)
    if k > 1:
        operaciones += int(k * math.ceil(math.log2(k)))

    return sorted(elegidas, key=lambda j: (j[0], j[1])), operaciones


# Re-exportar funciones del esqueleto si se importan directamente desde estrategia
try:
    from exhaustivo import seleccionar_exhaustivo
    from regla_actual import asignar_por_llegada
except ImportError:
    pass
