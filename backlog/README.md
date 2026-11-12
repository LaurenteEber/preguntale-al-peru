# Backlog

Cómo se planifica y se ejecuta el trabajo desde la fase 5.

- **`plan_slices.md`**: los slices que faltan hasta la beta y después. Un slice es un corte vertical: al terminarlo, el usuario puede hacer algo que antes no podía, de punta a punta, con sus pruebas.
- **Slices del motor de inferencia (desde el 9/11/2026):** `slice-m0/`, `slice-m1/`… con historias `M<N>-<nn>-<nombre>.md` y la misma estructura que abajo. El diseño está en `docs/diseno/`. **El slice en curso es M0** (`slice-m0/README.md`, sección «Cómo empezar»); el slice 4 de beta queda en pausa hasta M4.
- **`slice-N/`**: el backlog de un slice. Solo se detalla el slice en curso; los siguientes se detallan al cerrar el anterior, con lo aprendido.
  - `README.md`: objetivo, orden de las historias, definición de hecho y decisiones del dueño que lo afectan.
  - `S<N>-<nn>-<nombre>.md`: una historia por archivo, con contexto, tareas, criterios de aceptación verificables y lo que queda fuera.
  - `consultas_al_dueno.md`: consultas que bloquean y supuestos aplicados por el implementador.
  - `evidencia/`: salidas de pruebas, informes de auditoría y reportes que prueban los criterios de aceptación.

## Quién implementa

El agente implementador sigue `agents.md` (raíz del proyecto): qué leer, en qué orden, cómo trabajar cada historia, qué hacer con los vacíos del diseño y qué no se hace nunca. Los valores por defecto del motor están en `curados/motor/parametros_motor.yaml`.
