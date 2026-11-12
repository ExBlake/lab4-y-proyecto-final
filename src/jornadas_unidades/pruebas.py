"""Batería de pruebas formales con assert para el Caso 2 (Plataforma Pulso).

Verifica exhaustivamente:
1. Casos límite (lista vacía, 1 elemento, sin cruces, con cruce total).
2. Ejemplo resuelto a mano paso a paso en la Parte 1.
3. Al menos 20 instancias aleatorias pequeñas contrastadas contra la solución exhaustiva.
4. Restricción del negocio: ninguna programación de unidad móvil tiene jornadas que se crucen.
5. Contraejemplo demostrado donde la regla actual falla frente a la estrategia voraz.

Validación técnica desarrollada por el equipo de consultoría (Grupo 8).
"""

import sys
import os

# Asegurar importación de módulos hermanos
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

from estrategia import Jornada, seleccionar_jornadas, hay_cruce
from exhaustivo import seleccionar_exhaustivo
from regla_actual import asignar_por_llegada
from datos import generar_solicitudes, generar_instancia_alta_densidad


def test_casos_limite() -> None:
    """Verifica el comportamiento en fronteras: vacíos, únicos, disyuntos y colapsados."""
    # 1. Entrada vacía
    assert seleccionar_jornadas([]) == [], "Fallo en entrada vacía para estrategia"
    assert seleccionar_exhaustivo([]) == [], "Fallo en entrada vacía para exhaustivo"
    assert asignar_por_llegada([]) == [], "Fallo en entrada vacía para regla actual"

    # 2. Un solo elemento
    unico: list[Jornada] = [(60, 120, 5)]
    assert seleccionar_jornadas(unico) == [(60, 120, 5)], "Fallo en lista de un solo elemento"
    assert seleccionar_exhaustivo(unico) == [(60, 120, 5)], "Fallo exhaustivo en elemento único"
    assert asignar_por_llegada(unico) == [(60, 120, 5)], "Fallo regla actual en elemento único"

    # 3. Caso en que nada se cruza (todas son mutuamente compatibles)
    sin_cruces: list[Jornada] = [
        (10, 50, 15),
        (50, 100, 20),
        (120, 180, 30),
        (200, 260, 25),
        (300, 400, 40)
    ]
    sol_sin_cruces = seleccionar_jornadas(sin_cruces)
    assert len(sol_sin_cruces) == 5, f"Esperadas 5 jornadas sin cruces, se obtuvieron {len(sol_sin_cruces)}"
    assert not hay_cruce(sol_sin_cruces), "Se detectó cruce espurio en conjunto disyunto"

    # 4. Caso en que todo se cruza (todas comparten un instante común)
    # Todas las solicitudes abarcan el minuto 200
    todo_se_cruza: list[Jornada] = [
        (100, 250, 10),
        (150, 220, 25),
        (180, 300, 30),
        (50, 400, 50),
        (190, 210, 8)
    ]
    sol_todo_se_cruza = seleccionar_jornadas(todo_se_cruza)
    assert len(sol_todo_se_cruza) == 1, (
        f"Esperada exactamente 1 jornada para cruce total, se obtuvieron {len(sol_todo_se_cruza)}"
    )
    # Debe haber elegido la de menor fin (190, 210, 8)
    assert sol_todo_se_cruza == [(190, 210, 8)], "Estrategia no eligió la jornada de fin más temprano"


def test_ejemplo_pequeno_a_mano() -> None:
    """Verifica el ejemplo pequeño de 6 elementos resuelto paso a paso en la Parte 1."""
    # Instancia documentada en el informe técnico
    solicitudes: list[Jornada] = [
        (60, 240, 25),   # R1: fin 240
        (180, 360, 30),  # R2: fin 360 (se cruza con R1)
        (240, 420, 20),  # R3: fin 420 (inicia justo al fin de R1, compatible)
        (300, 600, 45),  # R4: fin 600 (se cruza con R3 y R5)
        (420, 540, 15),  # R5: fin 540 (inicia justo al fin de R3, compatible)
        (540, 720, 35),  # R6: fin 720 (inicia justo al fin de R5, compatible)
    ]

    resultado = seleccionar_jornadas(solicitudes)
    esperado: list[Jornada] = [
        (60, 240, 25),
        (240, 420, 20),
        (420, 540, 15),
        (540, 720, 35)
    ]

    assert resultado == esperado, f"Resultado {resultado} no coincide con el esperado {esperado}"
    assert len(resultado) == 4, f"Se esperaban 4 jornadas óptimas, se obtuvieron {len(resultado)}"
    assert not hay_cruce(resultado), "El resultado óptimo calculado tiene cruces"

    # Verificar que el oráculo exhaustivo da exactamente el mismo valor (4)
    resultado_exh = seleccionar_exhaustivo(solicitudes)
    assert len(resultado_exh) == 4, "Exhaustivo difiere del valor calculado a mano"


