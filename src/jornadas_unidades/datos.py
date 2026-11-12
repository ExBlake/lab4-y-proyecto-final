"""Generador de instancias sintéticas de solicitudes de jornadas.

Todas las funciones reciben una semilla para que los experimentos y las
pruebas sean reproducibles.
"""

import random

from estrategia import Jornada

MINUTOS_POR_DIA = 24 * 60
DIAS_DEL_MES = 30
HORIZONTE_MES = DIAS_DEL_MES * MINUTOS_POR_DIA  # 43.200 minutos

# Duración de una jornada, incluido el desplazamiento (en minutos).
DURACION_MINIMA = 4 * 60
DURACION_MAXIMA = 12 * 60

# Pacientes de alto riesgo pendientes en un municipio.
PACIENTES_MINIMO = 5
PACIENTES_MAXIMO = 150

SEMILLA_POR_DEFECTO = 2026


def generar_solicitudes(
    n: int,
    semilla: int = SEMILLA_POR_DEFECTO,
    horizonte: int = HORIZONTE_MES,
    duracion_minima: int = DURACION_MINIMA,
    duracion_maxima: int = DURACION_MAXIMA,
) -> list[Jornada]:
    """Genera n solicitudes aleatorias en el orden en que "llegan".

    Args:
        n: número de solicitudes a generar.
        semilla: semilla del generador pseudoaleatorio.
        horizonte: minutos disponibles para programar (por defecto, un mes
            de 30 días). Un horizonte corto produce más cruces.
        duracion_minima: duración mínima de una jornada en minutos.
        duracion_maxima: duración máxima de una jornada en minutos.

    Returns:
        Lista de jornadas (inicio, fin, pacientes) con inicio < fin y
        fin <= horizonte, en un orden de llegada aleatorio.

    Raises:
        ValueError: si n es negativo o las duraciones no caben en el
            horizonte.
    """
    if n < 0:
        raise ValueError("n debe ser mayor o igual que 0")
    if not 0 < duracion_minima <= duracion_maxima <= horizonte:
        raise ValueError("Las duraciones deben caber en el horizonte")

    generador = random.Random(semilla)
    solicitudes: list[Jornada] = []
    for _ in range(n):
        duracion = generador.randint(duracion_minima, duracion_maxima)
        inicio = generador.randint(0, horizonte - duracion)
        pacientes = generador.randint(PACIENTES_MINIMO, PACIENTES_MAXIMO)
        solicitudes.append((inicio, inicio + duracion, pacientes))
    return solicitudes


def generar_instancias_pequenas(
    cantidad: int,
    n_minimo: int = 1,
    n_maximo: int = 12,
    semilla: int = SEMILLA_POR_DEFECTO,
) -> list[list[Jornada]]:
    """Genera instancias pequeñas para comparar contra la exhaustiva.

    Usa un horizonte de 2 días para que haya muchos cruces y la elección
    de jornadas no sea trivial.

    Args:
        cantidad: número de instancias.
        n_minimo: tamaño mínimo de cada instancia.
        n_maximo: tamaño máximo de cada instancia.
        semilla: semilla del generador pseudoaleatorio.

    Returns:
        Lista de instancias; cada una es una lista de jornadas.
    """
    generador = random.Random(semilla)
    instancias = []
    for _ in range(cantidad):
        n = generador.randint(n_minimo, n_maximo)
        instancias.append(
            generar_solicitudes(
                n,
                semilla=generador.randint(0, 10**9),
                horizonte=2 * MINUTOS_POR_DIA,
            )
        )
    return instancias
