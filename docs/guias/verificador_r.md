# Estrategia: R como verificador de las encuestas

> **Estado: DIFERIDA (decisión del dueño, 9/10/2026).** Se guarda para usarla cuando haga falta. Por ahora la validación de las cifras de encuesta es contra lo publicado por el INEI (R-ENC-18). El prototipo ya mostró que svy y R `survey` coinciden (≤ 1e-13 en la ENAHO 2025). Se retoma si una cifra no reproduce al INEI, si svy cambia de versión mayor o al desplegar el proyecto en la nube.
>
> **Resuelto después de la auditoría (9/10/2026):** la variante NCHS de Korn-Graubard ajusta primero por grados de libertad y trunca después (hallazgo A4). Se comprobó con el Apéndice II de Parker et al. 2017 (`referencias/sr02_175.pdf`): con n = 74 y n efectivo 108,7, se obtiene el publicado 36,0–59,7 solo con ese orden. Coincide con `ci_method="korn-graubard"` de svy. El estrato de diseño de la ENAHO (departamento × estrato) ya se guarda en `enaho_sumaria.id_estrato_diseno`.

Definida el 9/10/2026 a partir del informe del analista (`analista/informe.md`) y de la auditoría independiente (`auditor/auditoria.md`, veredicto «apto con correcciones»; las 13 correcciones están incorporadas abajo). Pendiente de visto del dueño en 3 puntos (§6).

## 1. Qué hace R y qué no

- **svy** (Python) calcula todas las cifras que se publican. **R `survey`** las recalcula por separado y deben coincidir (≤ 1e-6). R es el «oráculo»: verifica el **cálculo**.
- La **preparación** de los datos (factor, recodificación, agrupación de años) la hace Python y R no la ve. Esa parte la verifican las pruebas unitarias y la comparación con las cifras publicadas por el INEI (±0,1 pp, R-ENC-18).
- R se llama como proceso aparte (`Rscript`), sin rpy2. Nunca lee los crudos.

## 2. Paquetes y versiones

| | Decisión |
|---|---|
| Paquetes de R | **`survey`** (4.5) y **`jsonlite`**. Infraestructura: **`renv`**. Sin arrow ni haven |
| Versión de R | La del Mac (R 4.6 pide macOS 14 o superior). `renv.lock` la registra; no se fija la menor (4.2-1 y 4.5 dieron resultados idénticos) |
| Python | Agregar `svy==0.32.1` (exacta) y `polars` a `pyproject.toml`. **`pyreadstat` no hace falta**: svy lee `.dta` y `.sav` |

## 3. Cómo queda en el repo

```
verificador_r/
  verificar.R          # oráculo (contrato pap-verificador/1)
  .Rprofile, renv.lock, renv/activate.R, renv/settings.json   # en git; renv/library/ fuera
  casos/<caso>.json    # 20–30 cifras doradas, con la cifra del INEI y su cita
  registro/<caso>.json # resultado versionado
  respaldo/instalar_contenedor.sh
src/pap/oraculo_r.py         # extracto → Rscript → comparar → registrar
tests/test_verificador_r.py
```

Comando: `uv run pap verificar-encuestas [--caso X] [--oraculo auto|si|no]` (y `just verificar-encuestas`).

**Intercambio:**
- Python arma un extracto con solo `y`, `peso`, `estrato`, `upm`, los dominios y `universo` (unos 200 KB en CSV.gz). Va a una carpeta temporal y se borra; queda solo su huella, así que no hay copias del crudo.
- La especificación y la salida van en JSON.
- Las filas fuera del universo no se borran: se estiman como subpoblación.

**Salida por celda (R-ENC-01):**
- estimación, EE, CV, gl, n sin ponderar y deff;
- IC por dos métodos: beta (`svyciprop`) y la variante del NCHS;
- `n_efectivo` = min(n, p(1−p)/EE²), y aparte `n_efectivo_bruto` (corrección A5).

## 4. Reglas del registro (corregidas tras la auditoría)

