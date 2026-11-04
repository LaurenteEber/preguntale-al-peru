# Verificación de las correcciones de S1-09

Verificador: subagente nuevo, distinto del auditor, del revisor de usuario y del implementador (P-06). Encargo: `encargo_s1-09_verificador.md`. Rama `slice-1`, HEAD `018b186`; commit de comparación `249ea7a`. No editó ningún archivo. Respuestas en `salidas/s1-09_verificador/` (fuera de git).

## Veredicto: **correcciones verificadas, sin regresiones de cifras, semáforos, confianza ni reglas en Q1–Q4. Queda un defecto nuevo en la CLI (N-1).**

Los 10 hallazgos bloqueantes o altos están corregidos: 6 sin reservas y 4 con observación (H3, H4, H5, H7). La corrección de H3 introdujo N-1, pequeño pero bloqueante según los criterios de verificación (ignora sin avisar un valor que la persona escribió).

## Hallazgos bloqueantes y altos

| ID | Estado | Evidencia (`uv run pap preguntar … --salida salidas/s1-09_verificador/<n>`) |
|---|---|---|
| A-H1 (bloqueante) | corregido | `evolucion desnutricion_cronica "Huancavelica" --elegir 1 --anio 2020` → «No podemos decir cómo cambió hasta 2020: … 2020 no se compara con otros años», 32,4 % sin «pasó de», aviso de R-ENC-13 en la capa 2; `"Perú" --hasta 2020` igual con 12,1 %. Comparaciones válidas sin cambio (Huancavelica 2015→2025 y Perú 2015→2021 «bajó de forma estadísticamente clara»). `planificador.py:67-76` |
| A-H2 (alto) | corregido (aviso); datos por C-05 | `evolucion gasto_publico "Perú" --desde 2023` → «Pediste la serie desde 2023, pero 2023 no se compara con 2025: … Empezamos en 2024.»; `desnutricion "Perú" --desde 2020` → «… Empezamos en 2021.» |
| A-H3 (alto) | corregido | `evolucion anemia "Perú"`, cita 2015 → «Fuente: Pregunta al Perú, cálculo propio con ENDES 2015 (INEI); el INEI publicó 43,5 %.»; desnutrición 2015 «…el INEI publicó 14,4 %.»; la cita de 2025 sigue siendo el documento del INEI. `capas.py:44-47` |
| H1 (bloqueante) | corregido | `comparacion pobreza "Cusco" --comparar-con "Puno" --elegir 1,1` → «fue mayor en Puno que en Cusco, con una diferencia estadísticamente clara», dos cifras en capa 1; `"Lima Región" --comparar-con "Callao"` → «sin diferencia estadísticamente clara» |
| H2 (bloqueante) | corregido | `identificar_extremo anemia --nivel departamento` → «En 2025, Puno es el departamento con la anemia … más alta, con diferencia estadísticamente clara frente a los demás», cifra clave 56,1 %, sin «No los ordenes», «Territorio: todos los departamentos del país»; desnutrición (8 departamentos) como antes |
| H3 (alto) | corregido con observación | `--elegir 1,1` termina (código 0); la pista lo explica; «No encontramos ese lugar» ya no menciona `--elegir`; `1,9` → «✘ La opción 9 no existe» (código 1). Observación: N-1 |
| H4 (alto) | corregido con observación | `nivel_actual anemia "San Juan" --elegir 3` → «San Juan (Cajamarca, Cajamarca)» en corta, cifra clave, «Ojo» y cita. Observación: límites «Territorio: distrito de San Juan» |
| H5 (alto) | corregido con observación | Lima Metropolitana → «S/ 260,6 millones es lo que se gastó en 2025 … registrado por entidades con sede en Lima Metropolitana» y «No incluye a las entidades nacionales con sede en Lima…»; sin «PAN» ni «devengado» en capa 1. Observación: esa última frase sale dos veces (Ojo y tarjeta) |
| H6 (alto) | corregido | `"Putis"` → «No tenemos registros de anemia en Putis. Eso no quiere decir que no haya casos.» |
| H7 (alto) | corregido con observación | `--anio 2010` → «Sí tenemos la cifra de 2025 … con la forma de medir actual, 2024 y 2025; con la anterior, de 2015 a 2025.», sin «de de». Observación (previa): con `--anio 2018` empieza «No tenemos datos de anemia de 2018» y luego dice que la forma anterior tiene 2015–2025 |

