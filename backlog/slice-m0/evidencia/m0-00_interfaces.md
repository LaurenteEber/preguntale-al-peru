# M0-00 — Interfaces actuales que reutiliza el motor nuevo

Mapa levantado el 9/11/2026 sobre `main` en `850ba79`. Líneas exactas del código de hoy.

## 1. ENDES: `src/pap/capa0/encuestas.py` y `curados/capa0/definiciones_endes.yaml`

| Concepto | Dónde | Qué hace |
|---|---|---|
| Peso | `encuestas.py:144` | `peso_hogar = HV005 / 1e6` |
| Peso 2020 | `encuestas.py:145`, `:163` | `HV005A / 1e6` si existe; si no, `peso_hogar` |
| Estrato | `encuestas.py:140` | `f"{HV024:02d}-{HV022}"` |
| UPM | `encuestas.py:137` | `id_conglomerado = HV021` |
| Población de hecho | `encuestas.py:146` (RECH1 leído en `:114`) | `pernocto = HV103 == 1` |
| Edad | `encuestas.py:148` | `edad_meses = HC1` |
| Anemia 2015–2023 | `encuestas.py:154`, `:167-168` | `HC57` en 1–4; `anemia_hist = nivel ≤ 3` |
| Anemia OMS 2024 | `encuestas.py:155`, `:167-168` | `HC57A` en 1–4; `anemia_oms2024 = nivel ≤ 3` |
| DCI | `encuestas.py:157`, `:169-170` | `haz = HC70/100` con HC70 en −9989…9989 (`haz_valido`); `dci = haz < −2` (≡ HC70 < −200) |
| Universo | `encuestas.py:213-227` | `_en_universo`: edad, `hb_medida`, `variable_no_nula`, `haz_valido`, `pernocto` |
| Parámetros | `definiciones_endes.yaml:13-34` | anemia 6–35 m (`:17`); OMS 2024 (`:23-27`); DCI 0–59 m (`:31-34`) |

Precisión respecto de la historia: cada indicador de anemia lee **una** variable (`endes_anemia_6_35m` → HC57; `_oms2024` → HC57A), no «HC57 o HC57A». La edad de la DCI es 0–59 meses.

**Lecturas de ZIP en memoria (A3):** `encuestas.py:64` (`t.write(z.read(miembro))`), `insumos.py:105` (`miembro_zip`) y `insumos.py:110` (`miembros_zip`).

## 2. Ámbitos: `src/pap/capa0/ambitos_lima.py` y `src/pap/motor/calculo.py:157-160`

- `ambito_por_ubigeo` (`ambitos_lima.py:41-48`): `"15…"` → LIMA_REGION (`:45`); `"1501…"` → LIMA_METROPOLITANA (`:46`, sobrescribe); `"07…"` → CALLAO (`:47`). El orden importa.
- `ambito_lima_endes` (`:60`): desde 2018 por ubigeo (`ENDES_PRIMER_ANIO_UBIGEO = 2018`, `:36`); 2015–2017 por estrato (`ENDES_ESTRATOS_2015_2017`, `:38`).
- Departamento sin el 07: `calculo.py:159` (ENDES) y `:191` (ENAHO), `departamento.where(departamento != "07")`.
- `calculo.py:157-160` arma `etiquetas`: `nacional="PE"`, `dominio_subnacional=area`, `departamento` sin 07 y los ámbitos de Lima.

## 3. `src/pap/motor/calculo.py`

- `_svy_niveles(d, y, universo, etiquetas, estrato, psu, peso) -> list[dict]` (`:108-140`). Un dict por (nivel, territorio): `nivel`, `territorio_id`, `valor` (%), `ee` (%), `cv`, `ic_inf`, `ic_sup` (%), `gl`, `n_muestra`, `deff`, `n_efectivo`.
- svy: `svy.Sample` (`:120`) con `svy.Design(stratum="h", psu="c", wgt="w", singleton=svy.Singleton("center", domains="standard"))`; `estimation.prop("y", by=col, where=…, ci_method="korn-graubard", deff="wr")` (`:124-125`); si el dominio no tiene «sí», usa el complemento (`:126-135`).
- `n_efectivo = p(1−p)/ee²` (`:139`), **sin tope**. El tope está en `reglas_etapa4.py:320` (`min(n_ef, n)`).
- Redondeo: `DECIMALES = 8` (`:32`), comentario en `:643`, `round(DECIMALES)` en `:646` (valor, ee, cv, ic, n_efectivo, deff, numerador, denominador, cotas) y `:648`.

## 4. `src/pap/motor/validador/reglas_etapa4.py` (oráculo de las compuertas)

