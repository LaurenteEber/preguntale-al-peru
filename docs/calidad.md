# Pregunta al Perú — Calidad: pruebas, regresión y revisión

Versión al 3/11/2026 (slice 1 cerrado; piloto cerrado el 13/10/2026). Sirve para comprobar que el piloto sigue dando las respuestas aceptadas después de cualquier cambio en datos, reglas o código, y para extender las pruebas.

## 1. Qué se prueba y en qué capa

| Capa | Qué asegura | Dónde | Cómo se corre |
|---|---|---|---|
| 1. Datos de referencia | Las 206 cifras doradas son las que publican el INEI (176) y el INS (30, SIEN), con cita oficial y página | `curados/capa0/cifras_doradas.csv`; validación en `03_auditoria/validacion_doradas/` y `validacion_doradas_sien/` | Al editar una dorada: leerla en el documento oficial (§6) |
| 2. Construcción | Cada tabla cumple sus pruebas bloqueantes; si falla una, no se escribe | Archivos `pruebas_*.json` junto a cada manifiesto | `pap construir …`, `pap calcular` |
| 3. Cubo | Reproduce las 89 doradas bloqueantes (60 de encuestas y Mapa; 29 del SIEN con conteos exactos), los controles del gasto y R-GASTO-01 | Pruebas CAL-01 a CAL-10 | `pap calcular`, `test_calculo_p1.py` |
| 4. Validador | Cada una de las 68 reglas hace lo que dice su texto | 535 casos de un analista independiente y 448 de los implementadores | `pap validar-reglas` |
| 5. Respuestas | Q1–Q4 con el semáforo, el texto, la ficha, las decisiones esperadas y el contrato por capas | `test_respuesta_p3.py` (consultas archivadas del piloto) | pytest |
| 5a. Motor por intenciones | Que la consulta mínima, el resolver, el planificador, las plantillas, «no se puede» y la CLI den las mismas cifras que el piloto y no se caigan en ninguna combinación | `test_consulta_minima.py`, `test_resolver_territorio.py`, `test_planificador.py`, `test_plantillas_intencion.py`, `test_regresion_q1_q4.py`, `test_no_se_puede.py`, `test_cli_preguntar.py`, `test_matriz_cobertura.py`, `test_s1_09_correcciones.py` | pytest; la matriz completa a mano (§3) |
| 5b. Comprensión | Que una persona real entienda la respuesta y no saque conclusiones equivocadas | `03_auditoria/revision_usuario/` (4 perfiles de lector) | Manual, con un revisor independiente, después de cambiar el formato |
| 6. Aceptación | Un auditor independiente compara contra el esperado ajustado y los PDF | `00_proyecto/piloto/p4/` | Manual, con la lista del §5 |

## 2. Prueba rápida (≈ 2 minutos)

```bash
cd ~/Documents/SideProjects/pregunta-al-peru && git checkout main
uv sync
uv run pap calcular                       # debe terminar con todas las pruebas CAL en ✔
uv run pap validar-reglas                 # casos: 535  ok: 535  fallan: 0
uv run pap validar-reglas --carpeta casos_implementador
uv run pap preguntar curados/motor/consultas_minimas/       # Q1–Q4 por el motor por intenciones
uv run pap preguntar tests/fixtures/consultas_piloto/q1.yaml tests/fixtures/consultas_piloto/q2.yaml \
                     tests/fixtures/consultas_piloto/q3.yaml tests/fixtures/consultas_piloto/q4.yaml
```

**Resultado esperado**
- **Cubo:** `biblioteca/indicadores/manifiesto_p1_indicadores.json` con `fact_indicador.hash = sha256:ba1fbc55…`. Debe ser igual en macOS y Linux.
- **Semáforos internos:** `Q1 verde`, `Q2 ambar`, `Q3 rojo`, `Q4 rojo`. Al usuario se le muestran como confianza alta, media, baja y baja.

## 3. Pruebas automáticas

