# Revisión de usuario — S2-07

Revisor: subagente independiente (encargo `encargo_s2-07_usuario.md`). No vi la conversación del implementador, el informe del otro revisor ni las carpetas vedadas del intérprete. Material leído: `docs/manual_de_uso.md`, `contrato_respuesta.md` y la línea 4 de la revisión de usuario del slice 1 (4 personas). Escribí 20 preguntas propias (`preguntas_s2-07_usuario.yaml`) antes de correr nada. Corrí `PAP_INTERPRETE_MODO=completar uv run pap preguntar --texto …`: 36 corridas (20 primeras y 16 con `--elegir`). Salidas en `salidas/s2-07_usuario/` (git no las sigue). No edité nada más.

## Veredicto: **apto con observaciones**

Las preguntas con lugar claro y tema claro (u06, u10, u16, u05, u08, u15, u19) se entienden y se contestan bien, y «Entendimos…» dice casi siempre lo que la persona preguntó. Hay dos casos en que la respuesta contesta algo distinto de lo preguntado (u18, u13) y uno en que el mensaje de «no se puede» da una pista falsa (u14). Ninguno llega a bloqueante, pero los tres son altos y conviene corregirlos antes de abrir al público.

## Las 20 preguntas

| id | Persona | Pregunta (resumen) | Resultado |
|---|---|---|---|
| u01 | madre | Anemia en Huancavelica | Aclaración (3 niveles) → respuesta (38,6 %) |
| u02 | madre | «flaquito y bajo de talla», Puno | Aclaración → respuesta (desnutrición crónica, ~9 %) |
| u03 | madre | Anemia en Puno, ¿bajó o subió? | Aclaración → respuesta (sin cambio claro) |
| u04 | madre | «cuanta anemia ay en Ayaviri» | Aclaración (2 distritos) → «no se puede saber» con alternativa SIEN |
| u05 | madre | Desnutrición, Huancavelica o Puno | Aclaración → respuesta (comparación) |
| u06 | periodista | Departamento con más anemia | Respuesta directa (Puno 56,1 %) |
| u07 | periodista | ¿Sirvió el gasto contra la anemia en Cusco? | Aclaración → respuesta parcial (efecto) |
| u08 | periodista | Pobreza Cusco y Puno en 2025 | Aclaración → respuesta (comparación) |
| u09 | periodista | Gasto en Loreto y niños con anemia | Aclaración (dos preguntas) → segunda aclaración (Loreto) → respuesta de gasto |
| u10 | periodista | Cambio de desnutrición desde 2015 | Respuesta directa |
| u11 | regidor | Pobreza en el distrito de San Juan | Aclaración (4 distritos) → respuesta (Mapa de Pobreza 2018) |
| u12 | regidor | Distrito de Puno con más desnutrición | Aclaración → no se puede |
| u13 | regidor | Cuánto gastó el gobierno en anemia en Lima | Aclaración (3 ámbitos) → respuesta de gasto |
| u14 | regidor | Anemia en Huancavelica en 2019 | Aclaración → no se puede |
| u15 | regidor | Pobreza «Cuzco» vs Arequipa | Aclaración («No encontramos «Cuzco»») → respuesta |
| u16 | estudiante | % de menores de 5 con desnutrición | Respuesta directa |
| u17 | estudiante | ¿Por qué hay tanta anemia? | No se puede (fuera de alcance) |
| u18 | estudiante | ¿El gasto en nutrición redujo la desnutrición en Huancavelica? | Aclaración → respuesta de efecto sobre **anemia** |
| u19 | estudiante | Evolución de la pobreza en Ucayali | Aclaración → respuesta |
| u20 | estudiante | «Pobreza en Pnuo» | Mensaje «No encontramos ese lugar» |

## Hallazgos

Resumen: 0 bloqueantes, 3 altos, 6 medios, 3 bajos.

