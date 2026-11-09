# Auditoría de dependencia — paquetes de R del verificador (`renv` 1.3.1, `nanoparquet` 0.5.2, `survey` 4.5 y dependencias)

Plantilla de M0-00b (`backlog/plantillas/auditoria_dependencia.md`).

**Historia:** M0-09 · **Fecha:** 9/11/2026 · **Quién la hizo:** agente

> **Estado: aprobado con condiciones.** El dueño restauró la biblioteca el 9/11/2026 solo con binarios de la instantánea de Posit (`sonoma-arm64`), sin la caché de renv, y regeneró `renv.lock` con el `minqa` 1.2.8 real (commit `2847b2b`). No se compiló nada en el Mac.

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** `survey` calcula proporciones con diseño muestral (la segunda implementación frente a `svy`); `nanoparquet` lee el Parquet del sintético; `jsonlite` lee los parámetros; `renv` fija las versiones.
- **Alternativa sin dependencia nueva:** ninguna. El objetivo es contrastar contra una implementación independiente; `arrow` en lugar de `nanoparquet` arrastra mucho más (tecnologías §3).
- **Dónde se usa:** solo `verificador_r/verificar.R`, que corre a mano en el Mac (`just esperados-r`), nunca dentro de pytest ni en la web.

## 2. Origen y antigüedad
Fuente única: CRAN, a través de la instantánea `https://packagemanager.posit.co/cran/2026-10-26` (Posit Package Manager), fijada en `verificador_r/renv.lock` (`R.Repositories`). La instantánea tiene 14 días o más de antigüedad el 9/11/2026 (hoy: 14 días justos, regla de M0-00b).

| Paquete | Versión | Publicada (CRAN) | Días al 9/11/2026 | Licencia |
|---|---|---|---|---|
| `renv` | 1.3.1 | 6/10/2026 | 34 | MIT |
| `nanoparquet` | 0.5.2 | 16/9/2026 | 54 | MIT |
| `survey` | 4.5 | 24/2/2026 | 258 | GPL-2 \| GPL-3 |
| `jsonlite` | 2.0.0 | 27/3/2025 | 592 | MIT |
| `minqa` | 1.2.8 | 17/8/2024 | 449 | GPL-2 |
| `mitools` | 2.7 | 31/8/2026 | 70 | GPL-2 |
| `Rcpp` | 1.1.2 | 5/7/2026 | 127 | GPL-2 \| GPL-3 |
| `RcppArmadillo` | 15.6.2-1 | 17/10/2026 | 23 | GPL-2 \| GPL-3 |
| `numDeriv` | 2016.8-1.1 | 6/6/2019 | 2 713 | GPL-2 |
| `DBI` | 1.3.0 | 25/2/2026 | 257 | LGPL-2.1 \| LGPL-3 |
| `Matrix`, `lattice`, `survival` | 1.7-6, 0.23-1, 3.8-12 | vienen con R 4.6.2 (paquetes recomendados) | — | GPL |

- **Versiones que no entran:** `renv` 1.2.4 y `nanoparquet` 0.5.1 (no pasaron la auditoría anterior; M0-09 las excluye).
- **`survey` 4.5-2:** no existe en CRAN el 9/11/2026 (la 4.5 es la última publicada); ver `m0-09_r.md`.
- **Versión retirada:** ninguna (todas las versiones del lock son las actuales de CRAN el 9/11/2026).
- **Versión fijada:** sí, `renv.lock` fija versión y repositorio. El lock que escribió renv **no trae hash por paquete**; la integridad la da la instantánea fechada. Una prueba (`tests/inferencia/test_verificador_r.py`) valida versiones y repositorio.

## 3. Qué trae
- **Dependencias nuevas que arrastra:** las de la tabla (`survey` → `minqa`, `mitools`, `numDeriv`, `Rcpp`, `RcppArmadillo`, `DBI`, `Matrix`, `lattice`, `survival`). Todas de CRAN, GPL/LGPL/MIT.
- **Binarios, extensiones de C o Fortran, scripts de instalación:** se instalan como **binarios de macOS arm64** de la instantánea fechada de Posit (`https://packagemanager.posit.co/cran/2026-10-26`, etiqueta `4.6-macos-arm64`), con `options(pkgType = "binary")`; no se compila nada. Traen código nativo ya compilado de C/C++ (`jsonlite`, `nanoparquet`, `Rcpp`, `RcppArmadillo`, `survey`) y de Fortran (`minqa`). `nanoparquet` trae copias empaquetadas de zstd, snappy, thrift y miniz. Ningún paquete usa un script de instalación propio (`configure` de `RcppArmadillo` solo detecta el compilador).
- **Qué hace en segundo plano:** nada de red al cargarse. `renv` descarga solo en `restore()`/`install()`, del repositorio fechado.

## 3b. Binarios descargados (sha256)

