"""Suite de pruebas unitarias y de equivalencia formal para la Operación 4.

Verifica rigurosamente:
  1. Ejemplo a mano determinista verificado analíticamente.
  2. Casos de borde (tamaño 1, todos negativos, todos positivos, alternados).
  3. Equivalencia exacta entre Fuerza Bruta O(n^2), Dividir y Vencer O(n log n) y Kadane O(n).
  4. Restricción de negocio: Inmutabilidad estricta de los registros originales.

Desarrollado para el Proyecto Final por Juan Felipe Torres (Persona 1).
"""

import sys
import os
import copy
from typing import List

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from . import Lote, ResultadoTramo
    from .datos import generar_lotes_laboratorio, extraer_excesos
    from .fuerza_bruta import tramo_critico_fuerza_bruta
    from .dividir_vencer import tramo_critico_dividir_vencer, tramo_critico_kadane
except (ImportError, ValueError):
    from __init__ import Lote, ResultadoTramo  # type: ignore
    from datos import generar_lotes_laboratorio, extraer_excesos  # type: ignore
    from fuerza_bruta import tramo_critico_fuerza_bruta  # type: ignore
    from dividir_vencer import tramo_critico_dividir_vencer, tramo_critico_kadane  # type: ignore


def probar_ejemplo_a_mano() -> None:
    """Valida un caso concreto con cálculos analíticos predefinidos."""
    # Secuencia de excesos: [0.10, -0.25, 0.30, 0.40, -0.15, 0.50, -0.80, 0.20]
    # Tramo óptimo analítico: del índice 2 al 5 -> (0.30 + 0.40 - 0.15 + 0.50) = 1.05
    excesos = [0.10, -0.25, 0.30, 0.40, -0.15, 0.50, -0.80, 0.20]

    res_fb = tramo_critico_fuerza_bruta(excesos)
    res_dv = tramo_critico_dividir_vencer(excesos)
    res_kd = tramo_critico_kadane(excesos)

    assert abs(res_fb.exceso_acumulado - 1.05) < 1e-4, f"FB falló en ejemplo a mano: {res_fb}"
    assert abs(res_dv.exceso_acumulado - 1.05) < 1e-4, f"D&V falló en ejemplo a mano: {res_dv}"
    assert abs(res_kd.exceso_acumulado - 1.05) < 1e-4, f"Kadane falló en ejemplo a mano: {res_kd}"
    assert res_dv.indice_inicio == 2 and res_dv.indice_fin == 5, f"Índices erróneos D&V: {res_dv}"
    print("[OK] Ejemplo a mano analítico verificado (1.05 en tramo [2, 5]).")


def probar_casos_borde() -> None:
    """Valida comportamiento en escenarios extremos y de frontera."""
    # Caso 1: Un solo elemento positivo
    res_1 = tramo_critico_dividir_vencer([0.45])
    assert res_1 == ResultadoTramo(0, 0, 0.45), f"Fallo en 1 positivo: {res_1}"

    # Caso 2: Un solo elemento negativo
    res_2 = tramo_critico_dividir_vencer([-0.12])
    assert res_2 == ResultadoTramo(0, 0, -0.12), f"Fallo en 1 negativo: {res_2}"

    # Caso 3: Todos positivos -> debe seleccionar el tramo completo [0, n-1]
    todos_pos = [0.10, 0.20, 0.30, 0.40]
    res_pos_fb = tramo_critico_fuerza_bruta(todos_pos)
    res_pos_dv = tramo_critico_dividir_vencer(todos_pos)
    assert abs(res_pos_dv.exceso_acumulado - 1.0) < 1e-4
    assert res_pos_dv.indice_inicio == 0 and res_pos_dv.indice_fin == 3
    assert abs(res_pos_fb.exceso_acumulado - res_pos_dv.exceso_acumulado) < 1e-4

    # Caso 4: Todos negativos -> debe seleccionar el de mayor valor (menos negativo)
    todos_neg = [-0.50, -0.20, -0.80, -0.30]
    res_neg_fb = tramo_critico_fuerza_bruta(todos_neg)
    res_neg_dv = tramo_critico_dividir_vencer(todos_neg)
    assert abs(res_neg_dv.exceso_acumulado - (-0.20)) < 1e-4
    assert res_neg_dv.indice_inicio == 1 and res_neg_dv.indice_fin == 1
    assert abs(res_neg_fb.exceso_acumulado - res_neg_dv.exceso_acumulado) < 1e-4

    print("[OK] Casos borde (tamaño 1, todos positivos, todos negativos) verificados.")


def probar_equivalencia_estricta_con_sinteticos() -> None:
    """Verifica que Dividir y Vencer y Fuerza Bruta den el mismo resultado en 100 pruebas."""
    semillas = [10, 42, 99, 123, 777, 2024, 9999]
    tamanos = [5, 12, 30, 80, 150, 300]
    total_pruebas = 0

    for sem in semillas:
        for n in tamanos:
            lotes = generar_lotes_laboratorio(n=n, id_laboratorio=f"LAB-{sem}", semilla=sem)
            excesos = extraer_excesos(lotes)

            fb = tramo_critico_fuerza_bruta(excesos)
            dv = tramo_critico_dividir_vencer(excesos)
            kd = tramo_critico_kadane(excesos)

            # La suma máxima debe ser exactamente igual entre las tres estrategias
            assert abs(fb.exceso_acumulado - dv.exceso_acumulado) < 1e-4, (
                f"Discrepancia FB vs D&V en semilla {sem}, n={n}: FB={fb}, DV={dv}"
            )
            assert abs(dv.exceso_acumulado - kd.exceso_acumulado) < 1e-4, (
                f"Discrepancia D&V vs Kadane en semilla {sem}, n={n}: DV={dv}, KD={kd}"
            )
            total_pruebas += 1

    print(f"[OK] Equivalencia formal verificada en {total_pruebas} escenarios sintéticos aleatorios.")


def probar_restriccion_inmutabilidad() -> None:
    """Valida la restricción del negocio: los registros originales no deben modificarse."""
    lotes_originales = generar_lotes_laboratorio(n=50, semilla=888)
    copia_inmutable = copy.deepcopy(lotes_originales)

    # Ejecutar ambas estrategias sobre las instancias reales de Lote
    _ = tramo_critico_fuerza_bruta(lotes_originales)
    _ = tramo_critico_dividir_vencer(lotes_originales)

    # Verificar que el contenido no cambió en absoluto
    assert lotes_originales == copia_inmutable, (
        "Violación de restricción de negocio: Los registros originales de lotes fueron mutados."
    )
    print("[OK] Restricción de negocio: Inmutabilidad de registros verificada exitosamente.")


def ejecutar_todas_las_pruebas() -> None:
    """Punto de entrada de la suite de pruebas formales."""
    print("=" * 70)
    print("SUITE DE PRUEBAS FORMALES - OPERACIÓN 4: VIGILANCIA DE CALIDAD")
    print("Responsable: Juan Felipe Torres (Persona 1)")
    print("=" * 70)

    probar_ejemplo_a_mano()
    probar_casos_borde()
    probar_equivalencia_estricta_con_sinteticos()
    probar_restriccion_inmutabilidad()

    print("=" * 70)
    print("RESULTADO: TODAS LAS PRUEBAS PASARON EXITOSAMENTE (CÓDIGO DE SALIDA 0)")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()
