# S3-02 — Observaciones bajas aprobadas y base de la web

## Por qué

La revisión del slice 1 dejó observaciones bajas (`../slice-1/evidencia/revision_usuario.md` y `correcciones_s1-09.md`) que cambian el texto de Q1–Q4. Con la web, ese texto llega a más gente.

Hay dos casos:

**A. Las aprueba el agente** (`agents.md` §5.1: solo cambian la forma de decir lo mismo o quitan algo, sin afirmaciones nuevas). Se registran con `aprobado_por: agente` y deben cumplir las cuatro condiciones de §5.1; si alguna falla, es consulta tipo C.

| ID | Qué pasa hoy | Cambio | Dónde |
|---|---|---|---|
| H14 | El sujeto se repite entre la respuesta corta y la cifra clave | «En 2025, en Huancavelica, la anemia en niñas y niños de 6 a 35 meses fue:» antes de la cifra, sin repetirlo en la corta | Plantillas de `curados/motor/textos/plantillas/` |
| H15 | «Forma de medir vigente desde 2024» sin entrada de glosario donde aparece | Agregar el término (que ya existe) al glosario de toda respuesta que lo use | La lista `glosario` de cada plantilla |
| H21 | En «Más contexto» de Q4, la lista de departamentos con porcentajes invita a ordenarlos | En «Más contexto», solo el rango del grupo; los porcentajes quedan en «Para citar y verificar» | Plantilla de `identificar_extremo` |

**B. Necesitan al dueño**, porque son textos de reglas y `agents.md` §7 solo permite cambiarlas si una decisión lo pide. El dueño marca la columna con la fecha; esa marca, en git, es el registro que cita `ajustes_dueno.py`. Sin marca, no se hacen.

| ID | Hoy | Propuesta | Dueño |
|---|---|---|---|
| H17 | «solo sabemos de los que se les midió la hemoglobina» | «…de aquellos a quienes se les midió la hemoglobina». Solo el texto NC de la regla; «tamizados» en las citas no se toca (vive en `dim_indicador.yaml`, insumo con huella del cubo) | ☐ |
| H18 | «nada sobre provincias o distritos concretos… para Lima Metropolitana» | «nada sobre distritos concretos de Lima Metropolitana» | ☐ |

A-H8 (mostrar la anemia vigente junto a la anterior cuando se pide `--indicador`) **no está aquí**: agrega una cifra y toca E-06, así que es una decisión aparte para el dueño.

## Tareas

1. **A:** las tres, con §5.1. **B:** solo las marcadas. Los textos de reglas, únicamente por `reglas/consolidador/ajustes_dueno.py` (con comentario «S3-02, aprobado por el dueño el <fecha>») y `python3 reglas/consolidador/consolida_reglas.py`. Deben pasar `vp3_checks.py`, `prueba_guardia.py` y `pap validar-reglas`.
2. **Diferencias** en `regresion/Q*.yaml`, con `aprobado_por: agente` (A) o `aprobado_por: dueño` y la fecha (B). Las referencias no se tocan (regla de S3-01).
3. **Pruebas:** una por observación aprobada; el corrector, sin infracciones.
4. **Base de la web** (al final, una sola vez): en `evidencia/base_api/` va el `respuesta.json` completo de:
   - Q1–Q4, con `preguntar_minima` (Q1 también con `elegir=[1]` desde «Huancavelica»);
   - cada caso de la matriz reducida, con el mismo código que `tests/matriz/correr.py --reducida`, **incluidas las aclaraciones**, que la CLI no escribe;
   - el conjunto de evaluación con grabaciones, con `interpretar()`.

   Un script `evidencia/s3-02_generar_base.py` lo regenera. Es el patrón de equivalencia de S3-03.

## Criterios de aceptación

- [ ] Solo cambian los textos de A y los marcados de B; ninguna cifra, semáforo ni confianza.
- [ ] `reglas.json` sin ediciones a mano; su diff se limita a lo aprobado.
- [ ] `base_api/` generada por el script, con el commit del que salió.
