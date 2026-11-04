# Revisión de usuario — S1-09

Revisor: subagente independiente (encargo: `encargo_s1-09_revisor.md`). Rama `slice-1`, commit `cc7f58b`. No vi la conversación del implementador ni los informes de los otros revisores.
Material leído: `03_auditoria/revision_usuario/informe_revision_usuario_q1_q4.md`, que define las 4 personas (madre de Huancavelica/Puno, periodista, regidor o funcionario, estudiante o docente), y `00_proyecto/piloto/contrato_respuesta.md`.
Lectura: el `.md` que escribe la CLI, por capas. Las aclaraciones no escriben `.md`: las leí en la terminal. No edité ningún archivo del repositorio. Las salidas están en `salidas/s1-09_revisor/`, que git no sigue.

## Veredicto

**No apto.** Hay **2 hallazgos bloqueantes** (H1 y H2) y **5 altos** (H3 a H7):

- **Comparación (H1):** dice que la diferencia entre Cusco 18,8 % y Puno 37,5 % «puede deberse al azar», y rotula el segundo lugar como «no se compara».
- **Lugar más alto con un solo departamento (H2):** sale «son un departamentos, sin diferencias… entre ellos» y la capa 1 no nombra a Puno.

Las respuestas de nivel, evolución y efecto que siguen el patrón de Q1–Q4 se leen bien en general. Después de corregir H1 a H7, el resultado esperable es «apto con observaciones».

## Las 20 respuestas

Todas se generaron con `uv run pap preguntar … --salida salidas/s1-09_revisor/<n>`.

| n | Comando (opciones) | Tipo |
|---|---|---|
| 01 | `--intencion nivel_actual --tema anemia --territorio "Huancavelica"` | aclaración (3 niveles) |
| 02 | `--intencion nivel_actual --tema pobreza --territorio "Lima"` | aclaración (Lima) |
| 03 | `--intencion nivel_actual --tema anemia --territorio "San Juan"` | aclaración (homónimo, 4 distritos) |
| 04 | `--intencion nivel_actual --tema anemia --territorio "Ayaviri"` | aclaración (homónimo, 2 distritos) |
| 05 | `--intencion nivel_actual --tema anemia --territorio "Huancavelica" --elegir 1` | respondida, departamento, ENDES |
| 06 | `--intencion nivel_actual --tema pobreza --territorio "Lima" --elegir 1` | respondida, Lima Metropolitana, ENAHO |
| 07 | `--intencion nivel_actual --tema anemia --territorio "San Juan" --elegir 3` | respondida, distrito, SIEN + ENDES |
| 08 | `--intencion evolucion --tema anemia --territorio "Puno" --elegir 1` | respondida, evolución, departamento |
| 09 | `--intencion nivel_actual --tema desnutricion --territorio "Ayaviri" --elegir 2` | no se puede (nivel no válido) |
| 10 | `--intencion identificar_extremo --tema pobreza --nivel distrito --territorio "Perú"` | respondida, lugar más alto, Mapa 2018 + ENAHO |
| 11 | `--intencion identificar_extremo --tema anemia --nivel departamento --territorio "Perú"` | respondida, lugar más alto, departamentos |
| 12 | `--intencion efecto --tema gasto --territorio "San Juan de Lurigancho"` | respondida, efecto (gasto + SIEN + ENDES) |
| 13 | `--intencion comparacion --tema pobreza --territorio "departamento de Cusco" --comparar-con "departamento de Puno"` | respondida, comparación (ver H3: con «Cusco»/«Puno» no se llega) |
| 14 | `--intencion cruce --tema anemia --territorio "Ayacucho" --elegir 1` | respondida, cruce, departamento |
| 15 | `--intencion evolucion --tema pobreza --territorio "Uchuraccay"` | no se puede (serie de un solo año) |
| 16 | `--intencion nivel_actual --tema anemia --territorio "Perú" --anio 2010` | no se puede (año sin datos) |
| 17 | `--intencion identificar_extremo --tema pobreza --nivel distrito --territorio "Perú" --dentro-de "Puno" --elegir 1` | no se puede (lugar más alto «dentro de» un lugar) |
| 18 | `--intencion nivel_actual --tema desnutricion --territorio "Capachica"` | no se puede (nivel no válido) |
| 19 | `--intencion nivel_actual --tema anemia --territorio "Putis"` | no se puede (sin registros) |
| 20 | `--intencion nivel_actual --tema gasto --territorio "Lima Metropolitana"` | respondida, gasto, Lima Metropolitana |

