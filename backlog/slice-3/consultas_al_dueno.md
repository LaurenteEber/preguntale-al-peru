# Slice 3 — Consultas al dueño

Mismas reglas que los slices anteriores (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### W-01 — La etiqueta `slice-2-cerrado` no se pudo subir desde la nube (S3-00) · abierta (no bloquea)
- **Qué pasa:** el slice 2 se fusionó en `main` ([PR #2](https://github.com/LaurenteEber/preguntale-al-peru/pull/2), `e1a0d0f`). La etiqueta se creó en local, pero el push de etiquetas desde este entorno se corta («the remote end hung up»), aunque el de ramas funciona.
- **Propuesta:** desde el Mac: `git fetch origin main && git tag -a slice-2-cerrado e1a0d0f -m "Slice 2 cerrado" && git push origin slice-2-cerrado`.

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
