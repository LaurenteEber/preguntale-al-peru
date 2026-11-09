# Stack tecnológico — decisión y fundamentos

Versión 1.1 · 9 de octubre de 2026 · Estado: **aprobado por el dueño (6/10/2026)**; ajustes del 9/10/2026 en las filas Entorno, Encuestas y Servicio y en §6–§7.
Base: investigación con pruebas propias (`00_proyecto/investigacion/investigacion_stack.md`), validada por el orquestador.

## 1. Qué exige el proyecto (criterios de decisión)

| # | Requisito | Consecuencia técnica |
|---|---|---|
| 1 | Mismo crudo → mismas cifras | Formatos y cálculos deterministas; versiones fijadas |
| 2 | Cada cifra trazable hasta el archivo crudo exacto | Hash por archivo y por tabla; manifiestos; IDs estables |
| 3 | Estadística de encuestas complejas correcta | Varianza de diseño, IC Korn-Graubard, agrupación de años |
| 4 | Costo bajo o cero | Herramientas libres y locales; sin servidores al inicio |
| 5 | Mantenible por una persona con IA | Pocas piezas, sin servicios que operar, Python y SQL |
| 6 | Servir una web rápida (< 1–2 s) | Cubo de indicadores precalculado, consultas parametrizadas |
| 7 | Mapas | Formato geoespacial abierto y simple |
| 8 | Decir «esta respuesta usó la versión X» | Versión de la biblioteca en cada respuesta |

Volumen: decenas de GB de crudos (gasto MEF: 1–3 GB por año) y pocos GB curados; actualizaciones mensuales o anuales. Las descargas de .gob.pe solo funcionan desde tu laptop.

## 2. ¿DuckDB y Parquet son apropiados? Sí, con roles distintos

- **Parquet es la fuente de verdad** de cada tabla estandarizada, curada e indicador: es un formato abierto que leen Python, R, DuckDB y el navegador; comprime unas 8 veces (834 MB de CSV → 104 MB) y, escrito ordenado, da bytes idénticos entre corridas.
- **DuckDB es el motor**: procesa el CSV grande sin cargarlo en memoria. En la prueba con 5 millones de filas tardó 1,6 s con 207 MB de RAM; pandas tardó 8,5 s con 1,8 GB, lo que no cabe con holgura para los 3 GB del MEF.
- **El archivo `.duckdb` es un artefacto derivado**: se reconstruye desde los Parquet y nunca es fuente de verdad, porque no es idéntico byte a byte entre corridas y su formato cambia entre versiones (llega DuckDB 2.0 este mes).

Alternativas descartadas para esta etapa: PostgreSQL/PostGIS (un servidor que operar sin necesidad), SQLite (lento para agregaciones grandes), Iceberg/Delta (pensados para equipos y data lakes), un único `.duckdb` como biblioteca (riesgo de formato y de no determinismo), DuckLake (prometedor, pero sus Parquet no son autosuficientes y depende de una extensión que se descarga; se reevalúa con su versión 1.1 de fines de octubre).

## 3. Decisión por capa