En total: 10 respondidas, **6 «no se puede»** (09, 15–19) y **4 aclaraciones** (01–04). Pruebas de apoyo que no cuentan entre las 20 (`salidas/s1-09_revisor/extra/`): anemia en Perú con `--anio 2018` y `--anio 2024`; lugar más alto de desnutrición por departamento; comparación de anemia entre Puno y Lima Metropolitana.

## Malas lecturas probables por respuesta y persona

«—» significa que no encontré una mala lectura probable.

| n | Madre | Periodista | Regidor / funcionario | Estudiante / docente |
|---|---|---|---|---|
| 01 | — (las opciones se distinguen) | — | — | — |
| 02 | «Si no elijo, me responde Lima Metropolitana»: falso en la CLI (H10) | Puede pensar que «Callao» es parte de Lima | Echa de menos «todo el departamento de Lima» | — |
| 03 | — | — | — | — |
| 04 | — | — | — | — |
| 05 | «Forma de medir vigente desde 2024» no le dice nada (H15) | — | — | No encuentra en el glosario qué cambió en 2024 (H15) |
| 06 | — | — | «Nada sobre provincias»: Lima Metropolitana ya es una provincia (H18) | — |
| 07 | — | Titular «San Juan: 15 % de anemia» sin decir cuál San Juan; la cita tampoco lo dice (H4) | Si es de otro San Juan, cree que el dato es de su distrito (H4) | Cita «San Juan, 2025», ambiguo entre 4 distritos (H4) |
| 08 | — | «Bajó de 76,1 % a 56,1 %» (el «Ojo» lo previene) | — | No ve la cifra de 2024 con la que se compara 2025 (H11) |
| 09 | «En Ayaviri por distrito» le confunde; no sabe cómo «preguntar por ese lugar» (H13) | — | — | — |
| 10 | — | «Cajamarca, la región más pobre (41,0 %)» (H21) | — | — |
| 11 | No sabe qué departamento es: la capa 1 no lo nombra (H2) | «Varios departamentos empatan en anemia»: falso, el grupo es solo Puno (H2) | No sabe si su departamento está en el grupo (H2) | Lee «Territorio: departamento de Perú» (H2) |
| 12 | Confianza «baja», pero no ve la cifra a la que se refiere (H12) | «Estos datos muestran… cómo cambió el indicador» contradice «no podemos mostrar cómo cambió» (H12) | No sabe a qué gasto se refiere «este gasto» en el 5 % (H12) | — |
| 13 | «No se puede decir si en Puno hay más pobreza que en Cusco» (H1) | No puede titular lo evidente (37,5 % frente a 18,8 %); el texto dice «no se compara» (H1) | Concluye que Cusco y Puno están igual (H1) | Lee que la diferencia «puede deberse al azar» con intervalos que no se tocan (H1) |
| 14 | No ve la anemia que pidió: solo ve el gasto (H9) | «Ayacucho gastó S/ 93,4 millones contra la anemia» (el «Ojo» lo frena) | «Unidades ejecutoras» en la capa 1 (H9) | La tarjeta de anemia dice «no se compara», pero el cruce prometía lado a lado (H9) |
| 15 | «Puedo preguntar cuánto hay ahora» y recibe una cifra de 2018 (H8) | — | — | — |
| 16 | — | «No hay datos de anemia antes de 2024» (H7) | — | Cree que no hay serie 2015–2023, y la evolución sí la muestra (H7) |
| 17 | — | — | «Territorio: sin lugar identificado», aunque escribió Puno (H13) | — |
| 18 | Igual que 09 (H13) | — | — | — |
| 19 | «En Putis no hay anemia» (H6) | «Putis, sin casos de anemia» (H6) | Cree que su distrito no tiene el problema (H6) | — |
| 20 | «PAN» le suena a pan; «devengado» no lo entiende (H5) | «Lima Metropolitana gastó S/ 260,6 millones en nutrición infantil», como si fuera todo el gasto (H5) | Igual que el periodista (H5) | Encuentra otro alcance para la misma cifra en la 12 (H5) |

