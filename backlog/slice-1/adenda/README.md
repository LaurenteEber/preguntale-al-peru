# Slice 1 — Adenda: concluir la implementación

Actualizada el 4/11/2026, tras migrar al repositorio `preguntale-al-peru`. Rama `slice-1-adenda` desde `main`. Mismas reglas que el slice: `agents.md`, `curados/motor/parametros_motor.yaml`, consultas en `../consultas_al_dueno.md` y evidencia en `../evidencia/adenda/`.

## Por qué

La validación del cierre del slice 1 (3/11/2026) dejó dos cosas:

- **«¿Cómo cambió el gasto?» no se responde.** Los montos están en soles de cada año, y R-GASTO-12 bloquea comparar años sin deflactar. Deflactar ya está decidido (G-01, R-GASTO-12) y el IPC está en la biblioteca (`dim_ipc`).
- **Siguen abiertas observaciones medias y bajas de la revisión:** H9, H11, H12, N-2, N-3, A-H6, D-01 y la observación de H7. Están en `../evidencia/revision_usuario.md` (tabla «Estado de los hallazgos»), `../evidencia/auditoria_estadistica.md` y `../consultas_al_dueno.md`. H8 y H10 ya están corregidas y no se tocan.

## Antecedentes del repositorio nuevo (4/11/2026)

- El repositorio empezó de cero. Los commits y las etiquetas que cita la evidencia del slice 1 (`slice-1`, `slice-1-cerrado`, `1603698`…) son de la carpeta de trabajo anterior y no existen aquí (`docs/historia.md`).
- Los Parquet no están en git. Están en el release `biblioteca-ba1fbc55` de GitHub y S1-11 los baja y los comprueba (F-05: se trabaja en Claude Code en la nube). Si la nube no puede subir a `main`, S1-16 sube la rama y abre un PR; el dueño fusiona y pone la etiqueta. La reconstrucción hecha al migrar dio la huella del cubo `ba1fbc55…`, y los manifiestos en git la registran.
- El nombre del proyecto pasó a «Pregúntale al Perú» por decisión del dueño (commit `e3c611d`). Esto cambió el rótulo de la fuente en Q1–Q4 («Fuente: Pregúntale al Perú, cálculo propio…»). Las referencias de `tests/referencias/` ya lo traen y es la base de la regresión. No hay que aprobarlo de nuevo.

## Historias (en orden)

