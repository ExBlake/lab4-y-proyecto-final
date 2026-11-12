"""Programación de las jornadas de una unidad móvil (estrategia voraz).

Criterio declarado en el README: maximizar el número de jornadas atendidas
por la unidad móvil de una subregión, sin que dos jornadas se crucen.

Convención de tiempo: cada jornada ocupa el intervalo semiabierto
[inicio, fin). Por eso una jornada que empieza justo en el minuto en que
otra termina NO se cruza con ella.
"""

# (inicio, fin, pacientes_alto_riesgo); inicio y fin en minutos.
Jornada = tuple[int, int, int]


def validar_solicitudes(solicitudes: list[Jornada]) -> None:
    """Verifica que cada solicitud tenga un formato válido.

    Args:
        solicitudes: solicitudes del mes de una subregión.

    Raises:
        ValueError: si alguna solicitud tiene inicio negativo, fin menor o
            igual que el inicio o un número negativo de pacientes.
    """
    for inicio, fin, pacientes in solicitudes:
        if inicio < 0 or fin <= inicio:
            raise ValueError(
                f"Jornada con horario inválido: inicio={inicio}, fin={fin}"
            )
        if pacientes < 0:
            raise ValueError(f"Número de pacientes negativo: {pacientes}")


def se_cruzan(a: Jornada, b: Jornada) -> bool:
    """Indica si dos jornadas se cruzan en el tiempo.

    Args:
        a: primera jornada.
        b: segunda jornada.

    Returns:
        True si los intervalos [inicio, fin) comparten algún minuto;
        False si son disjuntos o solo se tocan en un extremo.
    """
    return a[0] < b[1] and b[0] < a[1]


def seleccionar_jornadas(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige las jornadas que atiende la unidad, sin cruces.

    Aplica la selección de actividades voraz: ordena las solicitudes por
    hora de fin y acepta cada una cuyo inicio sea mayor o igual que el fin
    de la última jornada aceptada. Ante un empate en la hora de fin se
    prefiere la jornada con más pacientes de alto riesgo; el empate no
    cambia el número de jornadas, solo cuál de ellas se escoge.

    Complejidad: O(n log n) en tiempo por el ordenamiento y O(n) en
    espacio.

    Args:
        solicitudes: solicitudes del mes de una subregión.

    Returns:
        Las jornadas elegidas, ordenadas por hora de inicio. Optimiza el
        criterio que el equipo declaró en el README (número de jornadas).
    """
    validar_solicitudes(solicitudes)
    ordenadas = sorted(solicitudes, key=lambda j: (j[1], -j[2], j[0]))

    elegidas: list[Jornada] = []
    ultimo_fin = -1
    for jornada in ordenadas:
        if jornada[0] >= ultimo_fin:
            elegidas.append(jornada)
            ultimo_fin = jornada[1]

    # Al no cruzarse, el orden por fin coincide con el orden por inicio.
    return elegidas


def hay_cruce(jornadas: list[Jornada]) -> bool:
    """Indica si alguna pareja de jornadas se cruza.

    Una jornada que empieza justo cuando otra termina NO se considera
    cruce (intervalos semiabiertos [inicio, fin)). Ordena por inicio y
    compara cada jornada con el mayor fin visto hasta ese momento, en
    O(n log n).

    Args:
        jornadas: jornadas a revisar.

    Returns:
        True si dos jornadas se cruzan; False en caso contrario.
    """
    ordenadas = sorted(jornadas)
    mayor_fin = None
    for inicio, fin, _ in ordenadas:
        if mayor_fin is not None and inicio < mayor_fin:
            return True
        mayor_fin = fin if mayor_fin is None else max(mayor_fin, fin)
    return False
