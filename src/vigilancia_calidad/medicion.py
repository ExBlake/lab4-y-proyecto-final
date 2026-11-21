"""Medición empírica y consumo eléctrico de la Operación 4 (Vigilancia de calidad).

Caso 2 — Plataforma Pulso. Compara experimentalmente las estrategias que
encuentran, para un laboratorio, el tramo de lotes consecutivos con mayor
exceso acumulado de positivos:

  - Fuerza bruta (estrategia actual de la Secretaría): Theta(n^2).
  - Dividir y vencer (estrategia propuesta): Theta(n log n).
  - Kadane (referencia lineal usada como oráculo): Theta(n).

Para cada tamaño n se mide:
  - Tiempo de reloj (mediana de varias repeticiones con time.perf_counter).
  - Tiempo de CPU del proceso (time.process_time, promedio por repetición).
  - Memoria pico asignada durante la ejecución (tracemalloc).
  - Energía estimada con la potencia del servidor informada por el cliente:
        Energía (kWh) = 0.38 kW x segundos / 3600

Uso:
    python src/vigilancia_calidad/medicion.py

Desarrollado para el Proyecto Final por Santiago Villada Arboleda (Persona 2).
"""

import gc
import os
import statistics
import sys
import time
import tracemalloc
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from . import ResultadoTramo
    from .datos import generar_lotes_laboratorio, extraer_excesos
    from .fuerza_bruta import tramo_critico_fuerza_bruta
    from .dividir_vencer import tramo_critico_dividir_vencer, tramo_critico_kadane
except (ImportError, ValueError):
    from __init__ import ResultadoTramo  # type: ignore
    from datos import generar_lotes_laboratorio, extraer_excesos  # type: ignore
    from fuerza_bruta import tramo_critico_fuerza_bruta  # type: ignore
    from dividir_vencer import tramo_critico_dividir_vencer, tramo_critico_kadane  # type: ignore


# ---------------------------------------------------------------------------
# Parámetros del cliente y del experimento
# ---------------------------------------------------------------------------

POTENCIA_SERVIDOR_KW: float = 380 / 1000  # Servidor dedicado de 380 W
SEGUNDOS_POR_HORA: float = 3600.0

TAMANOS_EXPERIMENTO: List[int] = [100, 500, 1_000, 5_000, 10_000]
SEMILLA_BASE: int = 2026

FUERZA_BRUTA: str = "Fuerza bruta"
DIVIDIR_VENCER: str = "Dividir y vencer"
KADANE: str = "Kadane"

FuncionTramo = Callable[[Sequence[float]], ResultadoTramo]

ESTRATEGIAS: Dict[str, FuncionTramo] = {
    FUERZA_BRUTA: tramo_critico_fuerza_bruta,
    DIVIDIR_VENCER: tramo_critico_dividir_vencer,
    KADANE: tramo_critico_kadane,
}

TOLERANCIA_EXCESO: float = 1e-4


@dataclass(frozen=True)
class Medicion:
    """Resultado de medir una estrategia sobre una instancia de tamaño n."""
    estrategia: str
    n: int
    repeticiones: int
    tiempo_reloj_s: float   # Mediana de time.perf_counter por repetición
    tiempo_cpu_s: float     # Promedio de time.process_time por repetición
    memoria_pico_kib: float  # Pico de memoria asignada (tracemalloc)
    energia_kwh: float      # Energía de una ejecución a 0.38 kW
    indice_inicio: int
    indice_fin: int
    exceso_acumulado: float


# ---------------------------------------------------------------------------
# Energía
# ---------------------------------------------------------------------------

def energia_kwh(segundos: float, potencia_kw: float = POTENCIA_SERVIDOR_KW) -> float:
    """Convierte un tiempo de ejecución en energía consumida por el servidor.

    Supone que el servidor consume su potencia nominal bajo carga sostenida
    durante todo el tiempo medido (aproximación del enunciado, no una medición
    eléctrica directa).

    Args:
        segundos: Tiempo de ejecución en segundos.
        potencia_kw: Potencia del equipo en kilovatios (0.38 kW por defecto).

    Returns:
        Energía en kilovatios-hora.
    """
    return potencia_kw * segundos / SEGUNDOS_POR_HORA


# ---------------------------------------------------------------------------
# Medición
# ---------------------------------------------------------------------------

def repeticiones_para(estrategia: str, n: int) -> int:
    """Define cuántas repeticiones se promedian según el costo esperado.

    La fuerza bruta es cuadrática y con n = 10.000 tarda varios segundos por
    corrida, así que se repite menos; las estrategias rápidas se repiten más
    para que el ruido del sistema operativo no domine la medición.

    Args:
        estrategia: Nombre de la estrategia.
        n: Tamaño de la instancia (número de lotes).

    Returns:
        Número de repeticiones a ejecutar.
    """
    if estrategia == FUERZA_BRUTA:
        return 3 if n >= 5_000 else 5
    return 15


def medir_tiempo(
    funcion: FuncionTramo, excesos: Sequence[float], repeticiones: int
) -> Tuple[float, float, ResultadoTramo]:
    """Mide el tiempo de reloj y de CPU de una estrategia.

    Desactiva el recolector de basura durante la medición para que sus pausas
    no se sumen al tiempo del algoritmo.

    Args:
        funcion: Estrategia a medir.
        excesos: Serie de excesos del laboratorio (no se modifica).
        repeticiones: Número de corridas.

    Returns:
        Tupla (mediana del tiempo de reloj en s, promedio del tiempo de CPU
        en s, resultado de la última corrida).
    """
    tiempos_reloj: List[float] = []
    resultado = ResultadoTramo(-1, -1, 0.0)
    gc_activo = gc.isenabled()
    gc.disable()
    try:
        cpu_inicio = time.process_time()
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            resultado = funcion(excesos)
            tiempos_reloj.append(time.perf_counter() - inicio)
        cpu_total = time.process_time() - cpu_inicio
    finally:
        if gc_activo:
            gc.enable()
    return statistics.median(tiempos_reloj), cpu_total / repeticiones, resultado


