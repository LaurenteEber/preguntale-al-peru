# Slice 3 — Consultas al dueño

Mismas reglas que los slices anteriores (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### W-01 — La etiqueta `slice-2-cerrado` no se pudo subir desde la nube (S3-00) · abierta (no bloquea)
- **Qué pasa:** el slice 2 se fusionó en `main` ([PR #2](https://github.com/LaurenteEber/preguntale-al-peru/pull/2), `e1a0d0f`). La etiqueta se creó en local, pero el push de etiquetas desde este entorno se corta («the remote end hung up»), aunque el de ramas funciona.
- **Propuesta:** desde el Mac: `git fetch origin main && git tag -a slice-2-cerrado e1a0d0f -m "Slice 2 cerrado" && git push origin slice-2-cerrado`.

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
| S3-01-a | S3-01 | El texto de la tarjeta «Gasto en Lima Metropolitana en 2024» (X-03) dice «registrado por unidades ejecutoras con sede en Lima Metropolitana», como la tarjeta del gasto de 2025. Sin esa frase, la regla R-LENGUAJE-02 (todo gasto nombra su base ejecutora) la marcaba. Es la misma información, sin afirmaciones nuevas | `curados/motor/textos/plantillas/cruce_efecto.yaml` → `tarjetas.mismo_anio.texto` |
| S3-01-b | S3-01 | El enlace de cada cita sale de `cifras_doradas.csv` (columna `url`) cuando la cifra tiene dorada y, si no, del portal de la fuente en `catalogo_fuentes.csv` (`url_portal`, si no `url_datos`). Si no hay enlace oficial, el campo va vacío. En el `.md` el enlace se muestra como «[Documento oficial](url)» al final de la cita. Las citas de ENDES sin dorada apuntan al portal de microdatos del INEI, no al informe del año | `src/pap/motor/capas.py` (`_url`); texto del enlace en `curados/motor/textos/capas.yaml` → `rotulos.enlace_oficial` |
| S3-01-c | S3-01 | `capa3` suma `citas` = lista de `{texto, url, id_cifra}`, con las mismas líneas que `para_citar` (que no cambia). La web lee `citas`. Se eligió una lista aparte para no cambiar la forma de `para_citar`, que usan la matriz y varias pruebas | `src/pap/motor/capas.py` |
| S3-01-d | S3-01 | Además de los 8 rótulos que pedía la historia, se movió a YAML «Cómo citar» (rótulo de la lista de citas) y se agregó «Documento oficial» (texto del enlace). El `.md` de Q1–Q4 solo cambia por los enlaces y por X-02/X-03 | `curados/motor/textos/capas.yaml` → `rotulos` |

## Pendientes del dueño que siguen abiertos

- **X-01 — texto de «¿Qué puedo hacer?» (R-06):** el dueño todavía no lo aprobó, así que `curados/motor/textos/que_hacer.yaml` → `anemia.revisado_dueno` sigue en `false` y la respuesta conserva «(texto pendiente de revisión)». S3-01 no lo toca. Cuando lo apruebe: poner `true`, pasar R-06 a «vigente» y sacar X-01 de las pendientes.
