# S1-03 — Catálogo de intenciones y planificador de cifras

## Por qué

Es el corazón del slice: decidir qué cifras hacen falta para responder bien, siguiendo las decisiones del proyecto, en vez de escribirlas a mano en cada `q*.yaml`.

## Contexto

- `curados/capa0/dim_indicador.yaml`: `id`, `tema`, `niveles_validos`, `niveles_no_validos`, `anios_disponibles`, `quiebres`, `anios_con_quiebre`, `base_geografica`, `naturaleza_dato`.
- `curados/capa0/cruces_permitidos.yaml` (solo CR-01 activo).
- Formato de las especificaciones de cifra que consume `Motor.cifra()` (`pap/motor/respuesta.py`): `{id, indicador, anio, nivel, territorio, rol, comparar_con?, serie?, medida?, nivel_pedido?}` y los `grupos` de Q4 (`plantillas.expandir_grupo`).

## Tareas

1. `curados/motor/intenciones.yaml`: tabla declarativa por **tema × intención** (sin repetir lo que ya está en `dim_indicador.yaml`, `cruces_permitidos.yaml` ni `map_intencion_tema` de R-GASTO-08b: se leen de ahí) con:
   - indicador principal y suplentes por nivel (p. ej. anemia por distrito → SIEN «en establecimientos ubicados en…»; por departamento → ENDES);
   - cifras de contexto obligatorias, cada una con la decisión que la exige;
   - comparación por defecto (año contra año, desde cuándo);
   - nivel al que se sube si el pedido no es válido.
   Reglas mínimas que debe codificar (cada fila cita su ID de decisión):
   - **E-06:** anemia de la ENDES con intención `evolucion` → las dos formas de medir en paralelo; la vigente compara con el año anterior disponible; la anterior, con el primer año de la serie. En `nivel_actual` y como contexto de otra cifra, solo la vigente (patrón de Q2 y Q3). *Alcance decidido por el dueño el 3/11/2026 (E-06).*
   - **Series (E-06):** primer y último año y la prueba de cambio; no se planifican años intermedios. Por eso Q1 ya no lleva 2022 (decisión del dueño del 3/11/2026, C-01).
   - **E-07:** quiebre de modo (ENDES 2020) excluye solo ese punto; los demás quiebres cortan la serie.
   - **S-01:** SIEN por distrito siempre con la ENDES de su departamento (o de su ámbito en Lima) y la cobertura de tamizaje de su departamento o ámbito como contexto; la cobertura nunca por provincia ni distrito.
   - **T-03:** en Lima, el ámbito en vez del departamento 15.
   - **E-08:** «más pobre» por distrito → grupo robusto del Mapa 2018; por departamento → grupos oficiales del INEI.
   - **G-07 / R-03:** gasto contra la anemia → serie por concepto como principal; cruce solo CR-01, lado a lado, nunca coeficientes; con el parámetro `pendientes_dueno.cr01_mismo_anio` (X-03).
   - **Solo metadatos fijos:** el planificador decide con `niveles_validos`, `niveles_no_validos`, `anios_disponibles`, `quiebres` y `cruces_permitidos`. Si el nivel pedido no está en `niveles_validos`, planifica el nivel superior (`no_se_puede.nivel_alternativo`) y deja el motivo para S1-05. **No anticipa** la supresión por precisión, privacidad ni falta de inferencia (E-02, E-03, P-04): eso lo hace el validador (`Motor.evaluar` → R-MOTOR-01, R-ENC-08), y S1-05 lee el resultado (`estado_cifra` y su traza).
   - **Cruce y efecto (R-03, R-CRUCES-07):** con tema `gasto_publico` o `anemia` y territorio con datos de ambos lados → CR-01 de `cruces_permitidos.yaml`. `efecto` ("¿sirvió?") lleva la estructura de efecto en 5 partes y `respuesta_parcial = true`; `cruce` es solo lado a lado, sin esa estructura.
   - **Periodo por intención:** si la consulta no trae periodo, se usa `periodo.por_intencion` (`evolucion` → serie desde el primer año disponible); si no, `periodo.por_defecto`.
2. `pap/motor/planificador.py`: `planificar(consulta_minima, resuelto, motor) -> consulta` (recibe el motor para usar `Motor.anio` y el contexto `ctx`) (la misma estructura que hoy tienen los `q*.yaml`: `id`, `pregunta`, `intencion`, `territorio`, `periodo`, `cifras`, `grupos`, `plantilla`). Los `id` de cifra se generan de forma estable con `planificador.formato_id_cifra`. `territorio.nombre_pedido` = `nombre_mostrado` del territorio resuelto (vacío en `identificar_extremo`); así R-TERRITORIO-09 encuentra el lugar. Años `ultimo` y series se resuelven con `anios_disponibles` y con la misma función que usa hoy el motor (`Motor.anio`, R-MOTOR-03); no se duplica esa lógica.
3. Pruebas: para Q1–Q4, el plan generado debe coincidir con las cifras de `q1–q4.yaml` en indicador, año, nivel, territorio, rol y comparación (los `id` pueden diferir). Más 20 casos unitarios de las reglas de arriba.

## Criterios de aceptación

- [ ] Ninguna regla de negocio queda en Python fuera del planificador genérico: todo lo específico de un tema está en `intenciones.yaml` con su decisión citada.
- [ ] Planes de Q1–Q4 equivalentes a los manuales (prueba automática).
- [ ] Ningún plan pide una cifra prohibida por las decisiones (cobertura SIEN por distrito, cruce fuera de la lista blanca, tendencia entre criterios de anemia).
- [ ] Al terminar, la fase 1 de S1-07 (comparación de planes) está en verde (sin 2022 en Q1). Las plantillas viejas `_q1…_q4` buscan las cifras por su `id` fijo, así que la respuesta completa por el camino nuevo recién se compara en S1-04.

## Fuera

Redactar el texto (S1-04). Indicadores nuevos.
