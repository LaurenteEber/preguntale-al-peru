# Reglas de publicación y atribución (v1.1)

Reglas que aplica el validador a cada cifra y a cada cruce antes de que el redactor (LLM) las use.

| Archivo | Qué es |
|---|---|
| `reglas.md` | Resumen por etapa (11 etapas, 0 a 10), conflictos resueltos, diccionario de campos, veredictos de la auditoría y decisiones del dueño. **Empezar aquí.** |
| `reglas.json` | Detalle completo de cada regla: condición, parámetros, implementación, casos borde, referencias y hallazgos que la modificaron |
| `ficha_limites_y_lenguaje.md` | Ficha de límites (corta y larga) y reglas de lenguaje del corrector |
| `especificaciones_capa0.md` | Especificación de las tablas de la capa 0 (ubigeo histórico, población, tablas curadas del MVP) |
| `alcance_piloto.csv` | Reglas del alcance del validador del piloto (68 implementadas); lo leen `pap validar-reglas` y las pruebas |
| `propuestas/` | Propuestas originales de los 5 subagentes y el contexto que recibieron (no se editan) |
| `consolidador/` | `consolida_reglas.py` genera los archivos de arriba a partir de `propuestas/` + `correcciones_prueba.py` + `correcciones_auditoria.py` + `ajustes_dueno.py` (decisiones del dueño, rondas 3 y 4, detector de mensajes y avisos del corrector; decisiones del gasto de las rondas 1–2: R-GASTO-08b y 18–21 nuevas, cambios en R-GASTO-05, 07, 08, 09 y 15, y 2 patrones del corrector); `corrector_estructural.py` (R-LENGUAJE-02 según los metadatos de cada cifra) |
| `consolidador/pruebas/` | Corpus del corrector: `corpus_reserva.json`, `corpus_auditor.json` y `corpus_ronda4.json` (232 oraciones únicas en total; tolerancia 0 de falsos positivos); `prueba_guardia.py` (prueba negativa de la guardia) y `vp3_checks.py` (comprobación de los cierres de la auditoría de reglas: `python3 -I reglas/consolidador/pruebas/vp3_checks.py .`, sin abiertos) |

**D-R4-1 (años de RMM, TMI y TMN).** Interruptor `D_R4_1` en `consolidador/correcciones_auditoria.py`: hoy `'C'` (periodos de 3 años 2017–2019, 2020–2022 y 2023–2025). Para ampliar a 5 años, poner `'B'` (2017–2021 y 2022–2026, con 2026 cerrado) y regenerar; las ventanas de 3 años se retiran. `None` aplica el estado seguro (años sueltos) y deja la decisión en `decisiones_pendientes` de `reglas.json`; un valor inválido detiene la consolidación.

**Guardia.** El consolidador se detiene si `CAMPOS_REGLAS` de `ajustes_dueno.py` pisa un campo ya corregido por una capa anterior. Prueba: `python3 reglas/consolidador/pruebas/prueba_guardia.py`.

**Decisiones del gasto, rondas 1–2 (7/10/2026).** Bloque final de `ajustes_dueno.py` (`NUEVAS_GASTO_R2`, `ETAPAS_GASTO_R2`, `PROHIBIDAS_GASTO_R2`, `CASOS_CORRECTOR_GASTO_R2`). Pruebas de consistencia nuevas: `gasto_r2_no_detectada`, `gasto_r2_falso_positivo`, `tema_fuera_de_gramatica`, `tema_sin_definir`, `alternativa_inexistente` y `prefijo_no_coincide_con_cadena`.

**Decisiones del dueño del 8/10/2026 (E1).** Bloque final de `ajustes_dueno.py`: R-ENC-08 para toda encuesta muestral (lee `catalogo/inferencia_verificada.csv` por fuente × año × módulo), R-DEP-01 sin MEF-PPR y con la compuerta leída solo del catálogo, nombres por año en R-GASTO-08 y la línea «transferido a municipalidades» de Llamkasun, R-GASTO-03 (advertencia de mixtas obligatoria en 5 funciones; línea aparte y aviso de sesgo de sede siempre) y R-GASTO-07/18/19 sin foto mensual del PIM. 23 pruebas de consistencia nuevas (contra `insumos.lock.yaml`, los manifiestos de la capa 0, `programas_sociales.yaml` y la tabla de inferencia, cuando existen). Informe y prueba negativa: `00_proyecto/analisis_2026-10-08/implementacion/e1_reglas/`.

**Lima en tres ámbitos (decisiones L1–L9 del dueño, 9/10/2026).** Bloque final de `ajustes_dueno.py`: NIVEL_RANK con LIMA_METROPOLITANA 3, LIMA_REGION 3,5, CALLAO 4 y dominio 8 4,5; R-CRUCES-01 sin fusión obligatoria y con contención territorial; R-ENC-08 con la rama «ámbito publicado» (aviso `ambito_no_dominio`); «Lima» → preguntar (R-TERRITORIO-09); `cuenta_en_ambito` para los dpto 15 y 07 (R-GASTO-03); SIEN por LM, LR y Callao; ranking de 26 unidades; CV > 15 % → referencial (R-ENC-04); se anula PR-03. El consolidador genera además el anexo S4 de `especificaciones_capa0.md` (antes agregado a mano). 18 tipos de prueba de consistencia nuevos (`PRUEBAS_LIMA_L`).

**Avisos del corrector.** 3 patrones que solo avisan, no bloquean (`lenguaje.avisos_pendientes_validacion` en `reglas.json`), «pendiente validación por terceros»: falta un corpus de ≥ 40 oraciones escrito por otra persona.

Las correcciones nunca se escriben a mano en `reglas.json` o `reglas.md`: se agregan a `correcciones_*.py` o a `ajustes_dueno.py` y se regenera.
