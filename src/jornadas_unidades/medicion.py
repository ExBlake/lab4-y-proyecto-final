"""Medición experimental y generación de gráficas de desempeño (Caso 2).

Compara experimentalmente el tiempo de ejecución y el número de operaciones
elementales de la estrategia voraz, la solución exhaustiva y la regla actual (FCFS),
generando las gráficas técnicas requeridas para el informe.

Módulo de evaluación empírica desarrollado por el Grupo 8.
"""

import os
import sys
import time
import math
from typing import List, Dict, Tuple

# Asegurar importación de módulos hermanos
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

# Configurar backend no interactivo para evitar errores de GUI/Display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from estrategia import (
    Jornada,
    seleccionar_jornadas,
    seleccionar_jornadas_con_conteo,
    hay_cruce
)
from exhaustivo import (
    seleccionar_exhaustivo,
    seleccionar_exhaustivo_con_conteo
)
from regla_actual import (
    asignar_por_llegada,
    asignar_por_llegada_con_conteo
)
from datos import generar_instancia_alta_densidad, generar_solicitudes


def medir_comparativo_pequeno(
    tamanos: List[int],
    repeticiones: int = 5,
    semilla_base: int = 42
) -> Dict[str, List[float]]:
    """Mide tiempo y operaciones para tamaños pequeños donde corre exhaustivo.

    Args:
        tamanos: lista de tamaños n a evaluar.
        repeticiones: repeticiones por cada tamaño para promediar ruido.
        semilla_base: semilla inicial para reproducibilidad.

    Returns:
        Diccionario con series de tiempos y operaciones por método.
    """
    resultados: Dict[str, List[float]] = {
        "tamanos": tamanos,
        "tiempo_voraz": [],
        "tiempo_exhaustivo": [],
        "tiempo_actual": [],
        "ops_voraz": [],
        "ops_exhaustivo": [],
        "ops_actual": []
    }

    print("Iniciando medición comparativa para instancias pequeñas...")
    for n in tamanos:
        t_voraz_acc = 0.0
        t_exh_acc = 0.0
        t_act_acc = 0.0

        ops_voraz_val = 0
        ops_exh_val = 0
        ops_act_val = 0

        for r in range(repeticiones):
            semilla = semilla_base + (n * 100) + r
            instancia = generar_instancia_alta_densidad(n=n, semilla=semilla, ventana_minutos=1440)

            # 1. Medir Estrategia Voraz
            t0 = time.perf_counter()
            sol_voraz = seleccionar_jornadas(instancia)
            t1 = time.perf_counter()
            t_voraz_acc += (t1 - t0)

            # 2. Medir Solución Exhaustiva
            t0 = time.perf_counter()
            sol_exh = seleccionar_exhaustivo(instancia)
            t1 = time.perf_counter()
            t_exh_acc += (t1 - t0)

            # 3. Medir Regla Actual
            t0 = time.perf_counter()
            sol_act = asignar_por_llegada(instancia)
            t1 = time.perf_counter()
            t_act_acc += (t1 - t0)

            # Verificación en línea de equivalencia de valor óptimo
            assert len(sol_voraz) == len(sol_exh), (
                f"Error: Voraz ({len(sol_voraz)}) != Exhaustivo ({len(sol_exh)}) en n={n}"
            )
            assert not hay_cruce(sol_voraz), f"Cruces en voraz para n={n}"

            # Contar operaciones elementales en la última repetición
            if r == repeticiones - 1:
                _, ops_voraz_val = seleccionar_jornadas_con_conteo(instancia)
                _, ops_exh_val = seleccionar_exhaustivo_con_conteo(instancia)
                _, ops_act_val = asignar_por_llegada_con_conteo(instancia)

        t_voraz_med = t_voraz_acc / repeticiones
        t_exh_med = t_exh_acc / repeticiones
        t_act_med = t_act_acc / repeticiones

        resultados["tiempo_voraz"].append(t_voraz_med)
        resultados["tiempo_exhaustivo"].append(t_exh_med)
        resultados["tiempo_actual"].append(t_act_med)
        resultados["ops_voraz"].append(ops_voraz_val)
        resultados["ops_exhaustivo"].append(ops_exh_val)
        resultados["ops_actual"].append(ops_act_val)

        print(
            f"  n={n:2d} | Voraz: {t_voraz_med * 1000:7.4f} ms ({ops_voraz_val:5d} ops) | "
            f"Exh: {t_exh_med * 1000:9.4f} ms ({ops_exh_val:7d} ops) | "
            f"Actual: {t_act_med * 1000:7.4f} ms ({ops_act_val:4d} ops)"
        )

    return resultados


