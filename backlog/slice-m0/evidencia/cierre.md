# Cierre del slice M0: cimientos del motor de inferencia (10/11/2026)

## Qué puede hacer ahora el usuario

Todavía nada nuevo en la web: M0 no cambia ninguna respuesta. Q1–Q4, la matriz y la evaluación grabada siguen iguales. Lo que hay es la base del motor nuevo, que calcula **a pedido desde los microdatos** de la ENDES 2024:

- los 34 archivos de la ENDES 2024 en Parquet, con su manifiesto y una huella de contenido, y un índice de 2 856 variables;
- un plan que se verifica sin escribir SQL a mano, un ejecutor con tiempos y memoria acotados, y las compuertas de publicación leídas de `reglas.json`;
- tres recetas que **igualan las 90 filas de 2024 del cubo** y reproducen sus 21 cifras doradas;
- el ciclo del almacén: respaldo en el repo privado, restauración probada y liberación del espacio local (simulada).

El dueño puede comprobar una receta con `uv run pap inferencia receta endes_dci_menores_5 --anio 2024 --comparar-cubo`, y el respaldo con `uv run pap almacen restaurar --bloque endes-2024` (`docs/guia_de_operacion.md` §3.5d).

## Definición de hecho, punto por punto

| # | Punto | Cumple | Evidencia |
|---|---|---|---|
| 1 | Las 3 recetas igualan las 90 filas de 2024 del cubo `010ea965` (8 decimales, \|dif\| ≤ 1e-8; n y gl idénticos; n efectivo; 1e-12 sin redondear) | **sí** | 90 de 90 filas con diferencia 0 y 21 de 21 doradas ([m0-10_recetas.md](m0-10_recetas.md), [90 filas](m0-10_recetas_vs_cubo.csv)). El CSV, regenerado por el revisor, sale idéntico. Las recetas están en `revisado`: `verificado` espera el visto del dueño (K-03) |
| 2 | Índice completo de la ENDES 2024 | **sí** | 34 archivos, 2 856 variables y 7 602 categorías; las uniones sin pérdida ([m0-05_conteos.md](m0-05_conteos.md)). Reindexado el 10/11, sale idéntico byte a byte ([m0-11_medicion.md](m0-11_medicion.md) §3) |
| 3 | El ejecutor coincide con R `survey` (1e-9; gl y n exactos) y pasa las pruebas de seguridad, tiempo y memoria | **sí en el Mac; Linux pendiente** | `svy` 0.35.0 = `survey` 4.5 en 50 de 50 casos, máx. 1,3e-15 ([m0-09_r.md](m0-09_r.md)); pool ([m0-08_ejecutor.md](m0-08_ejecutor.md)). Falta correr el pool en Linux |
| 4 | Compuertas R-ENC-02 a 04 desde `reglas.json`, con el mismo estado que el validador en las 90 filas | **sí** | 85 publicables y 5 referenciales, iguales fila por fila ([m0-09_compuertas.md](m0-09_compuertas.md)) |
| 5 | Medición en el Mac: almacén y proyección del tope de F-04, índice, p95 del ejecutor | **sí** | [m0-11_medicion.md](m0-11_medicion.md). La propuesta de tope es la consulta C-M0-11-1 |
| 6 | Decisiones, reglas y `agents.md` al día; `reglas.json` regenerado con el consolidador | **sí** | [m0-01_decisiones.md](m0-01_decisiones.md). El revisor regeneró las reglas y salen idénticas byte a byte. R-ENC-19 espera K-07 |
| 7 | Q1–Q4, la matriz y la evaluación grabada sin cambios; suite completa en verde | **sí** | Suite: **1818 pasan, 1 se salta** (la que genera capturas, solo con `PAP_CAPTURAS=1`, igual que en el slice 3). `regresion_microdatos`: 74 pasan ([m0-11/pytest_completo.txt](m0-11/pytest_completo.txt)). Q1–Q4 (`test_regresion_q1_q4.py`), la matriz reducida (`test_matriz_cobertura.py`) y la evaluación grabada (`interprete/test_evaluacion_grabada.py`) corren dentro de la suite. La única diferencia es la huella de reglas, regrabada con el visto del dueño (C-M0-01-1) |
| 8 | Revisión independiente por partes | **sí** | 12 partes revisadas: 11 aprobadas con observaciones; M0-11 salió bloqueante y quedó corregida ([revision_por_partes.md](revision_por_partes.md)) |
| 9 | Seguridad: A1–A9 aplicadas, dependencias auditadas, `just auditar` y gitleaks en verde | **sí, salvo la imagen Docker** | pip-audit y osv-scanner limpios; gitleaks sin fugas en 95 commits de todas las ramas ([m0-11/seguridad.txt](m0-11/seguridad.txt)). `just` no está instalado en el Mac: se corrieron los mismos comandos del `justfile`. La imagen (A6) no se construyó porque el demonio de Docker está apagado |
| 10 | El bloque ENDES 2024 respaldado, con la restauración probada; `liberar` probado en simulación; tamaños medidos | **sí** | Release `crudos-endes-2024` (22 archivos) en el repo privado; 20 de 20 recursos OK y PS_BECA18 reconvertido con la misma huella ([m0-11_restauracion.txt](m0-11_restauracion.txt)). Simulación: 11 ZIP, 73,0 MB ([m0-11_liberar_simulacion.txt](m0-11_liberar_simulacion.txt)). Las pruebas de `liberar` cubren la lista protegida y el caso sin restauración (`tests/test_almacen_bloques.py`, 21 pruebas) |