```bash
# las del piloto (≈ 75 s)
uv run pytest -q tests/test_calculo_p1.py tests/test_piloto_indicadores.py \
                 tests/test_validador_p2.py tests/test_respuesta_p3.py
# toda la suite (748 pruebas, ≈ 6 min; las del gasto reconstruyen tablas grandes y necesitan varios GB libres:
# en la VM de Claude test_gasto.py no cabe, se corre en el Mac)
uv run pytest -q
# consistencia de las reglas (al cambiarlas)
python3 reglas/consolidador/consolida_reglas.py
python3 reglas/consolidador/pruebas/prueba_guardia.py
```

| Archivo | Qué cubre |
|---|---|
| `test_calculo_p1.py` | Clave única del cubo, 89 doradas bloqueantes reproducidas (29 del SIEN contra el INS), DCI 2024 igual al INEI (casos, CV e IC), ámbitos de Lima, controles del gasto |
| `test_piloto_indicadores.py` | Tablas curadas: vocabularios, cobertura de doradas por indicador, una dorada mal copiada o con cita de prensa hace fallar la construcción |
| `test_validador_p2.py` | Las dos carpetas de casos pasan y las 68 reglas del alcance están implementadas y cubiertas |
| `test_respuesta_p3.py` | Ver la lista de abajo |
| `test_consulta_minima.py` | Esquema de la consulta mínima y sus mensajes de error en lenguaje sencillo |
| `test_resolver_territorio.py` | Resolver territorial (133 casos): niveles, tildes, Lima en tres ámbitos (T-03), homónimos (R-TERRITORIO-09), distritos creados después |
| `test_planificador.py` | El plan de cifras por tema × intención, el año (R-MOTOR-03), X-03, cruces permitidos |
| `test_plantillas_intencion.py` | Las cinco plantillas genéricas: marcadores, nombres antiguos y que el texto no tenga números sueltos |
| `test_regresion_q1_q4.py` | **Regresión Q1–Q4**, fase 1 (los planes igualan a los q*.yaml del piloto) y fase 2 (cifras, semáforos y confianza iguales a `tests/referencias/q1–q4.json`; las diferencias de texto aprobadas están en `backlog/slice-1/evidencia/regresion/`). Única excepción decidida por el dueño (C-01): Q1 no muestra 2022 |
| `test_no_se_puede.py` | Un caso por motivo de «no se puede» y las aclaraciones: sin cifras, la corta dice primero lo que no se puede, alternativa verificada |
| `test_cli_preguntar.py` | `pap preguntar`: opciones, archivos y carpetas, `--elegir`, `--plan`, `--salida` y códigos de salida |
| `test_matriz_cobertura.py` | Matriz reducida (60 casos fijos) y pruebas del generador y de las comprobaciones |
| `test_s1_09_correcciones.py` | Las correcciones de la revisión independiente del slice 1 (S1-09) |
| Demás `test_*.py` | Ingesta, almacén, territorio, población, gasto, Lima en tres ámbitos, SIEN, transferencias y trazabilidad |

Qué comprueba `test_respuesta_p3.py` en Q1–Q4 (lee las consultas archivadas en `tests/fixtures/consultas_piloto/`):
- **En todas las respuestas:**
  - el semáforo;
  - que no queden marcadores sin rellenar;
  - la ficha corta de 4 líneas como máximo;
  - que el corrector no bloquee;
  - que no haya dígitos fuera de los marcadores (salvo años);
  - que no haya códigos internos.
- **Decisiones del 11/10:**
  - intervalo doble;
  - Q1 con dos criterios en paralelo y su contraste oficial;
  - Q3 con la comparación 2024–2025 y la cobertura de Lima Metropolitana;
  - Q4 con el grupo oficial del INEI y el Mapa como principal.
- **SIEN (12/10):** Q2 y Q3 se contrastan con la cifra del INS y coinciden.
- **Contrato por capas (12–13/10):**
  - capa visible de 125 palabras como máximo;
  - de 1 a 3 «Ojo al leer»;
  - confianza sin colores;
  - una cita por cifra;
  - glosario;
  - sin avisos meta;
  - la respuesta corta dice primero lo que no se puede (Q2–Q4);
  - Q4 en orden alfabético;
  - «¿Qué puedo hacer?» solo con fuente oficial y fuera de Q4;
  - las observaciones de la verificación de usuario.

