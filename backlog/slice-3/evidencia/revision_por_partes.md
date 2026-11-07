# Revisión independiente del slice 3, por partes (7/11/2026)

El dueño pidió «revisa el slice por partes». Todo el slice de una vez (692 archivos desde `main`) no entra en el límite de lo que un revisor puede leer. Por eso se revisó cada historia por separado, con la revisión nativa de gentle-ai (lentes de riesgo, resiliencia, legibilidad y confiabilidad, según lo que tocó cada historia).

**Cómo se partió.**
- Cada historia se revisó en una carpeta de trabajo aparte (`git worktree`) con un commit temporal que solo tenía su código: `src`, `curados`, `tests`, `docs`, `scripts` y `Dockerfile`.
- Quedaron fuera la evidencia generada (`backlog/`, por ejemplo los JSON de `base_api`), `odd/`, `uv.lock`, las grabaciones del intérprete y la librería de terceros `axe.min.js`.
- La rama `slice-3` no cambió. La carpeta aparte se borró al terminar.

## Resultado: todas las partes aprobadas, sin hallazgos que bloqueen

| Parte | Commits | Riesgo | Lentes | Resultado | Observaciones (no bloquean) |
|---|---|---|---|---|---|
| S3-00 | b18e473..6f6abba | bajo | — | sin revisión: solo una línea de documentación | — |
| S3-01 | e720518 | medio | riesgo, confiabilidad | aprobada | 3 |
| S3-02 | ddbdc0a, 965280f | medio | confiabilidad | aprobada | 1 |
| S3-03 | 764e785, e35991a | medio | riesgo, resiliencia, confiabilidad | aprobada | 9 |
| S3-01b | 329dda2 | alto | riesgo, confiabilidad | aprobada | 4 |
| S3-04 | ac21912 | medio | riesgo, legibilidad, confiabilidad | aprobada | 16 |
| S3-05 | fb10541 | medio | legibilidad, confiabilidad | aprobada | 19 |
| S3-07 | 095f5ef | medio | riesgo, resiliencia, confiabilidad | aprobada | 6 |
| S3-09 | bc7ecf0 | alto | riesgo, resiliencia, confiabilidad | aprobada | 7 |
| S3-06 | 6f18b5e | medio | confiabilidad | aprobada | 5 |
| S3-08 | 752ddc3 | alto | confiabilidad | aprobada | 6 |
| S3-10 (parcial) | f1e3769 | medio | legibilidad, confiabilidad | aprobada | 7 |
| S3-10 (correcciones) | 693f96f | medio | legibilidad, confiabilidad | aprobada | 17 |
| S3-10 (tarea 3) | 8505396 | medio | confiabilidad | aprobada | 1 |

## Observaciones que conviene atender (propuesta para S3-11 o el slice 4)

Ninguna bloquea. Estas son las que pueden afectar a una persona o al servicio; el resto son de estilo o de pruebas.

| Dónde | Qué observó el revisor | Propuesta |
|---|---|---|
| `src/pap/web/app.py` (S3-03) | Si el precalentamiento falla, `/salud` igual responde «ok» | Que `/salud` diga «no disponible» si el precalentamiento falló |
| `src/pap/web/app.py` (S3-03) | Un error interno no deja la traza en el registro | Registrar la traza sin el texto de la pregunta (P-03) |
| `src/pap/web/app.py` (S3-03) | El candado de una respuesta a la vez puede trabar a los demás pedidos | Medirlo en el slice 4, con más de una persona |
| `src/pap/web/estatico/app.js` (S3-04) | Si se vuelve atrás en el navegador, los botones pueden quedar trabados en «Buscando…» | Reactivar los botones al volver a la página (evento `pageshow`) |
| `src/pap/web/registro.py` (S3-07) | Un texto con saltos de línea podría meter renglones falsos en el registro de accesos | Escapar los saltos de línea antes de registrar |
| `src/pap/web/limites.py` (S3-07) | Las IP viejas del límite por IP no se limpian del todo | Limpiar las entradas vencidas |
| `src/pap/web/servir.py` (S3-09) | `pap servir` avisa que está listo antes de escuchar de verdad | Avisar después de abrir el puerto |
| `Dockerfile` (S3-09) | La imagen escucha en todas las interfaces de red | Es intencional (S3-09-a); revisarlo en el despliegue del slice 4 |
| `tests/web/test_accesibilidad.py` (S3-06) | La prueba de axe podría pasar sin haber revisado nada | Comprobar que axe sí corrió (que revisó alguna regla) |
| `src/pap/web/guiado.py:117-121` (S3-10) | Una parte del manejo del lugar no encontrado en el formulario (H-08) no tiene prueba | Agregar la prueba que falta |

Nada de esto cambia cifras, semáforos ni reglas.
