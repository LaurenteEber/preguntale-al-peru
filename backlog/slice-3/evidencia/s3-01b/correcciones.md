# S3-01b — Correcciones del motor antes de la web (evidencia)

6/11/2026, en el Mac, rama `slice-3`. Cubo `sha256:010ea965…` (igual al manifiesto). Base de pytest: `../pytest_base_local.txt` (1010 pasan).

## Qué cambió, punto por punto

| # | ID | Resultado | Detalle |
|---|---|---|---|
| 1 | H-A | Hecho (aprobado por el dueño) | «que da cifras más altas» → «que no se compara con la de hoy» (dos textos de `bloques.yaml` y el glosario `forma_de_medir`). [textos_y_gasto.md](textos_y_gasto.md) |
| 2 | H-B | Hecho | Q3: el gasto de 2024 en Lima Metropolitana pasa de S/ 260,7 millones (soles de 2024) a **S/ 264,6 millones en soles de 2025**; la cita trae el monto registrado (S/ 260,7 millones) y el factor de inflación. Cifra exceptuada en la regresión de Q3. [textos_y_gasto.md](textos_y_gasto.md) |
| 3 | u13 | Hecho (aprobado por el dueño) | Toda respuesta de gasto (nivel actual) abre con lo que cubre la cifra y lo que no; la cifra va después; se quitó el «Ojo al leer» que repetía lo mismo. Cifras, semáforos y confianza sin cambios. [textos_y_gasto.md](textos_y_gasto.md#u13) |
| 4 | H-F | Hecho (aprobado por el dueño) | Título «Por qué esta cifra no se compara con la de la encuesta». El cuerpo de la tarjeta repite el aviso del INS («podrían subestimar la anemia real»): no compara con la encuesta, se dejó |
| 5 | H-G | Pendiente del dueño (W-04) | El INS publica las mismas cifras (San Antonio 1 516/1 597; Pullo 342/427; Incahuasi 529/680; Santo Domingo de los Olleros 171/195; Unión Progreso no figura, es de 2021). En el crudo, la hemoglobina sin ajustar de San Antonio tiene mediana 11,5 g/dL; el 95 % sale del ajuste por 3 456 m (altura de la capital del distrito) aplicado a todos sus establecimientos, que en su mayoría están en anexos de Jicamarca. El dueño aportará alturas por distrito. Sin cambios |
| 6 | H-I | Hecho: decisión X-22 | El nombre de un departamento se responde como departamento; en «Avisos» se ofrece la provincia o el distrito del mismo nombre. Lima sigue con T-03. Fila X-22 en `docs/decisiones.md`. [x22_territorio.md](x22_territorio.md) |
| 7 | H-J | Hecho | Alias «Lurigancho Chosica» y «Lurigancho-Chosica» → 150118 |
| 8 | H-K | Hecho (enlace elegido por el dueño) | SIEN → colección de informes SIEN del INS en gob.pe. `scripts/comprobar_enlaces.sh`: 34 enlaces, 33 bien; falla RENIEC (certificado vencido, W-06). [enlaces.txt](enlaces.txt) |
| 9 | Matriz | Hecho | `tests/matriz/comprobar.py` → `comparaciones` (también en `revisar`). Detectó H-A (Cajamarca 2025: forma anterior 35,3 % < vigente 39,4 %) y H-F (Lurigancho: SIEN 44,7 % > ENDES 25,3 %) antes de corregirlos: [comparaciones_antes.txt](comparaciones_antes.txt). Después pasan (`tests/test_comparaciones_escritas.py`) |
| 10 | Cubo | Hecho | `pytest` se detiene antes de la primera prueba con «el cubo local no es el del manifiesto: corre `pap calcular`». Release nuevo `biblioteca-010ea965` publicado (SHA256 `4c10cad0…`) y valor por defecto de `bajar_biblioteca.sh`. [cubo_docs_avisos.md](cubo_docs_avisos.md) |
| 11 | Documentos | Hecho | Manual = usar; guía = mantener; «Trabajar en local o en la nube» en la guía; correcciones pedidas. [cubo_docs_avisos.md](cubo_docs_avisos.md) |
| 12 | E-04 | Hecho | 18 preguntas `pd01`–`pd18`, grabadas por US$ 0,06 (tope 1). La del celular entra con `[dato personal]`. pd02 espera aclaración (decisión del dueño, W-08). Umbrales cumplidos. [e04_prueba_dueno.md](e04_prueba_dueno.md), [evaluacion.md](evaluacion.md) |
| 13 | H-L | Hecho | `filterwarnings` en `pyproject.toml`, solo para esos dos avisos |
| 14 | W-02 | Cerrada sin aplicar | — |

## Base de la web

`../base_api/` regenerada con `../s3-02_generar_base.py` (autorizado por el dueño): 447 archivos. El caso «Huancavelica + elegir 1» pasa a «Abancay + elegir 1», porque con X-22 Huancavelica ya no aclara.

## Observación para después

«departamento de Lima» escrito así se resuelve como el departamento 15 y la respuesta de gasto dice «con sede en departamento de Lima». Ya pasaba antes; no se tocó.

## Pruebas

Ver la sección final (suite completa).

Suite completa en el Mac (6/11/2026): 1051 pasan y 3 fallan, todas por textos o conteos que estas correcciones cambiaron a propósito:
- dos pruebas de H5 (S1-09) buscaban la frase vieja «no incluye a las entidades nacionales…», que u13 reemplazó por «no incluye lo que gastan las entidades nacionales…». Se actualizaron y la prueba sigue exigiendo que la frase salga una sola vez;
- la equivalencia web por texto exigía 140 casos. Ahora compara con el total del conjunto (158).

Al repetir `tests/web`, `test_s1_09_correcciones.py` y `test_sin_secretos.py`, pasan 74 de 74. Total: 1054 pasan y 0 fallan, frente a 1010 en la base (44 pruebas nuevas). La regresión Q1–Q4 y la matriz reducida forman parte de la suite. La evaluación con grabaciones cumple todos los umbrales ([evaluacion.md](evaluacion.md)).
