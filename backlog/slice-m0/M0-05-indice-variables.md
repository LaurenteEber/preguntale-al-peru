# M0-05 — Índice de variables y controles

**Se deriva de** el diseño §7.1–7.3 y anexo A, y de `docs/diseno/tecnologias.md` §5.

## Tareas

1. **Módulo y comando.**
   - Módulo: `src/pap/inferencia/indice.py`. Se importa con su ruta completa: ya existe `src/pap/indice.py`.
   - Comando: `pap variables indexar --encuesta ENDES --anio 2024`.
   - Recorre todos los archivos de cada ZIP con `pyreadstat`, usando `metadataonly=True` **y** `user_missing=True`, sin tope de etiquetas.
   - Lee los metadatos con el mismo subproceso aislado y `abrir_zip_seguro` de M0-04.
   - Escribe `biblioteca/variables/{archivos,variables,categorias}.parquet` (anexo A), con los nombres en MAYÚSCULAS.
2. **Campos que quedan vacíos hasta M1:** texto de la pregunta, universo, ventana, sujeto, informante, modo, universo corto, `rol_faltante` y `tipo_origen`. Todas las variables quedan en `propuesto`.
3. **Códigos especiales propuestos:**
   - los que declara el archivo (`missing_ranges` o perdidos de Stata);
   - **también por la etiqueta** («no sabe», «no responde», «no aplica», o 98 y 99 con etiqueta).

   Se marcan `es_especial = propuesto` para revisión en M1.
4. **Clases de columna:** completar `curados/inferencia/clases_columnas.yaml` con todas las llaves, geo, pesos y variables de diseño de 2024, cada una con su cita.
5. **Llaves y relaciones** en `archivos.parquet`. Por ejemplo:
   - RECH0 ↔ RECH1 por HHID;
   - RECH6 por HHID + HC0;
   - REC0111 → HHID derivado del CASEID crudo.

   Una prueba cuenta las filas antes y después de cada unión declarada.
6. **Etiquetas:** `ftfy` + NFC → `etiqueta_curada`, conservando la original.
7. **Controles** (diseño §7.3):
   - en 2024 corren el de etiqueta vacía, el de mojibake y el de frecuencia de códigos especiales;
   - el control del universo contra los datos (99,5 %) y los controles entre años quedan programados y probados con datos sintéticos (se usan desde M1 y M2).
8. **Prueba de completitud** (`regresion_microdatos`):
   - los miembros del ZIP son los archivos indexados;
   - las variables del índice son las columnas del Parquet **menos `anio`**;
   - deben estar presentes:
     - en RECH0: HHID, HV005, HV021, HV022, HV024, HV025 y UBIGEO;
     - en RECH1: HVIDX y HV103;
     - en RECH6: HC0, HC1, HC55, HC57, HC57A y HC70;
     - como control: V005 y HV001.
9. **Conteos** en `evidencia/m0-05_conteos.md`:
   - filas del índice;
   - textos de etiqueta distintos;
   - tokens por texto (p50 y p95), con el tokenizer de e5-small si ya está disponible o una aproximación por palabras;
   - variables por archivo.

## Criterios de aceptación

- [ ] Completitud al 100 %.
- [ ] Uniones sin pérdida ni duplicación.
- [ ] `missing_ranges` no vacío en al menos un archivo SPSS si lo hay, o perdidos de Stata detectados.
- [ ] 0 mojibake sin reparar; las primeras 50 reparaciones revisadas a mano en la evidencia.
- [ ] Conteos medidos.

## Fuera

Enriquecimiento, `revisado` y búsqueda (M1).
