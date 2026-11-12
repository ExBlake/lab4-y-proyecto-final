# Laboratorio evaluativo 04 — Programación dinámica y algoritmos voraces

- **Asignatura:** Análisis de algoritmos - Asíncrono  
- **Grupo:** Grupo 8   
- **Caso Asignado:** Caso 2 — Plataforma Pulso: Consolidación, priorización y agendamiento del tamizaje de diabetes  
- **Operación Desarrollada:** Operación 3 — Programación de las jornadas de las unidades móviles  
- **Integrantes del Equipo:**
  - Juan Felipe Patiño Calderón
  - Januar Stiwar Martinez Palacios
  - Juan Felipe Torres Torres
  - Santiago Villada Arboleda

---
## 0. Sección de reproducción

### Requisitos Previos
- Python 3.10 o superior.
- Git.

### 1. Clonar el Repositorio y Configurar el Entorno
```bash
# Clonar el repositorio
git clone https://github.com/juanfelipepc3/lab4-analisis-algoritmos.git
cd lab4-analisis-algoritmos

# Crear y activar entorno virtual
python -m venv .venv

# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Suite de Pruebas Formales
Para verificar todos los casos límite, el ejemplo a mano, la restricción de negocio y la coincidencia con la solución exhaustiva:
```bash
python src/jornadas_unidades/pruebas.py
```
*Salida esperada:* Todas las aserciones pasan con código de salida 0.

### 3. Ejecutar las Mediciones y Regenerar Gráficas
Para ejecutar los experimentos de escalabilidad y actualizar las figuras técnicas en `graficas/jornadas_unidades/`:
```bash
python src/jornadas_unidades/medicion.py
```
*Salida generada:*
- `graficas/jornadas_unidades/tiempo_vs_n.png`
- `graficas/jornadas_unidades/operaciones_vs_n.png`

## Parte 1 — Modelado y resolución manual del problema

### Modelado del problema

El problema consiste en programar las jornadas de valoración médica solicitadas por los municipios de una subregión, teniendo en cuenta que existe una única unidad móvil disponible. Por esta razón, no se pueden asignar dos jornadas cuyos horarios se crucen.

Cada solicitud se representa mediante una tupla:

$$
s_i=(inicio_i, fin_i, pacientes_i)
$$

Donde:

- `inicio`: minuto en el que comienza la jornada.
- `fin`: minuto en el que termina la jornada, incluyendo el desplazamiento.
- `pacientes`: cantidad de pacientes de alto riesgo pendientes de atención.

**Entrada:** una lista de solicitudes de jornadas de una subregión.

**Salida:** un subconjunto de solicitudes compatibles, ordenadas cronológicamente, que maximice la cantidad de jornadas asignadas.

**Restricciones:**

- Una unidad móvil no puede atender dos jornadas simultáneamente.
- Las jornadas no se pueden dividir ni modificar sus horarios.
- Una jornada puede comenzar exactamente cuando termina la anterior.
- Cada subregión tiene su propia unidad móvil, por lo que las programaciones son independientes.

### Estrategia seleccionada y justificación

Se seleccionó el algoritmo voraz de selección de actividades (*Activity Selection*), debido a que el objetivo es maximizar la cantidad de jornadas municipales atendidas sin que existan cruces de horarios.

La estrategia consiste en ordenar las solicitudes por hora de finalización, de menor a mayor. Después, se selecciona la primera solicitud y se continúa recorriendo la lista, aceptando únicamente aquellas cuyo inicio sea mayor o igual al final de la última jornada seleccionada.

Esta estrategia funciona porque elegir la jornada que termina más temprano permite liberar la unidad móvil lo antes posible, dejando más tiempo disponible para programar otras jornadas.

La propiedad de elección voraz se justifica mediante un argumento de intercambio: siempre existe una solución óptima que puede comenzar con la jornada que termina más temprano. Si una solución óptima comienza con otra jornada, se puede reemplazar por la de finalización más temprana sin reducir la cantidad de jornadas compatibles.

Además, después de seleccionar una jornada, el problema restante consiste en seleccionar la mayor cantidad de jornadas compatibles con ella, conservando la misma estructura del problema original.

### Ejemplo resuelto manualmente

Se consideran seis solicitudes:

| Solicitud | Inicio | Fin | Pacientes |
|---|---:|---:|---:|
| R1 | 60 | 240 | 25 |
| R2 | 180 | 360 | 30 |
| R3 | 240 | 420 | 20 |
| R4 | 300 | 600 | 45 |
| R5 | 420 | 540 | 15 |
| R6 | 540 | 720 | 35 |

**Paso 1. Ordenar por hora de finalización.**

El orden obtenido es:

R1 (fin 240), R2 (fin 360), R3 (fin 420), R5 (fin 540), R4 (fin 600) y R6 (fin 720).

**Paso 2. Seleccionar las jornadas compatibles.**

- R1: se acepta porque es la primera solicitud. Último fin: 240.
- R2: se rechaza porque inicia en 180, antes de que termine R1 (240).
- R3: se acepta porque inicia en 240, exactamente cuando termina R1. Último fin: 420.
- R5: se acepta porque inicia en 420, exactamente cuando termina R3. Último fin: 540.
- R4: se rechaza porque inicia en 300, antes de que termine R5 (540).
- R6: se acepta porque inicia en 540, exactamente cuando termina R5. Último fin: 720.

**Paso 3. Resultado.**

Las jornadas seleccionadas son:

$$
S^*=\{R1,R3,R5,R6\}
$$

Se asignan 4 de las 6 jornadas solicitadas, atendiendo un total de:

$$
25+20+15+35=95
$$

Por tanto, la solución obtiene cuatro jornadas compatibles y 95 pacientes asociados a ellas.

### Limitación de la regla actual y alternativa

La regla actual de la organización consiste en aceptar las solicitudes por orden de llegada, rechazando las que se crucen con jornadas previamente asignadas.

Esta estrategia puede producir resultados subóptimos porque no considera cuánto tiempo ocupa cada jornada ni cómo afecta la programación de las solicitudes posteriores.

Como se demuestra en el contraejemplo de la sección 6, una jornada extensa aceptada primero puede bloquear varias jornadas más cortas que, en conjunto, permitirían atender más municipios.

Por otro lado, si el objetivo cambiara y se buscara maximizar la cantidad total de pacientes de alto riesgo atendidos, en lugar del número de jornadas, sería conveniente utilizar programación dinámica para resolver el problema de intervalos ponderados. Esto se debe a que una jornada más larga podría atender muchos más pacientes que varias jornadas cortas, por lo que seleccionar siempre la que termina primero ya no garantizaría el mejor resultado.

## Parte 2 — Implementación y verificación

### Supuestos de interpretación

- **Unidades de tiempo:** `inicio` y `fin` son minutos contados desde el inicio del mes (minuto 0 = día 1 a las 00:00). Un mes de 31 días no cambia nada: el algoritmo solo compara números, no depende de la longitud del mes.
- **Jornadas que se tocan:** cada jornada ocupa el intervalo semiabierto `[inicio, fin)`. Si una jornada empieza justo en el minuto en que otra termina, **no** se considera cruce, porque `fin` ya incluye el desplazamiento.
- **Solicitudes válidas:** se exige `0 <= inicio < fin` y `pacientes >= 0`. Una solicitud que no cumpla esto se rechaza con `ValueError` en lugar de programarse.
- **Solicitudes repetidas:** dos solicitudes idénticas se cruzan entre sí, así que solo una puede atenderse.
- **Empates:** si dos solicitudes terminan a la misma hora, la estrategia escoge la que tiene más pacientes de alto riesgo. El número de jornadas no cambia, pero se atiende a más pacientes.
- **Una unidad por subregión:** cada subregión se resuelve por separado; la función recibe las solicitudes de una sola subregión.
- **Regla actual:** se interpreta que el coordinador revisa las solicitudes en el orden en que llegaron y acepta cada una que no se cruce con **ninguna** de las ya aceptadas (no solo con la última).

### Implementación

El código de la operación está en [src/jornadas_unidades/](src/jornadas_unidades/):

| Módulo | Contenido |
|---|---|
| [estrategia.py](src/jornadas_unidades/estrategia.py) | `seleccionar_jornadas` (voraz por hora de fin) y `hay_cruce`. Define también el tipo `Jornada` y los auxiliares `se_cruzan` y `validar_solicitudes`. |
| [exhaustivo.py](src/jornadas_unidades/exhaustivo.py) | `seleccionar_exhaustivo`: prueba los 2^n subconjuntos con máscaras de bits y se queda con el más grande sin cruces. |
| [regla_actual.py](src/jornadas_unidades/regla_actual.py) | `asignar_por_llegada`: reproduce la regla del coordinador. |
| [datos.py](src/jornadas_unidades/datos.py) | Generador de solicitudes sintéticas con semilla fija. |
| [pruebas.py](src/jornadas_unidades/pruebas.py) | Pruebas con `assert`. |

Decisiones de implementación:

- **Estrategia:** ordena las solicitudes por `(fin, -pacientes, inicio)` y las recorre una vez, guardando el fin de la última jornada aceptada. Una solicitud entra si `inicio >= ultimo_fin`. Como las jornadas elegidas no se cruzan, quedan ordenadas por hora de inicio, que es lo que pide el esqueleto. Costo: O(n log n) en tiempo y O(n) en espacio.
- **`hay_cruce`:** ordena por inicio y compara cada jornada con el mayor fin visto hasta ahora. Así detecta también el caso en que una jornada larga contiene a otras dos. Costo: O(n log n).
- **Exhaustiva:** recorre las 2^n máscaras y solo revisa cruces cuando el subconjunto es más grande que el mejor encontrado. Costo: O(2^n · n log n). Se limita a 22 solicitudes (`MAXIMO_EXHAUSTIVO`), porque su único fin es validar la estrategia.
- **Regla actual:** compara cada solicitud con todas las ya aceptadas, porque no están ordenadas por hora. Costo: O(n²) en el peor caso. Devuelve las jornadas en el orden en que se aceptaron.
- **Datos sintéticos:** jornadas de 4 a 12 horas (incluido el desplazamiento), entre 5 y 150 pacientes y un horizonte de 30 días (43.200 minutos). Para comparar con la exhaustiva se usa un horizonte de 2 días, para que haya muchos cruces y la elección no sea trivial.
- No se usa ninguna biblioteca de optimización; todo está escrito a mano con la biblioteca estándar.

### Verificación

[pruebas.py](src/jornadas_unidades/pruebas.py) se ejecuta con `python src/jornadas_unidades/pruebas.py` y comprueba:

1. **Definición de cruce:** jornadas que se solapan, una contenida en otra, idénticas, y jornadas que solo se tocan en un extremo (no es cruce).
2. **Casos límite:** entrada vacía, una sola solicitud, ninguna se cruza (se aceptan todas), todas se cruzan (se acepta una), solicitudes repetidas, empates en la hora de fin y rechazo de solicitudes inválidas.
3. **Ejemplo resuelto a mano (Parte 1):** la estrategia devuelve R1, R3, R5 y R6, es decir, 4 jornadas y 95 pacientes; la exhaustiva también obtiene 4.
4. **200 instancias aleatorias pequeñas** (de 1 a 12 solicitudes, semilla 2026): la estrategia y la exhaustiva obtienen siempre el mismo número de jornadas, y la regla actual nunca obtiene más.
5. **Restricción del negocio:** ninguna programación tiene dos jornadas que se crucen y todas las jornadas elegidas salen de las solicitudes. Se revisa en 50 instancias pequeñas y en 9 instancias del volumen real (una por subregión, de 40 a 120 solicitudes).
6. **Contraejemplo de la regla actual:** con las solicitudes, en orden de llegada, C1 = (420, 1020, 40), C2 = (420, 600, 30), C3 = (600, 780, 25) y C4 = (780, 1020, 35), la regla por orden de llegada acepta solo C1 (1 jornada, 40 pacientes). La estrategia acepta C2, C3 y C4 (3 jornadas, 90 pacientes), lo mismo que la exhaustiva. La diferencia es de 2 jornadas.
