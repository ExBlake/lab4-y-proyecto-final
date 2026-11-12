"""Pruebas con assert de la operación 3: jornadas de las unidades móviles.

Ejecución desde la raíz del repositorio:
    python src/jornadas_unidades/pruebas.py
"""

from datos import generar_instancias_pequenas, generar_solicitudes
from estrategia import Jornada, hay_cruce, seleccionar_jornadas
from exhaustivo import seleccionar_exhaustivo
from regla_actual import asignar_por_llegada

# Ejemplo resuelto a mano en la Parte 1 (README): R1..R6.
EJEMPLO_MANUAL: list[Jornada] = [
    (60, 240, 25),    # R1
    (180, 360, 30),   # R2
    (240, 420, 20),   # R3
    (300, 600, 45),   # R4
    (420, 540, 15),   # R5
    (540, 720, 35),   # R6
]
RESULTADO_MANUAL: list[Jornada] = [
    (60, 240, 25),
    (240, 420, 20),
    (420, 540, 15),
    (540, 720, 35),
]

# Contraejemplo de la regla actual, en orden de llegada: llega primero una
# jornada larga (07:00 a 17:00) que bloquea tres jornadas cortas.
CONTRAEJEMPLO: list[Jornada] = [
    (420, 1020, 40),   # C1: 07:00-17:00, llega primero
    (420, 600, 30),    # C2: 07:00-10:00
    (600, 780, 25),    # C3: 10:00-13:00
    (780, 1020, 35),   # C4: 13:00-17:00
]

CANTIDAD_ALEATORIAS = 200
SEMILLA_PRUEBAS = 2026


def es_subconjunto(elegidas: list[Jornada], solicitudes: list[Jornada]) -> bool:
    """Indica si cada jornada elegida proviene de las solicitudes.

    Respeta las repeticiones: una solicitud duplicada solo puede elegirse
    tantas veces como aparece.

    Args:
        elegidas: jornadas devueltas por un algoritmo.
        solicitudes: solicitudes originales.

    Returns:
        True si elegidas es un submulticonjunto de solicitudes.
    """
    disponibles = list(solicitudes)
    for jornada in elegidas:
        if jornada not in disponibles:
            return False
        disponibles.remove(jornada)
    return True


def probar_hay_cruce() -> None:
    """Verifica la definición de cruce declarada en el README."""
    assert not hay_cruce([])
    assert not hay_cruce([(0, 60, 1)])
    assert hay_cruce([(0, 60, 1), (30, 90, 1)])
    assert hay_cruce([(0, 100, 1), (20, 40, 1)])  # una contiene a la otra
    assert hay_cruce([(0, 60, 1), (0, 60, 1)])    # idénticas
    # Tocarse en un extremo NO es cruce.
    assert not hay_cruce([(0, 60, 1), (60, 120, 1)])
    assert not hay_cruce([(60, 120, 1), (0, 60, 1)])
    # Cruce con una jornada que no es la inmediatamente anterior.
    assert hay_cruce([(0, 500, 1), (100, 200, 1), (300, 400, 1)])


def probar_casos_limite() -> None:
    """Entrada vacía, un elemento, nada se cruza y todo se cruza."""
    # Entrada vacía.
    assert seleccionar_jornadas([]) == []
    assert seleccionar_exhaustivo([]) == []
    assert asignar_por_llegada([]) == []

    # Un solo elemento.
    assert seleccionar_jornadas([(60, 120, 5)]) == [(60, 120, 5)]
    assert seleccionar_exhaustivo([(60, 120, 5)]) == [(60, 120, 5)]
    assert asignar_por_llegada([(60, 120, 5)]) == [(60, 120, 5)]

    # Nada se cruza: se aceptan todas, ordenadas por inicio.
    sin_cruces = [(300, 400, 3), (0, 100, 1), (100, 200, 2)]
    esperado = [(0, 100, 1), (100, 200, 2), (300, 400, 3)]
    assert seleccionar_jornadas(sin_cruces) == esperado
    assert seleccionar_exhaustivo(sin_cruces) == esperado
    assert sorted(asignar_por_llegada(sin_cruces)) == esperado

    # Todo se cruza: solo cabe una jornada; la voraz toma la de fin más
    # temprano.
    todas_cruzadas = [(0, 500, 10), (100, 300, 20), (200, 600, 30)]
    assert seleccionar_jornadas(todas_cruzadas) == [(100, 300, 20)]
    assert len(seleccionar_exhaustivo(todas_cruzadas)) == 1
    assert asignar_por_llegada(todas_cruzadas) == [(0, 500, 10)]

    # Solicitudes idénticas: se cruzan entre sí, solo una se atiende.
    assert seleccionar_jornadas([(0, 60, 5)] * 3) == [(0, 60, 5)]

    # Empate en la hora de fin: se prefiere la de más pacientes.
    assert seleccionar_jornadas([(0, 100, 5), (50, 100, 9)]) == [(50, 100, 9)]

    # Solicitudes inválidas se rechazan.
    for invalida in [(100, 100, 1), (200, 100, 1), (-5, 10, 1), (0, 10, -1)]:
        try:
            seleccionar_jornadas([invalida])
        except ValueError:
            pass
        else:
            raise AssertionError(f"Debió rechazarse {invalida}")


