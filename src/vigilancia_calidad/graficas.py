"""Gráficas técnicas de la Operación 4 (Vigilancia de calidad).

Genera, a partir de los resultados guardados en experimentos/vigilancia_calidad/,
las figuras del informe en graficas/vigilancia_calidad/:

  - escalabilidad_tiempo.png: Fuerza bruta vs. Dividir y vencer (y Kadane),
    en escala lineal y log-log con la extrapolación a 33.000 lotes.
  - consumo_energetico_anual.png: kWh por año de cada estrategia y ahorro
    frente al proceso actual.
  - ajuste_teorico_complejidad.png: tiempos medidos contra el modelo teórico
    ajustado (n^2, n log n, n) y la razón t / f(n).

Uso (regenera las gráficas sin volver a medir):
    python src/vigilancia_calidad/graficas.py

Desarrollado para el Proyecto Final por Santiago Villada Arboleda (Persona 2).
"""

import csv
import os
import sys
from typing import Dict, List, Optional, Sequence

# Backend no interactivo: las figuras se guardan en disco sin abrir ventanas
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter

# Soporte para ejecución directa como script y como paquete
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

try:
    from .medicion import (
        DIRECTORIO_EXPERIMENTOS, DIVIDIR_VENCER, ESTRATEGIAS, FUERZA_BRUTA, KADANE,
        LOTES_HISTORICO, NOTACION_MODELO, NUM_LABORATORIOS, RAIZ_REPOSITORIO,
        Extrapolacion, Medicion, filtrar_estrategia, leer_mediciones_csv,
        predecir_tiempo,
    )
except (ImportError, ValueError):
    from medicion import (  # type: ignore
        DIRECTORIO_EXPERIMENTOS, DIVIDIR_VENCER, ESTRATEGIAS, FUERZA_BRUTA, KADANE,
        LOTES_HISTORICO, NOTACION_MODELO, NUM_LABORATORIOS, RAIZ_REPOSITORIO,
        Extrapolacion, Medicion, filtrar_estrategia, leer_mediciones_csv,
        predecir_tiempo,
    )


DIRECTORIO_GRAFICAS: str = os.path.join(RAIZ_REPOSITORIO, "graficas", "vigilancia_calidad")

# Paleta categórica de referencia (orden fijo, validada para daltonismo) y
# tintas de texto. Cada estrategia conserva su color en todas las figuras.
COLORES: Dict[str, str] = {
    DIVIDIR_VENCER: "#2a78d6",  # azul: estrategia propuesta
    FUERZA_BRUTA: "#eb6834",    # naranja: proceso actual
    KADANE: "#1baf7a",          # aqua: referencia lineal
}
TINTA_PRIMARIA: str = "#0b0b0b"
TINTA_SECUNDARIA: str = "#52514e"
TINTA_TENUE: str = "#8a8984"
SUPERFICIE: str = "#fcfcfb"
REJILLA: str = "#e6e5e0"

ORDEN_SERIES: List[str] = [FUERZA_BRUTA, DIVIDIR_VENCER, KADANE]
DPI: int = 200


# ---------------------------------------------------------------------------
# Lectura de resultados
# ---------------------------------------------------------------------------

