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