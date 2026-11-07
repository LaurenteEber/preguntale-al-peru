# Revisión de usuario S3-10 (celular, 360 × 780 px)

Revisor independiente. Web local en 127.0.0.1:8765 (proceso detenido al terminar), Playwright con Chromium en modo móvil (`is_mobile`, táctil). Preguntas propias en `preguntas_s3-10_usuario.yaml`; capturas en `s3-10/`. No se tocó código, datos, textos ni pruebas.

## Veredicto: **apto con observaciones**

No hay hallazgos bloqueantes. Hay 2 altos (una persona probable lee mal el lugar o el alcance de una cifra) y varios medios. Las cifras que vi coinciden con las del manual y con sus citas; la confianza se entiende sin color («Confianza en los datos: alta/media/baja», en palabras). La web se lee sin zoom, los botones y opciones son grandes y se tocan bien, y «Buscando…» se ve mientras espera (capa `w09.png`).

## Las 20 preguntas

Captura = ventana de 360 px (`_capas` = página completa con «Más contexto» y «Para citar» abiertos). Todas en `backlog/slice-3/evidencia/s3-10/`.

| id | persona | vía | resultado | captura |
|---|---|---|---|---|
| w01 | madre de Huancavelica | texto | respuesta (38,6 %, 2025) | w01.png, w01_capas.png |
| w02 | madre de Puno | texto | respuesta (desnutrición bajó, 2015–2025) | w02.png, w02_capas.png |
| w03 | periodista | texto | respuesta (Puno, 56,1 %) | w03.png, w03_capas.png |
| w04 | regidor | texto | aclaración (Ayaviri de Yauyos o de Melgar) → respuesta (23–42 %, 2018, confianza baja) | w04_aclaracion.png, w04.png, w04_capas.png |
| w05 | funcionario | texto | respuesta parcial: «No se puede saber si el gasto … sirvió» + gasto | w05.png, w05_capas.png |
| w06 | estudiante | texto | respuesta (pobreza Puno > Cusco) | w06.png, w06_capas.png |
| w07 | periodista | texto | respuesta (gasto en soles de 2025 «aumentó») | w07.png, w07_capas.png |
| w08 | madre de Huancavelica | texto | aclaración (4 «San Juan»); **no la resolví** (tope de envíos) | w08.png |
| w09 | docente | texto | aclaración «¿Quisiste decir…?» (Huancavelica, 3 niveles); toqué «departamento», **no llegué a leer la respuesta** (tope de envíos) | w09_aclaracion.png, w09.png |
| w10 | estudiante | texto | aclaración de tema (4 temas); **no la resolví** | w10.png |
| w11 | madre de Puno | formulario | respuesta (56,1 %) | w11.png, w11_capas.png |
| w12 | madre de Huancavelica | formulario | respuesta (bajó; 20,3 %) | w12.png, w12_capas.png |
| w13 | periodista | formulario | respuesta (Puno > Cusco) | w13.png, w13_capas.png |
| w14 | periodista | formulario | respuesta (Puno, único en el grupo más alto) | w14.png, w14_capas.png |
| w15 | regidor | formulario | respuesta (S/ 132,1 millones, con aviso de alcance) | w15.png, w15_capas.png |
| w16 | funcionario | formulario | respuesta de cruce (gasto + anemia + cobertura) | w16.png, w16_capas.png |
| w17 | funcionario | formulario | aclaración (Lima Metropolitana / Región / Callao) → respuesta parcial (efecto) | w17_respuesta.png |
| w18 | estudiante | formulario | aclaración (provincia o distrito) → respuesta (12–27 %, 2018, baja) | w18_respuesta.png |
| w19 | docente | formulario | mensaje «No encontramos ese lugar» (Cuzko) | w19.png |
| w20 | madre de Puno | formulario | respuesta (sin cambio claro 2024–2025) | w20.png, w20_capas.png |

Probado además: página de inicio (`inicio.png`), guiado paso 1 (`guiado_inicio.png`), paso 2 (`w11_paso2.png`). «Más contexto» y «Para citar y verificar» se abren y se leen bien. Los enlaces «Documento oficial» existen en cada cifra citada y llevan a: INEI (PDF del informe ENDES 2025, gob.pe de pobreza 2016-2025 y 2015-2024, Mapa de Pobreza 2018), INS (colección SIEN en gob.pe), MINSA (gob.pe/69889) y `datosabiertos.gob.pe` (gasto). No los abrí.

