# M0-04 — Conversor y almacén de microdatos

**Se deriva de** el diseño §6 y de `docs/diseno/tecnologias.md` §5.

## Tareas

1. **Módulo y comando.**
   - Módulo: `src/pap/inferencia/almacen.py`. Se importa con su ruta completa: ya existe `src/pap/almacen.py`, que es el almacén de crudos.
   - Comando: `pap microdatos convertir --encuesta ENDES --anio 2024`.
2. **Apertura segura y lectura aislada:**
   - los ZIP se abren con `abrir_zip_seguro` (`src/pap/zip_seguro.py`, de M0-00b; control C7);
   - cada archivo SAV o DTA se lee en un subproceso con límites de memoria (RLIMIT_AS), CPU y tiempo (C8);
   - solo `pyreadstat` lee estos formatos; `svy_io` nunca.
3. **Qué hace con cada archivo** de cada ZIP registrado:
   - **Lectura:** con `pyreadstat`, opciones `user_missing=True`, `apply_value_formats=False`, `output_format="polars"` y `encoding=None` (en un DTA sin codificación declarada, `WINDOWS-1252`).
     - Los archivos de más de 200 MB se leen en bloques de 25 000 filas.
     - Los perdidos extendidos de Stata (.a–.z) y los de usuario de SPSS quedan como nulo en la columna, y su código va al índice (`categorias.parquet`, `es_especial`). Si esto cambia un universo de las recetas, es tipo C.
   - **Clases de columna:** se toman de `curados/inferencia/clases_columnas.yaml`, una versión provisional con las llaves conocidas que M0-05 completa.
     - Llaves y geo: texto. Se recortan **solo por fuera**; los espacios internos y los ceros se conservan. El ancho se verifica, y un ancho distinto es un error: no se corta.
     - **CASEID → HHID** se deriva del valor crudo, antes de normalizar.
     - Categorías: INTEGER. Medidas: DOUBLE.
   - **Escritura:** `biblioteca/microdatos/ENDES/2024/{archivo}.parquet` con DuckDB `COPY` (zstd 3, grupos de 122 880 filas), con la columna `anio` y los nombres en MAYÚSCULAS.
4. **Manifiesto** `biblioteca/microdatos/ENDES/2024/manifiesto.json`. Por archivo lleva:
   - origen (ZIP y miembro);
   - `huella_datos`;
   - `huella_contenido_v1`, con -0.0 y NaN normalizados (`tecnologias.md` §5);
   - filas y columnas;
   - versiones.
5. **Lock:** `pap microdatos convertir` agrega a `curados/insumos.lock.yaml` las huellas de los ZIP que usó, con `insumos.escribir_lock`.
6. **Marca de prueba:** registrar `regresion_microdatos` en `pyproject.toml`. Estas pruebas llevan también `solo_mac`.
7. **Pruebas rápidas,** sin datos reales:
   - ZIP maliciosos sintéticos (ruta con `..`, enlace simbólico, bomba de compresión), que deben ser rechazados;
   - SAV y DTA sintéticos con perdidos de usuario y extendidos, nombres con Ñ, UBIGEO y HHID con ceros a la izquierda, un CASEID con espacios y un archivo grande que se lee por bloques;
   - la huella de contenido es estable al reescribir con polars o con pyarrow, al barajar las filas y con -0.0 y NaN.
8. **Pruebas `regresion_microdatos`** (en el Mac):
   - las filas de cada Parquet son iguales a las del miembro del ZIP;
   - UBIGEO y HHID conservan su ancho;
   - una prueba con un nombre con Ñ.

## Criterios de aceptación

- [ ] Todos los archivos de 2024 convertidos, con su manifiesto.
- [ ] Huellas de los ZIP en el lock.
- [ ] RSS máximo por archivo < 1,5 GB, y huella de contenido en < 5 s por archivo.
- [ ] Tamaño medido por archivo y total en `evidencia/m0-04_tamano.md`.
- [ ] No se tocan `biblioteca/estandarizada/` ni el cubo.

## Fuera

El índice (M0-05).
