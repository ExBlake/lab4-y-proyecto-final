"""Generador de datos sintéticos para lotes de procesamiento de laboratorios.

Produce instancias realistas que modelan el comportamiento histórico de
los 290 laboratorios e IPS del departamento en la Plataforma Pulso (Caso 2).

Cada laboratorio procesa un promedio de 30 lotes diarios, acumulando
aproximadamente 33.000 lotes en un histórico de 3 años.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from . import Lote
except (ImportError, ValueError):
    from __init__ import Lote  # type: ignore


def generar_lotes_laboratorio(
    n: int,
    id_laboratorio: str = "LAB-001",
    tasa_base_esperada: float = 0.25,
    inyectar_anomalia: bool = True,
    anomalia_inicio: Optional[int] = None,
    anomalia_duracion: Optional[int] = None,
    semilla: int = 42
) -> List[Lote]:
    """Genera una serie cronológica de n lotes sintéticos para un laboratorio.

    En condiciones normales de calibración, la tasa observada oscila alrededor
    de la tasa esperada (con excesos positivos y negativos balanceados).
    Si se inyecta una anomalía, se simula un período donde el equipo estuvo
    descalibrado, generando un tramo de excesos marcadamente positivos.

    Args:
        n: Cantidad de lotes a generar (hasta 33.000 para el histórico completo).
        id_laboratorio: Identificador alfanumérico del laboratorio o IPS.
        tasa_base_esperada: Proporción poblacional esperada con riesgo >= 70.
        inyectar_anomalia: Si True, inserta un tramo consecutivo de descalibración.
        anomalia_inicio: Índice inicial del tramo anómalo (None para ubicarlo al azar).
        anomalia_duracion: Cantidad de lotes del tramo anómalo.
        semilla: Semilla pseudoaleatoria para reproducibilidad experimental.

    Returns:
        Lista de n instancias inmutables de Lote en orden cronológico.
    """
    if n <= 0:
        return []

    rng = random.Random(semilla)
    fecha_base = datetime(2023, 1, 1, 8, 0, 0)
    lotes: List[Lote] = []

    # Configuración de anomalía controlada si se solicita
    if inyectar_anomalia and n >= 5:
        if anomalia_duracion is None:
            anomalia_duracion = max(3, n // 10)
        anomalia_duracion = min(anomalia_duracion, n)
        if anomalia_inicio is None:
            max_inicio = max(0, n - anomalia_duracion)
            anomalia_inicio = rng.randint(0, max_inicio)
        anomalia_fin = anomalia_inicio + anomalia_duracion
    else:
        anomalia_inicio = -1
        anomalia_fin = -1

    for i in range(n):
        # Avanza el tiempo (~48 minutos entre lotes para cubrir 30 lotes/día)
        fecha_lote = fecha_base + timedelta(minutes=i * 48)
        fecha_str = fecha_lote.strftime("%Y-%m-%d %H:%M")

        # Tasa esperada para la población asignada (ligera variación por sede)
        esperada = max(0.10, min(0.40, tasa_base_esperada + rng.uniform(-0.03, 0.03)))

        # Generar tasa observada
        if anomalia_inicio <= i < anomalia_fin:
            # Tramo descalibrado: equipo sobreestima consistentemente el riesgo
            observada = min(0.95, esperada + rng.uniform(0.15, 0.45))
        else:
            # Calibración normal: ruido centrado en 0 con tendencia ligeramente negativa
            observada = max(0.02, min(0.98, esperada + rng.uniform(-0.12, 0.08)))

        # Exceso = observada - esperada (redondeado a 4 decimales para estabilidad numérica)
        exceso = round(observada - esperada, 4)

        lotes.append(
            Lote(
                id_lote=f"LOT-{id_laboratorio}-{i + 1:06d}",
                id_laboratorio=id_laboratorio,
                fecha_resultado=fecha_str,
                tasa_observada=round(observada, 4),
                tasa_esperada=round(esperada, 4),
                exceso=exceso
            )
        )

    return lotes


def extraer_excesos(lotes: List[Lote]) -> List[float]:
    """Extrae la secuencia numérica de excesos a partir de la lista de lotes.

    Args:
        lotes: Lista de registros de lote.

    Returns:
        Lista de valores float de exceso preservando el orden original.
    """
    return [lote.exceso for lote in lotes]
