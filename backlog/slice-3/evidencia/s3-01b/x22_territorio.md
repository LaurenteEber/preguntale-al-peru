# S3-01b · X-22 (H-I) y alias de Lurigancho Chosica (H-J)

## Qué cambió
- **X-22 (decidido por el dueño el 6/11/2026):** el nombre a secas de un departamento que también es provincia o distrito
  (Puno, Cusco, Huancavelica…) se responde como departamento, sin pregunta. La respuesta ofrece la alternativa en una frase
  dentro de «Avisos» (capa 2), así que la capa 1 no cambia ni crece.
- Sigue igual: «provincia de Puno» / «distrito de Puno» (palabra de nivel), «Lima» a secas (T-03), «Callao» (ámbito) y los
  homónimos del mismo nivel (p. ej. «San Juan»), que siguen preguntando.
- Solo se ofrecen los niveles que existen con ese nombre (provincia y distrito, solo provincia o solo distrito).
- **H-J:** «Lurigancho Chosica» y «Lurigancho-Chosica» → distrito 150118.
- La decisión es reversible: `territorio.departamento_a_secas.activo` en `parametros_motor.yaml` (en `false` vuelve la aclaración).

## Antes / después
| Pregunta | Antes | Ahora |
|---|---|---|
| «anemia en Puno» | «Hay varios lugares llamados Puno» + 3 opciones | Responde el departamento 21; Avisos: «Respondimos por el departamento de Puno. Si buscabas la provincia o el distrito de Puno, pregúntalo así: «provincia de Puno» o «distrito de Puno».» |
| «provincia de Puno» | Provincia | Igual |
| «Lima» | Aclaración T-03 | Igual |
| «San Juan» | Aclaración de mismo nivel | Igual |
| «Lurigancho Chosica» | No se encontraba | Distrito 150118 |

## Supuestos (tipo B, `S3-01b`)
- Texto de la frase de alternativa y su lugar (Avisos de la capa 2): `curados/motor/textos/territorio.yaml`, `oferta_otros_niveles`.
- Alias de H-J en `alias_distrito` del mismo archivo.

## Archivos
`src/pap/motor/territorio.py`, `src/pap/motor/preguntar.py`, `curados/motor/textos/territorio.yaml`,
`curados/motor/parametros_motor.yaml`, `docs/decisiones.md` (fila X-22), `tests/test_x22_departamento_a_secas.py` (nuevo),
`tests/test_cli_preguntar.py`, `tests/matriz/generar.py` («Huancavelica» a secas sale de las aclaraciones esperadas; entra «San Juan»),
`tests/interprete/evaluacion.yaml` (solo `notas` de d09, t07 y m10; ningún `esperado` cambia: se comparan lugares ya resueltos).

## Pruebas
- Nuevas (`tests/test_x22_departamento_a_secas.py`): 11 en verde; antes de implementar, 7 en rojo (departamento a secas ×3, capa 1 igual, alias ×3).
- `tests/test_matriz_cobertura.py`: 22 en verde. `tests/test_cli_preguntar.py`: 21 de 22 (ver abajo).
- `uv run python tests/interprete/evaluar.py --evaluar` (solo repetición de grabaciones, 0 sin grabar): las mismas 3 fallas que en
  `s2-10_evaluacion_final.md` (d12, d18, e04); no hay fallas nuevas.
- `tests/test_sin_secretos.py`: en verde.

## Lo que queda abierto
- `test_via_estructurada_igual_a_la_base_de_s2_00` (q1): la única diferencia que queda es el texto de glosario de H-A (otro encargo), no X-22.
- `tests/web/test_servicio.py` (3 pruebas de equivalencia con `base_api/`): fallan hasta regenerar la base (ahora trae la frase de X-22 en Avisos).
- Pruebas fuera de mi alcance que codifican la aclaración de nombres de departamento (lista en el informe al coordinador).

## Pruebas ajustadas a X-22
Entrada nueva donde la prueba trata de la aclaración: **Abancay** (provincia y distrito, ningún departamento se llama así) y **Ambo**.
- `test_resolver_territorio.py`: `test_huancavelica_a_secas` → `test_abancay_a_secas_aclara_entre_provincia_y_distrito` (+ `test_huancavelica_a_secas_se_resuelve_como_departamento`); `test_homonimos_entre_niveles` pasa a Acomayo, Aija, Ambo, Andahuaylas, abancay (provincia, distrito); nuevo `test_nombre_de_departamento_a_secas_se_resuelve_como_departamento` (Puno, Cusco, Arequipa, Cajamarca, huancavelica); `test_niveles_ordenados` usa Abancay y, con `depto_a_secas` apagado por `monkeypatch`, Puno (tres niveles, departamento primero).
- `test_s1_09_correcciones.py`: H3/N1 (7 pruebas `--elegir`) y `h19` con Abancay/Ambo en vez de Cusco/Puno/Huancavelica (las mismas afirmaciones de código, mensaje y archivos; la de «mayor en Puno que en Cusco» queda cubierta por `test_h1_comparacion_con_diferencia_clara…`); `a_h1` (×3), `h5` Puno y `h13` sin `elegir`; `h1_sin_diferencia` ignora la frase «no se compara con la de hoy» del glosario (H-A); `h3_ayuda_y_guia` lee `manual_de_uso.md` (el uso de `--elegir` salió de la guía de operación).
- `test_no_se_puede.py`: `aclaracion_no_calcula` y `elegir_fuera_de_rango` con Abancay (2 opciones).
- `interprete/test_cli_texto.py`: `aclaracion_de_territorio` con Abancay; comparación del corrector con Abancay/Ambo; Q1 por texto responde sin aclaración. `test_conjunto.py` q1: el resolver devuelve el departamento 09. `test_interpretar.py`: caso «homónimo», `LUGAR_AMBIGUO` y `--elegir 2,1` con Abancay (nivel actual). `test_robustez.py`: la cifra inyectada con Abancay.
- `test_s3_02_observaciones.py` (H14, H15) fallaban por X-22 (`elegir=1`): sin `elegir`.
- `test_cli_preguntar.py`: `tests/fixtures/textos_antes_s3_02/glosario.yaml` (texto de antes de H-A) entra al espejo de la base de S2-00.
- Regresión Q1: no hacen falta entradas nuevas; su consulta usa «departamento de Huancavelica» y no pasa por el nombre a secas (9 pruebas en verde).
