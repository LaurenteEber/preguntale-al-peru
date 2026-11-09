#!/usr/bin/env Rscript
# Verificador ("oráculo") de estimaciones de encuestas con R `survey`.
# Contrato pap-verificador/1.
#
# Uso: Rscript verificar.R <especificacion.json> <extracto.csv[.gz]> <salida.json>
#
# Paquetes: survey (estimación) y jsonlite (leer/escribir JSON). Nada más.
# La entrada es un CSV (opcionalmente .gz) con las columnas que nombra la
# especificación: variable, peso, estrato, upm, dominios y, si existe, universo.

suppressPackageStartupMessages({
  library(survey)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Uso: Rscript verificar.R <especificacion.json> <extracto.csv[.gz]> <salida.json>")
}
ruta_spec <- args[[1]]; ruta_datos <- args[[2]]; ruta_salida <- args[[3]]
spec <- fromJSON(ruta_spec, simplifyVector = TRUE)
if (!identical(spec$contrato, "pap-verificador/1")) stop("Contrato no soportado: ", spec$contrato)

d <- spec$diseno
lonely <- if (is.null(d$lonely_psu)) "adjust" else d$lonely_psu
options(survey.lonely.psu = lonely)
# Igual que svy con singleton domains="standard": no tratar como singleton
# un estrato que solo es singleton dentro del dominio.
options(survey.adjust.domain.lonely = FALSE)

# --- Lectura: todo como texto salvo peso y variable -------------------------
num_cols <- c(d$peso, spec$variable)
cab <- names(read.csv(ruta_datos, nrows = 1, check.names = FALSE))
clases <- ifelse(cab %in% num_cols, "numeric", "character")
datos <- read.csv(ruta_datos, colClasses = clases, check.names = FALSE,
                  na.strings = c("", "NA"), encoding = "UTF-8")

# estrato como factor: survey < 4.4-3 falla con lonely.psu="adjust" y estratos texto
datos[[d$estrato]] <- factor(datos[[d$estrato]])
if (!is.null(spec$universo)) {
  datos$.universo <- datos[[spec$universo]] %in% c("1", "TRUE", "true")
} else {
  datos$.universo <- TRUE
}
datos$.universo <- datos$.universo & !is.na(datos[[spec$variable]])

des <- svydesign(
  ids = as.formula(paste0("~", d$upm)),
  strata = as.formula(paste0("~", d$estrato)),
  weights = as.formula(paste0("~", d$peso)),
  nest = isTRUE(d$nest),
  data = datos
)

nivel <- if (is.null(spec$ic$nivel)) 0.95 else spec$ic$nivel
f_y <- as.formula(paste0("~", spec$variable))
deff_arg <- switch(if (is.null(spec$deff)) "wor" else spec$deff,
                   wor = TRUE, wr = "replace", stop("deff no soportado"))

# Korn-Graubard según el estándar NCHS (Parker et al. 2017; macro SAS KG_macro):
# n efectivo ajustado por gl y truncado en n; p = 0 o 1 con n efectivo = n.
# Implementación propia en R base (qbeta), independiente del código de svy.
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

estimar <- function(sub, n_sin) {
  gl <- degf(sub)
  extra <- list()
  if (spec$estimador == "proporcion") {
    m <- svymean(f_y, sub, deff = deff_arg)
    p <- unname(coef(m)[1]); v <- unname(vcov(m)[1, 1])
    # IC de survey (svyciprop beta = KG sin truncar) y KG-NCHS; ambos se reportan
    ci_beta <- suppressWarnings(attr(svyciprop(f_y, sub, method = "beta", level = nivel), "ci"))
    ci_beta[!is.finite(ci_beta)] <- NA_real_
    ci_nchs <- ic_kg_nchs(p, sqrt(v), gl, n_sin, nivel)
    ci <- switch(spec$ic$metodo, beta = ci_beta, kg_nchs = ci_nchs,
                 stop("ic.metodo para proporciones: 'kg_nchs' o 'beta'"))
    extra <- list(ic_beta_inf = unname(ci_beta[1]), ic_beta_sup = unname(ci_beta[2]),
                  ic_kg_nchs_inf = ci_nchs[1], ic_kg_nchs_sup = ci_nchs[2])
    n_ef <- if (v > 0) p * (1 - p) / v else NA_real_
  } else if (spec$estimador == "media") {
    m <- svymean(f_y, sub, deff = deff_arg)
    p <- unname(coef(m)[1]); v <- unname(vcov(m)[1, 1])
    ci <- confint(m, level = nivel, df = gl)
    n_ef <- NA_real_
  } else if (spec$estimador == "total") {
    m <- svytotal(f_y, sub, deff = deff_arg)
    p <- unname(coef(m)[1]); v <- unname(vcov(m)[1, 1])
    ci <- confint(m, level = nivel, df = gl)
    n_ef <- NA_real_
  } else stop("estimador no soportado: ", spec$estimador)
  ee <- sqrt(v)
  dfx <- unname(deff(m)[1]); if (!is.finite(dfx)) dfx <- NA_real_
  c(list(estimacion = p, ee = ee, cv = if (p != 0) ee / abs(p) else NA_real_,
         ic_inf = unname(ci[1]), ic_sup = unname(ci[2]), gl = gl,
         n_sin_ponderar = n_sin, n_efectivo = n_ef, deff = dfx,
         suma_pesos = sum(weights(sub)[weights(sub) > 0])), extra)
}

filas <- list()
for (dv in spec$dominios) {
  niveles <- sort(unique(datos[[dv]][datos$.universo]))
  for (lv in niveles) {
    en_dom <- datos$.universo & datos[[dv]] == lv
    sub <- des[en_dom, ]   # subconjunto de dominio: conserva el diseño completo
    r <- estimar(sub, sum(en_dom))
    filas[[length(filas) + 1]] <- c(list(dominio_var = dv, dominio = lv), r)
  }
}

salida <- list(
  contrato = "pap-verificador/1",
  caso = spec$caso,
  motor = "R survey",
  version_r = paste(R.version$major, R.version$minor, sep = "."),
  version_survey = as.character(packageVersion("survey")),
  version_jsonlite = as.character(packageVersion("jsonlite")),
  plataforma = R.version$platform,
  opciones = list(survey.lonely.psu = getOption("survey.lonely.psu"),
                  survey.adjust.domain.lonely = getOption("survey.adjust.domain.lonely"),
                  survey.use_rcpp = if (is.null(getOption("survey.use_rcpp"))) "no_aplica" else getOption("survey.use_rcpp")),
  md5_especificacion = unname(tools::md5sum(ruta_spec)),
  md5_extracto = unname(tools::md5sum(ruta_datos)),
  ejecutado = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  filas = filas
)
writeLines(toJSON(salida, auto_unbox = TRUE, digits = NA, pretty = TRUE, na = "null"),
           ruta_salida, useBytes = TRUE)
cat("OK:", length(filas), "filas ->", ruta_salida, "\n")
