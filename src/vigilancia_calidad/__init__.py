"""Módulo de Vigilancia de la Calidad de los Laboratorios (Operación 4).

Caso 2 — Plataforma Pulso: Consolidación, priorización y agendamiento
del tamizaje de diabetes.

Este módulo implementa las estrategias algorítmicas para identificar el tramo
consecutivo de lotes con mayor exceso acumulado de resultados positivos
(Maximum Subarray Problem):
  1. Estrategia actual: Búsqueda exhaustiva por fuerza bruta O(n^2).
  2. Estrategia propuesta: Algoritmo de Dividir y Vencer O(n log n).
  3. Estrategia lineal de verificación: Algoritmo de Kadane O(n).

Desarrollado para el Proyecto Final por Juan Felipe Torres (Persona 1).
"""

from typing import NamedTuple


class Lote(NamedTuple):
    """Representación inmutable de un lote de pruebas de laboratorio."""
    id_lote: str
    id_laboratorio: str
    fecha_resultado: str
    tasa_observada: float  # Tasa de riesgo >= 70 observada en el lote (0.0 a 1.0)
    tasa_esperada: float   # Tasa esperada para la población asignada (0.0 a 1.0)
    exceso: float          # tasa_observada - tasa_esperada (puede ser negativa)


class ResultadoTramo(NamedTuple):
    """Resultado del análisis de tramo crítico con mayor exceso acumulado."""
    indice_inicio: int
    indice_fin: int
    exceso_acumulado: float
