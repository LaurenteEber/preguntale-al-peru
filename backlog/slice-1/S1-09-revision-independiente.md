# S1-09 — Revisión independiente (usuario y estadística)

## Por qué

P-06: analistas y auditores independientes donde un error se escaparía fácilmente. Aquí hay dos riesgos así: que el planificador aplique mal una decisión estadística, y que las respuestas nuevas se lean mal.

## Tareas

Quién revisa: si el implementador es un solo agente, el auditor, el revisor y el verificador son **subagentes nuevos**, sin la conversación del implementador, cada uno con un encargo escrito y guardado (`evidencia/encargo_s1-09_<rol>.md`: qué revisar, con qué criterios y qué entregar), o el dueño. Ninguno ve los informes de los otros antes de entregar el suyo.

1. **Auditor estadístico** (agente o persona que no haya escrito el código): revisa `intenciones.yaml` y el planificador contra E-03 a E-08, S-01, G-07 y R-03; elige 15 respuestas de la matriz y verifica, para al menos una cifra de cada fuente, que coincide con la dorada oficial o con el cubo. Informe en `evidencia/auditoria_estadistica.md` con hallazgos clasificados (bloqueante, alto, medio, bajo).
2. **Revisor de usuario:** con las 4 personas de `03_auditoria/revision_usuario/`, lee 20 respuestas de la matriz (incluidas 4 de «no se puede» y 2 aclaraciones) y anota malas lecturas probables. Informe en `evidencia/revision_usuario.md`.
3. Corregir los hallazgos altos y bloqueantes; un verificador (tercer subagente) confirma las correcciones sin regresiones (S1-07 y S1-08 en verde) y deja `evidencia/verificacion_correcciones.md`.
4. Las correcciones que cambien una decisión no se aplican: van a `consultas_al_dueno.md`.

## Criterios de aceptación

- [ ] Dos informes con veredicto «apto» o «apto con observaciones».
- [ ] 0 hallazgos bloqueantes o altos abiertos; `verificacion_correcciones.md` existe.
