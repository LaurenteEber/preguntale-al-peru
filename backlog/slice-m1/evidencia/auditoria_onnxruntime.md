# Auditoría de dependencia — onnxruntime 1.31.1 (solo CPU)

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** ejecuta el modelo de significado (formato ONNX) para convertir textos en vectores, en el recuperador de M1-09 y en el banco de M1-09b (e5-small, granite-97m, granite-311m).
- **Alternativa sin dependencia nueva:** ninguna práctica (PyTorch pesa mucho más y arrastra más código).
- **Dónde se usa:** `src/pap/inferencia/` (embeddings, M1-09). No se usa en el servicio web.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. PyPI `https://pypi.org/project/onnxruntime/` (proyecto de Microsoft, `https://github.com/microsoft/onnxruntime`) |
| Fecha de publicación (≥ 14 días) | **1.31.1:** 26/10/2026 (**17 días**). La 1.31.0 es del 9/10/2026 (34 días). No hay versión más nueva |
| Versión fijada y con hash | Todavía no está en el lock. cp312 macOS arm64 (`onnxruntime-1.31.1-cp312-cp312-macosx_14_0_arm64.whl`, 20 882 125 bytes): `96dd2564b10ea7153ad9c207e7cd8e5917cb3ba521e0e0a62ac03486fdc8d56c`. cp312 manylinux x86_64 (`…-cp312-cp312-manylinux_2_28_x86_64.whl`, 23 760 988 bytes): `1f3dea47f2f0e5117c2404cea7d21fd253ae7836a3bf167a501cdfbb2600d536` |
| Versión retirada (*yanked*) | No |
| Mantenedor y repositorio público | Microsoft Corporation; repo público |
| Licencia compatible | MIT |

## 3. Qué trae
- **Dependencias nuevas que arrastra** (sin extras): `flatbuffers` 25.12.19 (19/12/2025, OSV: 0), `protobuf` 7.36.2 (17/9/2026, 56 días, OSV: 0; la 7.37.0rc1 es *pre-release* y uv la ignora), `numpy` (ya en el lock, 2.5.3) y `packaging` (ya en el lock, 26.3). Los extras `symbolic` y `quantization` no se instalan.
- **Binarios, extensiones de C o Rust, scripts de instalación:** biblioteca nativa de C++ dentro del wheel. Solo wheel; no se compila nada. **El wheel de macOS exige macOS 14 o superior** (etiqueta `macosx_14_0_arm64`), igual que dice la auditoría previa.
- **Qué hace en segundo plano:** carga el modelo que se le dé. Trae activo el proveedor de Azure, por eso se fuerza CPU (condición 1). No hace telemetría ni red por sí solo.

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | API `POST /v1/query`, paquete `onnxruntime`, versión 1.31.1 y sin versión; también `flatbuffers` 25.12.19 y `protobuf` 7.36.2 | 0 en los tres |
| GitHub Advisories | `api.github.com/advisories?ecosystem=pip&affects=onnxruntime` | 0 |
| `pip-audit` | no disponible (ver `auditoria_pip_audit.md`) | pendiente de M1-09 |
| Rust / CRAN | no aplica | — |
| Si aparece algo | no hay hallazgos | |

## 5. Condiciones de uso
1. `InferenceSession(..., providers=["CPUExecutionProvider"])` siempre (control C10). Prohibido llamar sin `providers`.
2. Sin operadores personalizados: nunca `register_custom_ops_library` ni `SessionOptions` con bibliotecas externas. Un modelo con un operador personalizado fallará al cargar, que es lo deseado.
3. El modelo se carga desde bytes, después de verificar su SHA-256 contra el valor fijado en `datapackage.json` (los de `auditoria_modelos_lista_dueno.md`).
4. Los modelos de Granite y e5 no usan archivos de datos externos (`.onnx_data`): el árbol de cada commit no trae ninguno. Si aparece uno, no se carga.
5. Solo modelos de la lista aprobada (`auditoria_multilingual_e5_small.md`, `auditoria_granite_97m_r2.md`, `auditoria_granite_311m_r2.md`).

## 6. Veredicto
**aprobado con condiciones** (versión 1.31.1). La aprobación previa (1.31.x, solo CPU, sin operadores personalizados, modelo desde bytes verificado, macOS 14+) **sigue vigente**.
- **Revisión siguiente:** al subir la versión o al agregar un modelo.
