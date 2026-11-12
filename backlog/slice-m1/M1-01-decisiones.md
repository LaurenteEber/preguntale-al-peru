# M1-01 — Decisiones del 12/11, reglas y tablas curadas

**Se deriva de** la tabla «Decisiones del dueño» del README y del diseño §26.1.

## Tareas

1. **`docs/decisiones.md`:** editar la fila de cada tema (no filas nuevas, salvo tema nuevo) con lo decidido el 12/11/2026 y su motivo:
   - F-01 y F-05: fichas de tabla, bloques y temas provisionales (`docs/diseno/fichas.md`);
   - F-04: tope de la ENDES 2015–2025 (2 GB en el Mac, 1,5 GB en el repo privado);
   - F-03: licencia por año de la ENAHO (K-08);
   - E-03 y R-01: compuertas también con 25 a 49 casos; R-ENC-19 aprobada con sus umbrales (R-01 (c) deja de decir «todavía no se agrega») y el número de reglas vigentes actualizado;
   - F-01 (tablas curadas del motor): 2024–2025 `conglomerados_repetidos`; HV001 solo es identificador estable desde 2021 (antes los números se reutilizan: lo midió el auditor en `endes_nino.parquet`); el parámetro `inferencia.admitir_propuesto_en_sombra` (M1-07), que se deriva de K-04;
   - P-07: topes del LLM;
   - R-03 y R-08: el proyecto va por los niveles 1 y 2 con varias fuentes; en M1 solo se prepara (bloques y contrato con partes).
2. **Reglas, con el consolidador** (nunca a mano):
   - **C-M0-11-2:** R-ENC-03 y R-ENC-04 dejan de exigir `n_sin_ponderar >= 50`; se aplican desde 25 casos. De R-ENC-02 no cambian los umbrales (menos de 25 suprime; 25 a 49 marca referencial); se ajustan su `condicion` («>= 50 → pasa a R-ENC-03/04») y el enunciado de R-ENC-03 («Con 50 casos o más»).
   - **R-ENC-19** (nueva): tasa de no respuesta del ítem > 5 % → aviso en la capa 2; > 20 % → referencial. Activar `compuertas.paso_no_respuesta_activo` y hacer que el código lo lea (hoy nunca se lee: H09-3).
   - **Antes de aplicar C-M0-11-2, medir:** con las reglas nuevas, ¿qué filas del cubo completo (todos los años e indicadores de encuesta) cambian de estado? Guardar la lista en `evidencia/m1-01_cambios_de_estado.csv`. Los valores no cambian; solo el estado.
   - El validador del motor actual también cambia: `src/pap/motor/validador/reglas_etapa4.py` (las condiciones de 50 casos, hoy en las líneas 265 y 310).
   - **Bases grabadas:** regenerar `reglas.json` cambia la huella de reglas que llevan las respuestas (como en C-M0-01-1). El dueño ya aprobó estos cambios de reglas: **regrabar queda autorizado si lo único que cambia es esa huella.** Si además cambia un estado, una cifra visible o un texto de Q1–Q4, de la matriz o de las bases, **es tipo C:** se muestra la lista al dueño antes de regrabar.
3. **Tablas curadas** (aquí se escriben los valores decididos; el esquema que permite tramos y categorías agrupadas lo amplía M1-03, tarea 1b):
   - `relacion_entre_anios.csv`: 2024–2025 → `conglomerados_repetidos`, `HV001`, con la cita de la ficha 2025 (recurso `endes-2025-ficha-tecnica`, §3.1 y §IV, con su página).
   - `cortes_estandar.yaml`:
     - `grupo_edad` para la unidad niño, **solo dentro de las recetas en M1** (un plan compuesto que lo pida se recorta y se avisa), con dos juegos de tramos según el indicador: anemia (6–8, 9–11, 12–17, 18–23, 24–35 meses) y desnutrición crónica (menores de 36, 36–59 meses), con la cita de los Cuadros 06B, 6.1B y 04 del informe «Indicadores de Resultados de los Programas Presupuestales, ENDES 2024»;
     - `region_natural`: categorías Costa (SHREGION 1 y 2), Sierra y Selva, con la nota «verificado contra las cifras publicadas»; la categoría 1 se rotula «Lima Metropolitana y Callao» y la 2 «resto de la Costa» cuando se muestran por separado;
     - `quintil_riqueza`: se rotula «quintil de bienestar»; la nota sobre las dos versiones de la ficha queda en el YAML.
   - `universos_analiticos.yaml`: universo de disciplina infantil que exige a la mujer en REC0111 (deja fuera las 341 filas); nota en la ficha de REC93DVdisciplina (M1-06).
4. **Recetas:** las 3 pasan a `estado: verificado` y se quita `pendiente: visto_dueno`. La confianza de sus cifras publicables deja de ser `baja` (§15.2).
5. **Catálogo:** INEI-ENAHO pasa a `ODbL-1.0`, con las fichas de la Plataforma Nacional de Datos Abiertos de 2023 y 2024 como fuente. Regenerar con el script del catálogo, no a mano.
6. **Parámetros:** `tope_llm_usd_dia: 5` (`curados/web/parametros.yaml`; el tope vigente `llamadas_llm_por_dia` sigue rigiendo hasta que M1-17 lo reemplace); en `curados/inferencia/parametros.yaml`: `batch.tope_lote_usd: 20`, `almacen.tope_endes_mac_gb: 2`, `almacen.tope_endes_repo_privado_gb: 1.5` e `inferencia.admitir_propuesto_en_sombra: true`; cada uno con `decision`.
7. **`agents.md`:** agregar `docs/diseno/fichas.md` a «Qué leer».
8. **Actualizar `docs/diseno/motor_inferencia.md`** para que no contradiga lo decidido (cada cambio con su motivo en la tabla del §26.1):
   - §15.1: pasos 3 a 7 desde 25 casos; el paso 8 deja de ser «propuesta»;
   - §12.1 y anexo A: unión por el padre común, `cardinalidad`, `mediciones.yaml` y tramos de edad por indicador;
   - §7.2 y §10: `bloque_id`, texto del bloque temático y búsqueda en dos pasos (remite a `fichas.md`);
   - §7.2, §10, §12.1 y §19.1: `propuesto` solo con `inferencia.admitir_propuesto_en_sombra` y nunca con `motor.version: nuevo`;
   - §19.2, §17.1 y §24: contrato con `partes[]` (lo redacta M1-16);
   - §27: el lote a `revisado` ya no es la primera historia de la fase ni la bloquea (K-04);
   - anexo B: `batch.tope_lote_usd` 20, umbrales de no respuesta aprobados, `recuperador.dos_pasos`, `inferencia.admitir_propuesto_en_sombra` y los topes de almacén.

## Criterios de aceptación

- [ ] `decisiones.md` sin filas duplicadas ni contradictorias; cada cambio con su motivo y fecha.
- [ ] `reglas.json` regenerado por el consolidador; la huella nueva de reglas anotada.
- [ ] Lista de cambios de estado entregada. Las 90 filas de 2024 conservan sus valores (|dif| ≤ 1e-8).
- [ ] `pap inferencia validar-tablas` y `validar-recetas` salen con 0.
- [ ] Las 3 recetas en `verificado`.
- [ ] Suite en verde, con las bases regrabadas solo si el dueño dio el visto.

## Fuera

Usar los cortes nuevos en las recetas (M1-03).
