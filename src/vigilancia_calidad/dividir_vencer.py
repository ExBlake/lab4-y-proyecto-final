"""Estrategia de Dividir y Vencer para la Vigilancia de Calidad de Laboratorios.

Resuelve el problema del Subarreglo de Suma Máxima (Maximum Subarray Problem)
aplicado a la detección de tramos críticos de lotes consecutivos con mayor
exceso acumulado de resultados positivos.

Complejidad Teórica:
    - Ecuación de Recurrencia: T(n) = 2*T(n/2) + Theta(n)
    - Por el Teorema Maestro (Caso 2): T(n) = Theta(n log n)
    - Complejidad Espacial: Theta(log n) por la profundidad del call stack.

Desarrollado para el Proyecto Final por Juan Felipe Torres (Persona 1).
"""

import sys
import os
from typing import List, Sequence, Tuple, Union

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from . import Lote, ResultadoTramo
except (ImportError, ValueError):
    from __init__ import Lote, ResultadoTramo  # type: ignore


def _encontrar_tramo_cruzado(
    valores: List[float], bajo: int, medio: int, alto: int
) -> Tuple[int, int, float]:
    """Encuentra el tramo máximo que cruza el punto medio en tiempo O(n).

    Se extiende desde el punto medio hacia la izquierda buscando la suma máxima,
    y desde el punto medio + 1 hacia la derecha buscando la suma máxima.

    Args:
        valores: Lista numérica de excesos.
        bajo: Índice inicial del subarreglo.
        medio: Índice central de partición.
        alto: Índice final del subarreglo.

    Returns:
        Tupla (indice_inicio, indice_fin, suma_maxima_cruzada).
    """
    # Extensión hacia la izquierda desde medio hacia bajo
    suma_izq = float("-inf")
    suma_acum = 0.0
    max_izq = medio
    for i in range(medio, bajo - 1, -1):
        suma_acum += valores[i]
        suma_red = round(suma_acum, 6)
        if suma_red > suma_izq:
            suma_izq = suma_red
            max_izq = i

    # Extensión hacia la derecha desde medio + 1 hacia alto
    suma_der = float("-inf")
    suma_acum = 0.0
    max_der = medio + 1
    for j in range(medio + 1, alto + 1):
        suma_acum += valores[j]
        suma_red = round(suma_acum, 6)
        if suma_red > suma_der:
            suma_der = suma_der if suma_red < suma_der else suma_red
            max_der = j

    suma_total_cruzada = round(suma_izq + suma_der, 6)
    return max_izq, max_der, suma_total_cruzada


def _tramo_maximo_recursivo(
    valores: List[float], bajo: int, alto: int
) -> Tuple[int, int, float]:
    """Función recursiva núcleo que implementa el paradigma Dividir y Vencer.

    Args:
        valores: Lista numérica de excesos.
        bajo: Índice inicial de la porción actual.
        alto: Índice final de la porción actual.

    Returns:
        Tupla (indice_inicio, indice_fin, suma_maxima).
    """
    # Caso base: el subarreglo contiene un único elemento
    if bajo == alto:
        return bajo, alto, round(valores[bajo], 6)

    # División
    medio = (bajo + alto) // 2

    # Conquista: resolver recursivamente mitad izquierda y mitad derecha
    izq_inicio, izq_fin, izq_suma = _tramo_maximo_recursivo(valores, bajo, medio)
    der_inicio, der_fin, der_suma = _tramo_maximo_recursivo(valores, medio + 1, alto)

    # Combinación: tramo que cruza el punto central
    cruz_inicio, cruz_fin, cruz_suma = _encontrar_tramo_cruzado(valores, bajo, medio, alto)

    # Retornar el tramo con la mayor suma acumulada
    if izq_suma >= der_suma and izq_suma >= cruz_suma:
        return izq_inicio, izq_fin, izq_suma
    elif der_suma >= izq_suma and der_suma >= cruz_suma:
        return der_inicio, der_fin, der_suma
    else:
        return cruz_inicio, cruz_fin, cruz_suma


def tramo_critico_dividir_vencer(
    datos: Union[Sequence[float], Sequence[Lote]]
) -> ResultadoTramo:
    """Calcula el tramo de mayor exceso acumulado mediante Dividir y Vencer.

    Aplica descomposición recursiva bipartita garantizando una complejidad
    asintótica O(n log n), reduciendo drásticamente el tiempo de procesamiento
    frente a la estrategia cuadrática de fuerza bruta actual.

    Args:
        datos: Secuencia de flotantes o lista inmutable de Lote.

    Returns:
        ResultadoTramo con índice inicio, índice fin y exceso acumulado máximo.
    """
    if not datos:
        return ResultadoTramo(indice_inicio=-1, indice_fin=-1, exceso_acumulado=0.0)

    if isinstance(datos[0], Lote):
        valores: List[float] = [item.exceso for item in datos]  # type: ignore
    else:
        valores = list(datos)  # type: ignore

    inicio, fin, suma = _tramo_maximo_recursivo(valores, 0, len(valores) - 1)

    return ResultadoTramo(
        indice_inicio=inicio,
        indice_fin=fin,
        exceso_acumulado=round(suma, 4)
    )


def tramo_critico_kadane(
    datos: Union[Sequence[float], Sequence[Lote]]
) -> ResultadoTramo:
    """Implementación de referencia lineal O(n) basada en el Algoritmo de Kadane.

    Se utiliza como oráculo complementario de pruebas para verificar
    formalmente que la solución de Dividir y Vencer es óptima y exacta.

    Complejidad Temporal: Theta(n)
    Complejidad Espacial: Theta(1)
    """
    if not datos:
        return ResultadoTramo(indice_inicio=-1, indice_fin=-1, exceso_acumulado=0.0)

    if isinstance(datos[0], Lote):
        valores: List[float] = [item.exceso for item in datos]  # type: ignore
    else:
        valores = list(datos)  # type: ignore

    max_actual = valores[0]
    max_global = valores[0]
    inicio_temp = 0
    mejor_inicio = 0
    mejor_fin = 0

    for i in range(1, len(valores)):
        v = valores[i]
        if v > max_actual + v:
            max_actual = v
            inicio_temp = i
        else:
            max_actual = round(max_actual + v, 6)

        if max_actual > max_global:
            max_global = max_actual
            mejor_inicio = inicio_temp
            mejor_fin = i

    return ResultadoTramo(
        indice_inicio=mejor_inicio,
        indice_fin=mejor_fin,
        exceso_acumulado=round(max_global, 4)
    )
