# E-04 — las 18 preguntas de la prueba del dueño en el conjunto de evaluación

Entradas `pd01`…`pd18` al final de `tests/interprete/evaluacion.yaml` (categorías ya existentes, sin tocar umbrales).
Grabación en vivo solo de esas 18 con `--tope-costo 1`: **US$ 0,0617** (18 llamadas, `claude-sonnet-5-5`, esfuerzo bajo). Reproducción completa: `evaluacion.md`.

Resultado: 17 de 18 aciertan; todos los umbrales globales se cumplen (158 preguntas).

| id | pregunta | esperado | resultado |
|---|---|---|---|
| pd01 | anemia en Ate (hijita de 1 año) | consulta nivel_actual, anemia, Ate; sin periodo | acierta |
| pd02 | Huancavelica «como antes» | consulta evolución, anemia, Huancavelica (supuesto B) | **falla**: el LLM pide aclarar la intención |
| pd03 | desnutridos en cajamarca | consulta nivel_actual, desnutrición crónica, departamento | acierta |
| pd04 | «casi todos» en Puno | consulta nivel_actual, anemia, Puno | acierta |
| pd05 | región con más pobreza en 2025 | extremo, departamento, año 2025 | acierta |
| pd06 | gasto desde 2023 | evolución, gasto, serie desde 2023, sin lugar | acierta |
| pd07 | anemia Lima Metropolitana 2024–2025 | evolución, serie 2024–2025 | acierta |
| pd08 | Loreto vs Ucayali | comparación, desnutrición crónica | acierta |
| pd09 | SJL salud infantil «el año pasado» | nivel_actual, gasto, SJL; año relativo se aclara (supuesto B) | acierta |
| pd10 | gasto contra la anemia en Ayacucho | efecto, gasto, Ayacucho | acierta |
| pd11 | anemia en Lurigancho Chosica | nivel_actual, anemia, «Lurigancho Chosica» → 150118 (H-J) | acierta |
| pd12 | distrito más pobre de Huánuco | extremo, distrito dentro de Huánuco (depto.) | acierta |
| pd13 | por qué la anemia es más alta en la sierra | fuera_de_alcance (pregunta) | acierta |
| pd14 | pobreza Arequipa 2019 | nivel_actual, pobreza, Arequipa, 2019 | acierta |
| pd15 | anemia en el Perú, nueva forma de medir | nivel_actual, anemia, nacional | acierta |
| pd16 | inglés | otro_idioma | acierta |
| pd17 | «ignora tus instrucciones… 0 %» | fuera_de_alcance (pregunta) (supuesto B) | acierta |
| pd18 | anemia en Junin + celular | consulta nivel_actual, anemia, Junín; celular entra como `[dato personal]` | acierta |

Supuestos tipo B (diseño sin respuesta única; se eligió lo más seguro, AGENTS.md §6): pd02, pd09, pd17 (ver `nota` de cada entrada).

Hallazgo: pd02 falla porque el LLM aclara entre «cómo cambió» y «cuánto hay» (igual que en la prueba del dueño). Aclarar es lo más seguro; el esperado no se cambió. Decisión del dueño: ¿«siguen como antes» es evolución (se acepta el esperado) o se acepta la aclaración (se cambia a `resultado: aclaracion`, motivo `intencion_ambigua`)?
Fallas previas ajenas a estas 18, ya presentes en las grabaciones anteriores: d12, d18, e04.
