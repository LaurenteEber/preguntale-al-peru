# M1-10 — Planificador

**Se deriva de** el diseño §11 y `tecnologias.md` §8.

## Tareas

1. **Cliente:** ampliar `interprete/llm.py` (sin el SDK del proveedor). Corregir `_de_cuerpo`, que aplica una sola tarifa de escritura de caché.
2. **Una llamada por muestra.** El LLM ve, por candidato: ID, etiqueta curada, texto de la pregunta, categorías con IDs (`k1`…, hasta 30), universo corto, ventana, sujeto, años y el nombre de su bloque temático. Con `inferencia.admitir_propuesto_en_sombra` puede ver candidatos `propuesto` (M1-07).
3. **Salida en esquema fijo** validada con pydantic (`extra="forbid"`): `candidato`, `categorias_si`, `restricciones_universo`, `motivo`. El código comprueba que cada ID esté en la lista de esa pregunta; un reintento con el error; si vuelve a fallar, la muestra cuenta como falla del plan.
4. **3 muestras en paralelo** (hilos, un cliente por muestra, plazo común de 9 s), con el orden de los candidatos permutado por una semilla determinista y dos variantes del prompt (una obligada a descartar el candidato más parecido y decir por qué). El cierre anticipado por huella se agrega en M1-11, que es donde nace `huella_uy`; aquí queda el punto de enganche.
5. **Plan normalizado** (§11.2): el código traduce a `var_id` del índice; los cortes salen de `cortes_estandar.yaml`; el diseño y el universo analítico **no** van en el plan.
6. **Caché del proveedor:** el prompt fijo en `system` con caché de 1 h; los candidatos, sin caché.
7. **Grabaciones** con la llave de `tecnologias.md` §8 y `cuerpo_sha256`.
8. **Costo por pregunta** medido (con receta, con plan compuesto y peor caso).

## Criterios de aceptación

- [ ] Pruebas con un LLM falso: ID inexistente, categoría de otra variable, orden cambiado en la segunda llamada, respuesta fuera de plazo.
- [ ] Ningún texto del LLM llega al SQL: solo IDs validados.
- [ ] Costo por pregunta informado en `evidencia/m1-10_costo.md`.
- [ ] La permutación es reproducible con la misma interpretación.
- [ ] Corrida de estabilidad en vivo (`tecnologias.md` §8): las mismas 20 preguntas 3 veces; se informa cuántas cambian de plan.

## Fuera

Decidir el número final de muestras y el esfuerzo (M1-19).