## Qué quedó fuera

- **El pool en Linux** (M0-08): repetir allí `tests/inferencia/test_pool_ejecutor.py` y el caso de 4 años con 192 dominios. Primero hay que corregir H08-1: la prueba de la llamada nativa larga depende de la velocidad de la máquina.
- **La imagen Docker** (M0-00b, A6): con el demonio prendido, `docker build` y `/salud`. Hay que confirmar que `uv sync --no-build` instala el propio `pap`.
- **Liberar los ZIP de 2024:** decide el dueño. Hoy solo está la simulación.
- **`verificado` de las 3 recetas:** espera el visto K-03.

## Supuestos aplicados que el dueño debe revisar

- **El repo de crudos estaba vacío** y GitHub no deja crear un release ahí. El agente agregó un `README.md` (commit `60e40a0` del repo privado) y después subió el respaldo con `scripts/respaldar_crudos.sh`.
- **`restaurar` vuelve a poner en el almacén los ZIP liberados,** comprobados contra su huella. El diseño (§6) pide que «reconvertir un bloque liberado obliga a bajarlo antes con `pap almacen restaurar`», y `pap registrar` no vuelve a poner un objeto cuya huella ya está registrada.
- **Ningún parámetro del ejecutor cambió** con lo medido; ver [m0-11_medicion.md](m0-11_medicion.md) §7. El margen de memoria con 4 años apilados es justo: 1 176 MB de 1 536.
- **Los supuestos anteriores de M0** siguen en `consultas_al_dueno.md`, en «Supuestos aplicados».

## Consultas abiertas

| ID | Qué | Bloquea |
|---|---|---|
| **C-M0-11-1** | Tope de F-04 para la ENDES 2015–2025. Propuesta: 2 GB en el Mac y 1,5 GB en el repo privado | bajar 2015–2023 |
| **C-M0-11-2** | Con 25 a 49 casos y un CV muy alto, la cifra queda referencial en vez de suprimirse (R-ENC-03/04 exigen n ≥ 50). Recomendación: suprimir | no |
| K-03 | Visto por lote de las tablas curadas y las recetas | `verificado` |
| K-07 | Umbrales de R-ENC-19 (no respuesta del ítem) | no |
| K-04, K-05, K-08 | Horas de revisión, tope del LLM, licencia de la ENAHO | M1 a M3 |
| C-M0-05-2, C-M0-06-1 a 4, D-M0-03-1, D-M0-05-1, D-M0-10-1 | Ver `consultas_al_dueno.md` | no |

## Qué se aprendió para detallar M1

- **Lista de hallazgos para M1:** la sección «Para M1 o después» de [revision_por_partes.md](revision_por_partes.md). Lo más importante:
  - **H05-1:** corregir `reparar_dos` **antes** de indexar los años en SPSS (2015–2020), porque corrompe caracteres sin que el control lo note;
  - **H04-2:** que la conversión cambie los Parquet y el manifiesto juntos, de una sola vez;
  - **H00b-1 y H00b-2:** endurecer la prueba del lock y la herramienta de auditoría;
  - **H06-3 y H10-2:** que los validadores fallen, y no se salten la comprobación en silencio, cuando falta el índice;
  - **D-M0-10-1:** pasar el universo analítico de la receta al plan.
- **El margen de memoria del pool es justo:** si M1 sube `anios_apilados_max_llamada` o los cortes, hay que medir de nuevo, y también en Linux.
- **La gramática es la barrera de seguridad,** y ahora DuckDB también: solo ejecuta un `SELECT`. M1 no debe agregar ningún camino que ejecute SQL fuera de `ejecutar_select`.
- **No commitear mientras otro (el dueño o un trabajador) edita archivos versionados.** `d89db55` se llevó la mitad de M0-10 con un mensaje de M0-09.
- **El ciclo por bloque funciona y es barato:** respaldar y restaurar la ENDES 2024 tomó menos de 20 s. Para cada año nuevo: registrar, convertir, indexar, respaldar, restaurar y, si el dueño lo decide, liberar.

## Fusión y cierre (12/11/2026)

- El dueño pidió hacer el merge a `main` para cerrar M0.
- El PR #4 se fusionó en `main` con un commit de merge (`0ac8c7b`).
- La etiqueta `slice-m0-cerrado` se creó sobre ese commit y se subió a GitHub.
- La suite completa en `main` después de la fusión: 1818 pasan y 1 se salta (la de capturas).
- La rama `slice-m0` se conserva.
