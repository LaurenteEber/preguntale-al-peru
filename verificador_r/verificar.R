#!/usr/bin/env Rscript
# Verificador ("oráculo") de proporciones con R `survey` (M0-09; docs/diseno/tecnologias.md §3).
#
# Uso (siempre con lista de argumentos, sin shell; ver src/pap/inferencia/verificador_r.py):
#   Rscript --vanilla verificar.R <parametros.json>
#
# Adaptado de verificar_prototipo.R (carpeta de trabajo anterior, K-02): mismo diseño, mismo Korn-Graubard según el estándar
# NCHS escrito a mano, pero lee el Parquet con nanoparquet 0.5.2, recibe todo en un JSON y escribe un CSV con las versiones en la
# cabecera (líneas «# clave: valor»). Los paquetes salen de renv.lock (renv 1.3.1): survey, jsonlite y nanoparquet. Nada más.
#
# Parámetros (JSON):
#   datos, salida     rutas absolutas del Parquet y del CSV de salida
#   diseno            {estrato, upm, peso, nest, lonely_psu}
#   variable, universo, anio, ic.nivel
#   excluir           {columna: [valores]}: filas que se quitan antes de declarar el diseño
#   casos             [{caso, anio, por: [columnas], dominios: [[valor, …], …]}]; un dominio sin casos sale con n = 0

args <- commandArgs(trailingOnly = FALSE)
raiz <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)][1])))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Uso: Rscript --vanilla verificar.R <parametros.json>")
ruta_params <- normalizePath(args[[1]], mustWork = TRUE)

# --vanilla no lee .Rprofile: se activa el proyecto renv a mano (biblioteca local de verificador_r/renv/library)
setwd(raiz)
if (!file.exists("renv/activate.R")) stop("Falta verificador_r/renv/activate.R")
source("renv/activate.R")
suppressPackageStartupMessages({
  library(survey)
  library(jsonlite)
  library(nanoparquet)
})

spec <- fromJSON(ruta_params, simplifyVector = FALSE)
d <- spec$diseno
options(survey.lonely.psu = if (is.null(d$lonely_psu)) "adjust" else d$lonely_psu)
# Igual que svy con Singleton("center", domains="standard"): un estrato que solo es singleton dentro del dominio no cuenta como tal.
options(survey.adjust.domain.lonely = FALSE)
nivel <- if (is.null(spec$ic$nivel)) 0.95 else spec$ic$nivel

datos <- as.data.frame(read_parquet(spec$datos))
for (col in names(spec$excluir)) {
  datos <- datos[!(datos[[col]] %in% unlist(spec$excluir[[col]])), , drop = FALSE]
}
datos$.u <- datos[[spec$universo]] %in% TRUE
if (any(datos$.u & is.na(datos[[spec$variable]]))) stop("Hay filas del universo con la variable nula")
datos$.y <- ifelse(datos$.u, datos[[spec$variable]], 0)       # fuera del universo y no cuenta; 0 evita NA en el subconjunto

# Korn-Graubard según el estándar NCHS (Parker et al. 2017; macro SAS KG_macro): n efectivo ajustado por gl y truncado en n;
# p = 0 o 1 con n efectivo = n. R no lo trae (svyciprop(method = "beta") no trunca), así que se escribe a mano en R base.
ic_kg_nchs <- function(p, ee, gl, n, nivel) {
  a <- 1 - nivel; tol <- 1e-12
  if (is.na(gl) || gl <= 0) return(c(NA_real_, NA_real_))
  borde <- p <= tol || p >= 1 - tol
  if (!borde && ee <= tol) return(c(p, p))
  n_ef <- if (borde) n else p * (1 - p) / ee^2
  if (n > 1) n_ef <- min(n, n_ef * (qt(1 - a / 2, n - 1) / qt(1 - a / 2, gl))^2)
  if (borde) p <- if (p <= tol) 0 else 1
  x <- n_ef * p
  c(if (x > 0) qbeta(a / 2, x, n_ef - x + 1) else 0,
    if (n_ef - x > 0) qbeta(1 - a / 2, x + 1, n_ef - x) else 1)
}

num <- function(x) if (is.na(x)) "NA" else sprintf("%.17g", x)
filas <- list()
for (caso in spec$casos) {
  por <- unlist(caso$por)
  dat <- datos[datos[[spec$anio]] == caso$anio, , drop = FALSE]
  dat[[d$estrato]] <- factor(dat[[d$estrato]])   # survey < 4.4-3 falla con lonely.psu = "adjust" y estratos de texto
  des <- svydesign(ids = as.formula(paste0("~", d$upm)), strata = as.formula(paste0("~", d$estrato)),
                   weights = as.formula(paste0("~", d$peso)), nest = isTRUE(d$nest), data = dat)
  for (dom in caso$dominios) {
    valores <- unlist(dom)
    en_dom <- dat$.u
    for (i in seq_along(por)) en_dom <- en_dom & (as.character(dat[[por[i]]]) %in% valores[i])
    en_dom[is.na(en_dom)] <- FALSE
    n <- sum(en_dom)
    if (n == 0) {
      r <- c(NA, NA, NA, NA, NA)
    } else {
      sub <- des[en_dom, ]                        # subconjunto de dominio: conserva el diseño completo
      m <- svymean(~.y, sub)
      p <- unname(coef(m)[1]); ee <- sqrt(unname(vcov(m)[1, 1])); gl <- degf(sub)
      ci <- ic_kg_nchs(p, ee, gl, n, nivel)
      r <- c(p, ee, gl, ci[1], ci[2])
    }
    filas[[length(filas) + 1]] <- paste(c(caso$caso, caso$anio, paste(valores, collapse = "|"), n, vapply(r, num, "")), collapse = ",")
  }
}

cabecera <- c(
  "# Esperados de R survey para tests/inferencia/datos/sintetico.parquet (M0-09). No editar a mano: just esperados-r",
  paste0("# r: ", R.version$major, ".", R.version$minor),
  paste0("# plataforma: ", R.version$platform),
  paste0("# survey: ", as.character(packageVersion("survey"))),
  paste0("# jsonlite: ", as.character(packageVersion("jsonlite"))),
  paste0("# nanoparquet: ", as.character(packageVersion("nanoparquet"))),
  paste0("# renv: ", as.character(packageVersion("renv"))),
  paste0("# opciones: survey.lonely.psu=", getOption("survey.lonely.psu"),
         ";survey.adjust.domain.lonely=", getOption("survey.adjust.domain.lonely")),
  paste0("# ic: korn-graubard-nchs nivel=", nivel),
  paste0("# md5_parametros: ", unname(tools::md5sum(ruta_params))),
  paste0("# md5_datos: ", unname(tools::md5sum(spec$datos))),
  "caso,anio,dominio,n,est,ee,gl,ic_inf,ic_sup")
writeLines(c(cabecera, unlist(filas)), spec$salida, useBytes = TRUE)
cat("OK:", length(filas), "filas ->", spec$salida, "\n")
