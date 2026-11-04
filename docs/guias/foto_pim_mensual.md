# Guía: foto mensual del PIM — DESACTIVADA

> **Desactivada el 8/10/2026 por decisión del dueño** (`docs/decisiones.md`, F-04 y G-09): no habrá foto mensual del PIM y no se descargan más datos pesados; R-GASTO-07/18/19 trabajan con el PIM final del año. **No sigas los pasos de esta guía.** `pap foto-pim registrar|extraer`, `pap registrar MEF-FOTO-PIM-MENSUAL` y `pap descargar MEF-FOTO-PIM-MENSUAL` se niegan con un mensaje (bloque `desactivada` de la receta). El código y la guía se conservan por si se reactiva: haría falta una decisión nueva del dueño y quitar ese bloque.

---

_Texto original (7/10/2026), solo como referencia:_


Decisión 12 del dueño (7/10/2026). El MEF no publica el PIM mes a mes: cada descarga del archivo del año en curso trae
el PIM **vigente ese día**. Si no guardamos una descarga por mes, ese dato se pierde. Receta: `MEF-FOTO-PIM-MENSUAL`.

## Cada mes

| Qué | Detalle |
|---|---|
| **Cuándo** | Entre el 3.er y el 5.º día hábil del mes. El MEF actualiza el archivo a inicios de mes (el 5/10/2026 decía «actualizado 02-10-2026»). Si la fecha «actualizado» sigue siendo del mes anterior, reintenta otro día de esa ventana |
| **Qué descargar** | Solo `2026-Gasto-Mensual.csv` (de unos pocos GB a ~11 GB en diciembre). **Nunca** el `-Diario` (R-GASTO-04). En enero de 2027 descarga una última vez el de 2026 (cierre del año) y empieza con `2027-Gasto-Mensual.csv` |
| **De dónde** | Página: https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto. Anota la fecha «actualizado» del recurso. Enlace directo: https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Mensual.csv. Si Chrome muestra «Error de privacidad»: Configuración avanzada → Acceder; ver `GUIA_DESCARGA_MEF.md` |
| **Comando** | ver abajo |

```bash
cd ~/Documents/SideProjects/pregunta-al-peru
uv run pap foto-pim registrar ~/Downloads/2026-Gasto-Mensual.csv --corte 2026-11-03 --mover   # fecha «actualizado»
uv run pap foto-pim listar          # muestra las fotos y avisa si falta algún mes
git add biblioteca/cruda/capturas/MEF-FOTO-PIM-MENSUAL biblioteca/cruda/verificaciones.jsonl
git commit -m "Foto del PIM 2026-10"
```

### Qué hace el comando

- Lee el CSV, escribe la tabla compacta `foto_pim` en `biblioteca/estandarizada/gasto/foto_pim/` y registra el CSV como una captura nueva con su fecha. Nunca pisa una anterior. Tarda varios minutos.
- Si el mismo archivo ya estaba registrado, no se crea nada.
- `--mover` lleva el CSV al almacén y no deja copia en Descargas.

### Qué mes cubre cada foto

La foto se identifica por **(año, `mes_ref`)**. `mes_ref` es el último mes cerrado antes de la fecha «actualizado». Si no pones `--corte`, se toma la fecha de descarga.

| Descarga | `mes_ref` |
|---|---|
| 2/11/2026 | 10 (PIM a fines de octubre) |
| 5/1/2027, archivo 2026 | 12 |

Esto calza con R-GASTO-07: el avance al mes m es el devengado acumulado hasta m dividido entre el PIM de la foto m. Con o sin `--corte`, una descarga de los primeros días del mes da el mismo `mes_ref`. `--corte` sirve para que la cita diga «datos al …».

### Cuándo se detiene

- Si el archivo no trae devengado del `mes_ref`, el comando se detiene y avisa: el MEF todavía no lo actualizó. Reintenta otro día.
- También se detiene si el formato cambió: PIM fuera del mes 0 o meses fuera de 0–12.

### Si además quieres ese mes en la fact del gasto