def medir_memoria_pico(funcion: FuncionTramo, excesos: Sequence[float]) -> float:
    """Mide el pico de memoria que asigna una estrategia en una corrida.

    Se hace en una corrida aparte porque tracemalloc ralentiza la ejecución
    y distorsionaría el tiempo.

    Args:
        funcion: Estrategia a medir.
        excesos: Serie de excesos del laboratorio.

    Returns:
        Memoria pico asignada durante la corrida, en KiB.
    """
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        funcion(excesos)
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return pico / 1024


def verificar_equivalencia(resultados: Dict[str, ResultadoTramo], n: int) -> None:
    """Comprueba que todas las estrategias reportan el mismo exceso máximo.

    Es la restricción del negocio "el tramo reportado es el de mayor exceso
    acumulado": una estrategia rápida que diera otro valor no sería válida.

    Args:
        resultados: Resultado de cada estrategia para la misma instancia.
        n: Tamaño de la instancia (para el mensaje de error).

    Raises:
        AssertionError: Si alguna estrategia difiere de la fuerza bruta.
    """
    referencia = resultados[FUERZA_BRUTA].exceso_acumulado
    for nombre, resultado in resultados.items():
        diferencia = abs(resultado.exceso_acumulado - referencia)
        assert diferencia < TOLERANCIA_EXCESO, (
            f"n={n}: {nombre} reporta {resultado.exceso_acumulado} "
            f"y la fuerza bruta {referencia}"
        )


def medir_estrategias(
    tamanos: Sequence[int] = TAMANOS_EXPERIMENTO, semilla: int = SEMILLA_BASE
) -> List[Medicion]:
    """Ejecuta el experimento completo sobre tamaños crecientes de lotes.

    Para cada n genera un histórico sintético de un laboratorio (con un tramo
    descalibrado inyectado), mide las tres estrategias sobre la misma serie y
    verifica que coincidan.

    Args:
        tamanos: Tamaños n (número de lotes) a evaluar.
        semilla: Semilla base para la generación reproducible de datos.

    Returns:
        Lista de mediciones, una por estrategia y tamaño.
    """
    mediciones: List[Medicion] = []
    for n in tamanos:
        lotes = generar_lotes_laboratorio(n=n, semilla=semilla + n)
        excesos = extraer_excesos(lotes)
        resultados: Dict[str, ResultadoTramo] = {}

        for nombre, funcion in ESTRATEGIAS.items():
            reps = repeticiones_para(nombre, n)
            print(f"  n={n:>6,}  {nombre:<17} ({reps} rep.)...", end="", flush=True)
            t_reloj, t_cpu, resultado = medir_tiempo(funcion, excesos, reps)
            memoria = medir_memoria_pico(funcion, excesos)
            print(f" {t_reloj:.6f} s")

            resultados[nombre] = resultado
            mediciones.append(
                Medicion(
                    estrategia=nombre,
                    n=n,
                    repeticiones=reps,
                    tiempo_reloj_s=t_reloj,
                    tiempo_cpu_s=t_cpu,
                    memoria_pico_kib=memoria,
                    energia_kwh=energia_kwh(t_reloj),
                    indice_inicio=resultado.indice_inicio,
                    indice_fin=resultado.indice_fin,
                    exceso_acumulado=resultado.exceso_acumulado,
                )
            )

        verificar_equivalencia(resultados, n)
    return mediciones


# ---------------------------------------------------------------------------
# Reporte en consola
# ---------------------------------------------------------------------------

def imprimir_tabla_mediciones(mediciones: Sequence[Medicion]) -> None:
    """Imprime la tabla de tiempos, memoria y energía por estrategia y tamaño.

    Args:
        mediciones: Mediciones obtenidas con medir_estrategias.
    """
    encabezado = (
        f"{'Estrategia':<17} {'n':>7} {'Reloj (s)':>12} {'CPU (s)':>12} "
        f"{'Memoria (KiB)':>14} {'Energia (kWh)':>14} {'Tramo':>15} {'Exceso':>9}"
    )
    print(encabezado)
    print("-" * len(encabezado))
    for m in mediciones:
        tramo = f"[{m.indice_inicio}, {m.indice_fin}]"
        print(
            f"{m.estrategia:<17} {m.n:>7,} {m.tiempo_reloj_s:>12.6f} "
            f"{m.tiempo_cpu_s:>12.6f} {m.memoria_pico_kib:>14.1f} "
            f"{m.energia_kwh:>14.3e} {tramo:>15} {m.exceso_acumulado:>9.4f}"
        )


def ejecutar_experimentos() -> List[Medicion]:
    """Punto de entrada: mide las estrategias e imprime los resultados.

    Returns:
        Lista de mediciones obtenidas.
    """
    print("=" * 70)
    print("OPERACION 4 - VIGILANCIA DE CALIDAD: MEDICION EMPIRICA")
    print(f"Potencia del servidor: {POTENCIA_SERVIDOR_KW} kW | Semilla: {SEMILLA_BASE}")
    print("=" * 70)

    mediciones = medir_estrategias()
    print()
    imprimir_tabla_mediciones(mediciones)
    print("\n[OK] Las tres estrategias reportan el mismo exceso maximo en todos los tamanos.")
    return mediciones


if __name__ == "__main__":
    ejecutar_experimentos()