def probar_ejemplo_manual() -> None:
    """El ejemplo de la Parte 1 da R1, R3, R5, R6 y 95 pacientes."""
    elegidas = seleccionar_jornadas(EJEMPLO_MANUAL)
    assert elegidas == RESULTADO_MANUAL
    assert len(elegidas) == 4
    assert sum(j[2] for j in elegidas) == 95
    assert len(seleccionar_exhaustivo(EJEMPLO_MANUAL)) == 4


def probar_contra_exhaustivo() -> None:
    """La voraz y la exhaustiva obtienen el mismo óptimo en instancias
    aleatorias pequeñas generadas con semilla fija."""
    instancias = generar_instancias_pequenas(
        CANTIDAD_ALEATORIAS, n_minimo=1, n_maximo=12, semilla=SEMILLA_PRUEBAS
    )
    assert len(instancias) >= 20
    for solicitudes in instancias:
        voraz = seleccionar_jornadas(solicitudes)
        exacta = seleccionar_exhaustivo(solicitudes)
        llegada = asignar_por_llegada(solicitudes)
        assert len(voraz) == len(exacta), (solicitudes, voraz, exacta)
        # La regla actual nunca supera al óptimo.
        assert len(llegada) <= len(voraz)


def probar_restriccion_negocio() -> None:
    """Ninguna unidad queda con dos jornadas que se crucen.

    Se revisa con instancias pequeñas y con el volumen real del caso: 9
    subregiones con entre 40 y 120 solicitudes al mes cada una.
    """
    instancias = generar_instancias_pequenas(50, semilla=SEMILLA_PRUEBAS + 1)
    for subregion, n in enumerate([40, 55, 70, 80, 90, 100, 110, 115, 120]):
        instancias.append(generar_solicitudes(n, semilla=subregion))

    for solicitudes in instancias:
        for algoritmo in (seleccionar_jornadas, asignar_por_llegada):
            elegidas = algoritmo(solicitudes)
            assert not hay_cruce(elegidas)
            assert es_subconjunto(elegidas, solicitudes)
        # La salida de la estrategia queda ordenada por hora de inicio.
        elegidas = seleccionar_jornadas(solicitudes)
        assert elegidas == sorted(elegidas, key=lambda j: j[0])

    for solicitudes in instancias[:50]:
        elegidas = seleccionar_exhaustivo(solicitudes)
        assert not hay_cruce(elegidas)
        assert es_subconjunto(elegidas, solicitudes)


def probar_contraejemplo() -> None:
    """La regla por orden de llegada atiende 1 jornada; la voraz, 3."""
    llegada = asignar_por_llegada(CONTRAEJEMPLO)
    voraz = seleccionar_jornadas(CONTRAEJEMPLO)
    assert llegada == [(420, 1020, 40)]
    assert voraz == [(420, 600, 30), (600, 780, 25), (780, 1020, 35)]
    assert len(seleccionar_exhaustivo(CONTRAEJEMPLO)) == 3
    assert len(voraz) - len(llegada) == 2
    # Además deja sin atender a más pacientes: 40 frente a 90.
    assert sum(j[2] for j in llegada) == 40
    assert sum(j[2] for j in voraz) == 90


def main() -> None:
    """Ejecuta todas las pruebas e informa el resultado."""
    pruebas = [
        probar_hay_cruce,
        probar_casos_limite,
        probar_ejemplo_manual,
        probar_contra_exhaustivo,
        probar_restriccion_negocio,
        probar_contraejemplo,
    ]
    for prueba in pruebas:
        prueba()
        print(f"OK  {prueba.__name__}")
    print(f"Todas las pruebas pasaron ({len(pruebas)} grupos).")


if __name__ == "__main__":
    main()