def test_veinte_instancias_aleatorias_coincidencia() -> None:
    """Verifica que la estrategia voraz coincide exactamente con exhaustivo en >= 20 instancias."""
    instancias_probadas = 25
    for i in range(instancias_probadas):
        semilla = 1000 + i
        # Instancias de alta congestión con n entre 6 y 13 para verificar exhaustivo
        n = 6 + (i % 8)
        instancia = generar_instancia_alta_densidad(n=n, semilla=semilla, ventana_minutos=1440)

        opt_voraz = seleccionar_jornadas(instancia)
        opt_exh = seleccionar_exhaustivo(instancia)

        # Mismo valor óptimo (cardinalidad máxima de jornadas asignadas)
        assert len(opt_voraz) == len(opt_exh), (
            f"Discrepancia en instancia {i} (n={n}, semilla={semilla}): "
            f"Voraz obtuvo {len(opt_voraz)} jornadas, Exhaustivo obtuvo {len(opt_exh)}"
        )

        # Ninguna solución debe tener cruces
        assert not hay_cruce(opt_voraz), f"Voraz produjo un cruce en instancia {i}"
        assert not hay_cruce(opt_exh), f"Exhaustivo produjo un cruce en instancia {i}"

        # Resultado de voraz debe estar estrictamente ordenado por hora de inicio
        for k in range(len(opt_voraz) - 1):
            assert opt_voraz[k][0] <= opt_voraz[k + 1][0], "Salida de voraz no ordenada por inicio"


def test_restriccion_negocio_sin_cruces() -> None:
    """Valida la restricción estricta de negocio: ninguna unidad móvil tiene dos jornadas que se crucen."""
    # Probar 30 instancias de tamaños representativos del volumen del caso (40 a 120 solicitudes)
    for i in range(30):
        semilla = 5000 + i
        n = 40 + (i * 3)  # tamaños desde 40 hasta 127
        instancia = generar_solicitudes(n=n, semilla=semilla)
        solucion = seleccionar_jornadas(instancia)

        assert not hay_cruce(solucion), (
            f"Violación de la restricción de negocio en n={n}: la programación contiene cruces"
        )
        # Verificar formalmente que para todo par sucesivo, inicio_(k+1) >= fin_k
        for k in range(len(solucion) - 1):
            assert solucion[k + 1][0] >= solucion[k][1], (
                f"Traslape temporal entre jornada {solucion[k]} y {solucion[k+1]}"
            )


def test_contraejemplo_regla_actual() -> None:
    """Comprueba la instancia formal donde la regla actual falla drásticamente."""
    # Contraejemplo exacto de la Parte 1
    # Llega una solicitud extensa que bloquea a tres solicitudes más cortas y de mayor beneficio
    solicitudes: list[Jornada] = [
        (60, 480, 20),   # Solicitud 1 (llega primero, abarca 7 horas)
        (60, 180, 25),   # Solicitud 2 (2 horas)
        (180, 300, 30),  # Solicitud 3 (2 horas)
        (300, 420, 28)   # Solicitud 4 (2 horas)
    ]

    resultado_actual = asignar_por_llegada(solicitudes)
    resultado_voraz = seleccionar_jornadas(solicitudes)

    # La regla actual solo acepta la primera y rechaza las demás
    assert len(resultado_actual) == 1, (
        f"Regla actual debió aceptar 1 sola jornada, aceptó {len(resultado_actual)}"
    )
    assert resultado_actual == [(60, 480, 20)], "Regla actual no aceptó la primera en llegar"

    # La estrategia voraz selecciona las 3 jornadas no solapadas
    assert len(resultado_voraz) == 3, (
        f"Estrategia debió seleccionar 3 jornadas, seleccionó {len(resultado_voraz)}"
    )
    assert resultado_voraz == [(60, 180, 25), (180, 300, 30), (300, 420, 28)]

    # Cuantificar la diferencia
    jornadas_ganadas = len(resultado_voraz) - len(resultado_actual)
    pacientes_actual = sum(j[2] for j in resultado_actual)
    pacientes_voraz = sum(j[2] for j in resultado_voraz)

    assert jornadas_ganadas == 2, f"Diferencia esperada de 2 jornadas, obtenida: {jornadas_ganadas}"
    assert pacientes_actual == 20, f"Pacientes atendidos por regla actual erróneo: {pacientes_actual}"
    assert pacientes_voraz == 83, f"Pacientes atendidos por voraz erróneo: {pacientes_voraz}"
    assert pacientes_voraz > pacientes_actual, "Estrategia voraz no superó a regla actual en pacientes"


def ejecutar_todas_las_pruebas() -> None:
    """Ejecuta toda la suite de pruebas unitarias y de integración."""
    print("Iniciando ejecución de pruebas formales...")
    test_casos_limite()
    print("  [OK] Casos límite verificados con éxito.")
    test_ejemplo_pequeno_a_mano()
    print("  [OK] Ejemplo resuelto a mano validado con éxito.")
    test_veinte_instancias_aleatorias_coincidencia()
    print("  [OK] 25 instancias aleatorias: coincidencia exacta con solución exhaustiva demostrada.")
    test_restriccion_negocio_sin_cruces()
    print("  [OK] Restricción de negocio (cero cruces) verificada en 30 escenarios de 40 a 127 solicitudes.")
    test_contraejemplo_regla_actual()
    print("  [OK] Contraejemplo contra la regla actual validado y cuantificado con éxito.")
    print("Todas las pruebas pasaron satisfactoriamente (100% de aserciones válidas).")


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()