## Hallazgos

### Bloqueantes

**H1 — Bloqueante. La comparación dice que la diferencia puede ser azar y que el segundo lugar no se compara (13; también Puno–Lima Metropolitana).** Frases: «No concluyas que un lugar tiene más que el otro solo por la diferencia entre las cifras: puede deberse al azar de la encuesta.»; bajo la tarjeta de Puno: «*Otro territorio: no se compara con la cifra clave.*»; la capa 1 solo muestra «18,8 %… en Cusco» y la corta no dice cuál tiene más. Los intervalos del INEI no se tocan (Cusco 15,2–22,3; Puno 32,1–42,8); lo mismo en anemia (Puno 56,1 %, Lima Metropolitana 25,3 %). El JSON no trae ninguna prueba de diferencia (`comparacion: None`). Propuesta: corta «En 2025 la pobreza monetaria fue más alta en Puno (37,5 %) que en Cusco (18,8 %)», con «la diferencia es estadísticamente clara / no es clara» según la prueba de diferencia; las dos cifras en la capa 1; sin la etiqueta «no se compara» cuando fuente y año son los mismos; el «Ojo» depende de la prueba. Si calcular la prueba exige una decisión estadística, es consulta tipo C; mientras tanto, «puede deberse al azar» no debe aparecer cuando los intervalos no se tocan.

**H2 — Bloqueante. Lugar más alto con un grupo de un solo departamento (11).** Frases: «El grupo con la anemia en niñas y niños de 6 a 35 meses más alta en 2025 son un departamentos, sin diferencias estadísticamente claras entre ellos.»; «No los ordenes uno por uno…»; en la capa 2, Puno (56,1 %) con la etiqueta «no se compara con la cifra clave» sin cifra clave; límites «Territorio: departamento de Perú». La capa 1 no nombra a Puno y afirma un empate que no existe (con desnutrición, 8 departamentos, sale bien). Propuesta: corta «En 2025, Puno es el departamento con la anemia más alta en niñas y niños de 6 a 35 meses.»; cifra clave 56,1 % (ENDES 2025); una viñeta de «Ojo»; límites «Territorio: todos los departamentos del Perú»; sin «No los ordenes» con un solo lugar.

### Altos

**H3 — Alto. Una comparación entre dos nombres ambiguos no se puede terminar con la CLI.** Con `--territorio "Cusco" --comparar-con "Puno" --elegir 1`, el número resuelve Cusco y vuelve a preguntar por Puno («Para responder, repite el comando con --elegir <número>.»), en ciclo. Escribir la etiqueta ofrecida «Puno (departamento)» da «No encontramos ese lugar… repite el comando con --elegir <número>» sin opciones. Propuesta: para el segundo lugar, «escríbelo como en la opción, por ejemplo: --comparar-con "departamento de Puno"», o aceptar `--elegir 1,1`; en «No encontramos ese lugar», quitar la línea de `--elegir`.

**H4 — Alto. Un homónimo aclarado vuelve a quedar ambiguo en la capa 1 y en la cita (07).** «No se puede saber cuántos niños de San Juan tienen anemia…», «…en establecimientos públicos de San Juan…», cita «…San Juan, 2025…». Propuesta: «San Juan (Cajamarca, Cajamarca)» en la corta, la cifra clave y la cita cuando el lugar pasó por una aclaración de homónimo.