| Capa | Ahora (capa 0 + piloto) | Después (web) | Diferido hasta que… |
|---|---|---|---|
| Entorno | **uv + Python 3.12.16** (`.python-version`; ≥ 3.12.12 por CVE-2024-0450 y CVE-2025-8291 de `zipfile`) con `uv.lock`, `exclude-newer = "2 weeks"` e instalación con `--locked --no-build`; git. Hoy corre en el Mac del dueño | **Despliegue en un servicio en la nube con todo el proyecto** (código, almacén de crudos, biblioteca y web), con una imagen Docker desde `uv.lock` (decisión del dueño, 9/10/2026) | pixi: si R pasa a motor productivo |
| Crudos | Archivos inmutables guardados por su huella SHA-256, con manifiesto (ver `docs/especificaciones/datos_crudos.md`) | Igual | DVC/rclone: si hay que sincronizar crudos entre máquinas |
| Formato curado | **Parquet** (zstd), ordenado por clave; montos en DECIMAL; ubigeo como texto de 6 dígitos | Igual | — |
| Motor de transformación | **DuckDB SQL** para lo pesado; **Polars o pandas** para Excel y PDF; un script o un `.sql` por paso | Igual | SQLMesh o dbt: con más de 40–60 modelos o un segundo colaborador |
| Encuestas | **svy** (Python, versión exacta en `uv.lock`) como motor; lectura de SPSS/Stata con **pyreadstat**. **La validación es contra las cifras publicadas por el INEI** (R-ENC-18; `curados/capa0/cifras_control_inei.yaml`). Versiones (M0-03, 9/11/2026): `svy` 0.35.0 y `pyreadstat` 1.3.7, con `pydantic` 2.13.5 y `ftfy` 6.3.1 declaradas. **Política de `svy`:** versión exacta; cada cambio de versión es una historia propia (F-05) con su regresión de cifras y errores estándar contra el cubo anterior. El verificador con R se **activa en M0-09** (antes diferido): el prototipo mostró que svy y R `survey` coinciden (≤ 1e-13 en la ENAHO 2025) y allí se compara `svy` 0.35.0 con R | Cifras precalculadas | Verificador R (`estrategia.md`): si svy cambia de versión mayor, si una cifra no reproduce al INEI o al desplegar en la nube; R como motor: si svy no coincide en algún caso |
| Orquestación | **justfile + CLI propia** (`pap`), incremental por hash | Tarea programada mensual con la misma CLI | Dagster: ejecución desatendida o más de ~100 activos |
| Calidad de datos | Pruebas SQL + pandera | Igual | — |
| Validador de reglas (96 vigentes; 68 en el piloto) | Código propio: reglas en YAML compiladas a SQL | Corre antes de publicar cada versión | — |
| Metadatos | **Frictionless Data Package v2** + términos DCAT 3 y PROV-O | Exportar schema.org/DCAT en la web | OpenLineage, RO-Crate |
| Geoespacial | GeoPandas → **GeoParquet** (completo y simplificado) | Geometrías estáticas; PMTiles si crece | PostGIS |
| Servicio web | — | En el servicio en la nube: **FastAPI + DuckDB en solo lectura** sobre un cubo precalculado (~2 ms por consulta en la prueba) | PostgreSQL solo para datos de usuarios; MotherDuck si no se quiere operar servidor |
| Versionado | `version_lib` (etiqueta git) + hash de contenido de cada tabla | Cada respuesta guarda `version_lib` | DuckLake snapshots |

## 4. Reglas técnicas que se derivan

1. **Determinismo**: las sumas en coma flotante dan resultados distintos entre corridas paralelas. Los montos se guardan en DECIMAL, las estimaciones se redondean a precisión fija antes de guardar y todo Parquet se escribe con `ORDER BY`. El hash de versión se calcula sobre los Parquet, nunca sobre el `.duckdb`.
2. **Versiones fijadas**: DuckDB 1.5.x hasta que DuckDB 2.0 tenga su primer parche y pase las pruebas con cifras de referencia.
3. **Encuestas**: unas 20–30 cifras «doradas» (pobreza ENAHO, anemia ENDES por departamento y año) deben coincidir con R y con lo publicado por el INEI antes de usar cualquier indicador de encuesta. La agrupación de años sigue la regla EST-06: en ENAHO se conserva el estrato original y el conglomerado estable; solo en ENDES se usa año × estrato.
4. **Extensiones de DuckDB** (`spatial`, `ducklake`): se descargan al usarse y fallan detrás de un proxy; se usan solo en tu laptop o precargadas.
5. **Memoria**: en los pasos del MEF, `memory_limit` y carpeta temporal fijados; nada de pandas ahí.
6. **Licencias**: todo lo recomendado es MIT, BSD o Apache. Se evita rpy2 (GPL) llamando a R como proceso aparte.

## 5. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| svy está en versión beta y lo mantiene un solo proveedor | Versión exacta fijada; cifras doradas contra el INEI en cada construcción; el verificador R se activa en M0-09 y corre al subir svy de versión o si una cifra no reproduce |
| DuckDB 2.0 sale este mes | Versión fijada; el `.duckdb` se reconstruye desde Parquet |
| Python 3.10 de tu laptop llega a fin de vida este mes y no sirve para svy ni GeoPandas 1.2 | uv instala Python 3.12 aparte, sin tocar el del sistema |
| Herramienta propia (CLI `pap`) que hay que mantener | Pequeña (500–800 líneas), con pruebas; la escribe y mantiene la IA |

### Versiones fijadas por la seguridad (M0-00b, 9/11/2026)