**No probado:** tocar los 3 ejemplos de la portada (están en la página, pero ya estaba en el tope de envíos); w08 y w10 resueltos; la respuesta final de w09.

## Hallazgos

### Altos

**H-01 · alto · w11, w12, w15, w16, w20 (formulario) y w01** — La respuesta del formulario no dice a qué nivel se respondió. Frase de capa 1: «En 2025, en Huancavelica, la anemia en niñas y niños de 6 a 35 meses fue: 38,6 %». El aviso «Respondimos por el departamento de Huancavelica. Si buscabas la provincia o el distrito… pregúntalo así…» está solo en «Más contexto», cerrado. En la caja de texto sí aparece «Entendimos: … en el departamento de Huancavelica», pero en el formulario no hay «Entendimos» y en w01 (texto) la capa 1 dice «en Huancavelica» a secas. Quien escribe «Huancavelica» pensando en su distrito lee 38,6 % como cifra de su distrito. Capturas: w11.png, w12.png, w01.png. Propuesta: poner «departamento de» en la frase de capa 1 y repetir la línea «Entendimos…» en el formulario.

**H-02 · alto · w17 (también w05, w16)** — En «efecto» y «cruce» el gasto aparece sin el aviso de alcance que sí tiene «¿Cuánto hay hoy?» (w15: «Esta cifra no es solo de anemia… solo cuenta lo que registran las entidades con sede en Puno»). En w17: «Lo que sí se sabe es lo gastado : S/ 260,6 millones en servicios de salud y nutrición infantil en 2025, registrado por unidades ejecutoras con sede en Lima Metropolitana». Para Lima eso omite lo que gastan las entidades nacionales con sede allí, y se compara (en «Más contexto») con la anemia de Lima. La persona puede leer ese monto como todo el gasto del lugar. Además, en w17 la frase queda «lo gastado :» (falta el lugar y hay un espacio antes de los dos puntos). Capturas: w17_respuesta.png, w05.png. Propuesta: aplicar el mismo aviso de alcance a efecto y cruce, y corregir la frase («lo gastado en Lima Metropolitana:»).

### Medios

**H-03 · medio · w01, w03, w05, w11, w14, w16, w17** — «¿Qué puedo hacer? (texto pendiente de revisión)» se muestra a una madre como si fuera un consejo oficial sin revisar. Es la X-01 conocida del dueño. Propuesta: ocultarlo al público hasta que el dueño lo apruebe.

**H-04 · medio · w05, w16, w17** — La tarjeta «Niñas y niños de 6 a 35 meses con al menos una medición de hemoglobina en establecimientos del MINSA o del gobierno regional (de cada 100)… entre 39,8 % y 50,5 %» no dice que es cobertura de tamizaje, no anemia; un rango de porcentaje junto a la anemia se confunde. Propuesta: abrir la tarjeta con «Cuántos se midieron la hemoglobina:» en palabras sencillas.

**H-05 · medio · w05, w16, w17** — «Gasto en Puno en 2024 … el mismo año con el que se compara la anemia» confunde: no se entiende por qué aparece 2024. Y el monto de 2024 está en soles de 2025, pero la tarjeta no lo dice (solo la cita). Propuesta: «Para comparar con la anemia de 2024: S/ … (en soles de 2025)».

**H-06 · medio · w02, w12** — El glosario dice «ENDES … mide la hemoglobina de los niños» en respuestas de desnutrición (donde no se habla de hemoglobina). Y en w07 (gasto, serie del MEF) aparece «cambio estadísticamente claro … no se explica por el azar de la encuesta», cuando el gasto no es de una encuesta. Propuesta: glosario por tema.

**H-07 · medio · w02, w12** — Las citas de la desnutrición de 2025/2015 dicen «Pregúntale al Perú, cálculo propio con ENDES…» y su «Documento oficial» lleva a `proyectos.inei.gob.pe/microdatos/` (portal general). Con gasto pasa algo parecido (`datosabiertos.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto`, la misma página para todas las cifras). La persona que quiere verificar no encuentra la cifra ahí. Propuesta: decir en la cita «no hay tabla publicada con esta cifra; se calcula de microdatos» o enlazar el informe más cercano.

**H-08 · medio · w19** — «No encontramos ese lugar. Revisa cómo está escrito…» no repite lo que escribió, no sugiere nada (por escrito, «Huancabelica» sí recibió «¿Quisiste decir…?») y no vuelve al formulario: solo ofrece el enlace «Elegir paso a paso, sin escribir», que es el mismo formulario en el que ya estaba, y con ello pierde tema e intención. Propuesta: volver al paso 2 con el lugar vacío y el tema/intención conservados, y repetir «Cuzko» en el mensaje.