Regístralo también con `pap registrar MEF-DA-PRESUPUESTO-EJECUCION-GASTO …`. El almacén no duplica el CSV.

## Si falta un mes

- **El PIM de ese mes no se puede reconstruir.** El devengado sí se puede, desde cualquier archivo posterior.
- No dupliques la foto del mes siguiente ni le cambies la fecha. Registra la siguiente con normalidad: `listar` deja el hueco a la vista.
- En las respuestas se aplica R-GASTO-07 tal como está:
  - la comparación al mismo mes usa la foto (año, m) solo si existe para todos los años comparados;
  - si no existe, se usa el PIM final del año, con el rótulo «avance respecto del presupuesto final del año (no del vigente en ese mes)»;
  - en el año en curso, se usa el PIM de la última descarga, con su fecha.
  - Nunca se toma la foto de otro mes ni se interpola.
- **Si el MEF no actualizó el archivo en todo el mes**, la huella es la misma, no se crea foto y `listar` muestra el hueco. Ese hueco es real: no hay un PIM a fin de ese mes.
- Si un hueco importa, se puede pedir al MEF el PIM a esa fecha por la Ley 27806 (borrador a pedido).

## Retención (lo decides tú)

- **Tamaño:** el archivo del año en curso crece durante el año (2025 completo pesa 10,5 GB). Las fotos suman ~60–70 GB por año.
- **Espacio:** el 8/10/2026 el disco tenía 64 GB libres. No alcanza para un año completo.
- **Recomendación:** conservar todos los crudos, porque no se pueden volver a descargar y `foto_pim` puede cambiar de versión y habría que extraerla de nuevo.
- **Antes de que se llene:** decide dónde guardarlos, por ejemplo en un disco externo o en una copia comprimida fuera del almacén.

## Borrador de tarea programada (lo propone el coordinador; no está creada)

**Cuándo corre:** de lunes a viernes, los días 3 a 9 de cada mes, a las 9:00 (America/Lima). Es idempotente: si ya existe la foto de ese mes, no hace nada.

**Requisitos:** Claude en Chrome en tu computadora, con la carpeta del proyecto y Descargas conectadas.

**Límite mientras dure el certificado vencido del MEF:** la tarea se detiene ante «Error de privacidad» y no completa la descarga. Ese mes tendrás que aceptar la advertencia tú mismo.

**Texto propuesto para la tarea:**

> Tarea mensual de Pregunta al Perú: foto del PIM.
>
> 1. En la carpeta del proyecto `pregunta-al-peru`, corre `uv run pap foto-pim listar`. Si ya hay una foto con `mes_ref` igual al mes anterior al actual, termina sin hacer nada.
> 2. Con Claude en Chrome, abre https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto y lee la fecha «actualizado» del recurso `<AÑO>-Gasto-Mensual.csv` del año en curso. En enero, usa el del año anterior. Si esa fecha es del mes anterior, termina y avísame: se reintenta otro día.
> 3. Descarga `https://fs.datosabiertos.mef.gob.pe/datastorefiles/<AÑO>-Gasto-Mensual.csv` a Descargas. Nunca el `-Diario`. Si aparece «Error de privacidad», no lo aceptes por tu cuenta: detente y avísame.
> 4. Espera a que la descarga termine: que no quede `.crdownload` y que el tamaño deje de cambiar.
> 5. Corre el registro desacoplado de la shell:
>    `setsid nohup uv run pap foto-pim registrar ~/Downloads/<AÑO>-Gasto-Mensual.csv --corte <fecha actualizado AAAA-MM-DD> --mover > ~/foto_pim_<AAAA-MM>.log 2>&1 < /dev/null &`
>    Revisa el log cada pocos minutos hasta que termine.
> 6. Corre `uv run pap foto-pim listar`.
> 7. No borres nada, no hagas commit ni push y no cambies de rama.
> 8. Repórtame: `mes_ref`, fecha de corte, filas, PIM total, carpeta de la captura y meses que falten. Si algo falla, copia el error y detente.
