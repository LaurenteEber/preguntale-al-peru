# Verificador en R (M0-09)

Una segunda implementación, en otro lenguaje, de las proporciones con diseño muestral. Si `svy` (Python) y R `survey` dan lo mismo,
la cifra es confiable aunque no exista una cifra oficial con qué compararla. Diseño: `docs/diseno/tecnologias.md` §3.

**R no corre dentro de pytest.** Se corre a mano en el Mac, una vez, para guardar `tests/esperados/r_survey_sintetico.csv`; pytest
solo compara ese archivo con lo que calcula el adaptador de `svy` (`tests/inferencia/test_esperados_r.py`).

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| `verificar.R` | El verificador. Lee un JSON de parámetros y un Parquet, escribe un CSV con las versiones en la cabecera |
| `verificar_prototipo.R` | El prototipo de la carpeta de trabajo anterior (K-02), sin cambios. `verificar.R` lo adapta; se conserva como referencia |
| `renv.lock`, `renv/activate.R`, `.Rprofile`, `DESCRIPTION` | El proyecto `renv`: las versiones exactas de los paquetes de R |
| `renv/library/` | La biblioteca local. **No se versiona**: se reconstruye con `renv::restore()` |

## Paquetes (de `renv.lock`)

CRAN fijado a una instantánea con fecha: `https://packagemanager.posit.co/cran/2026-10-26` (Posit Package Manager; 14 días de antigüedad o más).

| Paquete | Versión | Nota |
|---|---|---|
| `renv` | **1.3.1** | la 1.2.4 no pasó la auditoría |
| `nanoparquet` | **0.5.2** | lee el Parquet sin `arrow`; la 0.5.1 leía mal los perdidos con `col_select` |
| `survey` | **4.5** | la última de CRAN. **No incluye la corrección de la 4.5-2** (ver abajo) |
| `jsonlite` | 2.0.0 | leer los parámetros |
| `minqa`, `mitools`, `numDeriv`, `Rcpp`, `RcppArmadillo`, `DBI`, `Matrix`, `lattice`, `survival` | ver `renv.lock` | dependencias de `survey` |

### `survey` 4.5 y la corrección de la 4.5-2

La 4.5 (CRAN, 24/2/2026) es la última publicada; la 4.5-2 **no está en CRAN** (ni en la instantánea). El `NEWS` de la 4.5 termina en la
entrada «4.5» y no dice nada de un error del error estándar, así que no se puede afirmar que la 4.5 incluya esa corrección. Lo que sí se
comprobó, con los casos del verificador (dominios por subconjunto, estratos con una sola UPM, una UPM por estrato dentro del dominio), está en
`backlog/slice-m0/evidencia/m0-09_r.md`. Cuando la 4.5-2 o una posterior aparezca en CRAN: subir la instantánea, `renv::update("survey")`,
`just esperados-r` y revisar el diff de `tests/esperados/r_survey_sintetico.csv`.

## Preparar el Mac (una vez)

1. R 4.6.x (`R --version`). No hace falta compilador: la instantánea de Posit del lock trae binarios para macOS arm64
   (`sonoma-arm64`), también el de `minqa`.
2. Reconstruir la biblioteca desde el lock, **solo con binarios y sin la caché de renv**:

```bash
cd verificador_r
RENV_CONFIG_CACHE_ENABLED=FALSE Rscript -e 'options(pkgType = "binary"); source("renv/activate.R"); renv::restore(prompt = FALSE)'
```

`renv::restore()` usa el repositorio fechado del lock (`https://packagemanager.posit.co/cran/2026-10-26`). Con
`pkgType = "binary"` no compila nada; si un paquete no tuviera binario, el restore falla en lugar de bajar los fuentes.

## Generar los esperados

```bash
just esperados-r                                          # con just
uv run python -m pap.inferencia.verificador_r esperados   # lo mismo, directo
```

Esto escribe `tests/esperados/r_survey_sintetico.csv`; después, `uv run pytest -q tests/inferencia/test_esperados_r.py`. Se regenera al
subir `svy` o `survey`. Si `svy` y R difieren más de 1e-9 en `est`, `ee` o el IC (o en `gl` o `n`, que son exactos), **no se afloja la
tolerancia**: se diagnostica (estratos con una sola UPM, variante de Korn-Graubard, grados de libertad) y se escribe una consulta tipo C.

## Cómo se llama (control C11)

`src/pap/inferencia/verificador_r.py` lanza:

```
Rscript --vanilla verificador_r/verificar.R <parametros.json>
```

- como subproceso, con **lista de argumentos y sin shell**;
- con los parámetros en un JSON (se escribe en un directorio temporal);
- con un **entorno mínimo** de lista blanca (`PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`, `R_HOME`): nunca `PAP_ANTHROPIC_API_KEY`, `GH_TOKEN` ni ninguna otra clave;
- `--vanilla` no lee `.Rprofile`, así que `verificar.R` activa el proyecto `renv` por su cuenta (`source("renv/activate.R")`).

`verificar.R` no llama a `system()` ni a la red; las únicas entradas son el JSON y el Parquet.

## Equivalencias con `svy`

| `svy` (Python) | R `survey` |
|---|---|
| `Design(stratum, psu, wgt)` | `svydesign(ids=~upm, strata=~estrato, weights=~peso, nest=TRUE)` |
| `Singleton("center", domains="standard")` | `options(survey.lonely.psu="adjust", survey.adjust.domain.lonely=FALSE)` |
| `prop(..., where=u, by=dominio)` | `des[en_dominio, ]` + `svymean` + `degf` |
| `ci_method="korn-graubard"` | Korn-Graubard NCHS escrito a mano (`ic_kg_nchs`, ocho líneas): `svyciprop(method="beta")` no trunca el n efectivo |