**H-09 · medio · (límite de uso) w04 y envíos seguidos** — Al enviar de nuevo la misma pregunta en pocos segundos salió «Espera un momento.» con una caja vacía («Escribe tu pregunta de nuevo»): se pierde lo escrito y no dice cuánto esperar. Pasó también con el formulario (6 envíos en ~20 s). Una familia que comparte la conexión o alguien que corrige y reenvía rápido lo vería. Propuesta: conservar el texto en la caja y decir «Espera unos segundos y vuelve a intentar».

**H-10 · medio · w04** — La aclaración repite mal lo escrito: «Hay varios lugares llamados «distrito Ayaviri»». El «distrito» lo escribió como tipo de lugar, no como nombre. Propuesta: quitar el tipo del nombre antes de preguntar («llamados «Ayaviri»»).

### Bajos

**H-11 · bajo · w06, w13** — La «Fuente» de capa 1 se repite y suena a relleno: «ENAHO 2025 (INEI); el INEI publica la misma cifra (18,8 %) · ENAHO 2025 (INEI); el INEI publica la misma cifra (37,5 %)». Propuesta: una sola vez, «ENAHO 2025 (INEI); cifras iguales a las del INEI».

**H-12 · bajo · w02** — Capa 1 dice «bajó» pero el punto de partida (14,6 % en 2015) está solo en «Más contexto», y la cifra grande («alrededor de 9 %») difiere de la cita (8,5 %). Propuesta: «bajó de 14,6 % en 2015 a 9 % en 2025».

**H-13 · bajo · w18** — «Abancay (Abancay, Apurímac)» repite el nombre; la advertencia de que el dato es de 2018 («antes de la pandemia») solo está en «Más contexto» (el título sí dice «En 2018»). Propuesta: «Abancay (provincia de Abancay, Apurímac)».

**H-14 · bajo · w09 y aclaraciones** — Al tocar una opción, su texto cambia a «Buscando…» y la persona ya no ve cuál eligió. Propuesta: «Buscando… Huancavelica (departamento)».

**H-15 · bajo · w17** — «Lima Región (Lima Provincias)» usa dos nombres para lo mismo. Propuesta: «Lima Región (las provincias de Lima fuera de Lima Metropolitana)».

## Respuestas a las preguntas guía

- ¿Entiende qué se le respondió? Sí en general; la excepción es el nivel del lugar (H-01) y el alcance del gasto (H-02).
- ¿Encuentra la fuente? Sí, cada cifra trae «Fuente» y «Documento oficial»; algunos enlaces son portales genéricos (H-07).
- ¿Entiende la confianza sin color? Sí, está en palabras y con el porqué.
- ¿Sabe qué hacer ante una aclaración o un «no se puede»? Ante las aclaraciones, sí (botones grandes). Ante «No encontramos ese lugar» en el formulario, no (H-08).
- ¿Algo lleva a una conclusión falsa? H-01 y H-02; las frases «sin cambio claro no quiere decir igual» y «no concluyas que el gasto funcionó o falló» están bien puestas.
- Celular: se lee sin zoom, los botones se tocan sin errores, «Buscando…» aparece.

## Costo en vivo

`salidas/interprete/uso.jsonl` pasó de 559 a 569 líneas (+10 llamadas al LLM, todas `consulta`): **US$ 0,0427** de US$ 0,50. Envíos por texto contados: 15 de 15 (10 preguntas + 1 rechazado por el límite + 1 repetida + 1 aclaración tocada de w04 + 1 pregunta repetida de w09 + 1 aclaración tocada de w09); los repetidos y las aclaraciones no llamaron al LLM. El formulario no usa el LLM. Servidor detenido al terminar.

## Correcciones (H-01 y parte de H-02)

Hechas tras la revisión (S3-10, tarea 2), solo las partes tipo A/B. Lo que queda de H-02 (aviso de alcance del gasto en efecto y cruce) es una pregunta para el dueño.