**H1 — ALTO — u18.** La pregunta es por la desnutrición crónica. «Entendimos: si en el departamento de Huancavelica el gasto público en salud y nutrición infantil tuvo efecto» ya no dice desnutrición. La respuesta empieza «No se puede saber si el gasto contra la anemia sirvió en Huancavelica» y trae cifras de anemia; la palabra «desnutrición» solo aparece en el título que repite la pregunta. Contesta otra pregunta sin avisar el cambio de tema. Propuesta: si el tema pedido no admite `efecto`, decir primero «No podemos decir si el gasto redujo la desnutrición crónica; esta pregunta solo la respondemos para anemia» y ofrecer la de anemia como alternativa; el «Entendimos» debe nombrar el tema pedido.

**H2 — ALTO — u13.** «¿Cuánto gastó el gobierno en anemia en Lima?» → «Entendimos: cuánto hay de gasto público en salud y nutrición infantil en Lima Metropolitana»; respuesta «S/ 260,6 millones es lo que se gastó en 2025 en servicios de salud y nutrición infantil». Una persona lee esos 260,6 millones como «lo gastado en anemia» y como «lo que gastó el gobierno» (la frase «No incluye a las entidades nacionales con sede en Lima» está, pero después de la cifra). Propuesta: abrir con «No tenemos el gasto solo en anemia: esta cifra es de todos los servicios de salud y nutrición infantil, y no incluye lo que gastan las entidades nacionales», y poner la cifra después.

**H3 — ALTO — u14.** «No hay datos de anemia de 2019 con la forma de medir actual… Tenemos datos de anemia: con la forma de medir actual, 2024 y 2025; con la anterior, de 2015 a 2025. De otros años no hay datos incorporados.» 2019 está dentro de 2015–2025 con la forma anterior, pero la frase final y «Puedes preguntar por ese año [2025]» llevan al regidor a creer que 2019 no existe. Propuesta: ofrecer directamente «Sí tenemos 2019 con la forma anterior de medir (no se compara con 2024–2025). ¿Quieres verla?», o quitar «De otros años no hay datos incorporados» cuando el año cae en el rango de la forma anterior.

**H4 — MEDIO — u09.** Pregunta doble (gasto en Loreto y niños con anemia). La aclaración obliga a elegir una sola («1) anemia, 2) gasto»), la persona queda con la otra mitad sin respuesta ni aviso de que debe repetir. Además, tras elegir viene otra aclaración (Loreto departamento/provincia) y `--elegir 2` no la resuelve: hizo falta `--elegir 2,1`, que ninguna pantalla explica para este caso. Propuesta: decir en la opción «luego puedes preguntar la otra» y aclarar en el texto «si te vuelve a preguntar por el lugar, escribe un número por cada pregunta, por ejemplo --elegir 2,1».

**H5 — MEDIO — u12.** «¿Qué distrito de Puno tiene más desnutrición crónica?» pregunta primero «Hay varios lugares llamados «Puno»» aunque la persona quería los distritos *dentro* de Puno. Luego «No podemos mostrar qué lugares tienen el valor más alto… el orden que calculamos es solo para todo el país. Por ahora no tenemos una comparación para ofrecerte. Las comparaciones entre lugares… se hacen con todo el país a la vez». Tres oraciones dicen lo mismo, no hay «lo más cercano» (por ejemplo, la cifra de desnutrición del departamento de Puno) y la ficha dice «nada sobre desnutrición crónica», que es demasiado. Propuesta: no repreguntar el lugar cuando la intención es «dentro de»; una sola oración de motivo; ofrecer la cifra de Puno departamento.

**H6 — MEDIO — u20.** «Pobreza en Pnuo» → «No encontramos ese lugar. Revisa cómo está escrito o dinos el departamento, la provincia o el distrito.» No repite lo que escribió ni sugiere «Puno», aunque con «Cuzco» (u15) sí ofreció «¿Quisiste decir…?». La salida es inconsistente. Propuesta: sugerir el lugar más parecido, o al menos repetir «No encontramos «Pnuo»».

**H7 — MEDIO — u07.** «Entendimos: si … el gasto público en salud y nutrición infantil tuvo efecto» omite la anemia, pero la respuesta dice «el gasto contra la anemia». La persona preguntó por anemia y el «Entendimos» no lo confirma. Además «con al menos una medición de hemoglobina… (de cada 100)… entre 54 % y 58 %» es difícil de leer. Propuesta: que «Entendimos» nombre el resultado (anemia) y la cobertura se diga en una frase corriente («de cada 100 niños, entre 54 y 58 se midieron la hemoglobina»).

