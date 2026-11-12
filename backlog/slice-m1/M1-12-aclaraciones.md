# M1-12 — Aclaraciones

**Se deriva de** el diseño §13.

## Tareas

1. **Tope común de 2 rondas** por pregunta (`aclaracion_rondas_max`), sumando las de lugar y las del motor. Después de 2, se calcula el plan más votado, se dice en «Entendimos» y las otras lecturas quedan como botones.
2. **Si hay una receta entre las lecturas, no se pregunta** (decisión 1).
3. **Una dimensión por pregunta,** en este orden: concepto → población → período → año → lugar.
4. **Opciones:** de 2 a 3 más «Otra cosa». Cada opción es un plan **ya calculado que pasó las compuertas**; las que no pasan se descartan en silencio. Si queda una sola, se responde con ella.
5. **`elegir_plan` con `id_plan`:** el motor guarda 24 h los planes ofrecidos, con llave sha256 de la interpretación estructurada (nunca el texto, P-03). Si el `id_plan` ya no está, pide preguntar de nuevo; no vuelve a planificar en silencio.
6. **«Otra cosa»** abre la caja de texto con lo escrito y la ayuda del §13; cuenta como ronda.
7. **Textos sin jerga** (nunca «universo», «módulo», «variable»), en `curados/motor/textos/`, por el corrector actual. Los aprueba el dueño.

## Criterios de aceptación

- [ ] Con un LLM falso que cambia el orden de las opciones, la cifra del plan elegido no cambia.
- [ ] «¿Los niños del campo en Puno reciben hierro?» produce una aclaración con opciones que difieren materialmente y pasan las compuertas.
- [ ] Nunca hay más de 2 rondas; prueba con lugar ambiguo más concepto ambiguo.
- [ ] La caché de planes no guarda el texto de la pregunta (prueba).