**H-01 (tipo B, cambia mi supuesto S3-01b-a).**
- Antes: «Respondimos por el departamento de Huancavelica. Si buscabas la provincia o el distrito…» iba primero en «Avisos» (capa 2, plegada).
- Después: el mismo texto (`territorio.yaml` → `oferta_otros_niveles`) va primero en «Ojo al leer» (capa 1), sin repetirse en «Avisos». `src/pap/motor/preguntar.py` (`preguntar_minima`).
- Excepción: en `comparacion` y `evolucion` sigue primero en «Avisos». Con dos departamentos a secas la comparación llegaba a 126–151 palabras y 4 «Ojo al leer», y la evolución de anemia (Q1 por texto: Huancavelica 142; Puno 142, Cusco 142, Ayacucho 135, Loreto 135) pasaba de 125 (`respuesta.capa1_palabras_max`; máximo de 3 «Ojo al leer»). Se conservan todas las advertencias de la cifra (decisión del padre: opción 1); las intenciones son `_OFERTA_EN_AVISOS` en el código, con comentario (S3-10).
- Comprobación de tope: de 8 intenciones × 4 temas × 5 departamentos a secas, 60 respuestas llevan la oferta; ninguna pasa de 125 palabras ni de 3 «Ojo al leer» (en comparación y evolución la oferta va en «Avisos», y 80 llevaban oferta antes de la excepción). Antes de la excepción pasaban 12 comparaciones y 5 evoluciones.
- No se agregó «departamento de» a la frase de la cifra ni un «Entendimos».
- Supuesto S3-01b-a actualizado en `consultas_al_dueno.md`.

**H-02, solo la frase rota (tipo A).**
- Antes: «Lo que sí se sabe es lo gastado : …» (y en cruce «Esto es lo que se gastó : …») en Lima Metropolitana, Lima Región, Callao y Perú: `nivel_en` solo tenía distrito, provincia y departamento.
- Después: `comunes.yaml` → `nivel_en` suma `nacional: «en todo el país»` y `defecto: «en {lugar}»`. Resultado: «lo gastado en Lima Metropolitana:», «en Lima Región», «en Callao», «en todo el país». Los tres niveles que ya existían no cambian.
- Otros usos de `{nivel_en}` (bloques de SIEN y gasto local): solo salen con distrito, provincia o departamento; sin cambio.

**Pruebas.**
- Nuevas: `tests/test_h02_lo_gastado.py` (efecto y cruce, 10 casos); `tests/test_x22_departamento_a_secas.py` (frase = `ojo_al_leer[0]`, no está en avisos; «departamento de Puno» no la tiene; comparación con dos departamentos a secas deja las ofertas en avisos y la capa 1 dentro del tope). Vistas en rojo antes del arreglo.
- `tests/web/test_guiado.py`: la idea de retirar el aviso X-22 antes de la regresión se mantiene (en Q1, evolución, sigue en «Avisos»; se comprueba que no está en «Ojo al leer»); la diferencia permitida con la base sigue siendo `capas.capa2.avisos` solo en Q1.
- Regresión Q1–Q4 (`test_regresion_q1_q4.py`): sin cambios en cifras, semáforos ni confianza; no hizo falta aprobar nada.
- Base web regenerada (`s3-02_generar_base.py`): cambian 8 respuestas, 7 por la frase X-22 (pd03, pd04, pd10, pd12, pd14, pd18, s07a) y 1 por la frase de cruce de Lima Metropolitana.
- Evaluación del intérprete (solo grabaciones): cumple todos los umbrales.

Suite completa en el Mac antes del commit parcial de S3-10: 1223 passed, 1 skipped in 880.14s (0:14:40).

## Correcciones tras las decisiones del dueño (7/11/2026)

Decisiones en `consultas_al_dueno.md` (W-10, W-11) y en el Log L14 de `odd/tasks/slice-3.md`.