## 4. Resultados aceptados (referencia de regresión)

| Q | Pregunta (reconstruida) | Semáforo | Cifras clave que deben salir | Debe decir / no debe decir |
|---|---|---|---|---|
| Q1 | Evolución de la anemia en Huancavelica | **verde** (confianza alta) | **Criterio vigente:** 38,6 % en 2025 (propio 31,9–45,6; INEI 32,0–45,1); 2024 = 32,9 %. **Criterio anterior:** 54,5 % en 2025 (INEI 47,4–61,6); 2015 = 53,5 %; 2022 = 65,0 % | **Debe:** las dos formas de medir en paralelo, cada una con su alcance; «sin cambio estadísticamente claro» en 2024–2025 (vigente) y en 2015–2025 (anterior); 2020 excluido. **No debe:** comparar cifras entre criterios, ni decir «bajó» |
| Q2 | Anemia en Ayaviri | **ámbar** (confianza media) | SIEN Ayaviri ≈ 10 % (7–12 %) de 547 niños medidos (INS: 9,5 %); ENDES Puno 56,1 %; cobertura de Puno 39,8–50,5 % | **Debe:** empezar con «No se puede saber cuántos niños de Ayaviri…», «último control», la advertencia del INS (puede subestimar), la nota de altitud y «no podemos decir si se midió a más o a menos de la mitad». **No debe:** «la anemia en Ayaviri es…» |
| Q3 | Gasto contra la anemia en SJL y si sirvió | **rojo** (confianza baja) | Gasto SJL S/ 4,0 M; Lima Metropolitana (provincia de Lima) S/ 260,6 M + S/ 3,2 M aparte; SIEN SJL ≈ 8 %; cobertura LM 30–38 %; ENDES LM 25,3 % (2024: 24,0 %) | **Debe:** empezar con «No se puede saber si el gasto…», la tarjeta del gasto con su alcance («solo de la municipalidad y de obras…»), la estructura de efecto en 5 partes, «En Lima Metropolitana, a menos de la mitad…», sin cambio claro 2024–2025, respuesta parcial. **No debe:** decir que el gasto causó o no causó algo |
| Q4 | Distrito más pobre | **rojo** (confianza baja) | Mapa 2018, grupo 1, en orden alfabético: Anguia (72–86 %), Oxamarca (75–87 %) y Uchuraccay (73–89 %), con provincia y departamento. ENAHO 2025, grupo 1 oficial del INEI: Ayacucho, Cajamarca, Huancavelica, Huánuco, Loreto, Pasco y Puno (35,7–39,8 %) | **Debe:** el Mapa como cifra principal y el aviso de dato de 2018. **No debe:** un ranking puntual («el más pobre es…») |

Las cifras del INEI se contrastaron con los PDF oficiales en la auditoría P4 (`00_proyecto/piloto/p4/dictamen_p4.md`).

## 5. Lista de verificación manual (después de un cambio grande)

Corre `uv run pap preguntar tests/fixtures/consultas_piloto/q*.yaml` (escribe en `salidas/preguntar/`, fuera de git; `00_proyecto/piloto/p3/respuestas/` es solo el archivo del piloto, de antes de T-02) y abre `salidas/preguntar/qN.md`. Revisa:

1. [ ] El semáforo coincide con el §4; si cambió, ¿hay una decisión o corrección que lo explique?
2. [ ] Cada cifra coincide con su dorada (columna «IC del INEI» y `6_contraste_oficial`: «Nuestra cifra coincide»).
3. [ ] El texto no tiene números sueltos, códigos internos ni jerga (ENDES y SIEN se nombran, pero se explican).
4. [ ] Están los avisos obligatorios: tamizados, altitud, sede de Lima, dato antiguo, criterio de medición y cobertura frente al 50 %.
5. [ ] La ficha corta tiene 4 líneas y su «no permite concluir» tiene sentido para la pregunta.
6. [ ] No hay afirmaciones causales, rankings puntuales ni comparaciones entre criterios o con 2020.
7. [ ] La sección de reproducibilidad cita la huella del cubo y de las reglas vigentes.

