# Auditoría de dependencia — paquetes de R del verificador (`renv` 1.3.1, `nanoparquet` 0.5.2, `survey` 4.5 y dependencias)

Plantilla de M0-00b (`backlog/plantillas/auditoria_dependencia.md`).

**Historia:** M0-09 · **Fecha:** 9/11/2026 · **Quién la hizo:** agente

> **Estado: aprobado con condiciones; el paso «compilado en el Mac» de `survey`/`minqa` está pendiente** (C-M0-09-1: falta `gfortran`).
> Hasta que el dueño lo instale y se corra `renv::restore()`, `survey` y `minqa` no están instalados con el lock.

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
- **Binarios, extensiones de C o Fortran, scripts de instalación:** se instalan **desde fuente** (no hay binarios de macOS para R 4.6). Compilan C/C++ (`jsonlite`, `nanoparquet`, `Rcpp`, `RcppArmadillo`, `survey`) y **Fortran** (`minqa`). `nanoparquet` trae copias empaquetadas de zstd, snappy, thrift y miniz. Ningún paquete usa un script de instalación propio (`configure` de `RcppArmadillo` solo detecta el compilador).
- **Qué hace en segundo plano:** nada de red al cargarse. `renv` descarga solo en `restore()`/`install()`, del repositorio fechado.

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
- **Pendiente (C-M0-09-1):** instalar `gfortran` oficial de R en el Mac, correr `renv::restore()` y comprobar que `minqa` y `survey` compilan desde el lock; después, anotar aquí la fecha. El `gfortran` es una herramienta de sistema que instala el dueño; el agente no bajó ningún compilador de terceros (F-04).

## 6. Veredicto
**Aprobado con condiciones** (las de la sección 5; la compilación en el Mac, pendiente).
- **Revisión siguiente:** al subir `survey` (por ejemplo, cuando aparezca la 4.5-2 en CRAN), `renv` o `nanoparquet`, y al cerrar cada slice.
