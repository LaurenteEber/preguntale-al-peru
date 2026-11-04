# S3-06 — Accesibilidad y celular

## Tareas

1. **Prueba automática** en `tests/web/test_accesibilidad.py`, con la marca `navegador`, registrada en `pyproject.toml` como `solo_mac`.
   - Herramientas: Playwright (dependencia de desarrollo) y el `axe.min.js` de axe-core con versión fija, en `tests/web/vendor/` con su huella, que se inyecta en la página.
   - Páginas: inicio, guiado (pasos 1 y 2), respuesta (Q1 y Q3), aclaración (Huancavelica), «no se puede», mensaje y error.
   - Anchos: 360 px y 1280 px.
   - Criterio: 0 fallas `serious` o `critical`.
2. **Comprobaciones a mano** (`evidencia/s3-06_accesibilidad.md`, con capturas a 360 px):
   - todo se usa con teclado y con foco visible;
   - zoom al 200 % sin perder contenido;
   - `lang="es"`;
   - encabezados en orden;
   - los `<details>` se anuncian;
   - la confianza se entiende sin color;
   - los enlaces dicen a dónde llevan;
   - contraste AA en modo claro y oscuro.
3. **Peso:** la respuesta de Q1 pesa ≤ 100 KB sin comprimir; sin imágenes salvo el ícono.
4. **Sin Chromium en el entorno** (por ejemplo, si `playwright install chromium` no puede descargar):
   - `navegador` se deja fuera y se anota;
   - el supervisor corre esas pruebas en su entorno y deja el resultado en la evidencia;
   - la historia queda «hecha, pendiente de verificación» hasta entonces.

## Criterios de aceptación

- [ ] axe: 0 graves o críticas en todas las páginas y anchos (del agente o del supervisor).
- [ ] Lista manual completa, con capturas; Q1 ≤ 100 KB.