| Regla | Líneas | Parámetros (`reglas.json` vía `ctx.param`) | Acción |
|---|---|---|---|
| R-ENC-02 | `:236-248` | `n_min_suprimir=25`, `n_min_publicar=50` | `suprimir` si n < 25; `publicar_referencial` si 25–49 |
| R-ENC-03 | `:262-299` | `cv_publicar=0.15`, `cv_suprimir=0.30`, `p_min_regla_cv=0.10`, `p_max_regla_cv=0.90`; `gl_min` de R-ENC-04 | `publicar_referencial` (modificador si gl < 8); `suprimir` si cv > 0.30; `revision_humana` si la estimación es 0 (media, total o razón) |
| R-ENC-04 | `:302-352` | `n_efectivo_suprimir=30`, `ancho_abs_max=0.30`, `ancho_rel_max=1.30`, `ancho_abs_presentar=0.05`, `ancho_rel_referencial=0.59`, `n_efectivo_min=50`, `gl_min=8`, `cv_referencial_inei=0.15` | `suprimir` o `publicar_referencial`; `rotular` si numerador = 0 o = denominador |

- `c` es una `Cifra` (`nucleo.py:79`), armada con `Cifra.desde(fila, ind)`; en proporciones, `p = valor/100` y `ee_prop = ee/100`.
- `ctx` es un `Contexto` (`nucleo.py:117`); `ctx.param(rid, clave)` en `nucleo.py:134`.
- `accion_final` (`nucleo.py:243`) toma la más restrictiva; `estado_cifra` (`:259`) da publicable, referencial, suprimida o sin_datos.
- Las tres están en la etapa `4_precision` (`reglas.json:368-376`).
- En ENDES el cubo no guarda `numerador` ni `denominador`: la cláusula «Además» de R-ENC-04 cae en `p == 0` o `p == 1`.

## 5. Consolidador (`reglas/consolidador/`)

- Fuente: `propuestas/*.json` (`consolida_reglas.py:5`), y encima las capas de `ajustes_dueno.py`:
  - `PARCHES_REGLAS` (`:30`): reemplaza texto exacto que aparece una vez (`consolida_reglas.py:133-135`);
  - `AGREGADOS_REGLAS` (`:39`): agrega texto al final de un campo (`consolida_reglas.py:136`);
  - `CAMPOS_REGLAS` (`:78`): reemplaza un campo por ruta. La guardia (`consolida_reglas.py:167-168`) falla si pisa un campo ya corregido, salvo `SOBRESCRITURAS_CONSCIENTES`.
- Reglas nuevas: `NUEVAS_GASTO_R2` (`ajustes_dueno.py:536`; `consolida_reglas.py:165`) y `ETAPAS_GASTO_R2 = [(rid, etapa, tras)]` (`:709`).
- La lógica Python vive en `validador/reglas_etapa*.py` con `@regla` (`nucleo.py:193`).
- Verificación: `python3 -I reglas/consolidador/pruebas/vp3_checks.py .` y `python3 reglas/consolidador/pruebas/prueba_guardia.py` (sale con 1 si hay fallos, `:36`).

## 6. Registro e insumos

- `registrar(rutas, source_id, archivos=None, …)` (`registrar.py:167`), `construir_recurso` (`:90`). No escribe el lock.
- `escribir_lock` (`insumos.py:58-76`): suma el hash de cada insumo usado (salvo `CAPA0:`, `CURADO`, `ESTANDARIZADA:`, `:29`); une con los fijados salvo `ACTUALIZAR_LOCK` (`:28`). Lo llama `cli.py:242` (`pap construir`).
- `filtrar_por_lock` (`insumos.py:42-55`).
- `curados/insumos.lock.yaml`: `FUENTE:` con una lista `- sha256:<hash>` (INEI-ENDES tiene 22).

## 7. Catálogo ENDES 2024 (`curados/recetas/inei_microdatos_catalogo.json`, código 968)

Los 13 módulos traen `url_stata`, `url_spss` y `url_ficha`:

1629 Características del Hogar · 1630 Características de la Vivienda · 1631 Datos Básicos de MEF · 1632 Historia de Nacimiento – Tabla de Conocimiento de Método · 1633 Embarazo, Parto, Puerperio y Lactancia · 1634 Inmunización y Salud · 1635 Nupcialidad – Fecundidad – Cónyuge y Mujer · 1636 Conocimiento de Sida y uso del condón · 1637 Mortalidad Materna – Violencia Familiar · 1638 Peso y talla – Anemia · 1639 Disciplina Infantil · 1640 Encuesta de salud · 1641 Programas Sociales

`url_patron` (`curados/recetas/INEI-ENDES.yaml:9`): `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/{formato}/{codigo}-Modulo{modulo}.zip`.

## 8. Oráculo de compuertas (tarea 5)

No hay un punto de entrada que recorra el cubo con la etapa 4. El oráculo se arma con las funciones existentes, sin reimplementar nada: `backlog/slice-m0/evidencia/m0-00_estados_cubo.py` (usa `cargar_contexto`, `Cifra.desde`, `correr_regla`, `accion_final` y `estado_cifra`). Resultado en `m0-00_estados_cubo.csv`: **90 filas, 85 publicables y 5 referenciales** (las 5 de DCI por R-ENC-04: Lima Región y los departamentos 04, 17, 18 y 23).

Alcance: el oráculo solo corre R-ENC-02 a R-ENC-04, que son las que replica M0-09. El estado completo de una respuesta también depende de las otras etapas (p. ej. R-ENC-06 y R-ENC-10), que siguen fuera de las compuertas de M0.
