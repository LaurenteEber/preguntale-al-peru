# Slice 2 — Consultas al dueño

Mismas reglas que el slice 1 (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### E-01 — El entorno no puede subir a GitHub (S2-00) · abierta
- **Qué pasa:** todo `git push` desde esta sesión de la nube responde 403 («Claude doesn't have GitHub access to LaurenteEber/preguntale-al-peru»). La adenda y el slice 2 están solo en la sesión.
- **Por qué importa:** el entorno de la nube es efímero; si se reclama antes de subir, se pierde el trabajo. Tampoco se puede abrir el PR.
- **Qué se hizo:** `slice-2` nace de la punta de `slice-1-adenda` (S1-16 en verde), como pide S2-00 tarea 3 cuando la adenda no está fusionada. El PR del slice 2 va después del de la adenda.
- **Propuesta:** reconectar GitHub en claude.ai (Ajustes → Conectores) o instalar la app de Claude en el repositorio; luego subir `slice-1-adenda` y `slice-2`.

### E-02 — No hay clave de la API del LLM en el entorno (S2-00) · abierta
- **Qué pasa:** el entorno no tiene `ANTHROPIC_API_KEY` (comprobado sin imprimirla) ni el paquete del cliente.
- **Por qué importa:** S2-04 (grabar), S2-07, S2-08 (grabar), S2-09 y la corrida de S2-10 necesitan el LLM real.
- **Qué se hace:** según el README del slice, se sigue hasta S2-03 y con lo que no necesita el LLM real.
- **Propuesta:** agregar la clave como variable secreta del entorno y permitir la salida de red a `api.anthropic.com`.

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
