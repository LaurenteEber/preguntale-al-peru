# M1-17 — Caché, costo y concurrencia

**Se deriva de** el diseño §20 y §21, y `tecnologias.md` §8.

## Tareas

1. **Caché de estimaciones:** llave `id_plan` + hash de las filas del índice que usa el plan + `huella_datos` + versión del ejecutor + versión de `svy`. Guarda la estimación cruda; las compuertas se aplican al leer. Tabla DuckDB con un solo escritor; limpieza por tamaño o por versión vieja.
2. **Costo:** contador en US$ por petición y por día (día de Lima), común al intérprete y al planificador; reserva el peor caso antes de llamar; se reconstruye desde `uso.jsonl` al arrancar. Al llegar al tope (`tope_llm_usd_dia`), se ofrece el formulario guiado. Este tope **reemplaza** a `llamadas_llm_por_dia` (diseño §21).
3. **Registro por petición,** sin el texto de la pregunta: `id_plan`, salida, compuertas que actuaron, `huella_datos`, versiones, costo y tiempo por etapa.
4. **Concurrencia:** el LLM fuera del candado global; estado por petición (`ContextVar`); escritura atómica de la caché del intérprete; cálculo en el pool con cola acotada (2 × trabajadores) y 503 «espera un momento» cuando se llena.
5. **Varios trabajadores:** probar el camino de recreación del pool con más de un trabajador (M0 lo dejó sin probar).
6. **Medición:** p95 por etapa y de punta a punta, con 1, 5 y 10 clientes a la vez; memoria del servicio, los trabajadores y el modelo.

## Criterios de aceptación

- [ ] Un cambio de umbral de compuerta no obliga a recalcular (prueba).
- [ ] Un reinicio no pone el contador en cero (prueba).
- [ ] 503 cuando la cola se llena; ninguna petición queda colgada.
- [ ] `evidencia/m1-17_rendimiento.md` con el p95 por etapa frente al §21.