def leer_extrapolacion_csv(ruta: str) -> Dict[str, Extrapolacion]:
    """Carga la extrapolación al volumen real guardada por medicion.py.

    Args:
        ruta: Ruta de extrapolacion.csv.

    Returns:
        Extrapolación indexada por nombre de estrategia.
    """
    with open(ruta, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    resultado: Dict[str, Extrapolacion] = {}
    for f in filas:
        valores = {k: (v if k in ("estrategia", "modelo") else float(v)) for k, v in f.items()}
        resultado[f["estrategia"]] = Extrapolacion(**valores)  # type: ignore[arg-type]
    return resultado


def leer_validacion_csv(ruta: str) -> Dict[str, float]:
    """Carga los tiempos medidos con n = 33.000, si la validación se ejecutó.

    Args:
        ruta: Ruta de validacion_33000.csv.

    Returns:
        Tiempo medido por estrategia (vacío si el archivo no existe).
    """
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as archivo:
        return {f["estrategia"]: float(f["tiempo_medido_s"]) for f in csv.DictReader(archivo)}


# ---------------------------------------------------------------------------
# Estilo común
# ---------------------------------------------------------------------------

def aplicar_estilo(eje: Axes, titulo: str, x: str, y: str) -> None:
    """Aplica el estilo común: rejilla y ejes recesivos, texto en tinta neutra.

    Args:
        eje: Eje de matplotlib.
        titulo: Título del panel.
        x: Etiqueta del eje x.
        y: Etiqueta del eje y.
    """
    eje.set_facecolor(SUPERFICIE)
    eje.set_title(titulo, loc="left", fontsize=11, color=TINTA_PRIMARIA, pad=10)
    eje.set_xlabel(x, fontsize=9, color=TINTA_SECUNDARIA)
    eje.set_ylabel(y, fontsize=9, color=TINTA_SECUNDARIA)
    eje.grid(True, which="major", color=REJILLA, linewidth=0.8)
    eje.set_axisbelow(True)
    eje.tick_params(colors=TINTA_SECUNDARIA, labelsize=8, length=0)
    for lado in ("top", "right"):
        eje.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        eje.spines[lado].set_color(REJILLA)


def formato_decimal(valor: float, decimales: int) -> str:
    """Formatea un número con coma decimal y punto de miles.

    Args:
        valor: Número a formatear.
        decimales: Cifras decimales.

    Returns:
        Texto del número, p. ej. 1.952,2.
    """
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formato_segundos(valor: float) -> str:
    """Formatea un tiempo en segundos con precisión según su magnitud.

    Args:
        valor: Tiempo en segundos.

    Returns:
        Texto con unidad, p. ej. 0,0101 s.
    """
    decimales = 1 if valor >= 10 else 2 if valor >= 0.1 else 3 if valor >= 0.01 else 4
    return f"{formato_decimal(valor, decimales)} s"


def formato_miles(valor: float, _: Optional[int] = None) -> str:
    """Formatea enteros con punto de miles (convención en español).

    Args:
        valor: Valor del eje.

    Returns:
        Texto del valor, p. ej. 33.000.
    """
    return f"{valor:,.0f}".replace(",", ".")


def guardar_figura(figura: plt.Figure, nombre: str) -> str:
    """Guarda la figura en graficas/vigilancia_calidad/ y la cierra.

    Args:
        figura: Figura de matplotlib.
        nombre: Nombre del archivo PNG.

    Returns:
        Ruta del archivo generado.
    """
    os.makedirs(DIRECTORIO_GRAFICAS, exist_ok=True)
    ruta = os.path.join(DIRECTORIO_GRAFICAS, nombre)
    figura.savefig(ruta, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(figura)
    return ruta


# ---------------------------------------------------------------------------
# Figura 1: escalabilidad del tiempo
# ---------------------------------------------------------------------------

def graficar_escalabilidad_tiempo(
    mediciones: Sequence[Medicion],
    extrapolacion: Dict[str, Extrapolacion],
    validacion: Dict[str, float],
) -> str:
    """Compara el tiempo de ejecución de las estrategias al crecer n.

    Panel izquierdo: escala lineal en el rango medido (se ve la parábola de la
    fuerza bruta frente a la curva casi plana de dividir y vencer). Panel
    derecho: escala log-log con la extrapolación hasta 33.000 lotes y, si
    existe, la medición real de validación.

    Args:
        mediciones: Mediciones del experimento.
        extrapolacion: Constantes ajustadas por estrategia.
        validacion: Tiempos medidos con n = 33.000 (puede estar vacío).

    Returns:
        Ruta del PNG generado.
    """
    figura, (eje_lin, eje_log) = plt.subplots(1, 2, figsize=(12, 4.8))

    for nombre in ORDEN_SERIES:
        puntos = filtrar_estrategia(mediciones, nombre)
        ns = [m.n for m in puntos]
        ts = [m.tiempo_reloj_s for m in puntos]
        color = COLORES[nombre]
        etiqueta = f"{nombre}  ({NOTACION_MODELO[nombre]})"

        eje_lin.plot(ns, ts, color=color, linewidth=2, marker="o", markersize=6, label=etiqueta)

        eje_log.plot(ns, ts, color=color, linewidth=2, marker="o", markersize=6, label=etiqueta)
        ns_ext = [ns[-1], LOTES_HISTORICO]
        c = extrapolacion[nombre].constante_s
        eje_log.plot(
            ns_ext, [predecir_tiempo(c, nombre, n) for n in ns_ext],
            color=color, linewidth=2, linestyle=(0, (4, 3)),
        )
        if nombre in validacion:
            eje_log.plot(
                LOTES_HISTORICO, validacion[nombre], marker="D", markersize=8,
                markerfacecolor="white", markeredgecolor=color, markeredgewidth=2,
                linestyle="none",
            )
        t_33k = extrapolacion[nombre].tiempo_laboratorio_s
        eje_log.annotate(
            formato_segundos(t_33k),
            xy=(LOTES_HISTORICO, t_33k), xytext=(8, 0), textcoords="offset points",
            fontsize=8, color=TINTA_PRIMARIA, va="center",
        )

    # Rótulos directos en el panel lineal para las dos series principales
    fb = filtrar_estrategia(mediciones, FUERZA_BRUTA)[-1]
    dv = filtrar_estrategia(mediciones, DIVIDIR_VENCER)[-1]
    eje_lin.annotate(
        formato_segundos(fb.tiempo_reloj_s), xy=(fb.n, fb.tiempo_reloj_s), xytext=(-8, 6),
        textcoords="offset points", ha="right", fontsize=8, color=TINTA_PRIMARIA,
    )
    eje_lin.annotate(
        formato_segundos(dv.tiempo_reloj_s), xy=(dv.n, dv.tiempo_reloj_s), xytext=(-8, 8),
        textcoords="offset points", ha="right", fontsize=8, color=TINTA_PRIMARIA,
    )

    aplicar_estilo(eje_lin, "Rango medido (escala lineal)", "Lotes por laboratorio (n)", "Tiempo (s)")
    eje_lin.xaxis.set_major_formatter(FuncFormatter(formato_miles))
    eje_lin.legend(frameon=False, fontsize=8, labelcolor=TINTA_PRIMARIA, loc="upper left")

    aplicar_estilo(
        eje_log, "Extrapolación al histórico del cliente (log-log)",
        "Lotes por laboratorio (n)", "Tiempo (s)",
    )
    eje_log.set_xscale("log")
    eje_log.set_yscale("log")
    eje_log.xaxis.set_major_formatter(FuncFormatter(formato_miles))
    eje_log.axvline(LOTES_HISTORICO, color=TINTA_TENUE, linewidth=1, linestyle=":")
    eje_log.text(
        LOTES_HISTORICO, eje_log.get_ylim()[0] * 1.6, " 33.000 lotes\n (3 años)",
        fontsize=8, color=TINTA_SECUNDARIA, ha="right",
    )
    eje_log.set_xlim(right=LOTES_HISTORICO * 3)
    manijas = [
        plt.Line2D([], [], color=TINTA_SECUNDARIA, linewidth=2, marker="o", label="Medido"),
        plt.Line2D([], [], color=TINTA_SECUNDARIA, linewidth=2, linestyle=(0, (4, 3)),
                   label="Extrapolado (t = c·f(n))"),
    ]
    if validacion:
        manijas.append(plt.Line2D(
            [], [], marker="D", markerfacecolor="white", markeredgecolor=TINTA_SECUNDARIA,
            markeredgewidth=2, linestyle="none", label="Medición real n = 33.000",
        ))
    eje_log.legend(handles=manijas, frameon=False, fontsize=8, labelcolor=TINTA_PRIMARIA,
                   loc="upper left")

    figura.suptitle(
        "Tiempo para encontrar el tramo crítico de un laboratorio",
        x=0.01, ha="left", fontsize=13, color=TINTA_PRIMARIA,
    )
    figura.tight_layout()
    return guardar_figura(figura, "escalabilidad_tiempo.png")


# ---------------------------------------------------------------------------
# Figura 2: consumo energético anual
# ---------------------------------------------------------------------------

def formato_kwh(valor: float) -> str:
    """Formatea kWh con coma decimal y precisión según la magnitud.

    Args:
        valor: Energía en kWh.

    Returns:
        Texto con unidad.
    """
    decimales = 1 if valor >= 100 else 2 if valor >= 1 else 3
    return f"{formato_decimal(valor, decimales)} kWh"


def graficar_consumo_energetico(extrapolacion: Dict[str, Extrapolacion]) -> str:
    """Grafica la energía anual de cada estrategia y el ahorro frente a la actual.

    Panel izquierdo: kWh/año de analizar los 290 laboratorios a diario (escala
    logarítmica, porque las estrategias difieren en varios órdenes de magnitud).
    Panel derecho: horas de servidor por corrida diaria, que es lo que la
    Secretaría percibe como "tarda varios días".

    Args:
        extrapolacion: Extrapolación por estrategia.

    Returns:
        Ruta del PNG generado.
    """
    figura, (eje_e, eje_t) = plt.subplots(1, 2, figsize=(12, 4.2))
    nombres = ORDEN_SERIES
    posiciones = list(range(len(nombres)))[::-1]
    colores = [COLORES[n] for n in nombres]
    actual = extrapolacion[FUERZA_BRUTA]

    energias = [extrapolacion[n].energia_anual_kwh for n in nombres]
    eje_e.barh(posiciones, energias, color=colores, height=0.55, edgecolor=SUPERFICIE, linewidth=2)
    eje_e.set_xscale("log")
    for pos, nombre, valor in zip(posiciones, nombres, energias):
        ext = extrapolacion[nombre]
        texto = formato_kwh(valor)
        if nombre != FUERZA_BRUTA:
            texto += f"   (ahorro {formato_decimal(ext.ahorro_porcentual, 2)} %)"
        eje_e.text(valor * 1.25, pos, texto, va="center", fontsize=8.5, color=TINTA_PRIMARIA)
    eje_e.set_yticks(posiciones, nombres)
    eje_e.set_xlim(right=max(energias) * 60)
    aplicar_estilo(
        eje_e, "Energía por año (365 corridas, escala log)", "kWh / año", "",
    )
    eje_e.grid(False, axis="y")

    horas = [extrapolacion[n].tiempo_corrida_h for n in nombres]
    eje_t.barh(posiciones, horas, color=colores, height=0.55, edgecolor=SUPERFICIE, linewidth=2)
    for pos, valor in zip(posiciones, horas):
        texto = f"{formato_decimal(valor, 2)} h" if valor >= 1 else f"{valor * 3600:.0f} s"
        eje_t.text(valor + max(horas) * 0.015, pos, texto, va="center", fontsize=8.5,
                    color=TINTA_PRIMARIA)
    eje_t.axvline(4, color=TINTA_TENUE, linewidth=1, linestyle=":")
    eje_t.text(4, (posiciones[1] + posiciones[2]) / 2, " ventana nocturna\n de 4 h (referencia)",
               fontsize=8, color=TINTA_SECUNDARIA, va="center")
    eje_t.set_yticks(posiciones, nombres)
    eje_t.set_xlim(right=max(horas) * 1.15)
    aplicar_estilo(
        eje_t, f"Tiempo de servidor por corrida ({NUM_LABORATORIOS} laboratorios)", "Horas", "",
    )
    eje_t.grid(False, axis="y")

    ahorro = actual.energia_anual_kwh - extrapolacion[DIVIDIR_VENCER].energia_anual_kwh
    figura.suptitle(
        f"Dividir y vencer ahorra {formato_kwh(ahorro)} al año frente al proceso actual "
        f"(servidor de 380 W)",
        x=0.01, ha="left", fontsize=13, color=TINTA_PRIMARIA,
    )
    figura.tight_layout()
    return guardar_figura(figura, "consumo_energetico_anual.png")


# ---------------------------------------------------------------------------
# Figura 3: ajuste teórico de la complejidad
# ---------------------------------------------------------------------------

def graficar_ajuste_teorico(
    mediciones: Sequence[Medicion], extrapolacion: Dict[str, Extrapolacion]
) -> str:
    """Contrasta los tiempos medidos con el modelo teórico ajustado.

    Tres paneles muestran, para cada estrategia, los puntos medidos y la curva
    c·f(n) ajustada con su R^2. El cuarto panel grafica t / f(n) normalizado:
    si el modelo teórico es el correcto, la razón se mantiene cerca de 1 al
    crecer n.

    Args:
        mediciones: Mediciones del experimento.
        extrapolacion: Constantes ajustadas y R^2 por estrategia.

    Returns:
        Ruta del PNG generado.
    """
    figura, ejes = plt.subplots(2, 2, figsize=(12, 8.4))
    paneles = [DIVIDIR_VENCER, FUERZA_BRUTA, KADANE]

    for eje, nombre in zip([ejes[0][0], ejes[0][1], ejes[1][0]], paneles):
        puntos = filtrar_estrategia(mediciones, nombre)
        ext = extrapolacion[nombre]
        n_max = puntos[-1].n
        ns_curva = [max(2, int(n_max * i / 200)) for i in range(1, 201)]
        eje.plot(
            ns_curva, [predecir_tiempo(ext.constante_s, nombre, n) for n in ns_curva],
            color=TINTA_TENUE, linewidth=2, linestyle=(0, (4, 3)),
            label=f"Teórico  c·{ext.modelo}   (R² = {ext.r2:.4f})",
        )
        eje.plot(
            [m.n for m in puntos], [m.tiempo_reloj_s for m in puntos],
            color=COLORES[nombre], marker="o", markersize=7, linestyle="none",
            label="Medido",
        )
        aplicar_estilo(
            eje, f"{nombre}: medido vs. Θ({ext.modelo})",
            "Lotes por laboratorio (n)", "Tiempo (s)",
        )
        eje.xaxis.set_major_formatter(FuncFormatter(formato_miles))
        eje.legend(frameon=False, fontsize=8, labelcolor=TINTA_PRIMARIA, loc="upper left")

    eje_razon = ejes[1][1]
    for nombre in ORDEN_SERIES:
        puntos = filtrar_estrategia(mediciones, nombre)
        c = extrapolacion[nombre].constante_s
        razones = [m.tiempo_reloj_s / predecir_tiempo(c, nombre, m.n) for m in puntos]
        eje_razon.plot(
            [m.n for m in puntos], razones, color=COLORES[nombre], linewidth=2,
            marker="o", markersize=6, label=f"{nombre}: t / (c·{NOTACION_MODELO[nombre]})",
        )
    eje_razon.axhline(1.0, color=TINTA_TENUE, linewidth=1, linestyle=":")
    eje_razon.set_xscale("log")
    eje_razon.xaxis.set_major_formatter(FuncFormatter(formato_miles))
    eje_razon.set_ylim(0, 2.0)
    aplicar_estilo(
        eje_razon, "Razón medido / teórico (1 = sigue el modelo)",
        "Lotes por laboratorio (n, escala log)", "t medido / t teórico",
    )
    eje_razon.legend(frameon=False, fontsize=8, labelcolor=TINTA_PRIMARIA, loc="upper right")

    figura.suptitle(
        "Contraste entre el tiempo medido y la complejidad teórica",
        x=0.01, ha="left", fontsize=13, color=TINTA_PRIMARIA,
    )
    figura.tight_layout()
    return guardar_figura(figura, "ajuste_teorico_complejidad.png")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def generar_graficas(
    mediciones: Optional[Sequence[Medicion]] = None,
) -> List[str]:
    """Genera las tres figuras técnicas a partir de los resultados guardados.

    Args:
        mediciones: Mediciones ya cargadas; si es None se leen de mediciones.csv.

    Returns:
        Rutas de los PNG generados.
    """
    if mediciones is None:
        mediciones = leer_mediciones_csv(os.path.join(DIRECTORIO_EXPERIMENTOS, "mediciones.csv"))
    extrapolacion = leer_extrapolacion_csv(
        os.path.join(DIRECTORIO_EXPERIMENTOS, "extrapolacion.csv")
    )
    validacion = leer_validacion_csv(os.path.join(DIRECTORIO_EXPERIMENTOS, "validacion_33000.csv"))

    assert set(extrapolacion) == set(ESTRATEGIAS), "extrapolacion.csv incompleto"
    return [
        graficar_escalabilidad_tiempo(mediciones, extrapolacion, validacion),
        graficar_consumo_energetico(extrapolacion),
        graficar_ajuste_teorico(mediciones, extrapolacion),
    ]


if __name__ == "__main__":
    for ruta in generar_graficas():
        print(f"[OK] {os.path.relpath(ruta, RAIZ_REPOSITORIO)}")