**H5 — Alto. Gasto de Lima Metropolitana con jerga en la capa 1 y sin alcance (20).** «**S/ 260,6 millones** es la cifra de gasto en servicios de salud y nutrición infantil que antes eran del PAN (devengado) en Lima Metropolitana en 2025.» Usa «devengado» y «PAN» (regla 5 del contrato) y no dice lo que la 12 sí dice de la misma cifra («registrado por unidades ejecutoras con sede en Lima Metropolitana», «No incluye a las entidades nacionales con sede en Lima…»). Propuesta: «En 2025 se gastaron S/ 260,6 millones en servicios de salud y nutrición infantil en Lima Metropolitana. Es lo que registran las entidades con sede en Lima Metropolitana; no incluye a las entidades nacionales que atienden a todo el país.»

**H6 — Alto. «Sin registros» se lee como «no hay anemia» (19).** «No tenemos registros de anemia en Putis.»; la aclaración clave solo está en la capa 2. Propuesta: «No tenemos registros de anemia de Putis en 2025: la fuente no trae datos de ese distrito. Eso no quiere decir que no haya niños con anemia.»

**H7 — Alto. El «no se puede» por año dice algo falso sobre los datos (16; también `--anio 2018`).** «Sí tenemos la cifra de 2024 para Perú.»; «Las cifras de anemia que usamos son de de 2024 a 2025. De otros años no hay datos incorporados.» La 08 muestra 2015 y 2025 con la forma anterior; ofrece 2024 cuando lo último es 2025; «de de». Propuesta: «No tenemos datos de anemia de 2010. Con la forma de medir actual tenemos 2024 y 2025; con la anterior, desde 2015. Puedes preguntar por 2025.» Ofrecer 2018 con la forma anterior sería consulta tipo C; el texto se puede corregir sin esa decisión.

### Medios

**H8 — Medio (15).** «Sí tenemos la cifra de 2018 para Uchuraccay. Puedes preguntar por cuánto hay ahora.» → «Puedes preguntar por la cifra de 2018, la última que hay por distrito.»

**H9 — Medio. El cruce promete «lado a lado» pero la capa 1 solo muestra el gasto (14).** «Estas cifras se muestran lado a lado…»; tarjeta de anemia «no se compara con la cifra clave»; «registrado por unidades ejecutoras con sede en Ayacucho» en capa 1; título «Niñas y niños de 6 a 35 meses con al menos una medición… (de cada 100) (Ayacucho)». Propuesta: corta «Mostramos dos cifras de Ayacucho, sin decir que una explique la otra: lo gastado y la anemia.»; etiqueta «Se muestra junto al gasto, no lo explica»; «registrado por entidades con sede en Ayacucho»; título «¿A cuántos niños se les mide la hemoglobina?».

**H10 — Medio (02).** «Si no eliges, usamos Lima Metropolitana.» y la CLI sale con código 2 sin responder. Quitar la frase o responder con Lima Metropolitana avisándolo.

**H11 — Medio (08).** «…ni entre 2024 y 2025 con la forma de medir actual…» sin mostrar 2024. Agregar 2024 a la tarjeta de la capa 2 («fue X % en 2024 y 56,1 % en 2025»).

**H12 — Medio. Respuesta de efecto (12).** «Estos datos muestran qué se gastó y cómo cambió el indicador» frente a «no podemos mostrar cómo cambió en el distrito» (texto de regla: consolidador); «En el departamento de Lima solo alrededor del 5 % de este gasto…» ambiguo; confianza «baja» explicada por una cifra fuera de la capa 1. Propuesta: frase de regla «…y, cuando se puede, cómo cambió la anemia, pero no si uno causó lo otro»; «Del gasto de este tipo en todo el departamento de Lima, solo alrededor del 5 % se puede ubicar…».

**H21 — Medio (10).** La lista de departamentos con porcentajes invita a ordenarlos («Ayacucho (33,7 %), Cajamarca (41,0 %)… Loreto (40,1 %)…»); el texto ya lo aclara. Propuesta: solo el rango del grupo y los porcentajes en la sección para citar.

### Bajos