| Hallazgo | Antes | Después | Dónde |
|---|---|---|---|
| H-02 / W-10 (motor) | En efecto y cruce, el gasto salía sin decir qué cubre | Departamento, ámbitos de Lima, Callao y Perú abren con el texto de u13 («Esta cifra no es solo de anemia…»). Provincia y distrito sin apertura: su frase ya dice «solo de la municipalidad y de obras ubicadas…» (dueño: tope de 125 palabras) | `bloques.yaml` (anclas `apertura_gasto`), `cruce_efecto.yaml`, `plantillas.py` → `cruce_efecto` |
| H-04 (motor) | «Niñas y niños de 6 a 35 meses con al menos una medición… (de cada 100) (Puno)» | «Cuántos se midieron la hemoglobina (Puno)»: «En 2025, en los establecimientos del MINSA y del gobierno regional se midió la hemoglobina a entre 39,8 % y 50,5 % de los niños de 6 a 35 meses del departamento…» | `cruce_efecto.yaml` → `tarjetas.cobertura` |
| H-05 (motor) | «En 2024, el gasto fue S/ 121,9 millones…: el mismo año con el que se compara la anemia.» | «Para comparar con la anemia de 2024: S/ 121,9 millones (en soles de 2025), registrado por unidades ejecutoras con sede en Puno (MEF 2024).» (solo si la cifra está en soles constantes) | `cruce_efecto.yaml` → `tarjetas.mismo_anio.texto_constantes` |
| H-06 (motor) | ENDES «mide la hemoglobina» también en desnutrición; «cambio estadísticamente claro» también en el gasto | ENDES según el tema; «cambio estadísticamente claro» solo si el verbo es de una cifra de encuesta o de modelo | `glosario.yaml`, `capas.py`, `plantillas.py` → `cierre` |
| H-07 (motor) | «Fuente: Pregúntale al Perú, cálculo propio con ENDES 2015 (INEI).» | «…; no hay tabla publicada con esta cifra; se calcula de microdatos.» Solo encuestas, sin cuadro oficial; el enlace no cambia | `capas.yaml` → `sin_tabla_publicada`, `capas.py` → `_cita` |
| H-10 (motor) | «Hay varios lugares llamados «distrito Ayaviri»» | «Hay varios lugares llamados «Ayaviri»» (el nombre oficial, con tildes, si todos los candidatos lo comparten) | `territorio.py` |
| H-03 (web) | «¿Qué puedo hacer? (texto pendiente de revisión)» visible | Oculto en la web mientras X-01 no esté aprobada; el JSON y la CLI no cambian | `curados/web/parametros.yaml` → `paginas.mostrar_que_hacer_sin_revisar`, `respuesta.html` |
| H-08 (web) | «No encontramos ese lugar» y un enlace al mismo formulario | Vuelve al paso 2 con tema e intención, lugar vacío y «No encontramos «Cuzko». Revisa cómo está escrito…» | `guiado.py`, `paginas.py`, `curados/web/textos.yaml` |
| H-09 (web) | «Espera un momento.» con la caja vacía | «Espera unos segundos y vuelve a intentar.», con lo escrito (o los campos del formulario) conservado; la pregunta no se registra | `app.py`, `paginas.py`, `_macros.html`, `aviso.html`, `textos.yaml` |
| H-14 (web) | La opción tocada quedaba «Buscando…» | «Buscando… Huancavelica (departamento)» | `aclaracion.html` |

**Pruebas.** `tests/test_s3_10_textos_motor.py` (21 casos) y `tests/web/test_s3_10_web.py`. Cada regla nueva se vio fallar antes de su arreglo. La regresión Q1–Q4 aprueba como «dueño» la cita de Q1 (H-07) y la tarjeta de 2024 de Q3 (H-05). Q3 es de distrito y no lleva la apertura. No cambia ninguna cifra, semáforo ni confianza. Base web regenerada (`s3-02_generar_base.py`): 52 respuestas cambian de texto, con las mismas cifras, semáforo, confianza y tipo.

## Tarea 3: preguntas con hallazgos en el conjunto de evaluación

Ninguna pregunta del revisor tuvo una mala interpretación: los hallazgos eran de presentación. Las cuatro preguntas por texto con un hallazgo se agregaron a `tests/interprete/evaluacion.yaml` con su resultado esperado y su grabación (`evaluar.py --grabar --solo w01,w04,w05,w07`), para que la evaluación del intérprete y la base web las vigilen:

| id | Hallazgo | Esperado | Lo que responde ahora |
|---|---|---|---|
| w01 | H-01 | nivel_actual · anemia · «Huancavelica» | la oferta de provincia o distrito abre «Ojo al leer» |
| w04 | H-10 | nivel_actual · pobreza · «distrito Ayaviri» | aclaración «Hay varios lugares llamados «Ayaviri»» |
| w05 | H-02 / W-10 | efecto · anemia · «Puno» | apertura de u13 en la capa 1; oferta de X-22 en «Avisos» |
| w07 | H-06 | evolucion · gasto · todo el país | glosario sin «cambio estadísticamente claro» |

w08, w09 y w10 no se resolvieron por el tope de envíos, no porque fallaran; sus aclaraciones (San Juan, Huancabelica, tema) ya están cubiertas por preguntas parecidas del conjunto. Evaluación con grabaciones: 4 de 4. Base web regenerada: solo se suman estas cuatro carpetas.

**Costo en vivo de S3-10:** US$ 0,0427 (revisión) + US$ 0,0305 (grabaciones) = **US$ 0,0732** de US$ 0,50.
