"""Procedimiento actual de asignación de jornadas en la Secretaría de Salud."""

import sys
import os

# Tipo Jornada: (inicio, fin, pacientes_alto_riesgo); inicio y fin en minutos.
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

    jornadas_ordenadas = sorted(jornadas, key=lambda j: (j[0], j[1]))
    max_fin = jornadas_ordenadas[0][1]

    for i in range(1, len(jornadas_ordenadas)):
        inicio_actual, fin_actual, _ = jornadas_ordenadas[i]
        if inicio_actual < max_fin:
            return True
        if fin_actual > max_fin:
            max_fin = fin_actual

    return False


def asignar_por_llegada(solicitudes: list[Jornada]) -> list[Jornada]:
    """Reproduce el procedimiento actual: orden de llegada, rechazando cruces.

    Args:
        solicitudes: solicitudes en el orden en que llegaron.

    Returns:
        Las jornadas aceptadas.
    """
    aceptadas: list[Jornada] = []

    for sol in solicitudes:
        s_ini, s_fin, _ = sol
        se_cruza = False
        for ac in aceptadas:
            a_ini, a_fin, _ = ac
            if max(s_ini, a_ini) < min(s_fin, a_fin):
                se_cruza = True
                break

        if not se_cruza:
            aceptadas.append(sol)

    return aceptadas


def asignar_por_llegada_con_conteo(solicitudes: list[Jornada]) -> tuple[list[Jornada], int]:
    """Ejecuta el procedimiento actual contabilizando las comparaciones temporales.

    Args:
        solicitudes: solicitudes en el orden en que llegaron.

    Returns:
        Tupla con las jornadas aceptadas y el total de comparaciones de cruce realizadas.
    """
    aceptadas: list[Jornada] = []
    comparaciones = 0

    for sol in solicitudes:
        s_ini, s_fin, _ = sol
        se_cruza = False
        for ac in aceptadas:
            comparaciones += 1
            a_ini, a_fin, _ = ac
            if max(s_ini, a_ini) < min(s_fin, a_fin):
                se_cruza = True
                break

        if not se_cruza:
            aceptadas.append(sol)

    return aceptadas, comparaciones
