# M0-11 — Medición, espacio local, documentación y cierre

**Se deriva de** el diseño §6 (ciclo por bloque y liberación del espacio local).

## Tareas

1. **`pap almacen restaurar --bloque endes-2024`** (reemplaza a `scripts/restaurar_crudos.sh`). En un directorio temporal:
   - baja el release del repo privado;
   - comprueba las huellas contra `datapackage.json`;
   - reconvierte un archivo y comprueba que su `huella_contenido_v1` es igual a la del manifiesto (`evidencia/m0-11_restauracion.txt`);
   - si todo cuadra, marca el bloque como `respaldado` en `biblioteca/cruda/almacen_zst.json`, con la fecha y la URL del release.
2. **`pap almacen liberar --bloque <encuesta>-<anio>`:**
   - `--simular` por defecto: muestra la lista y el espacio que liberaría;
   - solo libera ZIP de bloques `respaldado`;
   - **nunca** toca los Parquet, el manifiesto, `datapackage.json`, `insumos.lock.yaml`, `indice.duckdb`, los crudos de otras fuentes ni los ZIP que lee `pap calcular` (hogar y anemia de la ENDES, sumaria de la ENAHO). Una prueba lo comprueba;
   - pide confirmación y registra cada liberación en `biblioteca/cruda/verificaciones.jsonl`;
   - aviso cuando el espacio libre baja de `almacen.espacio_libre_min_gb`.

   En M0 se prueba en modo simulación y con datos sintéticos. Liberar de verdad el bloque de 2024 queda a decisión del dueño.
3. **Medición en el Mac** → `evidencia/m0-11_medicion.md`:
   - tamaño de los ZIP y de los Parquet de 2024, y proyección a 2015–2025, con una **propuesta de tope para F-04** (consulta al dueño);
   - espacio libre del Mac antes y después del bloque;
   - filas del índice, textos distintos y tokens por texto;
   - tiempos del conversor y del índice;
   - p95 del ejecutor (de M0-08);
   - tiempo real de `ejecutor_gracia_s`;
   - memoria residente del pool.
4. **Parámetros:** ajustar en `curados/inferencia/parametros.yaml` `dominios_max_llamada`, `anios_apilados_max_llamada`, `ejecutor_timeout_s`, `ejecutor_gracia_s` y `memoria_trabajador_mb` con lo medido, con `supuesto: M0-11` si cambian.
5. **Documentación:**
   - `docs/arquitectura.md`: el paquete `src/pap/inferencia/`;
   - `docs/especificaciones/stack.md`;
   - `docs/guia_de_operacion.md`: convertir, indexar, respaldar, restaurar y liberar, regenerar los esperados de R y correr `just auditar`;
   - `docs/estado.md`.
6. **Revisión independiente por partes,** una por historia con código, con las lentes de riesgo, confiabilidad y seguridad → `evidencia/revision_por_partes.md`.
7. **Cierre** → `evidencia/cierre.md`:
   - la definición de hecho, punto por punto;
   - lo aprendido para M1;
   - PR a `main` y etiqueta `slice-m0-cerrado` después de que el dueño escriba «fusiona».

## Criterios de aceptación

- [ ] Los 10 puntos de la definición de hecho, cada uno con su evidencia.
- [ ] Prueba de `liberar`: no toca nada de la lista protegida y no libera un bloque sin restauración probada.
