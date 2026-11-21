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

Con las mediciones se ajusta la constante c de cada modelo teórico
(t = c * f(n)), se extrapola al histórico real del cliente (33.000 lotes por
laboratorio, 290 laboratorios) y se proyecta el consumo a un año (365 corridas).
Los resultados se guardan en experimentos/vigilancia_calidad/.

Uso:
    python src/vigilancia_calidad/medicion.py
    python src/vigilancia_calidad/medicion.py --validar-volumen-real

La opción --validar-volumen-real mide además una corrida con n = 33.000 para
contrastar la extrapolación con una medición real (unos 3 minutos extra).

Desarrollado para el Proyecto Final por Santiago Villada Arboleda (Persona 2).
"""

import argparse
import csv
import gc
import json
import math
import os
import platform
import statistics
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence, Tuple

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

# Volumen real informado por el cliente
NUM_LABORATORIOS: int = 290
LOTES_HISTORICO: int = 33_000   # ~30 lotes/día durante 3 años
CORRIDAS_POR_ANIO: int = 365    # Supuesto: la vigilancia se recalcula a diario

# Modelo teórico de crecimiento f(n) de cada estrategia
MODELOS_COMPLEJIDAD: Dict[str, Callable[[float], float]] = {
    FUERZA_BRUTA: lambda n: n * n,
    DIVIDIR_VENCER: lambda n: n * math.log2(n),
    KADANE: lambda n: n,
}
NOTACION_MODELO: Dict[str, str] = {
    FUERZA_BRUTA: "n^2",
    DIVIDIR_VENCER: "n log2 n",
    KADANE: "n",
}

RAIZ_REPOSITORIO: str = os.path.dirname(os.path.dirname(directorio_actual))
DIRECTORIO_EXPERIMENTOS: str = os.path.join(
    RAIZ_REPOSITORIO, "experimentos", "vigilancia_calidad"
)


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


@dataclass(frozen=True)
class Extrapolacion:
    """Proyección de una estrategia al volumen real y a un año de operación."""
    estrategia: str
    modelo: str                    # f(n) usado en el ajuste t = c * f(n)
    constante_s: float             # c, en segundos por unidad de f(n)
    r2: float                      # Calidad del ajuste sobre las mediciones
    tiempo_laboratorio_s: float    # Un laboratorio con 33.000 lotes
    tiempo_corrida_s: float        # Los 290 laboratorios
    tiempo_corrida_h: float
    energia_corrida_kwh: float
    energia_anual_kwh: float       # 365 corridas
    ahorro_anual_kwh: float        # Frente a la fuerza bruta (proceso actual)
    ahorro_porcentual: float


@dataclass(frozen=True)
class Validacion:
    """Contraste entre el tiempo extrapolado y el medido con n = 33.000."""
    estrategia: str
    n: int
    tiempo_predicho_s: float
    tiempo_medido_s: float
    error_relativo: float


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
# Ajuste teórico y extrapolación al volumen real
# ---------------------------------------------------------------------------

def filtrar_estrategia(mediciones: Sequence[Medicion], estrategia: str) -> List[Medicion]:
    """Devuelve las mediciones de una estrategia ordenadas por n.

    Args:
        mediciones: Todas las mediciones del experimento.
        estrategia: Nombre de la estrategia.

    Returns:
        Mediciones de esa estrategia en orden creciente de n.
    """
    return sorted((m for m in mediciones if m.estrategia == estrategia), key=lambda m: m.n)


def ajustar_constante(
    mediciones: Sequence[Medicion], estrategia: str
) -> Tuple[float, float]:
    """Ajusta t = c * f(n) por mínimos cuadrados (recta por el origen).

    c = sum(t_i * f(n_i)) / sum(f(n_i)^2). El ajuste queda dominado por los
    tamaños grandes, que son los que importan para extrapolar a 33.000 lotes.

    Args:
        mediciones: Mediciones del experimento.
        estrategia: Estrategia a ajustar con su modelo de MODELOS_COMPLEJIDAD.

    Returns:
        Tupla (constante c en segundos, coeficiente de determinación R^2).
    """
    modelo = MODELOS_COMPLEJIDAD[estrategia]
    puntos = filtrar_estrategia(mediciones, estrategia)
    f = [modelo(m.n) for m in puntos]
    t = [m.tiempo_reloj_s for m in puntos]

    c = sum(ti * fi for ti, fi in zip(t, f)) / sum(fi * fi for fi in f)

    media_t = statistics.fmean(t)
    ss_res = sum((ti - c * fi) ** 2 for ti, fi in zip(t, f))
    ss_tot = sum((ti - media_t) ** 2 for ti in t)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return c, r2


def predecir_tiempo(constante: float, estrategia: str, n: int) -> float:
    """Predice el tiempo de una estrategia para n lotes con su modelo ajustado.

    Args:
        constante: Constante c obtenida con ajustar_constante.
        estrategia: Nombre de la estrategia.
        n: Número de lotes.

    Returns:
        Tiempo estimado en segundos.
    """
    return constante * MODELOS_COMPLEJIDAD[estrategia](n)


def extrapolar_volumen_real(mediciones: Sequence[Medicion]) -> List[Extrapolacion]:
    """Extrapola cada estrategia al histórico real y a un año de operación.

    Una corrida completa analiza los 290 laboratorios con 33.000 lotes cada uno
    (los laboratorios son independientes y se procesan uno tras otro en un solo
    hilo). El año se proyecta con 365 corridas. El ahorro se calcula frente a la
    fuerza bruta, que es el proceso actual de la Secretaría.

    Args:
        mediciones: Mediciones del experimento.

    Returns:
        Una extrapolación por estrategia, en el orden de ESTRATEGIAS.
    """
    preliminares: Dict[str, Tuple[float, float, float, float]] = {}
    for nombre in ESTRATEGIAS:
        c, r2 = ajustar_constante(mediciones, nombre)
        t_lab = predecir_tiempo(c, nombre, LOTES_HISTORICO)
        t_corrida = t_lab * NUM_LABORATORIOS
        preliminares[nombre] = (c, r2, t_lab, t_corrida)

    energia_anual_actual = energia_kwh(preliminares[FUERZA_BRUTA][3]) * CORRIDAS_POR_ANIO

    extrapolaciones: List[Extrapolacion] = []
    for nombre, (c, r2, t_lab, t_corrida) in preliminares.items():
        e_corrida = energia_kwh(t_corrida)
        e_anual = e_corrida * CORRIDAS_POR_ANIO
        ahorro = energia_anual_actual - e_anual
        extrapolaciones.append(
            Extrapolacion(
                estrategia=nombre,
                modelo=NOTACION_MODELO[nombre],
                constante_s=c,
                r2=r2,
                tiempo_laboratorio_s=t_lab,
                tiempo_corrida_s=t_corrida,
                tiempo_corrida_h=t_corrida / SEGUNDOS_POR_HORA,
                energia_corrida_kwh=e_corrida,
                energia_anual_kwh=e_anual,
                ahorro_anual_kwh=ahorro,
                ahorro_porcentual=100.0 * ahorro / energia_anual_actual,
            )
        )
    return extrapolaciones


def validar_volumen_real(
    extrapolaciones: Sequence[Extrapolacion], semilla: int = SEMILLA_BASE
) -> List[Validacion]:
    """Mide una corrida real con n = 33.000 y la compara con lo extrapolado.

    Args:
        extrapolaciones: Resultado de extrapolar_volumen_real.
        semilla: Semilla base de los datos.

    Returns:
        Una validación por estrategia.
    """
    excesos = extraer_excesos(
        generar_lotes_laboratorio(n=LOTES_HISTORICO, semilla=semilla + LOTES_HISTORICO)
    )
    validaciones: List[Validacion] = []
    resultados: Dict[str, ResultadoTramo] = {}
    for ext in extrapolaciones:
        reps = 1 if ext.estrategia == FUERZA_BRUTA else 5
        print(f"  n={LOTES_HISTORICO:,}  {ext.estrategia:<17} ({reps} rep.)...", end="", flush=True)
        t_medido, _, resultados[ext.estrategia] = medir_tiempo(
            ESTRATEGIAS[ext.estrategia], excesos, reps
        )
        print(f" {t_medido:.4f} s")
        validaciones.append(
            Validacion(
                estrategia=ext.estrategia,
                n=LOTES_HISTORICO,
                tiempo_predicho_s=ext.tiempo_laboratorio_s,
                tiempo_medido_s=t_medido,
                error_relativo=(t_medido - ext.tiempo_laboratorio_s) / t_medido,
            )
        )
    verificar_equivalencia(resultados, LOTES_HISTORICO)
    return validaciones


# ---------------------------------------------------------------------------
# Persistencia de resultados
# ---------------------------------------------------------------------------

def guardar_csv(filas: Sequence[object], ruta: str) -> None:
    """Guarda una lista de dataclasses en un archivo CSV.

    Args:
        filas: Instancias de una misma dataclass.
        ruta: Ruta del archivo de salida.
    """
    if not filas:
        return
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    registros = [asdict(fila) for fila in filas]  # type: ignore[call-overload]
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(registros[0].keys()))
        escritor.writeheader()
        escritor.writerows(registros)


def guardar_entorno(ruta: str, validado: bool) -> None:
    """Registra el entorno y los parámetros con que se obtuvieron los datos.

    Los tiempos dependen de la máquina, así que se deja constancia de ella para
    que la reproducción se pueda comparar.

    Args:
        ruta: Ruta del archivo JSON de salida.
        validado: Si se ejecutó la validación con n = 33.000.
    """
    entorno = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "implementacion": platform.python_implementation(),
        "sistema": platform.platform(),
        "procesador": platform.processor(),
        "parametros": {
            "tamanos": TAMANOS_EXPERIMENTO,
            "semilla_base": SEMILLA_BASE,
            "potencia_servidor_kw": POTENCIA_SERVIDOR_KW,
            "num_laboratorios": NUM_LABORATORIOS,
            "lotes_historico": LOTES_HISTORICO,
            "corridas_por_anio": CORRIDAS_POR_ANIO,
            "validacion_volumen_real": validado,
        },
    }
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(entorno, archivo, indent=2, ensure_ascii=False)


def leer_mediciones_csv(ruta: str) -> List[Medicion]:
    """Carga mediciones guardadas previamente (para regenerar gráficas sin medir).

    Args:
        ruta: Ruta de mediciones.csv.

    Returns:
        Lista de mediciones.
    """
    with open(ruta, encoding="utf-8") as archivo:
        return [
            Medicion(
                estrategia=f["estrategia"],
                n=int(f["n"]),
                repeticiones=int(f["repeticiones"]),
                tiempo_reloj_s=float(f["tiempo_reloj_s"]),
                tiempo_cpu_s=float(f["tiempo_cpu_s"]),
                memoria_pico_kib=float(f["memoria_pico_kib"]),
                energia_kwh=float(f["energia_kwh"]),
                indice_inicio=int(f["indice_inicio"]),
                indice_fin=int(f["indice_fin"]),
                exceso_acumulado=float(f["exceso_acumulado"]),
            )
            for f in csv.DictReader(archivo)
        ]


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


def imprimir_tabla_extrapolacion(extrapolaciones: Sequence[Extrapolacion]) -> None:
    """Imprime la extrapolación al volumen real y la proyección anual.

    Args:
        extrapolaciones: Resultado de extrapolar_volumen_real.
    """
    print(
        f"Volumen real: {NUM_LABORATORIOS} laboratorios x {LOTES_HISTORICO:,} lotes | "
        f"{CORRIDAS_POR_ANIO} corridas/anio"
    )
    encabezado = (
        f"{'Estrategia':<17} {'Modelo':>9} {'R^2':>7} {'1 lab (s)':>11} "
        f"{'290 labs (h)':>13} {'kWh/corrida':>12} {'kWh/anio':>11} {'Ahorro %':>9}"
    )
    print(encabezado)
    print("-" * len(encabezado))
    for e in extrapolaciones:
        print(
            f"{e.estrategia:<17} {e.modelo:>9} {e.r2:>7.4f} {e.tiempo_laboratorio_s:>11.3f} "
            f"{e.tiempo_corrida_h:>13.4f} {e.energia_corrida_kwh:>12.4e} "
            f"{e.energia_anual_kwh:>11.4f} {e.ahorro_porcentual:>9.3f}"
        )


def imprimir_tabla_validacion(validaciones: Sequence[Validacion]) -> None:
    """Imprime el contraste entre el tiempo extrapolado y el medido en n = 33.000.

    Args:
        validaciones: Resultado de validar_volumen_real.
    """
    print(f"{'Estrategia':<17} {'Predicho (s)':>13} {'Medido (s)':>12} {'Error':>8}")
    for v in validaciones:
        print(
            f"{v.estrategia:<17} {v.tiempo_predicho_s:>13.4f} "
            f"{v.tiempo_medido_s:>12.4f} {100 * v.error_relativo:>7.2f}%"
        )


def leer_argumentos() -> argparse.Namespace:
    """Lee las opciones de línea de comandos.

    Returns:
        Argumentos con el indicador validar_volumen_real.
    """
    parser = argparse.ArgumentParser(
        description="Mediciones empíricas y consumo eléctrico de la Operación 4."
    )
    parser.add_argument(
        "--validar-volumen-real",
        action="store_true",
        help="Mide además una corrida con n = 33.000 para validar la extrapolación.",
    )
    return parser.parse_args()


def ejecutar_experimentos(validar: bool = False) -> List[Medicion]:
    """Punto de entrada: mide, extrapola, imprime y guarda los resultados.

    Args:
        validar: Si se mide además una corrida con n = 33.000.

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
    print("\n[OK] Las tres estrategias reportan el mismo exceso maximo en todos los tamanos.\n")

    extrapolaciones = extrapolar_volumen_real(mediciones)
    imprimir_tabla_extrapolacion(extrapolaciones)

    validaciones: Optional[List[Validacion]] = None
    if validar:
        print(f"\nValidando la extrapolacion con n = {LOTES_HISTORICO:,}...")
        validaciones = validar_volumen_real(extrapolaciones)
        imprimir_tabla_validacion(validaciones)

    guardar_csv(mediciones, os.path.join(DIRECTORIO_EXPERIMENTOS, "mediciones.csv"))
    guardar_csv(extrapolaciones, os.path.join(DIRECTORIO_EXPERIMENTOS, "extrapolacion.csv"))
    if validaciones:
        guardar_csv(validaciones, os.path.join(DIRECTORIO_EXPERIMENTOS, "validacion_33000.csv"))
    guardar_entorno(os.path.join(DIRECTORIO_EXPERIMENTOS, "entorno.json"), validar)
    print(f"\n[OK] Resultados guardados en {os.path.relpath(DIRECTORIO_EXPERIMENTOS, RAIZ_REPOSITORIO)}")
    return mediciones


if __name__ == "__main__":
    argumentos = leer_argumentos()
    ejecutar_experimentos(validar=argumentos.validar_volumen_real)
