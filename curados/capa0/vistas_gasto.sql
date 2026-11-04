-- Vistas del motor sobre fact_gasto_territorial (GA-05, R-GASTO-05 v4; ronda 3, 7/10/2026).
-- Insumo curado de gasto.py, que las crea y las prueba (G-17c); el motor las carga al
-- abrir la biblioteca y pasa toda consulta por guardia_gasto.verificar_consulta() (R-GASTO-05).

-- 0) P3 (Lima en tres ámbitos, L6; 9/10/2026): ámbito de la cifra. Única definición del reparto de los dpto 15 y 07:
--    LM, LR y Callao SOLO con cuenta_en_ambito (H-A4: sin ese filtro LM se infla en 486 / 537 / 703 millones por obras
--    de sede y referencia nacional); lo no asignable y lo que sale de la cifra, en líneas propias; NULL fuera del 15 y
--    el 07. Cada fila del 15 y el 07 cae en exactamente una línea (G-41).
CREATE OR REPLACE MACRO ambito_gasto(dpto, ubigeo, cuenta, refnac) AS
CASE WHEN dpto NOT IN ('15', '07') THEN NULL
     -- ATU y demás lima_callao, con meta 15 o 07 (auditoría de P3, H-P3-3): Lima y Callao sin separar
     WHEN cuenta AND ubigeo = 'A-AREA_METROPOLITANA_LIMA_CALLAO' THEN 'NO_ASIGNABLE_LIMA_CALLAO'
     WHEN cuenta AND dpto = '07' THEN 'CALLAO'
     WHEN cuenta AND (ubigeo = 'A-LIMA_METROPOLITANA' OR ubigeo LIKE '1501%') THEN 'LIMA_METROPOLITANA'
     WHEN cuenta AND (ubigeo = 'A-LIMA_REGION' OR (ubigeo LIKE '15%' AND ubigeo <> '150000')) THEN 'LIMA_REGION'
     WHEN cuenta AND ubigeo = '150000' THEN 'NO_ASIGNABLE_DPTO_LIMA'
     WHEN cuenta THEN 'REVISAR'
     WHEN refnac THEN 'REFERENCIA_NACIONAL'
     ELSE 'SEDE_NACIONAL' END;

-- 1) Cifras temáticas (función, programa, tema; por territorio): solo gasto final. No hay forma de sumar (a), (b) ni fondos.
--    Pieza A: trae también actividad, clasificador, fuente/rubro y las marcas cuenta_en_lima / referencia_nacional /
--    ejecutora_mixta (y, desde E3, obra_sede_nacional). Cifra de Lima = cuenta_en_lima; línea aparte = referencia_nacional AND departamento_atribucion = '15'.
--    P3: cuenta_en_ambito (15 y 07) y ambito_gasto (macro 0); cifra de LM, LR o Callao = ambito_gasto = '<ámbito>'.
CREATE OR REPLACE VIEW v_gasto_tematico AS
SELECT * EXCLUDE (bloque_consolidado, categoria_transferencia, es_transferencia, es_transferencia_intergub),
       ambito_gasto(departamento_atribucion, ubigeo_atribucion, cuenta_en_ambito, referencia_nacional) AS ambito_gasto
FROM fact_gasto_territorial
WHERE bloque_consolidado = 'gasto_final';

-- 2) Consolidado multinivel, YA AGREGADO, con (b) en columna propia. No existe una columna «devengado» única:
--    una suma no puede mezclar el gasto final con lo entregado fuera del presupuesto sin escribir la suma explícita,
--    y la guardia rechaza esa expresión. (a) no está; los fondos por identificar tampoco (vista 3).
CREATE OR REPLACE VIEW v_gasto_consolidado AS
SELECT anio, mes, nivel_atribucion, ubigeo_atribucion, departamento_atribucion, ambito_id, alcance_ejecutora,
       -- pieza A (rondas 1-2): las cifras de Lima usan cuenta_en_lima; la línea aparte, referencia_nacional
       -- E3 (8/10/2026): obra_sede_nacional (obras de sede o función nacional, fuera de cuenta_en_lima)
       cuenta_en_lima, referencia_nacional, ejecutora_mixta, obra_sede_nacional,
       -- P3 (L6): cuenta_en_ambito y ámbito de la cifra (macro 0)
       cuenta_en_ambito,
       ambito_gasto(departamento_atribucion, ubigeo_atribucion, cuenta_en_ambito, referencia_nacional) AS ambito_gasto,
       nivel_gobierno, departamento_meta, funcion, division_funcional, programa_ppto,
       any_value(fecha_corte_datos) AS fecha_corte_datos, any_value(es_anio_cerrado) AS es_anio_cerrado,
       coalesce(sum(devengado) FILTER (WHERE bloque_consolidado = 'gasto_final'), 0) AS gasto_final_devengado,
       coalesce(sum(pim) FILTER (WHERE bloque_consolidado = 'gasto_final'), 0) AS gasto_final_pim,
       coalesce(sum(devengado) FILTER (WHERE bloque_consolidado = 'entregado_fuera_del_presupuesto'), 0)
         AS entregado_fuera_del_presupuesto_devengado,
       coalesce(sum(pim) FILTER (WHERE bloque_consolidado = 'entregado_fuera_del_presupuesto'), 0)
         AS entregado_fuera_del_presupuesto_pim
