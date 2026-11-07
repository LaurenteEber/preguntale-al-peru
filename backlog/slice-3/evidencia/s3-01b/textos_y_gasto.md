# S3-01b: textos de la forma de medir, enlace del SIEN y gasto de 2024 en Q3

Aprobado por el dueño el 6/11/2026. Filas de S3-01b cubiertas: 1 (H-A), 2 (H-B), 4 (H-F) y 8 (H-K, solo el cambio de enlace).

## Qué cambió

- **H-A.** El aviso de la forma de medir la anemia ya no dice «da cifras más altas». Ahora dice «que no se compara con la de hoy». Cambia en dos textos de `bloques.yaml` y en el término «forma de medir la anemia» de `glosario.yaml`.
- **H-F.** El título de la tarjeta pasa a «Por qué esta cifra no se compara con la de la encuesta». El cuerpo de la tarjeta no se tocó. Dice que las cifras del INS «podrían subestimar la anemia real», y eso sí afirma una dirección. Queda para que el dueño lo revise.
- **H-K.** El enlace del SIEN pasa a la colección de informes de vigilancia del INS en gob.pe. Cambió en `catalogo_fuentes.csv`, `catalogo_fuentes.md` y `curados/recetas/INS-CENAN-SIEN.yaml`. Antes de editar se revisó que ninguno de estos archivos entra en la huella del cubo ni en `insumos.lock.yaml`. Esas huellas se calculan sobre los datos descargados, no sobre el catálogo ni las recetas, así que no cambió ninguna. El mismo enlace viejo sigue en `catalogo/catalogo_fuentes.json`, que no estaba entre los archivos permitidos. Pendiente.
- **H-B.** En Q3 el gasto de 2024 de Lima Metropolitana se mostraba en soles de 2024 junto al de 2025 (soles de 2025). Ahora el planificador (`planificador.py`, `_soles_constantes`) pide `devengado_constante` para el gasto de un año anterior al más reciente cuando ambos se muestran juntos. Reutiliza la deflactación de S1-12. La cifra más reciente sigue en soles corrientes. La cita de 2024 trae el monto nominal y el factor.

## Q3, gasto de 2024 (Lima Metropolitana)

- Antes: S/ 260,7 millones (soles de 2024).
- Ahora: **S/ 264,6 millones** (soles de 2025). La cita dice «monto registrado en 2024: S/ 260,7 millones; factor de inflación: 1,0150108».
- El gasto de 2025 no cambia: S/ 260,6 millones.

## Regresión

Se aprobaron como `aprobado_por: dueño` las diferencias de texto en `backlog/slice-1/evidencia/regresion/Q1.yaml`, `Q2.yaml` y `Q3.yaml`. Se quitaron las entradas que quedaron caducadas: la del enlace viejo, la de la definición del glosario y las del gasto de 2024 en soles de 2024.

## Pruebas

- `tests/test_h_b_gasto_mismo_anio.py` (nueva). Primero falló, porque la cifra seguía en `devengado`. Pasa ahora.
- `tests/test_comparaciones_escritas.py`: pasa (antes fallaban 2).
- `tests/test_regresion_q1_q4.py`, `test_matriz_cobertura.py`, `test_evolucion_anios.py`, `test_cruce_efecto.py`, `test_gasto_constantes.py`, `test_planificador.py`, `test_plantillas_intencion.py`, `test_sin_secretos.py`: 133 pasan junto con las anteriores.
- `test_gasto.py`, `test_gasto_e3.py`, `test_gasto_lima.py`, `test_gasto_pieza_a.py`: 98 pasan.
- `uv run pap preguntar curados/motor/consultas_minimas/`: sin errores.
- No se corrió la suite completa.
- Se ajustaron `test_evolucion_anios.py` (texto nuevo), `test_planificador.py` (el id de cifra usa la medida de la cifra) y `test_regresion_q1_q4.py` (la cifra exceptuada de Q3 ahora es `devengado_constante`).

## u13 — qué cubre la cifra de gasto (punto 3, aprobado por el dueño el 6/11/2026)

Toda respuesta de gasto (nivel actual) abre con lo que cubre la cifra y lo que no; la cifra va después. Se quitó el «Ojo al leer» que repetía lo mismo; el otro («No concluyas que el gasto dio resultados…») se queda. Los textos están en `curados/motor/textos/bloques.yaml` (`gasto.nivel_actual.gasto.apertura` y `sesgo_sede_lima.nivel_actual.gasto_lima.apertura`). «Lima» es lo que ya manejaba `sesgo_sede_lima` (Lima Metropolitana y Lima Región); las municipalidades de Lima usan el texto de municipios.

**Lima Metropolitana (capa 1, respuesta corta)**
- Antes: «En 2025, en Lima Metropolitana, el gasto en servicios de salud y nutrición infantil fue:» → S/ 260,6 millones. Ojo: «No incluye a las entidades nacionales con sede en Lima, que atienden a todo el país.»
- Ahora: «Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil, y no incluye lo que gastan las entidades nacionales con sede en Lima. En 2025, en Lima Metropolitana, el gasto en servicios de salud y nutrición infantil fue:» → S/ 260,6 millones (97 palabras; antes 83). Ese ojo ya no está.

**Otras regiones (Ayacucho)**
- Antes: «En 2025, en Ayacucho, el gasto … fue:». Ojo: «No leas esta cifra como todo el gasto en Ayacucho: solo cuenta lo que registran las entidades con sede allí.»
- Ahora: «Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil, y solo cuenta lo que registran las entidades con sede en Ayacucho. En 2025, en Ayacucho, el gasto … fue:». Ese ojo ya no está.

**Municipios (San Juan de Lurigancho)**
- Antes: «En 2025, en San Juan de Lurigancho, el gasto … fue:». Ojo: «No es todo el gasto en el distrito: no incluye lo que gastan el Ministerio de Salud ni otras entidades.»
- Ahora: «Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil, y solo cuenta a la municipalidad y las obras ubicadas en San Juan de Lurigancho. En 2025, en San Juan de Lurigancho, el gasto … fue:». Ese ojo ya no está.

**Perú**
- Antes: «En 2025, en Perú, el gasto … fue:». Ojo: «No es el gasto de cada lugar: es la suma de lo que registran las entidades públicas.»
- Ahora: «Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil de todas las entidades públicas del país. En 2025, en Perú, el gasto … fue:». Ese ojo ya no está.

Sin cambio: cifras (260 593 096,7 / 93 375 145,82 / 3 960 205,2 / 2 455 856 886,1), semáforo (verde, verde, ámbar, verde), confianza, la cifra clave y su «registrado por …» (R-LENGUAJE-02). Si la cifra no se puede publicar, «no se puede» sigue primero y no lleva apertura.

Pruebas: `tests/test_u13_apertura_gasto.py` (12; con los textos viejos fallaban 8). Corrieron `test_gasto*.py`, `test_h_b_gasto_mismo_anio.py`, `test_regresion_q1_q4.py` (sin cambios de Q1–Q4: Q3 es «efecto», no «nivel actual»), `test_comparaciones_escritas.py`, `test_plantillas_intencion.py`, `test_sin_secretos.py` (172 pasan), y `test_matriz_cobertura.py` + `tests/interprete` (222 pasan). La evaluación grabada cumple todos los umbrales (`evaluacion.md`). Sin efecto en las 4 consultas mínimas, así que no se tocó `regresion/Q*.yaml`.
