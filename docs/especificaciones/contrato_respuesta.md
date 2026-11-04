# Contrato de respuesta por capas

Decidido por el dueño el 12/10/2026, tras la revisión desde la perspectiva del usuario (`03_auditoria/revision_usuario/`). Aplicado a Q1–Q4 y, desde el slice 1 (3/11/2026), a toda respuesta del motor por intenciones, incluidos los tipos `no_se_puede` y `aclaracion` (abajo).

## Capas

| Capa | Contenido | Reglas |
|---|---|---|
| **1. Visible** | respuesta corta · cifra clave · «Ojo al leer» · confianza | Objetivo ≈ 100 palabras, máximo 125 (prueba) |
| **2. Más contexto** (desplegable) | tarjetas de cifras secundarias · avisos de las reglas · límites (ficha corta) | Cada tarjeta lleva su etiqueta «no se compara» cuando aplica |
| **3. Para citar y verificar** (desplegable) | una cita por cifra · glosario · «¿Qué puedo hacer?» | La cita usa el documento oficial si hay dorada; si no, «cálculo propio con …» |
| Detalle técnico | tabla de cifras, semáforo interno, ficha larga, reglas, texto con marcadores | Solo para auditoría |

## Reglas de redacción

1. **La respuesta corta responde la pregunta literal.** Si la respuesta honesta es «no se puede saber», va primero; luego viene «lo más cercano».
2. **Una sola cifra clave** en la capa 1. Las cifras que no se comparan con ella van a la capa 2 con su etiqueta.
3. **«Ojo al leer»: 1 a 3 viñetas** con lo que el lector **no** debe concluir, en imperativo.
4. **Confianza sin colores:** «Confianza en los datos: alta / media / baja» (verde / ámbar / rojo internos) y el motivo, sin el rótulo técnico (decisión R-05). El semáforo de las reglas (R-CRUCES-09/10) no cambia.
5. **Sin jerga en la capa 1:** «medir la hemoglobina», no «tamizar»; «gastado», no «devengado». «Estadísticamente claro» se mantiene porque lo fija una regla, y se explica en el glosario y en «Ojo».
6. **Los avisos de las reglas** se muestran como lo que no se debe concluir (`capas._aviso_ciudadano`); la regla no cambia.
7. **Todo texto visible pasa por el validador.** `texto` es la unión de corta + clave + ojo + contexto. Los números solo entran por marcadores.
8. **Orden neutro** en listas que no se pueden ordenar (alfabético en Q4).
9. **«¿Qué puedo hacer?»:** solo texto fijo que resume y enlaza una fuente oficial (`curados/motor/textos/que_hacer.yaml`). Se muestra «pendiente de revisión» hasta que `revisado_dueno: true`.

## Tipos de respuesta

El campo `tipo` del `respuesta.json` dice cuál es. `respuesta` es la estructura de arriba; los otros dos aplican la regla 1 y no calculan cifras.

| Tipo | Cuándo | Qué contiene cada capa |
|---|---|---|
| **`no_se_puede`** | Los datos o las reglas no permiten responder (año sin datos, nivel no válido, precisión o privacidad insuficientes, distrito creado después, tema fuera del piloto, cruce fuera de la lista blanca…) | **1:** respuesta corta que dice primero lo que no se puede, de máximo `no_se_puede.respuesta_corta_max_oraciones` oraciones (hoy 2), y «Lo más cercano que sí tenemos» con una alternativa. **2:** el motivo («Por qué no se puede»), sin códigos internos, y los límites. **3:** citas y glosario solo si hay algo que citar |
| **`aclaracion`** | El lugar es ambiguo o falta el tema | Solo la pregunta («Hay varios lugares llamados «X». ¿Cuál quieres?») y las opciones numeradas. Sin capas, sin cifras, sin confianza |

Reglas de `no_se_puede`:
- **Primero lo que no se puede** (regla 1): la respuesta corta empieza con «No …» o «Todavía no …».
- **Nunca muestra una cifra**: ni la suprimida ni otra. Un número solo entra por marcador desde el cubo (R-LENGUAJE-03), y aquí no se usa ninguno.
- **La alternativa está verificada:** solo se ofrece un año, un nivel o un lugar cuya cifra el validador deja publicar; si no hay, lo dice. No la elige el texto, la elige el validador.
- **Parcial:** si alguna cifra principal sí es publicable, se responde con ella y una oración dice lo que falta («Lo que no pudimos mostrar»).
- Textos en `curados/motor/textos/no_se_puede.yaml`; códigos de motivo de R-LENGUAJE-05.

## Implementación

- `pap/motor/capas.py`: arma las capas; no calcula ni decide reglas.
- `pap/motor/preguntar.py`: produce los tipos `no_se_puede` y `aclaracion`.
- `pap/motor/plantillas.py`: cada plantilla (una por intención) devuelve `corta`, `clave` (`ids`, `valor`, `texto`), `ojo`, `contexto`, `glosario` y `tema`.
- `curados/motor/textos/glosario.yaml` y `que_hacer.yaml`: textos fijos.
- Salida: `respuesta.json` → `capas.capa1/2/3`; `.md` en ese orden.
- Pruebas: `test_contrato_respuesta_por_capas`, `test_respuesta_corta_dice_primero_lo_que_no_se_puede`, `test_que_hacer_solo_fuente_oficial`; para los tipos nuevos, `test_no_se_puede.py` (un caso por motivo) y la matriz de cobertura.

## Resultado en el piloto

| | Antes (palabras visibles) | Ahora (capa 1) |
|---|---|---|
| Q1 | ~208 + avisos | 106 |
| Q2 | ~211 + avisos | 124 |
| Q3 | ~420 + avisos | 113 |
| Q4 | ~175 + avisos | 123 |

Ninguna cifra, estado ni semáforo cambió frente a `main`. Q1 agrega la cifra de 2015 de la serie anterior (P4-15).

## Pendiente

- Revisión del dueño del texto de «¿Qué puedo hacer?».
- Q3: la confianza «baja» se explica por el SIEN, que no está en la capa 1.
- X-02 (P4-21, dar los 52 casos en Q2), en `docs/decisiones.md`. P4-09 quedó resuelto por T-02 (2/11/2026).

## Verificación independiente (13/10/2026)

El agente de la revisión de usuario releyó Q1–Q4 con las mismas 4 personas (`03_auditoria/revision_usuario/verificacion_respuesta_capas.md`). Veredicto: **apto con observaciones**; ya no hay malas lecturas graves en Q1, Q2 ni Q4. Corregido en la misma rama:
- **Q3:** la confianza explica la cifra que la fija (`motivo_confianza`); la tarjeta y la cita del gasto dicen su alcance (`alcance`); «no encontramos» en lugar de «no hay»; el «Ojo» ya no habla de cifras que no se ven.
- **Q1:** la respuesta corta dice con qué forma de medir se hace cada comparación.
- **Q4:** «En ese mapa…», orden alfabético explícito, la oración de departamentos dividida y la cita del Mapa con documento, anexo y página del INEI.
- **Q2:** «el INS publica la misma cifra (9,5 %)».
- «Límites» sin «tamizaron».
- El aviso de fuentes de distinto tipo ya no insinúa causalidad.
- «¿Qué puedo hacer?» pasa a un bloque propio bajo la confianza, con texto para cualquier lector.
- El conteo de palabras va al detalle técnico.

Quedan como estaban, porque son textos de las reglas (`reglas.json`) y su cambio pasa por el consolidador: la frase estándar de efecto («cómo cambió el indicador») y el código NC-TENDENCIA-QUIEBRE en «Límites» de Q1.
