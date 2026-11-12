# M1-08 — Intérprete en modo motor

**Se deriva de** el diseño §9 y §13.

## Tareas

1. **Modo motor** por parámetro (`inferencia.modo_interprete`), sin tocar el modo actual:
   - `tema_texto` literal y anclado a la pregunta; el tema curado de hoy queda como pista;
   - ranuras nuevas, ancladas o vacías: `poblacion`, `periodo_referencia`, `sujeto`, `medida` (proporción, cuántos, promedio) y `cortes[]` (texto);
   - se elimina `fuera_de_alcance` por tema; se conserva para predicciones, opiniones y lo que no es una pregunta.
2. **Cortes:** el código traduce el texto de `cortes[]` a `cortes_estandar.yaml` (con `sinonimos.yaml`). Lo que no se reconoce se informa en «Entendimos» y no se inventa.
3. **Valores por defecto sin preguntar** (último año con datos; nombre de departamento como departamento), dichos en «Entendimos». «Lima» a secas se pregunta y cuenta en el tope común de aclaraciones.
4. **Otro idioma:** si la pregunta no está en español, `mensaje` que ofrece seguir en español. Detección del quechua con una lista corta de marcas, sin dependencia nueva.
5. **Coincidencia con receta** (`inferencia/recetas.py`): condiciones del §9. Si coincide y no hay nada más pedido, no se llama al planificador; si se pide algo que la receta no cubre, la receta entra como un plan más.
6. **Prompt y esquema** versionados; la salida se valida en código (sin salida estructurada del proveedor), con un reintento.

## Criterios de aceptación

- [ ] El conjunto de evaluación del slice 2 (162 entradas) da los mismos resultados en el modo actual (sin pérdidas).
- [ ] Pruebas de cada ranura nueva con grabaciones; 0 valores sin ancla.
- [ ] «¿Los niños del campo en Puno reciben hierro?» → tema literal, sujeto niño, corte área rural, lugar Puno.
- [ ] Una pregunta de un tema nuevo ya no sale `fuera_de_alcance`.

## Fuera

Cambiar el modelo o el esfuerzo del intérprete.