Medios y bajos comprobados: A-H4, A-H7, H8, H10, H13, H16, H19, corregidos.

## Prueba de diferencia entre territorios (R-ENC-11)

Solo con las dos cifras publicables (`plantillas.py:604-605`), mismo indicador, año y medida (proporción), de encuesta, con error estándar y sin que un lugar contenga al otro (`plantillas.py:611-612`). «Mayor/menor» solo con `significativa` (p < 0,05; `plantillas.py:633`, `respuesta.py:169`). Recalculada con el cubo:

| Comparación | z | p | Respuesta |
|---|---|---|---|
| Cusco–Puno | −5,72 | 1e-08 | «mayor» |
| Puno–Lima Metropolitana | 8,08 | 6e-16 | «mayor» |
| Tacna–Moquegua (borde) | −2,10 | 0,036 | «mayor en Moquegua» |
| Lima Región–Callao | 1,04 | 0,30 | «sin diferencia» |
| Lima Metropolitana–Callao, desnutrición | −0,99 | 0,32 | «sin diferencia» |

Sin prueba y sin dirección (correcto): Lima Metropolitana frente a Perú (contenido), SIEN Ayaviri frente a San Juan de Lurigancho (registro), Mapa Melgar frente a Huanta (modelo), gasto Callao frente a Lima Metropolitana. Observación de método: usa la normal (z), no la t con `gl_prueba = min(gl_a, gl_b)` que nombra R-ENC-11; misma fórmula que entre años; en Tacna–Moquegua (gl = 89) la t da p = 0,039, misma conclusión.

## Pruebas corridas

| Comando | Resultado |
|---|---|
| `uv run pytest -q …test_regresion_q1_q4.py …test_matriz_cobertura.py …test_s1_09_correcciones.py` | 74 passed |
| `uv run pytest -q` | 732 passed |
| `uv run python codigo/ingesta/tests/matriz/correr.py --salida salidas/s1-09_verificador/matriz …` | 5 086 casos, 0 con fallos, 0 errores; igual a `evidencia/matriz.md` salvo el encabezado |
| `git diff 249ea7a HEAD --stat -- 04_reglas/reglas.json codigo/capa0/datos/ codigo/ingesta/tests/referencias/ backlog/slice-1/evidencia/regresion` | vacío |

`test_regresion_q1_q4.py:171-213` compara por clave cada campo de las cifras, el semáforo, la confianza, la parcialidad, las comparaciones bloqueadas y las reglas de acción firme contra `referencias/q1..q4.json`: pasa sin diferencias nuevas.

## Regresiones

Ninguna en Q1–Q4 (cifras, semáforos, confianza, reglas de bloqueo).

## Defectos nuevos

- **N-1 (de la corrección de H3; bloqueante según los criterios de verificación):** los números de más en `--elegir` se descartan sin aviso y sale código 0 (`--comparar-con "Puno" --elegir 1,1,1`; `nivel_actual pobreza "Cusco" --elegir 1,2`). Propuesta: error con código 1 («Escribiste 3 números pero solo había 2 lugares por elegir»).

## Advertencias (previas)

- `test_cli_preguntar.py:121` borra toda la carpeta `salidas/` si no existía `salidas/preguntar` (desde S1-06, `65d0c67`).
- Comparar un lugar consigo mismo deja un hueco: «…en Puno y en : 56,1 %…».
- El año dentro del rango de la forma anterior se contradice (observación de H7, `--anio 2018`).

## Notas

C-05 se cerró durante la verificación; al agregar 2023 a `comparable_con` cambian los textos y pruebas de A-H2 sobre el gasto. El verificador dejó por error un archivo vacío `salidas_tmp_dummy` en la raíz (lo retira el implementador) y carpetas temporales fuera del repositorio. Pruebas de regresión propuestas: N-1 (`--elegir` con números de más → código 1), H1 borde Tacna–Moquegua, H1 sin prueba no dice mayor ni menor (SIEN; lugar contenido), H7 año 2018 sin contradicción.
