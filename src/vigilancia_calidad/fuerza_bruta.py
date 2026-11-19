"""Estrategia actual de la Secretaría de Salud: Búsqueda por Fuerza Bruta.

Representa el procedimiento histórico implementado en la Plataforma Pulso,
el cual evalúa exhaustivamente todos los tramos posibles de lotes consecutivos.
Para el histórico de 33.000 lotes en 290 laboratorios, este método exhibe
una complejidad cuadrática O(n^2), tardando días de cómputo ininterrumpido.
"""

import sys
import os
from typing import List, Sequence, Union

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from . import Lote, ResultadoTramo
except (ImportError, ValueError):
    from __init__ import Lote, ResultadoTramo  # type: ignore


def tramo_critico_fuerza_bruta(
    datos: Union[Sequence[float], Sequence[Lote]]
) -> ResultadoTramo:
    """Encuentra el tramo consecutivo con mayor exceso acumulado usando fuerza bruta.

    Evalúa todos los posibles pares de índices (inicio, fin) tales que
    0 <= inicio <= fin < n, acumulando progresivamente los excesos para
    determinar el intervalo con la suma máxima.

    Complejidad Temporal:
        Theta(n^2) en el mejor, peor y caso promedio, dado que evalúa
        exactamente n*(n + 1)/2 combinaciones de intervalos.
    Complejidad Espacial:
        Theta(1) memoria auxiliar (no requiere estructuras adicionales).

    Args:
        datos: Secuencia de números flotantes (excesos) o lista de instancias Lote.

    Returns:
        ResultadoTramo con índice inicial, índice final y el exceso acumulado máximo.
        Si la entrada está vacía, retorna índices -1 y suma 0.0.
    """
    if not datos:
        return ResultadoTramo(indice_inicio=-1, indice_fin=-1, exceso_acumulado=0.0)

    # Extraer valores flotantes si se reciben instancias de Lote
    if isinstance(datos[0], Lote):
        valores: List[float] = [item.exceso for item in datos]  # type: ignore
    else:
        valores = list(datos)  # type: ignore

    n = len(valores)
    mejor_suma = float("-inf")
    mejor_inicio = 0
    mejor_fin = 0

    for i in range(n):
        suma_actual = 0.0
        for j in range(i, n):
            suma_actual += valores[j]
            # Redondeo para mitigar imprecisiones de coma flotante
            suma_redondeada = round(suma_actual, 6)
            if suma_redondeada > mejor_suma:
                mejor_suma = suma_redondeada
                mejor_inicio = i
                mejor_fin = j

    return ResultadoTramo(
        indice_inicio=mejor_inicio,
        indice_fin=mejor_fin,
        exceso_acumulado=round(mejor_suma, 4)
    )
