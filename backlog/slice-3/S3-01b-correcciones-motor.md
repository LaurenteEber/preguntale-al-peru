# S3-01b — Correcciones del motor antes de la web

## Por qué

La prueba del dueño (6/11/2026, `salidas/prueba_dueno/`) y la revisión del cubo encontraron afirmaciones que las cifras de la misma respuesta contradicen, una cifra de gasto que mezcla soles de dos años, nombres de departamento que terminan en una aclaración innecesaria y un enlace oficial que el navegador no abre. Con la web, eso llega a más gente: se corrige **antes de S3-04**.

Las tareas las fijó el dueño el 6/11/2026 (texto literal en `../../odd/tasks/slice-3.md`, L8). Los puntos tipo C se le preguntan a él y no se aplican sin su respuesta.

## Tareas

| # | ID | Qué pasa | Qué se hace | Tipo | Dueño |
|---|---|---|---|---|---|
| 1 | H-A | «la forma anterior da cifras más altas» es falso en 4 de 60 pares del cubo (Cajamarca 2024 y 2025, Arequipa 2025, Amazonas 2025); la respuesta de Cajamarca se contradice. Está en `bloques.yaml` (dos lugares) y en el glosario `forma_de_medir` | Texto: «que no se compara con la de hoy» | C | aprobado 6/11/2026 |
| 2 | H-B | Q3 muestra el gasto de Lima Metropolitana de 2024 y de 2025 juntos, cada uno en soles de su año (260,7 y 260,6 millones) | Por R-GASTO-12 y X-03: 2024 en soles de 2025 (~264,6 millones), con el nominal en la cita, como en S1-12. Se exceptúa la cifra en la regresión | datos | — |
| 3 | u13 | «¿Cuánto gastó el gobierno en anemia en Lima?» lleva a leer los 260,6 millones como gasto en anemia y del gobierno | Primero se dice qué cubre la cifra y qué no | C | aprobado 6/11/2026 |
| 4 | H-F | La tarjeta «Por qué esta cifra es más baja que la de la encuesta» (`bloques.yaml`, `tarjeta_porque`) sale siempre; en 152 de 1 878 distritos el SIEN es mayor o igual (Lurigancho: 45 % frente a 25,3 %) | Título: «Por qué esta cifra no se compara con la de la encuesta» | C | aprobado 6/11/2026 |
| 5 | H-G | San Antonio (Huarochirí, 150716): SIEN 95 % en 1 597 niños y establecimientos con 86–99 %. Otros ≥ 77 % con n ≥ 100: Unión Progreso, Santo Domingo de los Olleros, Pullo e Incahuasi | Contrastar con el archivo oficial del INS y reportar. No se cambian datos; si el INS publica lo mismo, se propone una regla de plausibilidad | C | reportado; pendiente (W-04) |
| 6 | H-I | 7 de 18 preguntas de prueba terminan en «Hay varios lugares llamados Puno» | X-22: el nombre de un departamento se responde como departamento y se ofrece la provincia o el distrito como alternativa; Lima sigue con T-03. Fila X-22 en `docs/decisiones.md` | C | aprobado 6/11/2026 |
| 7 | H-J | «Lurigancho Chosica» y «Lurigancho-Chosica» no se reconocen | Alias → 150118 en `curados/motor/textos/territorio.yaml` | B | — |
| 8 | H-K | El enlace del SIEN (`web.ins.gob.pe/.../sala-nutricional`) da ERR_CERT_AUTHORITY_INVALID | Proponer un documento oficial del INS en gob.pe que abra sin aviso. `scripts/comprobar_enlaces.sh` lista los códigos HTTP de todas las `url` de las citas; se corre en el Mac antes de cada cierre | C | enlace aprobado 6/11/2026 |
| 9 | Matriz | Nada comprueba que una comparación escrita coincida con las cifras | Comprobación nueva: toda comparación escrita («más alta», «más baja», «mayor», «menor») coincide con las cifras de la misma respuesta. Debe detectar H-A y H-F antes de corregirlos | A | — |
| 10 | Cubo | Con un cubo local que no es el del manifiesto, las pruebas fallan con mensajes dispersos | Una prueba que falla primero, con un solo mensaje: «el cubo local no es el del manifiesto: corre `pap calcular`». `scripts/bajar_biblioteca.sh` y la guía dicen que después de bajar el release hay que correr `pap calcular` | A | — |
| 11 | Documentos | Temas repetidos y datos viejos | Cada tema en un solo lugar: `manual_de_uso.md` = usar; `guia_de_operacion.md` = mantener. La guía quita su §4 y enlaza al manual; el manual quita su §3.3 y enlaza a la guía. La guía suma «Trabajar en local o en la nube». Corregir: el estado del encabezado (remitir a `estado.md`), slice 2 cerrado en la hoja de ruta, el número de pruebas, el enlace roto a `arquitectura_y_funcionamiento.md`, «Versión al 13/10/2026» y «la huella del cubo actual es ba1fbc55» | A | — |
| 12 | E-04 | Las 18 preguntas del dueño no están en el conjunto de evaluación | Agregar las 18 de `salidas/prueba_dueno/preguntas.txt`, con su resultado esperado según el diseño vigente y las decisiones de esta historia. Grabarlas con el tope de costo. La del celular entra con el número ya reemplazado | A | — |
| 13 | H-L | Avisos de Starlette (httpx en TestClient) y de openpyxl («Print area cannot be set») en pytest | Silenciar solo esos dos en la configuración de pytest, con un comentario. Sin dependencias nuevas | A | — |
| 14 | W-02 | — | Cerrar sin aplicar: quitar los porcentajes de Q4 también quita el aviso de fuentes de distinto tipo | — | decidido 6/11/2026 |

## Criterios de aceptación

- [x] La comprobación del punto 9 falla sobre el motor anterior a H-A y H-F (evidencia) y pasa después.
- [x] Solo cambian las cifras de H-B (exceptuadas en la regresión de Q3) y los textos de 1, 3, 4 y 6; ningún semáforo ni confianza.
- [x] H-G y H-K reportados al dueño con evidencia; nada aplicado sin su respuesta.
- [x] `uv run pytest -q` completo sin fallos nuevos respecto de la base local; regresión Q1–Q4, matriz reducida, evaluación con grabaciones y equivalencia web en verde.
- [x] `test_sin_secretos` en verde y grep del prefijo de las claves de Anthropic y de la cabecera de la clave vacío antes de cada commit.

Evidencia: [`evidencia/s3-01b/correcciones.md`](evidencia/s3-01b/correcciones.md).
