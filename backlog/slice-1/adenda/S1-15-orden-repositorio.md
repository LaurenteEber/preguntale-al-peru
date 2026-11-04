# S1-15 — Orden del repositorio

## Tareas

1. **`odd/tasks/slice-1.md`** (seguimiento interno del implementador): moverlo con `git mv` a `backlog/slice-1/evidencia/seguimiento_implementador.md` y borrar la carpeta `odd/` vacía. Desde ahora, el seguimiento de las historias vive solo en el `README.md` de cada slice (`agents.md` §9). Agregar esa línea a `agents.md` §9.
2. **Obsidian:** agregar `.obsidian/plugins/` y `.obsidian/community-plugins.json` a `.gitignore` (configuración local).
3. **README raíz:** la línea «Ramas: solo `main`» pasa a «Ramas: `main` y una rama por slice; los hitos llevan etiqueta».
4. **No se borra:** `biblioteca/_respaldo_pre_s1-00/` (lo decide el dueño), `biblioteca/cruda/almacen/` (crudos) ni la rama `slice-1`.

## Criterios de aceptación

- [ ] `git status` limpio tras el commit, sin archivos de Obsidian ni `odd/`.
- [ ] Ningún documento enlaza a `odd/`.