| ID | Historia | Estado |
|---|---|---|
| S1-11 | [Preparar el entorno y la biblioteca](S1-11-preparacion.md) | hecha ([biblioteca](../evidencia/adenda/s1-11_biblioteca.txt), [manifiestos](../evidencia/adenda/s1-11_manifiestos.txt), [pytest](../evidencia/adenda/pytest_base.txt): 714 pasan y 34 `solo_mac`) |
| S1-12 | [Gasto en soles constantes y su evolución](S1-12-gasto-deflactado.md) | hecha ([cubo](../evidencia/adenda/s1-12_comparacion_cubo.txt): huella nueva `sha256:010ea965…`; [un solo año](../evidencia/adenda/s1-12_un_anio.txt); [respuesta](../evidencia/adenda/s1-12_evolucion_gasto_peru.md); `tests/test_gasto_constantes.py`) |
| S1-13 | [La evolución muestra los dos años que compara](S1-13-evolucion-anios.md) | hecha (`tests/test_evolucion_anios.py`; comprobación `evolucion` de la matriz en `test_matriz_cobertura.py`; Q1 en [regresion/Q1.yaml](../evidencia/regresion/Q1.yaml) con `aprobado_por: dueño` (AD-1); respuestas: [Perú](../evidencia/adenda/s1-13_evolucion_anemia_peru.md), [hasta 2024](../evidencia/adenda/s1-13_evolucion_anemia_peru_hasta_2024.md), [hasta 2018](../evidencia/adenda/s1-13_evolucion_anemia_peru_hasta_2018.md)) |
| S1-14 | [Cruce y efecto: textos que no prometen ni contradicen](S1-14-cruce-efecto.md) | hecha (`tests/test_cruce_efecto.py`; comprobación `cruce` de la matriz; reglas regeneradas: vp3 sin cierres abiertos, guardia 0 fallos, `validar-reglas` 535/535; Q3 en [regresion/Q3.yaml](../evidencia/regresion/Q3.yaml); respuestas: [cruce Puno](../evidencia/adenda/s1-14_cruce_anemia_puno.md), [Q3](../evidencia/adenda/s1-14_q3.md); D-01 cerrada) |
| S1-15 | [Correcciones menores de la revisión](S1-15-menores.md) | hecha (`tests/test_menores_adenda.py`; respuestas: [N-3](../evidencia/adenda/s1-15_comparacion_lm_lr.md), [H7](../evidencia/adenda/s1-15_anemia_peru_2018.md); Q1–Q4 sin cambios) |
| S1-16 | [Verificación y cierre de la adenda](S1-16-cierre-adenda.md) | hecha salvo la fusión: [verificación](../evidencia/adenda/verificacion.md) «apto con observaciones»; [matriz](../evidencia/adenda/matriz.md) 0 fallos; [cierre](../evidencia/cierre.md#adenda-s1-11-a-s1-16-4112026). Falta subir la rama y abrir el PR (C-06: GitHub rechaza el push), y después la fusión, la etiqueta y `pytest_main.txt` |

## Decisiones del dueño

Las dos están decididas y ya figuran en `docs/decisiones.md`. Las diferencias de texto que producen en Q1–Q4 se registran con `aprobado_por: dueño` y citan la decisión.

| ID | Qué | Historia | Estado |
|---|---|---|---|
| AD-1 | En una evolución, «Más contexto» da la cifra del año con el que se compara. En Q1 se agrega la anemia de 2024 con la forma vigente | S1-13 | **aprobada** 4/11/2026 (fila R-04) |
| AD-2 | Nueva frase estándar de R-CRUCES-07: «Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió» | S1-14 | **aprobada** 4/11/2026 (fila R-03) |

Ya estaban decididas, sin consulta:
- deflactar con el IPC de Lima del último año cerrado (G-01, R-GASTO-12);
- alinear «Lima» de R-TERRITORIO-09 con T-03 (D-01);
- en «¿cuánta hay?» de anemia, solo la forma vigente (E-06; afecta a H7).

## Definición de hecho de la adenda

1. La biblioteca del entorno de trabajo (Mac o nube, F-05) reproduce la huella del cubo `ba1fbc55…` antes de cualquier cambio (S1-11).
2. «¿Cómo cambió el gasto?» compara 2023 con 2025 en soles constantes de 2025, con su rótulo, y R-GASTO-12 ya no la bloquea.
3. Están resueltas H9, H11 (AD-1), H12 (AD-2), N-2, N-3, A-H6, D-01 y la observación de H7, cada una con su prueba.
4. Regresión Q1–Q4: no cambian las cifras, los semáforos ni la confianza. Las diferencias de texto quedan aprobadas en `../evidencia/regresion/`: las de AD-1 y AD-2, por el dueño; las demás, por el agente si cumplen `agents.md` §5.1.
5. La matriz completa corre sin errores ni fallos. `uv run pytest -q` queda en verde, sin fallos nuevos frente a `../evidencia/adenda/pytest_base.txt` (S1-11).
6. Una verificación independiente da «apto». Quedan al día el manual, el cierre y el estado, y `main` lleva la etiqueta `slice-1-adenda-cerrada`.

## Fuera

- LLM, API, web y datos nuevos.
- Las observaciones bajas que cambian el patrón de Q1–Q4 (H14, H15, H17, H18, H21 y A-H8): se revisan en el slice 3, con la web.
- La separación de las ejecutoras mixtas (X-06).
- Registrar los 16 PDF de `biblioteca/cruda/bandeja/validacion_doradas/` (deuda menor de `docs/estado.md`, sin efecto en el motor).
