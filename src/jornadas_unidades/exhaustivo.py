"""Solución exhaustiva para la programación de jornadas de la unidad móvil."""

from itertools import combinations
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


def seleccionar_exhaustivo(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige el mejor subconjunto sin cruces probando todos los subconjuntos.

    Args:
        solicitudes: solicitudes del mes de una subregión.

    Returns:
        Un subconjunto óptimo para el mismo criterio.
    """
    n = len(solicitudes)
    if n == 0:
        return []

    mejor_subconjunto: list[Jornada] = []
    mejor_num_jornadas = 0
    mejor_pacientes = -1

    # Evaluar todos los 2^n subconjuntos posibles
    for r in range(1, n + 1):
        for combo in combinations(solicitudes, r):
            candidato = list(combo)
            if not hay_cruce(candidato):
                total_pacientes = sum(j[2] for j in candidato)
                if r > mejor_num_jornadas:
                    mejor_num_jornadas = r
                    mejor_pacientes = total_pacientes
                    mejor_subconjunto = candidato
                elif r == mejor_num_jornadas and total_pacientes > mejor_pacientes:
                    mejor_pacientes = total_pacientes
                    mejor_subconjunto = candidato

    return sorted(mejor_subconjunto, key=lambda j: (j[0], j[1]))


def seleccionar_exhaustivo_con_conteo(solicitudes: list[Jornada]) -> tuple[list[Jornada], int]:
    """Ejecuta la solución exhaustiva registrando las operaciones elementales.

    Args:
        solicitudes: lista de solicitudes del mes.

    Returns:
        Tupla con el subconjunto óptimo y el total de operaciones/combinaciones exploradas.
    """
    n = len(solicitudes)
    if n == 0:
        return [], 0

    operaciones = 0
    mejor_subconjunto: list[Jornada] = []
    mejor_num_jornadas = 0
    mejor_pacientes = -1

    for r in range(1, n + 1):
        for combo in combinations(solicitudes, r):
            operaciones += 1
            candidato = list(combo)
            if not hay_cruce(candidato):
                operaciones += 1
                total_pacientes = sum(j[2] for j in candidato)
                if r > mejor_num_jornadas:
                    mejor_num_jornadas = r
                    mejor_pacientes = total_pacientes
                    mejor_subconjunto = candidato
                elif r == mejor_num_jornadas and total_pacientes > mejor_pacientes:
                    mejor_pacientes = total_pacientes
                    mejor_subconjunto = candidato

    return sorted(mejor_subconjunto, key=lambda j: (j[0], j[1])), operaciones