def medir_gran_escala(
    tamanos_escala: List[int],
    repeticiones: int = 10,
    semilla_base: int = 777
) -> Dict[str, List[float]]:
    """Mide la estrategia voraz y regla actual en el rango operativo real y extendido.

    Args:
        tamanos_escala: tamaños grandes hasta miles de solicitudes.
        repeticiones: repeticiones para promediar.
        semilla_base: semilla de datos.

    Returns:
        Diccionario con métricas de gran escala.
    """
    resultados: Dict[str, List[float]] = {
        "tamanos": tamanos_escala,
        "tiempo_voraz": [],
        "tiempo_actual": [],
        "ops_voraz": [],
        "ops_actual": []
    }

    print("\nIniciando medición a gran escala (hasta 5,000 solicitudes)...")
    for n in tamanos_escala:
        t_voraz_acc = 0.0
        t_act_acc = 0.0
        ops_voraz_val = 0
        ops_act_val = 0

        for r in range(repeticiones):
            semilla = semilla_base + (n * 100) + r
            instancia = generar_solicitudes(n=n, semilla=semilla)

            t0 = time.perf_counter()
            sol_v = seleccionar_jornadas(instancia)
            t1 = time.perf_counter()
            t_voraz_acc += (t1 - t0)

            t0 = time.perf_counter()
            sol_a = asignar_por_llegada(instancia)
            t1 = time.perf_counter()
            t_act_acc += (t1 - t0)

            if r == repeticiones - 1:
                _, ops_voraz_val = seleccionar_jornadas_con_conteo(instancia)
                _, ops_act_val = asignar_por_llegada_con_conteo(instancia)

        t_voraz_med = t_voraz_acc / repeticiones
        t_act_med = t_act_acc / repeticiones

        resultados["tiempo_voraz"].append(t_voraz_med)
        resultados["tiempo_actual"].append(t_act_med)
        resultados["ops_voraz"].append(ops_voraz_val)
        resultados["ops_actual"].append(ops_act_val)

        print(
            f"  n={n:5d} | Voraz: {t_voraz_med * 1000:8.4f} ms ({ops_voraz_val:8d} ops) | "
            f"Actual: {t_act_med * 1000:8.4f} ms ({ops_act_val:8d} ops)"
        )

    return resultados


