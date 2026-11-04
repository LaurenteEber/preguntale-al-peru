# Preparación de `dim_indicador` (siguiente paso del piloto)

> **Hecho el 9/10/2026.** `dim_indicador`, `cruces_permitidos` y `cifras_doradas` están cargadas en `curados/capa0/` y se construyen con `pap construir indicadores`. Resultado y decisiones pendientes: `03_auditoria/piloto_tablas_curadas/README.md`. Este documento queda como guía histórica.

Estado al 9/10/2026: los insumos del piloto están estandarizados (S4) y reproducen 136 cifras publicadas por el INEI. Falta cargar `dim_indicador` con los indicadores del piloto. Después vienen el validador (68 reglas) y el motor.

## Qué hay que cargar

Los campos de nivel indicador están en el diccionario de `reglas/reglas.md`, que es la fuente de verdad. Estos son obligatorios para el piloto: si quedan vacíos, R-MOTOR-02 o R-CRUCES-03 suprimen la cifra (`04_reglas/auditoria/piloto_alcance/analista/informe.md`, riesgo 4):

- `velocidad_cambio`, `criterio_medicion`, `concepto_medido`, `rank_concepto`;
- `poblacion_objetivo`, `universo`, `es_socioeconomico`;
- `insumos[] = {id, rol}`, `tipo_denominador`, `requiere_estandarizacion`.

Además: `tipo_estimacion`, `base_geografica_usada`, `tema` y `origen_cifra`.

## Indicadores del piloto (preguntas 1–4) y de dónde salen

| # | Indicador | Tabla | Definición ya fijada | Nivel válido |
|---|---|---|---|---|
| 1 | Anemia en niñas y niños de 6 a 35 meses (ENDES; criterio anterior, serie 2015–2025) | `estandarizada/encuestas/endes_nino` | `definiciones_endes.yaml` → `anemia_6_35m` | Nacional, área, departamento (`inferencia_verificada`) |
| 2 | Anemia en niñas y niños de 6 a 35 meses, directriz OMS 2024 (2024–2025) | idem | → `anemia_6_35m_oms2024` | idem; no se empalma con el 1 (cambio de criterio) |
| 3 | Desnutrición crónica en menores de 5 años, OMS (ENDES) | idem | → `dci_menores_5` | idem (pregunta 7; se carga para el piloto ampliado) |
| 4 | % de tamizados con anemia (SIEN, por establecimiento) | `dimensiones/fact_sien_hb_ubigeo` | Ronda 3 (SP-03) | Establecimiento y distrito, con rótulo «solo tamizados» |
| 5 | Cobertura de tamizaje 6–35 m (SIEN) | `fact_sien_hb_ubigeo` + `fact_poblacion_grupo` | R-TERRITORIO-08 v3 (dos cotas) | Solo departamento |
| 6 | Devengado en servicios ex-PAN (MEF), por concepto y opción C | `dimensiones/fact_gasto_territorial` vía `gasto_tema('<tema_id>')` | Decisiones del gasto (rondas 1–2) | Nacional, departamento, ejecutora |
| 7 | Pobreza monetaria (ENAHO) | `estandarizada/encuestas/enaho_sumaria` | `pobre` con `peso_persona`; diseño `id_estrato_diseno` × `id_conglomerado` | Nacional, área, departamento (y Lima en sus dos definiciones) |
| 8 | Pobreza monetaria distrital 2018 (Mapa de Pobreza) | `estandarizada/mapa_pobreza/fact_mapa_pobreza` | Intervalo y grupo robusto; sin cifra puntual | Distrito y provincia (geografía 2018) |
| 9 | Población de 6 a 35 meses (denominador) | `dimensiones/fact_poblacion_grupo` | Ya construida (S2 y auditoría) | Departamento |

## Decisiones técnicas ya tomadas que `dim_indicador` debe reflejar

- **Encuestas:**
  - Taylor, IC 95 %, gl = conglomerados − estratos (R-ENC-01).
  - Estratos con un solo conglomerado: `adjust`.
  - IC de proporciones: Korn-Graubard en la variante NCHS (svy `ci_method="korn-graubard"`), confirmada con el Apéndice II de Parker et al. 2017.
  - Al agrupar años: año × estrato y año × conglomerado.
- **ENDES:**
  - Pesos normalizados: no estimar totales.
  - 2015–2017 no traen ubigeo, así que Lima solo se publica a nivel de departamento.
  - En 2015 la cifra nacional queda ~0,15 pp por debajo de la publicada (nota en `cifras_control_inei.yaml`).
- **ENAHO:** declarar en cada indicador qué «Lima Metropolitana» usa: `ambito_lima` (provincia 1501) o `lima_metropolitana_dominio8`.
- **Mapa 2018:**
  - Publicar siempre el año 2018, el intervalo y el grupo robusto.
  - No restar ni combinar con la ENAHO de otros años.
  - Los distritos creados después de 2018 no tienen dato.
- **Validación:** cada cifra de encuesta que publique el motor debe reproducir las de `cifras_control_inei.yaml` (R-ENC-18). El verificador R está diferido (`docs/guias/verificador_r.md`).

## Abierto (no bloquea la carga)

- La DCI departamental de 2024 (Cuadro 04A del informe de programas presupuestales) y los informes técnicos 2024–2025 que reemplacen a las notas de prensa como cita.
- Pregunta 3 «cómo evolucionó»: solo está el SIEN 2025. Propuesta pendiente de visto: aceptar una respuesta parcial.
