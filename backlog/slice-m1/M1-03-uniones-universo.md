# M1-03 — Uniones entre tablas hermanas, universo por medición y cortes nuevos

**Se deriva de** el diseño §12.1, de D-M0-10-1 y de la auditoría del supervisor del cierre de M0.

## Contexto

- El verificador solo une de hijo a padre. RECH6 (niños) y RECH23 (riqueza y región natural) cuelgan los dos de RECH0, así que no se alcanzan entre sí: los cortes por región natural y por quintil no se pueden calcular para niños.
- El verificador toma como universo analítico la base común de la unidad (`nino_hecho`) en vez del que corresponde a la medición (`nino_hecho_hb_medida`).

## Tareas

1. **Unión por el padre común.** `ruta_de_uniones` admite ir de A a B cuando ambos se unen a un mismo padre y B es 1:1 con ese padre por la misma llave (RECH23–RECH0 por HHID). Se compila como dos uniones izquierdas (A → padre → B). Controles de siempre: las filas de la unidad no cambian, pérdida de `u` ≤ 1 %, pesos, estratos y conglomerados informados.
   - Las relaciones se declaran en `archivos_endes_2024.yaml` y se comprueban contra los datos; no se infieren al vuelo. RECH23–RECH0 hoy figura `"n:1"` y es `"1:1"` (37 390 filas en ambas).
   - También se admite `"1:0..1"` (B tiene como máximo una fila por cada una del padre, pero no todas): por ejemplo REC42, RE223132, RE516171 y RE758081 frente a REC0111 (34 252 de 37 117). Las filas sin pareja quedan con el corte «sin dato» y cuentan para el control de pérdida de `u`.
1b. **Cortes con tramos y con categorías agrupadas.** Hoy un corte es un diccionario código → rótulo (`tablas_curadas.py`, `VariableCorte.categorias`) y la gramática usa el valor crudo de la columna. Ampliar el esquema de `cortes_estandar.yaml` y la compilación para:
   - `tramos` sobre una variable numérica (HC1): lista de rangos con su rótulo;
   - `agrupa`: una categoría formada por varios códigos (Costa = SHREGION 1 y 2);
   - juegos distintos según la receta (`aplica_a_recetas`).
   - Se compila como `CASE` con parámetros; ningún rótulo entra al SQL como texto. Prueba con cadenas maliciosas en los rótulos.
2. **Universo analítico según la medición.**
   - Una receta nombra su universo (`universo_analitico`) y el verificador lo aplica completo. Si el nombre no existe o no corresponde a la unidad, es falla del plan.
   - En un plan compuesto, el verificador elige el universo por la **medición** de las variables que intervienen (`aplica_a.mediciones` de `universos_analiticos.yaml`): una variable de hemoglobina exige `nino_hecho_hb_medida`.
   - La medición de cada variable se declara por tabla y batería en la tabla curada `curados/inferencia/mediciones.yaml`, nunca por el LLM.
3. **Recetas:** quitar de `cortes_no_permitidos` y pasar a `cortes_permitidos` los cortes `grupo_edad`, `region_natural` y `quintil_riqueza`, con los tramos y rótulos de M1-01.
4. **Doradas por corte.** `cifras_doradas.csv` solo identifica una cifra por nivel y territorio, y lo leen también la capa 0 y el motor actual: **no se toca.** Las doradas con corte van en un archivo nuevo, `curados/inferencia/doradas_cortes.csv` (`id_cifra, receta_id, anio, nivel, territorio, corte, categoria, valor_publicado, decimales, casos_publicados, cita`), y se amplían la clase `Dorada` y `reproducir_doradas` (`recetas.py`) para leerlo. Se toman del informe «Indicadores de Resultados de los Programas Presupuestales, ENDES 2024» (`pap_endes2024_ppr.pdf`), con cuadro y página:
   - por región natural (Costa, Sierra, Selva): Cuadros 04, 06 y 6.1;
   - por quintil de bienestar (5): los mismos cuadros;
   - por tramo de edad: Cuadros 06B y 6.1B (anemia, 5 tramos) y Cuadro 04 (desnutrición crónica, 2 tramos).
   - Cada cifra se copia del PDF (no de este backlog) y la revisa el auditor-agente. El informe es el recurso `endes-2024-informe-ppr` (M1-00). Los cuadros están en las hojas 51 (04), 57 (06B) y 60 (6.1B) del PDF.
   - Referencia para comprobar el resultado, medida por el auditor del supervisor el 12/11: Costa 7,3 / 36,1 / 27,0; quintil inferior 22,4 / 54,8 / 47,5 (desnutrición crónica, anemia criterio anterior, anemia OMS 2024).
5. **Pruebas:**
   - las recetas reproducen las doradas nuevas (±0,1 pp) y sus casos;
   - las 90 filas siguen iguales al cubo;
   - exigir HC55 = 0 no cambia ninguna de las 90 filas (hoy son 0 filas afectadas) y una prueba sintética muestra que sí excluye cuando HC55 ≠ 0.

## Criterios de aceptación

- [x] Las 3 recetas calculan por región natural, quintil y tramo de edad, y reproducen todas las doradas nuevas.
- [x] 90 filas con diferencia 0 frente al cubo.
- [x] La unión por el padre común rechaza los casos que no son 1:1 (prueba).
- [x] Revisión del auditor-agente de las doradas nuevas y de la tabla de mediciones en `evidencia/m1-03_revision.md`.

## Fuera

Uniones entre unidades distintas (por ejemplo, niño con su madre): M1-07 las declara y M1-11 las usa.
