"""Solución exhaustiva: prueba todos los subconjuntos de solicitudes.

Es la solución exacta con la que se verifica la estrategia voraz. Su costo
es O(2^n · n log n), así que solo se ejecuta con instancias pequeñas.
"""

from estrategia import Jornada, hay_cruce, validar_solicitudes

# Por encima de este tamaño la búsqueda exhaustiva deja de ser práctica.
MAXIMO_EXHAUSTIVO = 22


def seleccionar_exhaustivo(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige el mejor subconjunto sin cruces probando todos los subconjuntos.

    Recorre las 2^n máscaras de bits; cada bit indica si la solicitud
    correspondiente entra al subconjunto. Descarta los subconjuntos con
    cruces y se queda con el de mayor número de jornadas.

    Args:
        solicitudes: solicitudes del mes de una subregión.

    Returns:
        Un subconjunto óptimo para el mismo criterio (máximo número de
        jornadas sin cruces), ordenado por hora de inicio.

    Raises:
        ValueError: si la instancia supera MAXIMO_EXHAUSTIVO solicitudes o
            alguna solicitud es inválida.
    """
    validar_solicitudes(solicitudes)
    n = len(solicitudes)
    if n > MAXIMO_EXHAUSTIVO:
        raise ValueError(
            f"La búsqueda exhaustiva solo admite hasta {MAXIMO_EXHAUSTIVO} "
            f"solicitudes; se recibieron {n}."
        )

    mejor: list[Jornada] = []
    for mascara in range(1 << n):
        subconjunto = [solicitudes[i] for i in range(n) if mascara >> i & 1]
        if len(subconjunto) > len(mejor) and not hay_cruce(subconjunto):
            mejor = subconjunto

    return sorted(mejor)
