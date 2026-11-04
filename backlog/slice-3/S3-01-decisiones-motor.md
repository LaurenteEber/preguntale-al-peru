# S3-01 — Cambios del motor decididos (X-01 a X-04, enlaces de las citas, rótulos)

## Por qué

Antes de la web se aplican los cambios del motor que el dueño ya decidió o que la web necesita. Se hacen aquí, y no antes, para no mover la regresión de la adenda ni la del slice 2.

## Regla de regresión de este slice

Elimina la ambigüedad entre `regresion/` y las referencias:
- **Una diferencia de texto** se aprueba en `../slice-1/evidencia/regresion/Q*.yaml` (`aprobado_por: dueño`, motivo con la decisión y su fila). `tests/referencias/q*.json` **no** se toca por texto.
- **Una cifra nueva** se exceptúa con el mismo mecanismo que `CLAVE_2022_Q1`, el de C-01 y AD-1 en `tests/test_regresion_q1_q4.py`, tanto en `test_planes` como en `test_respuestas`. Se agrega su clave a `tests/referencias/q*.json` y, si la fase de planes lo pide, a `tests/fixtures/consultas_piloto/q*.yaml`. Es lo único que cambia en esos archivos.
- **Si una tarjeta nueva corre los índices de `mas_contexto`** y eso dispara diferencias en tarjetas que no cambiaron, la comparación se ajusta para identificar las tarjetas por su título, no por su posición. Es un cambio de la prueba (tipo A), con su propia prueba. No se aprueban diferencias falsas.

## Tareas

1. **Aplicar las decisiones** en `curados/motor/parametros_motor.yaml` → `pendientes_dueno`. `pendiente:` pasa a `decision:` con su fila.

   | Decisión | Parámetro | Valor | Qué se espera en Q1–Q4 |
   |---|---|---|---|
   | X-02 (S-01) | `mostrar_conteo_sien` | `true` | Q2: tarjeta nueva con el conteo, que es una cifra: se exceptúa según la regla |
   | X-03 (R-03) | `cr01_mismo_anio` | `true` | Q3: clave nueva `gasto_ex_pan` 2024 de Lima Metropolitana con rol contexto, que se exceptúa según la regla |
   | X-04 (E-04) | `intervalo_visible` | `uno` | **Q1–Q4 sin diferencias** (sus intervalos ya coinciden o ya usan el del INEI). Se verifica con un caso de la matriz cuya cifra clave tenga `ic_inei` distinto del propio, en una prueba nueva |
   | X-01 (R-06) | `que_hacer.yaml` → `anemia.revisado_dueno` | `true`, **solo si el dueño lo aprobó** | Desaparece «(texto pendiente de revisión)» |

   Cualquier otro cambio de cifra, semáforo o confianza es una consulta tipo C.
2. **Enlaces de las citas** (`plan_slices.md`, slice 3, y P-02): cada entrada de «Para citar y verificar» lleva un campo `url` con el enlace al documento oficial.
   - Se toma de la columna `url` de `curados/capa0/cifras_doradas.csv` para las cifras con dorada, o del catálogo de fuentes (`catalogo/catalogo_fuentes.csv`) para las demás.
   - Si no hay URL oficial, el campo va vacío. **Nunca** se pone un enlace que no sea de un documento oficial (P-02).
   - El `.md` de la CLI muestra el enlace.
   - Es un cambio de cita que pide el plan aprobado: se registra en `regresion/` como texto, citando «plan_slices.md, slice 3; P-02».
3. **Rótulos de sección a YAML:**
   - Hoy están fijos en `src/pap/motor/ficha.py`: «Ojo al leer», «Avisos», «Límites de esta respuesta», «Para citar y verificar», «Glosario», «¿Qué puedo hacer?», «(texto pendiente de revisión)», «Más contexto».
   - Pasan a `curados/motor/textos/capas.yaml`, clave `rotulos`, y los leen el `.md` y la web.
   - El `.md` de Q1–Q4 queda **idéntico byte a byte** (prueba).
4. **Docs:** en `docs/decisiones.md`, las filas E-04, S-01 y R-03 quitan «se aplica al empezar el slice 3…». Si X-01 se aprobó, R-06 pasa a «vigente» y X-01 sale de las pendientes. La fila P-02 agrega que la cita lleva el enlace al documento oficial cuando existe.
5. **Verificación:** pytest, la regresión, la matriz reducida, la evaluación con grabaciones y las pruebas del slice 2 listadas en S3-00 §4.

## Criterios de aceptación

- [ ] Q2 con el conteo y Q3 con el gasto del mismo año, como claves exceptuadas; ninguna otra cifra cambia.
- [ ] La prueba de X-04 sobre un caso con `ic_inei` está en verde.
- [ ] Los `.md` de Q1–Q4 son idénticos tras mover los rótulos.
- [ ] X-01 aplicada solo si el dueño la aprobó; si no, queda anotada.
- [ ] Toda cita de Q1–Q4 con dorada lleva su `url` oficial.