| Componente | Versión | Por qué |
|---|---|---|
| Python | 3.12.16 (`.python-version` e imagen `python:3.12.16-slim@sha256:5e2bdb1b…`) | CVE-2024-0450 y CVE-2025-8291 en `zipfile` |
| `uv` en la imagen | 0.13.5 (`ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39…`) | la 0.13.7 tenía menos de 2 semanas |
| Pillow (vía `pdfplumber`) | 13.0.0 (`constraint-dependencies ≥ 13.0.0`) | 12.3.0 tenía 39 advisories de GitHub |
| `certifi` | 2026.10.23 (`≥ 2026.10.18`) | PYSEC-2026-4320 |
| `python-multipart` | 0.0.32 (`≥ 0.0.32`) | la 0.0.33 tenía menos de 2 semanas |
| `opentelemetry-api` | 1.45.1 | la 1.45.2 tenía menos de 2 semanas (la fija `exclude-newer`) |
| `svy` / `svy-io` / `svy-rs` | 0.35.0 / 0.7.1 / 0.19.1 | M0-03 (F-05); las ramas 0.8 y 0.20 de `svy-io`/`svy-rs` son de `svy` 0.36; auditoría en `backlog/slice-m0/evidencia/auditoria_m0-03.md` |
| `pyreadstat` | 1.3.7 | M0-03; misma auditoría |
| `pydantic` / `ftfy` (y `wcwidth` 0.9.4, que arrastra `ftfy`) | 2.13.5 / 6.3.1 / 0.9.4 | declaradas en M0-03; misma auditoría |
| `pytest-socket` (solo desarrollo) | 0.8.1 | pruebas sin red (C5); auditoría en `backlog/slice-m0/evidencia/auditoria_pytest-socket.md` |
| `pip-audit` / `osv-scanner` / `gitleaks` | 2.10.1 / 2.7.0 / 8.30.1 | `just auditar` y el gancho de secretos; no son dependencias del proyecto |

## 6. Aprobado (6/10/2026)

1. Instalar **uv** y **Python 3.12** en tu laptop (no reemplaza el Python del sistema).
2. Usar **svy** como motor de encuestas. ~~Con R como verificador~~ → ajuste del 9/10/2026: el verificador R pasa a funcionalidad posterior; por ahora se valida contra las cifras publicadas por el INEI.
3. Construir la CLI propia `pap` en vez de adoptar un orquestador.


## 7. Ajustes del 9/10/2026 (dueño)

1. **Verificador R diferido (se activa en M0-09).** Se instaló R en el Mac, pero la verificación automática svy ↔ R (`renv`, registros firmados) queda como funcionalidad posterior. Lo avanzado (diseño, auditoría, scripts y resultados) está en `00_proyecto/investigacion/r_verificador/` (`estrategia.md`). Se activa en M0-09 (ajuste del 9/11/2026) y corre también si una cifra no reproduce al INEI, si svy cambia de versión o al desplegar en la nube.
2. **Validación con el INEI.** Toda cifra de encuesta del piloto debe reproducir lo publicado por el INEI (±0,1 pp, R-ENC-18). Desde S4 la estandarización ya lo comprueba con 36 cifras nacionales y departamentales.
3. **Korn-Graubard.** La variante que se publica es la del NCHS (Parker et al. 2017, `r_verificador/referencias/sr02_175.pdf`): primero se ajusta el n efectivo por grados de libertad y después se trunca en n. Se comprobó con los ejemplos del Apéndice II (p. ej., n = 74, publicado 36,0–59,7). En svy es `ci_method="korn-graubard"`; `ci_method="beta"` equivale a `svyciprop(method="beta")` de R. Se corrige así §4.1 de la investigación del stack.
4. **Despliegue.** Hoy todo corre en el Mac del dueño; cuando el proyecto madure se desplegará entero en un servicio en la nube. Consecuencias que ya se cuidan: rutas relativas a la raíz (`PAP_RAIZ`), almacén por huella transportable (1,2 GB) y ninguna dependencia de herramientas instaladas solo en el Mac.
5. **Modo de trabajo.** Analistas y auditores independientes solo donde un error se escaparía fácilmente (definiciones estadísticas, decisiones con varias opciones, cifras que se publican). El trabajo mecánico y verificable con pruebas lo hace el orquestador.
