# Encargo S1-09 — Verificador de las correcciones

Quién: un subagente nuevo, distinto del auditor, del revisor de usuario y del implementador (P-06). Rama `slice-1`. No se edita código ni datos: el verificador solo lee, corre pruebas y comandos, y entrega su informe.

## Qué revisar

1. Para cada hallazgo **bloqueante o alto** de `auditoria_estadistica.md` (A-H1, A-H2, A-H3) y de `revision_usuario.md` (H1 a H7), confirmar que está corregido: reproducir el comando o caso exacto del informe con `uv run pap preguntar … --salida salidas/s1-09_verificador` y leer la respuesta. La tabla de lo hecho está en `correcciones_s1-09.md`; no basta con confiar en ella. A-H2 tiene una parte de datos abierta como consulta C-05 (`consultas_al_dueno.md`): verificar solo que la respuesta avisa que no usa el año pedido.
2. Confirmar que las correcciones no introdujeron regresiones:
   - `uv run pytest -q codigo/ingesta/tests/test_regresion_q1_q4.py codigo/ingesta/tests/test_matriz_cobertura.py codigo/ingesta/tests/test_s1_09_correcciones.py` en verde (S1-07 y S1-08);
   - las cifras, semáforos y niveles de confianza de Q1–Q4 iguales a `codigo/ingesta/tests/referencias/q1..q4.json` (la prueba de regresión lo compara; leerla para confirmar que compara eso);
   - `backlog/slice-1/evidencia/matriz.md` regenerado con 0 errores y 0 fallos (opcional: volver a correr `codigo/ingesta/tests/matriz/correr.py` con salida bajo `salidas/`, unos 5 minutos);
   - que las correcciones no cambiaron `04_reglas/reglas.json`, `codigo/capa0/datos/` ni las referencias (`git diff 249ea7a HEAD --stat` sobre esas rutas).
3. Revisar en particular el uso de la prueba de diferencia entre territorios (R-ENC-11): que solo afirme «mayor» o «menor» con p < 0,05 y que no compare cifras suprimidas.

## Criterios

Cada hallazgo queda «corregido», «corregido con observación» o «no corregido», con evidencia (comando y frase de la respuesta, o `archivo:línea`). Cualquier cambio de cifra, semáforo, confianza o regla de bloqueo en Q1–Q4 es una regresión bloqueante.

## Qué entregar

El texto completo de `backlog/slice-1/evidencia/verificacion_correcciones.md`, en español: veredicto («correcciones verificadas, sin regresiones» o lo contrario); una tabla por hallazgo (ID, estado, evidencia); el resultado de las pruebas corridas; regresiones encontradas, si las hay.