def generar_graficas(
    res_peq: Dict[str, List[float]],
    res_gran: Dict[str, List[float]],
    directorio_salida: str
) -> None:
    """Genera y guarda las gráficas de tiempo vs n y operaciones vs n.

    Args:
        res_peq: resultados del rango exhaustivo.
        res_gran: resultados de gran escala.
        directorio_salida: carpeta donde almacenar las figuras PNG.
    """
    os.makedirs(directorio_salida, exist_ok=True)

    ruta_tiempo = os.path.join(directorio_salida, "tiempo_vs_n.png")
    ruta_ops = os.path.join(directorio_salida, "operaciones_vs_n.png")

    # -------------------------------------------------------------
    # 1. Gráfica tiempo_vs_n.png
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: Rango comparativo con solución exhaustiva
    ax1.plot(
        res_peq["tamanos"],
        [t * 1000 for t in res_peq["tiempo_exhaustivo"]],
        marker="o", color="#d62728", linewidth=2.2, label="Exhaustivo: $\\Theta(n \\cdot 2^n)$"
    )
    ax1.plot(
        res_peq["tamanos"],
        [t * 1000 for t in res_peq["tiempo_voraz"]],
        marker="s", color="#1f77b4", linewidth=2.0, label="Estrategia Voraz: $\\Theta(n \\log n)$"
    )
    ax1.plot(
        res_peq["tamanos"],
        [t * 1000 for t in res_peq["tiempo_actual"]],
        marker="^", color="#2ca02c", linewidth=1.8, linestyle="--", label="Regla Actual (FCFS): $O(n^2)$"
    )
    ax1.set_title("Contraste de Tiempo en Rango Exhaustivo ($n \\leq 16$)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Tamaño de la entrada $n$ (número de solicitudes)", fontsize=10)
    ax1.set_ylabel("Tiempo medio de ejecución (milisegundos, ms)", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)

    # Panel 2: Escala real y extendida (Voraz vs Regla Actual)
    ax2.plot(
        res_gran["tamanos"],
        [t * 1000 for t in res_gran["tiempo_voraz"]],
        marker="s", color="#1f77b4", linewidth=2.2, label="Estrategia Voraz $\\Theta(n \\log n)$"
    )
    ax2.plot(
        res_gran["tamanos"],
        [t * 1000 for t in res_gran["tiempo_actual"]],
        marker="^", color="#2ca02c", linewidth=2.0, linestyle="--", label="Regla Actual (FCFS) $O(n^2)$"
    )
    # Sombrear la zona del volumen real del caso (40 a 120 solicitudes/mes)
    ax2.axvspan(40, 120, color="#ffbb78", alpha=0.35, label="Volumen real del caso (40–120 solicitudes)")
    ax2.set_title("Escala Operativa Real y Extrapolación ($n \\leq 5000$)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Tamaño de la entrada $n$ (número de solicitudes)", fontsize=10)
    ax2.set_ylabel("Tiempo medio de ejecución (milisegundos, ms)", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=9)

    plt.suptitle(
        "Caso 2 — Plataforma Pulso: Tiempo de Ejecución vs. Tamaño de Entrada ($n$)",
        fontsize=13, fontweight="bold", y=0.98
    )
    plt.tight_layout()
    plt.savefig(ruta_tiempo, dpi=300)
    plt.close()
    print(f"Gráfica guardada exitosamente en: {ruta_tiempo}")

    # -------------------------------------------------------------
    # 2. Gráfica operaciones_vs_n.png
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: Operaciones en rango exhaustivo (escala logarítmica para visibilidad)
    ax1.plot(
        res_peq["tamanos"],
        res_peq["ops_exhaustivo"],
        marker="o", color="#d62728", linewidth=2.2, label="Exhaustivo: $\\Theta(n \\cdot 2^n)$ combinaciones"
    )
    ax1.plot(
        res_peq["tamanos"],
        res_peq["ops_voraz"],
        marker="s", color="#1f77b4", linewidth=2.0, label="Voraz: comparaciones de orden y selección"
    )
    ax1.plot(
        res_peq["tamanos"],
        res_peq["ops_actual"],
        marker="^", color="#2ca02c", linewidth=1.8, linestyle="--", label="Regla Actual: comparaciones secuenciales"
    )
    ax1.set_yscale("log")
    ax1.set_title("Operaciones Elementales en Rango Exhaustivo ($n \\leq 16$)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Tamaño de la entrada $n$ (número de solicitudes)", fontsize=10)
    ax1.set_ylabel("Operaciones elementales (escala logarítmica)", fontsize=10)
    ax1.grid(True, which="both", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)

    # Panel 2: Operaciones a gran escala
    ax2.plot(
        res_gran["tamanos"],
        res_gran["ops_voraz"],
        marker="s", color="#1f77b4", linewidth=2.2, label="Estrategia Voraz $\\Theta(n \\log n)$"
    )
    ax2.plot(
        res_gran["tamanos"],
        res_gran["ops_actual"],
        marker="^", color="#2ca02c", linewidth=2.0, linestyle="--", label="Regla Actual (FCFS) $O(n^2)$"
    )
    ax2.axvspan(40, 120, color="#ffbb78", alpha=0.35, label="Volumen real del caso (40–120 solicitudes)")
    ax2.set_title("Operaciones Elementales a Gran Escala ($n \\leq 5000$)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Tamaño de la entrada $n$ (número de solicitudes)", fontsize=10)
    ax2.set_ylabel("Operaciones elementales ejecutadas", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=9)

    plt.suptitle(
        "Caso 2 — Plataforma Pulso: Operaciones Elementales vs. Tamaño de Entrada ($n$)",
        fontsize=13, fontweight="bold", y=0.98
    )
    plt.tight_layout()
    plt.savefig(ruta_ops, dpi=300)
    plt.close()
    print(f"Gráfica guardada exitosamente en: {ruta_ops}")


def ejecutar_experimentos() -> None:
    """Función principal que coordina mediciones, validaciones y graficación."""
    # 6 tamaños para comparativa directa con exhaustivo (incluye n=4->8 y n=8->16)
    tamanos_exhaustivo = [4, 6, 8, 10, 12, 16]

    # Tamaños a gran escala para sostener la extrapolación (incluye volumen real 40 y 120)
    tamanos_escala = [20, 40, 80, 120, 240, 480, 1000, 2000, 5000]

    # Medición
    res_peq = medir_comparativo_pequeno(tamanos=tamanos_exhaustivo, repeticiones=5, semilla_base=1234)
    res_gran = medir_gran_escala(tamanos_escala=tamanos_escala, repeticiones=10, semilla_base=5678)

    # Directorio de salida: graficas/jornadas_unidades/
    directorio_graficas = os.path.abspath(
        os.path.join(directorio_actual, "..", "..", "graficas", "jornadas_unidades")
    )
    generar_graficas(res_peq, res_gran, directorio_graficas)
    print("\nProceso de medición y generación de gráficas finalizado exitosamente.")


if __name__ == "__main__":
    ejecutar_experimentos()

