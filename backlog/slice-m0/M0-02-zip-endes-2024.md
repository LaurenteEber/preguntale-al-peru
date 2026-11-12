# M0-02 — ZIP de la ENDES 2024: lista, registro y respaldo

**Se deriva de** el diseño §6 (obtención, respaldo y ciclo por bloque) y de F-03 y F-04 (editadas en M0-01). Respaldo en el repo **privado** `LaurenteEber/preguntale-al-peru-crudos`: decisión del dueño del 9/11/2026. El repo principal es público y nunca recibe crudos.

## Tareas

1. **Lista** `curados/inferencia/descargas/endes_2024.yaml`, armada desde `curados/recetas/inei_microdatos_catalogo.json` (código 968, módulos 1629 a 1641). Las URL se validan: solo `https://proyectos.inei.gob.pe`.
   - **Formato:** el de la respuesta a K-06; para 2024 se recomienda Stata, el del cubo.
   - **Por cada módulo:** código, URL (`url_patron` de `curados/recetas/INEI-ENDES.yaml`), nombre del módulo, formato y `recurso` propuesto (`endes-2024-<nombre>`).
   - **Documentos:** se agregan la ficha técnica, los cuestionarios (hogar, individual y salud) y los diccionarios en PDF.
   - **Ya registrados:** los módulos 1629 (`endes-2024-hogar`) y 1638 (`endes-2024-anemia`) ya están registrados en Stata. Se marcan como `ya_registrado` y no se vuelven a bajar en el mismo formato.
2. **Aprobación del dueño** (K-01). Nada se descarga hasta que el dueño la aprueba.
3. **Descarga:**
   - el dueño, o el agente si su entorno en el Mac llega a `proyectos.inei.gob.pe`, deja los ZIP y los PDF en `biblioteca/cruda/bandeja/INEI-ENDES/`;
   - **no se usa `pap descargar`**, porque no permite fijar el `--recurso`.
4. **Registro, uno por uno:**

   ```
   uv run pap registrar INEI-ENDES biblioteca/cruda/bandeja/INEI-ENDES/968-ModuloNNNN.zip \
       --recurso endes-2024-<nombre> --url-descarga <url> --mover
   ```

   Cada uno queda en `biblioteca/cruda/capturas/INEI-ENDES/*/datapackage.json` con su huella.
5. **Respaldo** con `scripts/respaldar_crudos.sh`:
   - antes de subir, verifica que el destino es `LaurenteEber/preguntale-al-peru-crudos` (de `almacen.repo_crudos`) y que es privado (`gh repo view --json visibility`). Si no, se niega;
   - usa `gh release create/upload crudos-endes-2024 --repo LaurenteEber/preguntale-al-peru-crudos`;
   - sube cada ZIP y PDF, más un `SHA256SUMS`;
   - agrega un `LEEME.txt` con la atribución al INEI y la licencia (ODbL 1.0 para la ENDES, según el catálogo de fuentes);
   - parte con `split` cualquier archivo de más de 2 GB;
   - el token de `gh` es de grano fino, solo para ese repo y con `contents: write` (K-09). Se guarda en el Llavero de macOS y se pasa solo como `GH_TOKEN` del comando; nunca se imprime ni queda en el registro (C12);
   - límites de GitHub: menos de 2 GiB por archivo y 1 000 archivos por release;
   - si `gh` no tiene permiso desde el entorno del agente, lo corre el dueño.
6. **Medición:** tamaño de cada ZIP y total del bloque → `evidencia/m0-02_tamano_zip.md`, con la proyección a 2015–2025.
7. **Restauración de los ZIP** con `scripts/restaurar_crudos.sh` (en M0-11 pasa a `pap almacen restaurar`): en un directorio temporal, baja el release y comprueba las huellas contra los `datapackage.json`. La reconstrucción de un Parquet idéntico se prueba en M0-11, cuando ya existe el conversor.

## Criterios de aceptación

- [ ] Lista aprobada, con fecha, en `consultas_al_dueno.md`.
- [ ] Todos los ZIP y PDF registrados en `capturas/INEI-ENDES/` con su huella.
- [ ] El release `crudos-endes-2024` está en el repo privado, con `SHA256SUMS` y `LEEME.txt`.
- [ ] Prueba del script: se niega a subir a un repo público o distinto del configurado.
- [ ] Tamaño de los ZIP medido.
- [ ] La restauración da las mismas huellas (`evidencia/m0-02_restauracion.txt`).

## Fuera

Otros años, la ENAHO y el modelo de búsqueda (M1).