- **H13 (09, 17, 18).** «…en Ayaviri por distrito», «Territorio: sin lugar identificado» (en 17 se dio Puno), aclaración sobre Puno antes de decir que «dentro de» no se responde. Propuesta: «No podemos dar una cifra de desnutrición crónica para el distrito de Ayaviri (Melgar, Puno)…», «Territorio: Puno (departamento)»; rechazar «dentro de» antes de aclarar.
- **H14 (05, 06, 13, 20).** Sujeto repetido entre la corta y la cifra clave. Propuesta: «En 2025, en Huancavelica, la anemia en niñas y niños de 6 a 35 meses fue:».
- **H15 (05, 11).** «Forma de medir vigente desde 2024» sin entrada de glosario: agregar «forma de medir la anemia».
- **H16 (09, 15–19).** Título «Cómo citar» vacío en los «no se puede»: quitarlo o «Esta respuesta no publica cifras».
- **H17 (07, 12).** «solo sabemos de los que se les midió la hemoglobina» → «de aquellos a quienes se les midió»; «tamizados» en citas → «con hemoglobina medida».
- **H18 (06).** «nada sobre provincias o distritos concretos… para Lima Metropolitana» → «nada sobre distritos concretos de Lima Metropolitana».
- **H19 (01–04).** Tres frases distintas para la aclaración: usar siempre «Hay varios lugares llamados «X». ¿Cuál quieres?».

H20 no se usa.

## Lo que se lee bien

- Las aclaraciones de nivel y de homónimo: opciones con provincia y departamento, distinguibles y con tildes.
- La evolución (08): dice primero que no hay cambio claro y advierte sobre el cambio en la forma de medir.
- La respuesta de efecto (12): dice primero que no se puede, aclara el alcance del gasto y el motivo de la confianza.
- El lugar más alto por distrito (10): dice primero que no se puede, orden alfabético explícito y aviso de no comparar con los departamentos.
- Los «no se puede» empiezan por lo que no hay y casi siempre dicen qué sí hay. Sin códigos internos en las capas 1 a 3.

## Segunda revisión (tras las correcciones)

Commit `1603698` de `slice-1`. Las 20 respuestas regeneradas con los mismos comandos (la 13 ahora con `--territorio "Cusco" --comparar-con "Puno" --elegir 1,1`), en `salidas/s1-09_revisor_r2/`, releídas con las 4 personas. Siete pruebas de apoyo en `extra/` (comparación sin `--elegir`, con `--elegir 1` y con «Puno (departamento)»; más alto de pobreza dentro de Puno; anemia Perú `--anio 2018`; anemia Puno–Lima Metropolitana; pobreza Huancavelica–Ayacucho). Sin pytest, sin ediciones, sin leer la auditoría estadística.

### Veredicto

**Apto con observaciones.** Los 2 bloqueantes (H1, H2) y los 5 altos (H3 a H7) están corregidos. Sin malas lecturas nuevas altas ni bloqueantes. Siguen abiertos 4 medios (H9, H11, H12, H21) y varios bajos; ninguno lleva a una conclusión falsa en la capa 1.

### Estado de los hallazgos

