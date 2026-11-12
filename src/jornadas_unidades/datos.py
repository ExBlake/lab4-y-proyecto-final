"""Generador de datos sintéticos para las solicitudes de jornadas de unidades móviles.

Produce instancias representativas del volumen y características operativas
de la Plataforma Pulso (Caso 2), utilizando semillas reproducibles.

Generador determinista desarrollado por el Grupo 8.
"""

import random
from typing import List, Tuple

# Tipo Jornada: (inicio_minutos, fin_minutos, pacientes_alto_riesgo)
Jornada = Tuple[int, int, int]

# Constantes del dominio operativo
MINUTOS_MES = 30 * 24 * 60  # 43,200 minutos en un mes de 30 días
DURACION_MIN_JORNADA = 180   # 3 horas mínimo (atención + traslado)
DURACION_MAX_JORNADA = 720   # 12 horas máximo


def generar_solicitudes(
    n: int,
    semilla: int = 42,
    minutos_horizonte: int = MINUTOS_MES,
    duracion_min: int = DURACION_MIN_JORNADA,
    duracion_max: int = DURACION_MAX_JORNADA,
    min_pacientes: int = 5,
    max_pacientes: int = 150
) -> List[Jornada]:
    """Genera una lista de n solicitudes de jornada sintéticas.

    Cada solicitud representa la petición de un municipio para la visita de
    la unidad móvil de su subregión durante el mes, con tiempos de inicio,
    fin (que incluye desplazamientos) y número de pacientes de alto riesgo.

    Args:
        n: número de solicitudes a generar.
        semilla: semilla para el generador pseudoaleatorio para reproducibilidad.
        minutos_horizonte: horizonte temporal de la programación en minutos (mes).
        duracion_min: duración mínima de una jornada en minutos.
        duracion_max: duración máxima de una jornada en minutos.
        min_pacientes: mínimo de pacientes de alto riesgo pendientes.
        max_pacientes: máximo de pacientes de alto riesgo pendientes.

    Returns:
        Lista de n jornadas en orden de llegada simulado.
    """
    if n <= 0:
        return []

    rng = random.Random(semilla)
    solicitudes: List[Jornada] = []

    for _ in range(n):
        # Duración de la jornada
        duracion = rng.randint(duracion_min, duracion_max)
        # Inicio distribuido en el horizonte del mes
        max_inicio = max(0, minutos_horizonte - duracion)
        inicio = rng.randint(0, max_inicio)
        fin = inicio + duracion
        pacientes = rng.randint(min_pacientes, max_pacientes)
        solicitudes.append((inicio, fin, pacientes))

    return solicitudes


def generar_instancia_alta_densidad(
    n: int,
    semilla: int = 123,
    ventana_minutos: int = 2880  # 2 días de alta concentración
) -> List[Jornada]:
    """Genera instancias con alta probabilidad de cruces (alta congestión).

    Útil para pruebas de estrés y contrastes rigurosos entre exhaustivo y voraz.

    Args:
        n: número de solicitudes.
        semilla: semilla pseudoaleatoria.
        ventana_minutos: ventana temporal comprimida para forzar traslapes.

    Returns:
        Lista de jornadas en ventana reducida.
    """
    return generar_solicitudes(
        n=n,
        semilla=semilla,
        minutos_horizonte=ventana_minutos,
        duracion_min=120,
        duracion_max=480,
        min_pacientes=10,
        max_pacientes=100
    )

