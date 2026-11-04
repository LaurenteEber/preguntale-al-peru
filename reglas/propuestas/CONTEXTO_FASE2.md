# Contexto común — Fase 2: reglas de publicación y atribución

Lee esto completo antes de proponer nada. Todas las reglas deben servir a este objetivo, no a uno genérico.

## 1. Qué estamos construyendo

**Pregúntale al Perú**: una web donde cualquier persona (ciudadano, periodista, funcionario municipal o regional) hace una pregunta en lenguaje natural sobre un problema del país —"¿cuánta anemia hay en mi provincia y cuánto se gasta en combatirla?"— y recibe una respuesta **calculada** cruzando fuentes públicas oficiales, por territorio (ubigeo), acompañada de una **ficha de límites** que dice qué tan confiable es cada cifra y qué no se puede concluir.

Flujo de una respuesta:
1. Un LLM interpreta la pregunta y elige indicadores de un catálogo curado (NO calcula cifras).
2. Consultas deterministas sobre la biblioteca curada producen los números (con IC, CV, n, año, nivel territorial).
3. **Un validador de reglas (lo que tú vas a especificar)** decide para cada cifra y cada cruce: publicar, publicar como referencial, agregar a otro nivel, agrupar años, suprimir o bloquear, y qué advertencia mostrar.
4. El LLM redacta la respuesta usando solo las cifras permitidas y las advertencias que el validador le entrega, con restricciones de lenguaje.

Por eso las reglas deben ser **verificables por código**: condiciones sobre campos del catálogo (esquema v2) y sobre estadísticos calculados (n sin ponderar, CV, IC, población del territorio, numerador), con umbrales explícitos y una acción concreta. Las reglas que no se puedan automatizar se marcan como "revisión humana".

Público: no especialista. Los rótulos deben entenderse sin saber estadística.

## 2. Decisiones ya tomadas (no se reabren)
- El LLM no calcula cifras; solo redacta a partir de resultados del motor.
- Ninguna fuente entra a la biblioteca sin la prueba de humo aprobada.
- El gasto del MEF se ubica por la sede de la unidad ejecutora; a distrito solo municipalidades o inversiones ubicadas por CUI (columna UBIGEO de MEF-DETALLE-INVERSIONES). La meta solo trae DEPARTAMENTO_META.
- No se almacenan ni publican datos personales (DNI, nombres) aunque la fuente los traiga.
- La tabla de distritos creados después de 2017 (ubigeo histórico) la construimos nosotros desde el Directorio Nacional de Municipalidades (INEI) y las leyes de creación.
- Hay tres poblaciones distritales: proyección INEI (total, 2018–2026, sin edad a nivel distrital), población estimada MINSA (por edad, en tableros REUNIS), RENIEC (población con DNI, no residente). Censos 2025: a oct-2026 solo primeros resultados nacionales y departamentales (29-05-2026); sin resultados distritales confirmados [corregido tras la prueba, PR-24]. La proyección por edad y sexo del INEI llega solo a departamento.

## 3. Dónde están los datos de referencia
- `esquema_v2.md`: campos del catálogo y vocabularios (base_geografica, tipo_medida, nivel_territorial_inferencia, anios_con_quiebre, etc.). **Las reglas deben referirse a estos campos por su nombre.** Si necesitas un campo que no existe, propónlo explícitamente en la sección "campos nuevos".
- `fuentes_ola0_ola1.md`: las 45 fuentes que se ingerirán primero, con su naturaleza, territorio, base geográfica, qué miden, llaves, años, quiebres y limitaciones.
- `catalogo_fuentes.json`: el catálogo completo (415 fuentes).
- `hallazgos_*.json`: hallazgos de la auditoría independiente. Tu encargo lista los IDs que te tocan; léelos completos (campo hallazgo, evidencia, recomendacion).

## 4. Formato obligatorio de cada regla (JSON)
```json
{
 "id": "R-<AMBITO>-NN",
 "ambito": "encuestas | registros | estimaciones | gasto | territorio | denominadores | cruces | lenguaje",
 "titulo": "frase corta",
 "enunciado": "1–2 oraciones normativas (debe/no debe)",
 "aplica_a": {"naturaleza_dato": [], "tipo_medida": [], "base_geografica": [], "fuentes": ["IDs del catálogo"]},
 "condicion": "expresión verificable: campos del catálogo y estadísticos (n_sin_ponderar, cv, ic_inf, ic_sup, numerador, poblacion, nivel_territorial, anio...)",
 "accion": "publicar | publicar_referencial | suprimir | agregar_nivel | agrupar_anios | bloquear_cruce | rotular | advertir | revision_humana",
 "parametros": {"umbral_x": 0},
 "mensaje_usuario": "texto en lenguaje ciudadano que se muestra junto a la cifra (o null)",
 "justificacion": "por qué; con base en práctica oficial (INEI, DHS, OMS, ONS, Eurostat, etc.)",
 "referencias": [{"titulo": "...", "url": "https://..."}],
 "hallazgos_auditoria": ["INF-03", "..."],
 "ejemplo": "caso concreto con fuentes del catálogo",
 "implementacion": "cómo calcularlo: campos, fórmula, pseudocódigo",
 "casos_borde": "qué pasa en situaciones límite",
 "prioridad": "mvp | posterior"
}
```
- Umbrales con número, no "bajo" o "alto".
- Las referencias deben ser reales y verificadas con WebSearch/WebFetch; si no confirmas una, no la cites. No inventes URLs.
- Prefiere práctica oficial peruana (INEI) y luego estándares internacionales.
- Evita reglas redundantes; si una regla tuya depende de otro ámbito, decláralo en "dependencias".

## 5. Entregable de cada subagente
Un JSON en `propuestas/<ambito>.json` con:
```json
{"ambito": "...", "reglas": [ ... ], "campos_nuevos": [{"campo": "...", "tipo": "...", "donde": "catalogo|indicador|resultado", "para_que": "..."}],
 "dependencias": ["IDs de reglas o ámbitos de otros"], "preguntas_abiertas": ["decisiones que debe tomar el dueño del proyecto"]}
```
Valida que parsee con python3. Mensaje final breve: n.º de reglas (mvp/posterior), campos nuevos, 3 decisiones abiertas más importantes. No pegues el JSON.
