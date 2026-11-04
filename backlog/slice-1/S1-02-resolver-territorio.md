# S1-02 — Resolver territorial determinista

## Por qué

Elegir mal el lugar arruina la respuesta, y el LLM del slice 2 no debe decidirlo. Este resolver convierte lo que escribió la persona en un territorio vigente o en una pregunta de aclaración.

## Contexto

- `biblioteca/dimensiones/dim_ubigeo_historico.parquet`: `nombre_mostrado` (con tildes, T-02), `nombre_normalizado`, `nombres_alternos`, `nivel`, `ubigeo_padre`, vigencias.
- `dim_ambito.parquet` (Lima Metropolitana, Lima Región, Área Metropolitana de Lima y Callao, Callao).
- Reglas: T-03 (Lima); R-TERRITORIO-09 (el texto se convierte en un ubigeo único; con cero o varias coincidencias se pregunta: «Huancavelica» es departamento, provincia y distrito); R-LENGUAJE-05 (distrito nuevo).

## Tareas

1. `pap/motor/territorio.py` con `resolver(entrada, fecha=hoy) -> Resuelto | Aclaracion`. Reutiliza la normalización y los índices de nombres que ya usa el validador para R-TERRITORIO-09 (`validador/reglas_etapa1_3.py`: `normalizar_texto`, `_indice_nombres`, `_candidatos`, `NIVEL_PISTA`); si hace falta, se mueven a un módulo común, sin copiarlos. Resuelve departamentos, provincias, distritos vigentes y ámbitos:
   - Emparejamiento exacto sin tildes ni mayúsculas sobre `nombre_normalizado` y `nombres_alternos`; en distritos, solo los vigentes.
   - Coincidencia parcial (`territorio.coincidencia_parcial`): si no hay exacta y todas las palabras del texto están dentro de un nombre o alterno (p. ej. «Albarracin» → «Coronel Gregorio Albarracín Lanchipa»; «Toledo» → «Santa Cruz de Toled», por su alterno), se devuelve siempre `Aclaracion` («¿Quisiste decir…?»), aunque haya una sola opción. La similitud de `difflib` solo sirve para los errores de tipeo.
   - Acepta «distrito, provincia, departamento» en cualquier orden y abreviado («Ayaviri, Melgar»).
   - Homónimos entre niveles: si el texto no dice el nivel, `Aclaracion` (R-TERRITORIO-09: con cero o varias coincidencias se pregunta) con opciones «Huancavelica (departamento)», «Huancavelica (provincia)», «Huancavelica (distrito, provincia de Huancavelica)». Palabras como «departamento», «región», «provincia» o «distrito» en el texto deshacen el empate.
   - Homónimos dentro del mismo nivel («San Juan», «Santa Rosa», «Independencia»): siempre `Aclaracion`, con provincia y departamento en cada opción, con `aclaracion_max_opciones`, `aclaracion_orden` y `aclaracion_exceso` de `parametros_motor.yaml` → `territorio` (si hay más opciones que el máximo, se pide la provincia o el departamento sin listar).
   - «Lima» a secas → `Aclaracion` (Lima Metropolitana, Lima Región, Callao) con `por_defecto: LIMA_METROPOLITANA` (T-03). «Lima Metropolitana», «Lima Región», «Lima provincias» y «Callao» se resuelven directo. «Callao» se devuelve como ámbito `CALLAO` (el nivel que usa el cubo; la ENDES por departamento tiene 24 unidades sin el 07). Rige T-03 aunque R-TERRITORIO-09 (`ambiguos_conocidos`) liste otras opciones para «Lima»; cuando el resolver ya aclaró, el planificador pasa el territorio resuelto y no se repite la aclaración de la regla (anotar la discrepancia en `consultas_al_dueno.md` como tipo D).
   - «Perú», «nacional», «todo el país» → nacional.
   - Sin coincidencias: `Aclaracion` con las sugerencias por similitud que permitan `sin_coincidencia_sugerencias_max` y `similitud_min_para_sugerir`, o «no encontramos ese lugar».
   - Distritos creados después de la fuente: se resuelven, y el resultado lleva `anio_datos_desde` para que el planificador sepa desde cuándo hay datos (T-01). Con `estado_ubigeo = pendiente` (Sangani) el resultado lo marca para que la respuesta siga R-LENGUAJE-05.
2. Batería de pruebas `tests/test_resolver_territorio.py` con ≥ 60 casos: los 4 de Q1–Q4, todos los de `nombres_mostrados.yaml` escritos sin tilde, Lima y sus variantes, homónimos de los dos tipos, Sangani (provisional), Alto Trujillo, errores de tipeo comunes y lugares inexistentes.

## Criterios de aceptación

- [ ] Los 60+ casos pasan y cubren cada rama de arriba.
- [ ] Ninguna resolución elige entre homónimos del mismo nivel sin preguntar.
- [ ] Las opciones de una aclaración muestran el nombre con tildes y su ubicación.
- [ ] El resolver solo lee las dimensiones y `parametros_motor.yaml` (sin red, sin LLM).
- [ ] «Toledo» y «Albarracin» dan una aclaración con la opción correcta; si `s1-00_datos_territorio.txt` muestra que 060506 no tiene el alterno «Santa Cruz de Toledo», se abre una consulta tipo C.
