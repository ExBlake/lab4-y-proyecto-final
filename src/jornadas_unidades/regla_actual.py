"""Regla actual del coordinador: asignación por orden de llegada.

Es la línea base del proceso actual. No es óptima: una jornada larga que
llega primero puede bloquear varias jornadas cortas que llegan después.
"""

from estrategia import Jornada, se_cruzan, validar_solicitudes


def asignar_por_llegada(solicitudes: list[Jornada]) -> list[Jornada]:
    """Reproduce el procedimiento actual: orden de llegada, rechazando cruces.

    Recorre las solicitudes en el orden recibido y acepta cada una que no
    se cruce con ninguna de las ya aceptadas. Compara contra todas las
    aceptadas porque, al no estar ordenadas por hora, una solicitud nueva
    puede caer antes, después o entre jornadas ya aceptadas. Complejidad:
    O(n · k), con k jornadas aceptadas (O(n^2) en el peor caso).

    Args:
        solicitudes: solicitudes en el orden en que llegaron.

    Returns:
        Las jornadas aceptadas, en el orden en que fueron aceptadas.
    """
    validar_solicitudes(solicitudes)
    aceptadas: list[Jornada] = []
    for solicitud in solicitudes:
        if not any(se_cruzan(solicitud, otra) for otra in aceptadas):
            aceptadas.append(solicitud)
    return aceptadas
