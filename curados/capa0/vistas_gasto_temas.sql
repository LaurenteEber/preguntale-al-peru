-- Vistas temáticas del motor (pieza C de las decisiones del gasto, rondas 1-2; R-GASTO-05, 08, 08b y 09).
-- Insumo curado de gasto.py, que las crea y las prueba (G-03, G-32). Requieren las vistas de vistas_gasto.sql
-- (v_gasto_tematico: solo gasto final) y las tablas dim_tema_gasto, rel_concepto_nodo, rel_concepto_grupo y
-- rel_programa_social_ejecutora (y rel_programa_social_linea_aparte, E3) de biblioteca/dimensiones/. Toda consulta pasa por guardia_gasto.verificar_consulta().
-- Acceso al gasto por tema: SOLO la macro gasto_tema('<tema_id>'), una vez por consulta (auditoría de la pieza C, H1:
-- un filtro sobre una vista con todos los temas se podía saltar con autojoins o filtrando otra tabla). La vista
-- v_gasto_tema_interna (todos los temas) es solo para las pruebas de construcción: la guardia rechaza leerla.

-- 1) Hojas del alcance «concepto» (cada sol, como máximo en una hoja: G-28). Solo filas de actividades y solo los
--    nodos de la base (origen = 'base'; los documentales anteriores a 2023 no tienen montos).
CREATE OR REPLACE VIEW v_gasto_concepto AS
SELECT r.concepto_id, f.*
FROM v_gasto_tematico f
JOIN rel_concepto_nodo r
  ON r.origen = 'base' AND f.anio = r.anio AND f.programa_ppto = r.programa_ppto
 AND f.producto_proyecto = r.producto_proyecto AND f.actividad_accion_obra = r.actividad_accion_obra
 AND f.tipo_act_proy = 'ACTIVIDAD'
 AND (r.sec_ejec IS NULL OR (f.sec_ejec = r.sec_ejec AND f.nivel_gobierno = 'E'))
 AND (r.excluye_sec_ejec IS NULL OR NOT (f.sec_ejec = r.excluye_sec_ejec AND f.nivel_gobierno = 'E'))
 AND (r.funcion IS NULL OR f.funcion = r.funcion)
 AND (r.excluye_funcion IS NULL OR f.funcion <> r.excluye_funcion);

-- 2) Gasto por tema de dim_tema_gasto v1.2, de todas las cadenas (USO INTERNO: pruebas G-03 y G-32). Una fila de la
--    fact aparece una vez por cada tema que la contiene.
CREATE OR REPLACE VIEW v_gasto_tema_interna AS
SELECT d.tema_id, d.cadena, f.*
FROM v_gasto_tematico f JOIN dim_tema_gasto d
  ON d.cadena = 'funcion' AND d.anio = f.anio AND d.funcion = f.funcion
UNION ALL BY NAME
SELECT d.tema_id, d.cadena, f.*
FROM v_gasto_tematico f JOIN dim_tema_gasto d
  ON d.cadena = 'division' AND d.anio = f.anio AND d.funcion = f.funcion AND d.division_funcional = f.division_funcional
UNION ALL BY NAME
SELECT d.tema_id, d.cadena, f.*
FROM v_gasto_tematico f JOIN dim_tema_gasto d
  ON d.cadena = 'programa' AND d.anio = f.anio AND d.programa_ppto = f.programa_ppto
UNION ALL BY NAME
SELECT d.tema_id, d.cadena, f.*
FROM v_gasto_tematico f JOIN dim_tema_gasto d
  ON d.cadena = 'programa_x_funcion' AND d.anio = f.anio AND d.programa_ppto = f.programa_ppto AND d.funcion = f.funcion
UNION ALL BY NAME
SELECT d.tema_id, d.cadena, c.* EXCLUDE (concepto_id)
FROM v_gasto_concepto c
JOIN rel_concepto_grupo g ON g.concepto_id = c.concepto_id
 AND (g.restriccion_programa_ppto IS NULL OR g.restriccion_programa_ppto = c.programa_ppto)
JOIN dim_tema_gasto d ON d.cadena = 'concepto' AND d.anio = c.anio AND d.concepto_grupo_id = g.grupo_id
UNION ALL BY NAME
SELECT d.tema_id, d.cadena, f.*
FROM v_gasto_tematico f JOIN dim_tema_gasto d
  ON d.cadena = 'programa_social' AND d.anio = f.anio AND d.nivel_gobierno = f.nivel_gobierno
 AND ((d.sec_ejec IS NOT NULL AND f.sec_ejec = d.sec_ejec)
      OR (d.actividad_accion_obra IS NOT NULL AND f.actividad_accion_obra = d.actividad_accion_obra));

-- 3) Línea aparte de los programas sociales (E3, decisión del dueño del 8/10/2026): gasto de la ejecutora del programa
--    que NO es gasto final y que la respuesta muestra siempre aparte, sin sumarlo (Llamkasun: «transferido a
--    municipalidades», 2.4.x.3.1.3). Lee el fact (filas fuera del gasto final); la guardia (G6) no la deja combinar con
--    otra vista de gasto ni con gasto_tema() en la misma consulta. G-38 la prueba en cada construcción.
CREATE OR REPLACE VIEW v_programa_social_linea_aparte AS
SELECT p.id_programa_social, p.tema_id, p.linea_aparte_id, p.rotulo, p.obligatoria,
       f.anio, f.mes, f.nivel_atribucion, f.ubigeo_atribucion, f.departamento_atribucion, f.ambito_id,
       f.cuenta_en_lima, f.cuenta_en_ambito, f.programa_ppto, f.clasificador_gasto,   -- P3: cuenta_en_ambito (15 y 07)
       sum(f.pim) AS pim, sum(f.devengado) AS devengado
FROM fact_gasto_territorial f
JOIN rel_programa_social_linea_aparte p
  ON f.nivel_gobierno = p.nivel_gobierno AND f.sec_ejec = p.sec_ejec AND f.clasificador_gasto = p.clasificador_gasto
WHERE f.bloque_consolidado <> 'gasto_final'
GROUP BY ALL;

-- P3 (9/10/2026): gasto_tema() trae la columna ambito_gasto de v_gasto_tematico; el gasto de un tema por ámbito (L5:
--    ex-PAN por LM, LR y Callao) es SELECT ambito_gasto, sum(devengado) FROM gasto_tema('<tema>') GROUP BY 1, leyendo
--    solo LIMA_METROPOLITANA, LIMA_REGION y CALLAO como cifras y el resto como líneas aparte (H-A4).

-- 4) Único acceso del motor al gasto por tema: un tema por llamada (la guardia admite una sola llamada por consulta,
--    con un argumento constante o parámetro).
CREATE OR REPLACE MACRO gasto_tema(tema) AS TABLE
SELECT * FROM v_gasto_tema_interna WHERE tema_id = tema;