El registro guarda las filas de R en git, así que pytest compara svy contra R aunque no haya R instalado. Para que no se pueda aprobar por accidente (A1, A2):
1. Las huellas de la especificación y del extracto deben coincidir en R, en svy y en los archivos de entrada. El caso tiene que ser el mismo y los dominios idénticos en ambos lados, con al menos 1 fila. La cifra del INEI es obligatoria.
2. El registro guarda además las huellas de `verificar.R`, de `renv.lock`, del crudo y **del código de preparación**, y la versión de svy. Si cualquiera cambia, el registro queda **vencido** y pytest falla con «corre `pap verificar-encuestas` donde esté el almacén».
3. Sin R, pytest **no falla por no tener R**: falla solo si el registro está vencido o discrepa.
4. La derivación de cada variable es una expresión ejecutable que Python aplica de verdad, no un texto de documentación (A8).

## 5. Precisiones por encuesta

- **ENAHO:** el estrato de diseño por defecto es **departamento × estrato**, porque la ficha técnica dice que la muestra es «independiente en cada departamento» (A3). La cifra no cambia; el EE cambia hasta en 6,7 %. Antes de fijarlo se confirma contra los IC del informe técnico del INEI.
- **ENDES:**
  - Diseño: peso `hv005/1e6`, estrato `hv022`, conglomerado `hv021`. Al agrupar años: año×estrato y año×conglomerado.
  - Los pesos están normalizados, así que **prohibido estimar totales** con ellos (A7).
  - En 2025 hay 17 estratos con un solo conglomerado: un caso dorado debe cubrirlo.
  - Los nombres de variables se pasan a minúsculas, porque `.sav` y `.dta` difieren (A12). Códigos como 9998 se recodifican de forma explícita.
- **Casos dorados obligatorios:**
  - uno con valores nulos y uno con subpoblación (A6);
  - uno de ENDES con estratos de un solo conglomerado;
  - uno con años agrupados, calculado a mano.
- **svy:** usar solo los nombres canónicos `beta` y `korn-graubard`. Los alias `kg` y `clopper-pearson` se rechazan (A13).
- **Corrección a la investigación del stack (§4.1):** en svy, `ci_method="korn-graubard"` **no** equivale a `svyciprop(method="beta")`. El equivalente de esa función es `ci_method="beta"`.

## 6. Pendiente del dueño

1. **Variante del IC para proporciones.** Recomendación: publicar la del NCHS, porque R-ENC-04 usa sus umbrales. Pero el orden de truncar y ajustar es ambiguo (A4: en 14 celdas chicas, 28,7 % frente a 30,3 %). Hay que fijarlo con el documento del NCHS (Parker et al. 2017, https://www.cdc.gov/nchs/data/series/sr_02/sr02_175.pdf), que no podemos bajar desde aquí: bajarlo con el navegador. Mientras tanto se verifican ambas variantes.
2. **El R del contenedor de Claude** (survey compilado desde github.com/cran/survey en la misma versión del lock, con `r-recommended`) puede firmar registros como `entorno: respaldo-contenedor`, para trabajar sin tu Mac. **Recomendación: sí**, con una compuerta en el código: para publicar se exige al menos un registro `mac-renv` vigente (A11).
3. **Estrato ENAHO:** departamento × estrato (recomendado, §5).

## 7. En tu Mac (una vez, cuando exista `verificador_r/`)

```bash
cd verificador_r   # desde la raíz del repositorio
Rscript -e 'install.packages("renv", repos="https://cloud.r-project.org")'
Rscript -e 'renv::init(bare=TRUE, restart=FALSE)'
Rscript -e 'options(pkgType="binary"); renv::install(c("survey","jsonlite"))'
Rscript -e 'renv::snapshot(type="all", prompt=FALSE); renv::status(); print(packageVersion("survey"))'
cd ../.. && uv sync && uv run pap verificar-encuestas --oraculo si
```

Si `install.packages` se detiene porque la librería no es escribible, primero: `mkdir -p ~/Library/R/library && export R_LIBS_USER=~/Library/R/library`. Si pide compilar, instalar las Command Line Tools con `xcode-select --install`.
