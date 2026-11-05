# Slice 3 — Consultas al dueño

Mismas reglas que los slices anteriores (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### W-01 — La etiqueta `slice-2-cerrado` no se pudo subir desde la nube (S3-00) · abierta (no bloquea)
- **Qué pasa:** el slice 2 se fusionó en `main` ([PR #2](https://github.com/LaurenteEber/preguntale-al-peru/pull/2), `e1a0d0f`). La etiqueta se creó en local, pero el push de etiquetas desde este entorno se corta («the remote end hung up»), aunque el de ramas funciona.
- **Propuesta:** desde el Mac: `git fetch origin main && git tag -a slice-2-cerrado e1a0d0f -m "Slice 2 cerrado" && git push origin slice-2-cerrado`.

### W-02 — H21: quitar los porcentajes de «Más contexto» de Q4 también quita un aviso (S3-02) · abierta (no bloquea)
- **Qué pasa:** la historia pide que «Más contexto» de Q4 muestre solo el rango del grupo (35,7 % a 39,8 %) y no los porcentajes de los siete departamentos. Lo probé: el texto cambia como se pidió, pero **también desaparece el aviso «Estas cifras vienen de fuentes de distinto tipo (encuesta a hogares, estimación con modelo)…»** y la regla R-LENGUAJE-06 (rotular) deja de dispararse, porque esa regla se activa cuando el texto mezcla cifras de distinta naturaleza. Quitar un aviso no es «decir lo mismo de otra forma» (`agents.md` §5.1, condición 2), y ante la duda es tipo C.
- **Por qué importa:** la respuesta sigue mostrando juntos el Mapa de Pobreza 2018 (modelo) y el grupo de ENAHO 2025 (encuesta); sin el aviso, esa diferencia queda solo en «Ojo al leer» y en «Límites».
- **No se hizo:** el texto de `identificar_extremo.yaml` queda como estaba; Q4 no cambia.
- **Propuesta:** (a) aprobar la pérdida del aviso (el cambio de texto ya está probado; se aplica en una línea de `curados/motor/textos/plantillas/identificar_extremo.yaml`: quitar «En orden alfabético: {items}.»), o (b) conservar el aviso: pide un cambio de código (que «Más contexto» nombre a los departamentos sin porcentaje), fuera de lo que S3-02 permite. Recomiendo (a).

### W-03 — H17 y H18: el dueño no los marcó (S3-02, caso B) · pendiente del dueño (no bloquea)
- **Qué pasa:** la tabla de S3-02 los deja en blanco (☐), así que no se hicieron y no se tocó `reglas/` ni `ajustes_dueno.py`. Siguen con el texto de hoy: H17 «solo sabemos de los que se les midió la hemoglobina»; H18 «nada sobre provincias o distritos concretos… para Lima Metropolitana».
- **Para aplicarlos:** el dueño marca la columna con la fecha en `S3-02-observaciones-y-base.md`; entonces se cambian solo por `reglas/consolidador/ajustes_dueno.py` y `consolida_reglas.py`.

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
| S3-01-a | S3-01 | El texto de la tarjeta «Gasto en Lima Metropolitana en 2024» (X-03) dice «registrado por unidades ejecutoras con sede en Lima Metropolitana», como la tarjeta del gasto de 2025. Sin esa frase, la regla R-LENGUAJE-02 (todo gasto nombra su base ejecutora) la marcaba. Es la misma información, sin afirmaciones nuevas | `curados/motor/textos/plantillas/cruce_efecto.yaml` → `tarjetas.mismo_anio.texto` |
| S3-01-b | S3-01 | El enlace de cada cita sale de `cifras_doradas.csv` (columna `url`) cuando la cifra tiene dorada y, si no, del portal de la fuente en `catalogo_fuentes.csv` (`url_portal`, si no `url_datos`). Si no hay enlace oficial, el campo va vacío. En el `.md` el enlace se muestra como «[Documento oficial](url)» al final de la cita. Las citas de ENDES sin dorada apuntan al portal de microdatos del INEI, no al informe del año | `src/pap/motor/capas.py` (`_url`); texto del enlace en `curados/motor/textos/capas.yaml` → `rotulos.enlace_oficial` |
| S3-01-c | S3-01 | `capa3` suma `citas` = lista de `{texto, url, id_cifra}`, con las mismas líneas que `para_citar` (que no cambia). La web lee `citas`. Se eligió una lista aparte para no cambiar la forma de `para_citar`, que usan la matriz y varias pruebas | `src/pap/motor/capas.py` |
| S3-01-d | S3-01 | Además de los 8 rótulos que pedía la historia, se movió a YAML «Cómo citar» (rótulo de la lista de citas) y se agregó «Documento oficial» (texto del enlace). El `.md` de Q1–Q4 solo cambia por los enlaces y por X-02/X-03 | `curados/motor/textos/capas.yaml` → `rotulos` |
| S3-03-a | S3-03 | Servidor local en 127.0.0.1:8000 (el de producción lo fija S3-09) | `curados/web/parametros.yaml` → `servicio` |
| S3-03-b | S3-03 | Topes de la entrada: `texto` hasta 2000 caracteres; `elegir` hasta 4 números, cada uno entre 1 y 50; se acepta un número o una lista | `curados/web/parametros.yaml` → `pregunta` |
| S3-03-c | S3-03 | Las pruebas esperan hasta 120 s a que termine el precalentamiento | `curados/web/parametros.yaml` → `precalentamiento` |
| S3-03-d | S3-03 | Estado HTTP: 200 para cualquier respuesta del motor (incluidos los mensajes fijos), 503 para `mensaje` con `motivo: no_disponible` y para «preparando», 422 para entradas inválidas. Tabla en `docs/especificaciones/api.md` | `curados/web/parametros.yaml` → `http`; `curados/web/textos.yaml` |

## Pendientes del dueño que siguen abiertos

- **X-01 — texto de «¿Qué puedo hacer?» (R-06):** el dueño todavía no lo aprobó, así que `curados/motor/textos/que_hacer.yaml` → `anemia.revisado_dueno` sigue en `false` y la respuesta conserva «(texto pendiente de revisión)». S3-01 no lo toca. Cuando lo apruebe: poner `true`, pasar R-06 a «vigente» y sacar X-01 de las pendientes.