FROM fact_gasto_territorial
WHERE bloque_consolidado IN ('gasto_final', 'entregado_fuera_del_presupuesto')
GROUP BY ALL;

-- 3) Fondos por identificar (posible doble conteo): solo para nota, nunca para sumar
CREATE OR REPLACE VIEW v_gasto_fondos_por_identificar AS
SELECT anio, sec_ejec, nivel_gobierno, funcion, programa_ppto, producto_proyecto,
       sum(pim) AS pim, sum(devengado) AS devengado,
       'Transferido a un fondo cuyo uso final no está identificado; puede reaparecer como gasto de otras entidades' AS nota
FROM fact_gasto_territorial
WHERE bloque_consolidado = 'posible_doble_conteo_fondo'
GROUP BY ALL;

-- 4) P3 (H-A4, L6, L8): devengado y PIM del gasto final por ámbito: LM, LR y Callao (solo cuenta_en_ambito), más las
--    líneas aparte del 15 y el 07: lo no asignable (departamento de Lima sin separar; Lima Metropolitana y Callao sin
--    separar), los centros de referencia nacional y el gasto nacional con sede en Lima o el Callao. Las líneas aparte
--    no se suman a ningún ámbito. Mientras el dueño no vea la lista del Callao, su gasto total va sin per cápita ni
--    ranking salvo con el aviso de sede (L6, R-GASTO-13 d).
CREATE OR REPLACE VIEW v_gasto_por_ambito AS
SELECT anio, ambito_gasto,
       CASE WHEN ambito_gasto IN ('LIMA_METROPOLITANA', 'LIMA_REGION', 'CALLAO') THEN 'cifra_ambito'
            WHEN ambito_gasto LIKE 'NO_ASIGNABLE%' THEN 'no_asignable'
            WHEN ambito_gasto = 'REFERENCIA_NACIONAL' THEN 'linea_aparte_referencia_nacional'
            WHEN ambito_gasto = 'SEDE_NACIONAL' THEN 'fuera_sede_nacional'
            ELSE 'revisar' END AS linea,
       CASE ambito_gasto
            WHEN 'LIMA_METROPOLITANA' THEN 'Lima Metropolitana (provincia de Lima)'
            WHEN 'LIMA_REGION' THEN 'Lima Región (Lima Provincias)'
            WHEN 'CALLAO' THEN 'Callao'
            WHEN 'NO_ASIGNABLE_DPTO_LIMA' THEN 'Departamento de Lima sin separar entre Lima Metropolitana y Lima Región'
            WHEN 'NO_ASIGNABLE_LIMA_CALLAO' THEN 'Lima Metropolitana y Callao sin separar'
            WHEN 'REFERENCIA_NACIONAL' THEN 'Centros nacionales de referencia con sede en Lima (línea aparte)'
            WHEN 'SEDE_NACIONAL' THEN 'Gasto nacional con sede en Lima o el Callao (fuera de la cifra del ámbito)'
       END AS rotulo,
       -- Aviso obligatorio del Callao (auditoría de P3, H-P3-1; la columna de canasta comparable es decisión del dueño):
       -- se muestra siempre junto con la cifra del Callao; las cifras por año, en la revisión callao_canasta_comparable
       -- de la construcción (G-42) y en p3_gasto/implementacion.md
       CASE WHEN ambito_gasto = 'CALLAO' THEN
            'El Callao incluye entidades que en Lima Metropolitana se cuentan como nacionales o mixtas (policía, '
            || 'fiscalías, Poder Judicial, programas sociales, SIS, INPE: ≈ 15-17 % de su gasto en 2023-2025); no se compara con '
            || 'Lima Metropolitana en per cápita ni en ranking sin este aviso. Incluye además la Vía Expresa Santa Rosa '
            || '(obra vial nacional, acceso al aeropuerto Jorge Chávez, CUI 2473375) y la SUAT PNP de Lima y Callao '
            || '(CUI 2407158), y las mixtas DIREFIN PNP (sin su aviación, que es nacional), Ministerio Público, Poder '
            || 'Judicial y SENASA (con advertencia).'
       END AS aviso,
       departamento_atribucion, nivel_gobierno, funcion,
       any_value(fecha_corte_datos) AS fecha_corte_datos, any_value(es_anio_cerrado) AS es_anio_cerrado,
       sum(pim) AS pim, sum(devengado) AS devengado
FROM v_gasto_tematico
WHERE ambito_gasto IS NOT NULL
GROUP BY ALL;