**H8 — MEDIO — u04.** «No se puede saber cuántos niños de Ayaviri tienen anemia…» seguido de «alrededor de 10 % (entre 7 % y 12 %)». La madre se queda con «10 %», aunque el texto advierte que no es la cifra de todos los niños y que no debe leerse como «poca anemia». El texto aclara, pero la cifra más visible es la que no responde. Propuesta: poner la cifra después de la advertencia, o decir «solo sabemos de los niños a los que midieron la hemoglobina: 10 %».

**H9 — MEDIO — u11.** «entre 45 % y 64 % es la cifra de pobreza monetaria por distrito (estimación del INEI) en San Juan (Cajamarca, Cajamarca) en 2018». La oración se lee mal (¿qué es el 45–64?), el «Entendimos» no avisa que será un dato de 2018 y el semáforo es rojo. Propuesta: «Entre 45 y 64 de cada 100 personas eran pobres en San Juan en 2018» y mencionar el año en «Entendimos».

**H10 — MEDIO — u01, u02, u03, u12, u18 (aclaraciones de lugar).** Para una madre, «Puno (departamento) / (provincia) / (distrito)» no se distingue sin saber qué es cada uno; falta «toda la región de Puno». Propuesta: «Puno (toda la región)» como primera opción, o una línea que explique la diferencia.

**H11 — BAJO — u02.** «¿en Puno hay muchos niños así?»: la respuesta («alrededor de 9 %») no dice si es mucho ni da un punto de comparación (país: 12,1 %, u16). Propuesta: añadir la cifra del país como referencia o decir que no se puede juzgar «mucho».

**H12 — BAJO — u17.** «Todavía no respondemos ese tipo de pregunta» sugiere que pronto sí; «No permite concluir: nada sobre ese tema» y «Territorio: sin lugar identificado» sobran. Propuesta: «No respondemos preguntas de “por qué”» y quitar la ficha en este caso.

**H13 — BAJO — u05, u08, u15.** «No leas esta cifra como exacta» va en singular aunque hay dos cifras. Propuesta: «estas cifras».

## Lo que funciona bien

- «Entendimos…» fiel a la pregunta en u01, u03, u05, u06, u08, u10, u15, u16, u19.
- La respuesta corta de u06 y u10 dice quién es el más alto y si el cambio es claro, sin jerga.
- Las aclaraciones de homónimos (u04, u11, u13) se distinguen por provincia y departamento.
- u17 y u14 dicen primero lo que no se puede y ofrecen salida.

## Respuesta del implementador (5/11/2026)

| Hallazgo | Dónde está | Qué se hizo |
|---|---|---|
| H1 (alto, u18) | Intérprete: el LLM eligió `tema: gasto_publico` y el motor responde el efecto del gasto contra la anemia | **Corregido**: regla nueva del prompt por categoría (efecto y cruce: si se nombra otro problema, el tema es ese problema), versión 3 en `cambios_prompt.md`. Verificado en vivo: «Entendimos: si en el departamento de Huancavelica el gasto contra la desnutrición crónica tuvo efecto» y la respuesta habla de la desnutrición. Entra al conjunto como `s07a` |
| H2 (alto, u13) | Motor del slice 1 (plantilla del gasto) | Fuera del slice 2 (README: sin cambios del motor ni de las plantillas). Consulta E-09 |
| H3 (alto, u14) | Motor del slice 1 (texto «no se puede» del año) | Fuera del slice 2. Consulta E-09 |
| H4 (u09), H10 | Aclaraciones del intérprete y del territorio | Registrados en E-09 para el slice 3 (formulario guiado) |
| H5, H6, H8, H9, H11–H13 | Motor y resolver del slice 1 | Registrados en E-09 |
| H7 (u07) | «Entendimos» de `efecto` con el gasto (textos del slice 2) | Medio; registrado en E-09 |
