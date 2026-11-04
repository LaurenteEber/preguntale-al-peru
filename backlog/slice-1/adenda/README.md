# Slice 1 — Adenda: concluir la implementación

3/11/2026. Rama `slice-1-adenda` desde `main`. Mismas reglas que el slice: `agents.md`, `curados/motor/parametros_motor.yaml`, consultas en `../consultas_al_dueno.md`, evidencia en `../evidencia/adenda/`.

## Por qué

La validación del cierre (3/11/2026) encontró una pregunta decidida que el motor no responde y observaciones medias que la revisión independiente dejó abiertas:

- **«¿Cómo cambió el gasto?» no se responde.** Los montos están en soles de cada año y R-GASTO-12 bloquea comparar años sin deflactar. Deflactar ya está decidido (G-01, R-GASTO-12) y el IPC está en la biblioteca (`dim_ipc`).
- Quedan observaciones medias sin resolver: H9, H10, H11, H12, N-2, N-3, A-H6 y D-01 (`../evidencia/correcciones_s1-09.md`, `../evidencia/auditoria_estadistica.md`, `../evidencia/revision_usuario.md`).
- Falta orden en el repositorio: la carpeta `odd/` y archivos de Obsidian sin seguimiento.

## Historias (en orden)

| ID | Historia | Estado |
|---|---|---|
| S1-11 | [Gasto en soles constantes y su evolución](S1-11-gasto-deflactado.md) | pendiente |
| S1-12 | [La evolución muestra los dos años que compara](S1-12-evolucion-anios.md) | pendiente |
| S1-13 | [Cruce y efecto: textos que no prometen ni contradicen](S1-13-cruce-efecto.md) | pendiente |
| S1-14 | [Correcciones menores de la revisión](S1-14-menores.md) | pendiente |
| S1-15 | [Orden del repositorio](S1-15-orden-repositorio.md) | pendiente |
| S1-16 | [Verificación y cierre de la adenda](S1-16-cierre-adenda.md) | pendiente |

## Decisiones del dueño que la adenda necesita

Se implementan con la recomendación. Si el dueño dice otra cosa, se cambia esa parte.

| ID | Qué | Recomendación | Historia | Estado |
|---|---|---|---|---|
| AD-1 | La evolución muestra en «Más contexto» la cifra del año con el que compara. Cambia una tarjeta de Q1 (agrega la anemia de 2024 con la forma vigente) | Sí: sin ese número, «sin cambio claro entre 2024 y 2025» no se puede comprobar | S1-12 | pendiente |
| AD-2 | Nuevo texto de la frase de R-CRUCES-07 que la respuesta de efecto contradice. Hoy: «Estos datos muestran qué se gastó y cómo cambió el indicador». Propuesta: «Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió» | Sí. Se cambia con el consolidador | S1-13 | pendiente |

Ya están decididas, sin consulta: deflactar con el IPC de Lima del último año cerrado (G-01, R-GASTO-12); alinear «Lima» de R-TERRITORIO-09 con T-03 (D-01).

## Definición de hecho de la adenda

1. «¿Cómo cambió el gasto?» compara 2023 con 2025 en soles constantes de 2025, con su rótulo, y R-GASTO-12 ya no la bloquea.
2. Están resueltas H9, H10, H11 (según AD-1), H12 (según AD-2), N-2, N-3, A-H6 y D-01, cada una con su prueba.
3. Regresión Q1–Q4: no cambian las cifras, los semáforos ni la confianza. Las diferencias de texto están aprobadas en `../evidencia/regresion/` (las de AD-1 y AD-2, con `aprobado_por: dueño`).
4. La matriz completa corre sin errores ni fallos. `uv run pytest -q` queda en verde (sin fallos nuevos frente a `s1-10_pytest_main.txt`).
5. Una verificación independiente da «apto». Quedan al día el manual, el cierre y el estado, y se pone la etiqueta `slice-1-adenda-cerrada`.

## Fuera

LLM, API, web y datos nuevos. Las observaciones bajas que cambian el patrón de Q1–Q4 (H14, H15, H17, H18, H21 y A-H8): se revisan en el slice 3, con la web. La separación de ejecutoras mixtas (X-06). El respaldo de `biblioteca/_respaldo_pre_s1-00/`, que borra el dueño cuando decida.