| Hallazgo | Gravedad | Estado | Evidencia |
|---|---|---|---|
| H1 | bloqueante | **corregido** | 13: «En 2025, la pobreza monetaria fue mayor en Puno que en Cusco, con una diferencia estadísticamente clara.»; cifra clave «18,8 %… en Cusco en 2025, frente a 37,5 % en Puno»; sin «no se compara» ni «puede deberse al azar». Puno–Lima «mayor…»; Huancavelica–Ayacucho «sin diferencia estadísticamente clara» con «“Sin diferencia clara” no quiere decir “igual”» |
| H2 | bloqueante | **corregido con observación** | 11: «En 2025, Puno es el departamento con la anemia… más alta, con diferencia estadísticamente clara frente a los demás.»; 56,1 %; «Territorio: todos los departamentos del país». Queda el aviso «…no tiene sentido ordenarlos uno por uno» (N2) |
| H3 | alto | **corregido con observación** | «…escribe un número por lugar, en orden: por ejemplo --elegir 1,1.»; `--elegir 1,1` responde; «No encontramos ese lugar…» ya no pide un número. La etiqueta «Puno (departamento)» sigue sin reconocerse |
| H4 | alto | **corregido** | 07: «…cuántos niños de San Juan (Cajamarca, Cajamarca) tienen anemia…»; cita «…San Juan (Cajamarca, Cajamarca), 2025» |
| H5 | alto | **corregido con observación** | 20: «**S/ 260,6 millones** es lo que se gastó en 2025 en servicios de salud y nutrición infantil, registrado por entidades con sede en Lima Metropolitana.»; «No incluye a las entidades nacionales con sede en Lima, que atienden a todo el país.» La cita sigue con «que antes eran del PAN (devengado)» (N4) |
| H6 | alto | **corregido** | 19: «No tenemos registros de anemia en Putis. Eso no quiere decir que no haya casos.» |
| H7 | alto | **corregido con observación** | 16: «No hay datos de anemia de 2010 con la forma de medir actual. … Sí tenemos la cifra de 2025 para Perú.»; capa 2 con los años de cada forma; sin «de de» (N1) |
| H8 | medio | **corregido** | 15: «Sí tenemos la cifra de 2018 para Uchuraccay, la más reciente. Puedes preguntar por ella.» |
| H9 | medio | **no corregido** | 14 sin cambio («Estas cifras se muestran lado a lado…», capa 1 solo con el gasto) |
| H10 | medio | **corregido** | 02: sin «Si no eliges, usamos Lima Metropolitana» |
| H11 | medio | **no corregido** | 08: «…ni entre 2024 y 2025 con la forma de medir actual…» sin la cifra de 2024 |
| H12 | medio | **no corregido** | 12: «Estos datos muestran qué se gastó y cómo cambió el indicador» (texto de regla) y «…solo alrededor del 5 % de este gasto…» |
| H13 | bajo | **corregido con observación** | 17: «Territorio: Puno»; 09 y 18 siguen con «…por distrito» |
| H14 | bajo | **no corregido** | «Esto es lo que dicen los datos oficiales sobre…» |
| H15 | bajo | **no corregido** | 05 y 11 sin la entrada «forma de medir» en el glosario |
| H16 | bajo | **corregido** | «Esta respuesta no publica cifras.» |
| H17 | bajo | **no corregido** | «solo sabemos de los que se les midió la hemoglobina»; «tamizados» en citas |
| H18 | bajo | **no corregido** | 06: «nada sobre provincias o distritos concretos… para Lima Metropolitana» |
| H19 | bajo | **corregido** | «Hay varios lugares llamados «X». ¿Cuál quieres?» |
| H21 | medio | **observación aceptada** | 10: el texto aclara el orden alfabético y el rango del grupo |

### Malas lecturas nuevas (ninguna alta ni bloqueante)

- **N1 — Medio (16, 2018).** «No hay datos de anemia de 2010 con la forma de medir actual.» sugiere que con la anterior sí hay 2010 (la capa 2 lo aclara). Propuesta: «No hay datos de anemia de 2010.» para años sin ninguna serie; «…de 2018 con la forma de medir actual; con la anterior sí.» para años solo de la serie anterior (ofrecer esa cifra es la consulta tipo C de H7).
- **N2 — Bajo (11).** Queda «…no tiene sentido ordenarlos uno por uno» con un grupo de uno; el glosario no explica «diferencia estadísticamente clara».
- **N3 — Bajo (13).** Línea de fuente repetida («ENAHO 2025 (INEI); el INEI publica la misma cifra (18,8 %) · ENAHO 2025 (INEI); …(37,5 %)»); «esta cifra» en singular con dos; la corta nombra primero a Puno y la cifra clave a Cusco.
- **N4 — Bajo (20, 12, 14).** Las citas dicen «que antes eran del PAN (devengado)»; el glosario no aclara que «PAN» es la sigla del Programa Articulado Nutricional.
- **N5 — Bajo (07).** «San Juan (Cajamarca, Cajamarca)» tres veces en la capa 1; límites con dos paréntesis seguidos.
- **N6 — Bajo.** Frase cortada: «En 2025, la pobreza monetaria en Huancavelica y en Ayacucho: sin diferencia estadísticamente clara.»
