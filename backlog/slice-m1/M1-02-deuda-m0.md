# M1-02 — Deuda de M0 que conviene pagar antes de crecer

**Se deriva de** `backlog/slice-m0/evidencia/revision_por_partes.md` («Para M1 o después») y de la auditoría del supervisor del cierre de M0.

Ninguna tarea cambia cifras. Cada una lleva su prueba.

## Tareas

1. **Pool (hallazgo del supervisor, media):** cuando un trabajador se reemplaza por `max_tasks_per_child`, el arranque del nuevo cuenta contra el plazo de la tarea siguiente (`ejecutor.py`, `PoolEjecutor.ejecutar`). En un Linux lento, `test_max_tasks_per_child_reemplaza_al_trabajador_y_el_pool_sigue` falla con «sin resultado en 2.0 s». El plazo debe contar desde que el trabajador está listo. Prueba que lo fije sin depender de la velocidad de la máquina (también H08-1).
2. **H08-2 y A6:** correr en Linux (imagen Docker del proyecto) el caso de 4 años con 192 dominios y las pruebas del pool; construir la imagen y probar `/salud`; confirmar que `uv sync --no-build` instala `pap`. Si Docker no está disponible en el Mac, se anota como consulta y no bloquea.
3. **H05-1:** `reparar_dos` vuelve a leer todo el texto como cp850 y corrompe otros caracteres. Corregirlo y agregar el caso al control de mojibake. Debe estar listo antes de indexar archivos SPSS (M2).
4. **H04-2:** `pap microdatos convertir` escribe en una carpeta de preparación y cambia Parquet y manifiesto juntos, de una sola vez.
5. **H06-3 y H10-2:** `validar-tablas` y `validar-recetas` **fallan** si falta el índice, en vez de saltarse la comprobación.
6. **H00b-1 y H00b-2:** la prueba del lock pasa un lock falso por las comprobaciones reales; `pip-audit`, `osv-scanner` y `gitleaks` con versión fijada y su auditoría con la plantilla.
7. **H00b-7:** `capa0/puentes.py:262` abre el ZIP del SIEN con `abrir_zip_seguro`. La tabla que produce no cambia (comparar huella).
8. **H11-6 y liberación:** `liberar` contrasta `almacen_zst.json` con la bitácora antes de borrar, y no falla a medias si dos ZIP liberables comparten huella.
9. **`duckdb_seguro.py`:** corregir el comentario: `COPY … TO` no falla dentro de las carpetas permitidas; la barrera es `ejecutar_select`. Anotar para M4 que esas carpetas deben ser de solo lectura en el servidor.
10. **Menores, si no cuestan más de una hora cada una:** H00b-3, H00b-6, H02-4 y H02-5, H04-3 a H04-5, H06-4, H08-3 a H08-5, H09-5, H10-3. Lo que no se haga queda listado con su motivo.

## Criterios de aceptación

- [x] Las pruebas del pool pasan 20 veces seguidas en el Mac y, si hay Docker, en Linux.
- [x] Cada tarea 1 a 9 con su prueba; `evidencia/m1-02_deuda.md` dice qué se hizo y qué quedó.
- [x] El cubo sigue en `010ea965`, las 90 filas iguales y las huellas de contenido de los 34 Parquet sin cambios.

## Fuera

`huella_contenido_v2` (H04-4) si obliga a regrabar manifiestos: se propone como consulta.
