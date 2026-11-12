# Auditoría de dependencia — modelo `hotchpotch/bekko-embedding-v1-a25m` (opcional)

Plantilla de M0-00b. **Historia:** M1-09b (tarea 2, «opcional, solo si su auditoría lo aprueba») · **Fecha:** 12/11/2026 · **Quién la hizo:** agente (solo la API de Hugging Face y la ficha; no se bajó ningún peso)

## 1. Qué es y por qué se evaluó
- Modelo de 123 M de parámetros (25 M activos por token), 384 dimensiones, MIT. La ficha informa 57,5 en recuperación multilingüe (medida por el propio autor con su banco HAKARI-Bench; la ficha misma dice que espera su envío a la tabla oficial).

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí, `https://huggingface.co/hotchpotch/bekko-embedding-v1-a25m` |
| Commit más reciente | `44f0b8af0f487acd0ccf1a7cb7ae7a29a6dfc09c` (5/8/2026, 99 días; solo cambia documentación). Si algún día entra, es el que se fijaría |
| Antigüedad del modelo | Creado el 19/7/2026: **116 días** |
| Mantenedor | **Un solo autor** (Yuichi Tateno, `hotchpotch`), cuenta personal; 5 533 descargas |
| Licencia | MIT (compatible) |
| Código remoto | No: sin `.py` en el árbol y `config.json` sin `auto_map` (bien) |
| ONNX oficial | Sí, `onnx/model.onnx` (199 300 251 bytes, SHA-256 `d676a3d4f769e63de4bf6778068761eced1721f29b1b6909e94b3f9544e2edd3`). **Pero** el propio autor escribe «para CPU nativa no recomendamos ONNX Runtime; usa OpenVINO» (con OpenVINO fue 6,1 veces más rápido en un Ryzen 9 y 1,9 veces en una Raspberry Pi 5). Además, ese `model.onnx` guarda la tabla de palabras en int8: es un artefacto particular del autor, distinto de un export estándar, y nada lo ha probado en `onnxruntime` 1.31 |

## 3. Qué se descargaría (no se pide)
Si algún día entrara: `onnx/model.onnx`, `tokenizer.json` (34 363 442 bytes, `8bd47075711f75a143d1b78e01a41cc65c1c591b00d3cfeffc23db07adce1392`) y los JSON de configuración. Datos de la ficha: 384 dimensiones (Matryoshka a 256, 128 y 64), agregación por promedio, **sin prefijos**, 8192 tokens.

## 4. Vulnerabilidades conocidas
No hay avisos aplicables a un modelo. No hay código remoto. El riesgo no es técnico sino de confianza y de integración (ver §6).

## 5. Condiciones de uso
No aplican: no entra.

## 6. Veredicto
**no aprobado por ahora; se omite del banco.**
- Motivos: un solo autor y un modelo de 3,8 meses con pocas descargas (criterio de la auditoría previa para componentes de un solo mantenedor); su cifra es del propio autor; el único ONNX está pensado para el navegador y el autor desaconseja ONNX Runtime en CPU, que es nuestra única vía (OpenVINO no está aprobado ni en el stack).
- Es un modelo **opcional** de M1-09b: según esa historia, «si la auditoría no lo aprueba, se anota y se sigue». **No es una consulta tipo C** (no cambia ninguna decisión) y no bloquea nada. El banco corre con e5-small, granite-97m-r2 y granite-311m-r2.
- **Revisión siguiente:** en M2, si el banco muestra que ninguno de los tres alcanza y bekko sigue disponible con más historia.