Cada binario de la instantánea `https://packagemanager.posit.co/cran/2026-10-26/bin/macosx/sonoma-arm64/contrib/4.6/` (redirige a `rspm-sync.rstudio.com/bin/4.6-macos-arm64/`). Huellas tomadas el 9/11/2026 volviendo a bajar cada archivo a una carpeta temporal, sin instalarlo ni ejecutarlo; se comprobó que cada uno es un `.tgz` con su `<paquete>/DESCRIPTION`. Como la restauración del dueño fue sin caché, renv no guardó los archivos que bajó; son los mismos de la misma URL fechada.

| Paquete | Versión | sha256 | Bytes | Comprobación |
|---|---|---|---:|---|
| DBI | 1.3.0 | 17ac851d1de50ac43040d42cd413800c4f3dd0ec59596b669f5628db436ad5e9 | 947922 | gzip compressed data; DESCRIPTION=1 |
| Rcpp | 1.1.2 | caf7ac197ebcf3815e02d1079c252c779caef962ff49192f7844c68a0ea58281 | 2298980 | gzip compressed data; DESCRIPTION=1 |
| RcppArmadillo | 15.6.2-1 | 51c4b405377433cd4abe2794ce44282a028d941f4dd641549f3db5fdf537ad4c | 1098776 | gzip compressed data; DESCRIPTION=1 |
| jsonlite | 2.0.0 | 2165a19e5f87f4e7f238da548bad1b7fc3ef8519bfc26f240ceedae67d5b31ad | 1088947 | gzip compressed data; DESCRIPTION=1 |
| minqa | 1.2.8 | 9975b2eb21398d47713fce6765e1ba89df4b2045ec8aad4fec89d432e12b23e8 | 120464 | gzip compressed data; DESCRIPTION=1 |
| mitools | 2.7 | 2dbbe56a662162450a3405dda62c660a19700ec54134a3b259dea7ae12a20e52 | 342081 | gzip compressed data; DESCRIPTION=1 |
| nanoparquet | 0.5.2 | 7ae10aedf0ba6fecc059160f8fcc841b6ce5a0e888c2abecf75841bb08c53bef | 1014316 | gzip compressed data; DESCRIPTION=1 |
| numDeriv | 2016.8-1.1 | 3d62d2677d09104ef7452fd8f759a367684c15e78a13c4a3004f9752ea86ce74 | 115703 | gzip compressed data; DESCRIPTION=1 |
| renv | 1.3.1 | 248a532ef23e6e47b36580c0e4e7add504bb394c99f4e646929f9defaf652acb | 2717179 | gzip compressed data; DESCRIPTION=1 |
| survey | 4.5 | b85e98eaf1d33a9b2b26db37d3037bdca81987408319b6e94da7792c5f30fab5 | 3611443 | gzip compressed data; DESCRIPTION=1 |

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | `osv-scanner scan source -L verificador_r/renv.lock` (9/11/2026) | «No issues found» (12 paquetes analizados) |
| OSV (API) | consulta por paquete y ecosistema CRAN para `survey`, `renv`, `nanoparquet`, `minqa`, `Rcpp`, `RcppArmadillo`, `mitools`, `jsonlite` | `survey`, `renv`, `nanoparquet`, `minqa`, `Rcpp`, `RcppArmadillo`, `mitools`: ninguna. `jsonlite`: RSEC-2023-3 (fuga de memoria en yajl) con rango afectado 0.9.12 a **antes de 1.8.8**; la 2.0.0 no está afectada (la consulta por la versión 2.0.0 no devuelve nada) |
| GitHub Advisories / `pip-audit` | no aplican a CRAN | — |
| Si aparece algo: ¿se alcanza desde nuestro uso? | — | No aparece nada que afecte a las versiones del lock |

## 5. Condiciones de uso
- R corre **solo** como subproceso de `pap.inferencia.verificador_r`: `Rscript --vanilla`, lista de argumentos sin shell, parámetros en JSON, entorno mínimo sin `PAP_ANTHROPIC_API_KEY` ni `GH_TOKEN` (C11); probado en `test_verificador_r.py` (`test_el_entorno_minimo…`, `test_la_llamada_es_rscript_vanilla…`).
- `verificar.R` no llama a `system()` ni a la red, no instala paquetes y solo lee el JSON y el Parquet (probado por inspección del código en el mismo archivo de pruebas).
- R no corre dentro de pytest ni en la web; los esperados se generan una vez y se versionan con las versiones en la cabecera.
- Subir cualquier versión del lock exige repetir esta auditoría y regenerar los esperados.
- La biblioteca se restaura solo con binarios y sin caché: `RENV_CONFIG_CACHE_ENABLED=FALSE` y `options(pkgType = "binary")` (`verificador_r/README.md`). Ningún `Title` del lock puede decir «stub» y todos los paquetes vienen de `CRAN` o `RSPM` (`tests/inferencia/test_verificador_r.py`).
- `Matrix`, `lattice` y `survival` son paquetes recomendados que vienen con R 4.6.2: no se descargan.

## 6. Veredicto
**Aprobado con condiciones** (las de la sección 5).
- **Revisión siguiente:** al subir `survey` (por ejemplo, cuando aparezca la 4.5-2 en CRAN), `renv` o `nanoparquet`, y al cerrar cada slice.