## 6. Cómo extender las pruebas

**Agregar una cifra dorada**
1. Ubica la cifra en un documento oficial del INEI. Guarda el PDF y su huella; si conviene, regístralo con `pap registrar`.
2. Agrega la fila a `cifras_doradas.csv`:
   - `tipo_cita = oficial_inei`;
   - `cuadro_pagina` con el cuadro y la página física e impresa;
   - `criterio` igual al del indicador;
   - `bloqueante = True` solo si debe impedir la construcción.
3. Corre `pap construir indicadores` y `pap calcular`. Si no se reproduce, revisa la definición antes de tocar el valor.

**Agregar un caso del validador**
1. Copia un caso parecido en `tests/casos_validador/casos/grupo_*.yaml`, con su `id`, `regla`, `descripcion`, `consulta`, `respuesta` y `espera` (`dispara`, `accion`, `motivo`).
2. Los anclas YAML (`&idNNN`) no pueden repetirse dentro del archivo.
3. Corre `pap validar-reglas`.

**Agregar una prueba de respuesta**
1. Agrega una función a `test_respuesta_p3.py` que use el fixture `respuestas`. Ejemplo: `respuestas["q1"]["cifras"]["anemia_hvca_2025"]["valor"]`.
2. Para comparar textos, normaliza el espacio fino (` `) que el formato pone antes de «%».

**Una pregunta nueva del piloto**
1. Con el motor por intenciones no hace falta una plantilla: escribe la consulta mínima (JSON, en `curados/motor/consultas_minimas/`) y corre `pap preguntar`. Si hace falta una intención nueva, va en `intenciones.yaml` y una plantilla genérica.
2. Agrega su semáforo a `ESPERADO` en `test_respuesta_p3.py` (solo para consultas del piloto) o una referencia en `tests/referencias/` y escribe sus pruebas propias.
3. Lo ideal es que un analista independiente escriba antes su esperado en `04_reglas/prueba/`.

## 7. Si algo falla

| Falla | Qué mirar |
|---|---|
| CAL-03 o DOR-07 (doradas) | `biblioteca/indicadores/revision/doradas_reproduccion_p1.csv`: qué cifra y por cuánto. ¿Cambió un insumo (`insumos.lock.yaml`) o una definición? |
| Un caso de `validar-reglas` | El mensaje muestra lo obtenido frente a lo esperado. ¿El cambio fue intencional? Entonces actualiza el caso y deja la nota con la fecha y la decisión |
| Cambió un semáforo de Q1–Q4 | Mira `motivos_semaforo_respuesta` en el `.json` y los resultados de R-CRUCES-09 y R-CRUCES-10 |
| El corrector bloquea (R-LENGUAJE-02/03) | Un texto nuevo tiene jerga, dígitos sin marcador o una cifra antigua sin su año en la misma oración |
| La huella del cubo no coincide | Revisa `uv sync` y `git status`. Si persiste entre macOS y Linux, compara `revision/` de los dos lados |

## 8. Pendientes conocidos (no bloquean)

- **Resueltos el 12 y 13/10:** P4-13 («personas encuestados»), N3 (cobertura de Lima Metropolitana «del departamento») y la parte de P4-18 sobre avisos duplicados.
- **Hallazgos bajos de P4 abiertos:** P4-14, P4-15 (Q1 ya muestra 2015), P4-16 (4 % frente a 5 %), P4-17 y N5.
- **Textos de las reglas que se ven en «Límites» o «Más contexto»:** la frase estándar de efecto y NC-TENDENCIA-QUIEBRE. Se cambian con el consolidador.
- **Revisión del dueño:** el texto de «¿Qué puedo hacer?».
- **Esperado ajustado:** actualizarlo con las decisiones del 11/10 (P4-19).
- **Decisiones del dueño pendientes:** X-02 (P4-21, conteo en Q2) y X-03 (P4-22, gasto LM 2024), en `docs/decisiones.md`. P4-09 quedó resuelto por T-02 (nombres con tildes y ñ, 2/11/2026).
- **Detalle:** `00_proyecto/piloto/p4/README.md`.
