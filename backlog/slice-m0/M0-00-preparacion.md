# M0-00 — Preparación

**Para qué.** Partir de una base medida y conocer las interfaces actuales que el motor nuevo reutiliza.

## Tareas

1. **Rama:**
   - crear `slice-m0` desde `main`;
   - el primer commit agrega los documentos nuevos que están en el árbol de trabajo: `docs/diseno/`, `backlog/README.md`, `backlog/plan_slices.md`, `backlog/slice-m0/` (con `evidencia/auditoria_seguridad_previa.md`) y `backlog/slice-m1/`.
2. **Base:**
   - `uv run pytest -q` completo en el Mac → `evidencia/pytest_base.txt` (cuántas pasan y cuánto tarda);
   - comprobar que el cubo tiene la huella `010ea965`;
   - **copiar el cubo** a `evidencia/fact_indicador_010ea965.parquet`, porque `pap calcular` lo sobrescribe en M0-00b y en M0-03. Va fuera de git: se agrega `backlog/**/evidencia/*.parquet` a `.gitignore` y se registra solo su huella.
3. **Interfaces actuales** que se reutilizan, con sus líneas exactas → `evidencia/m0-00_interfaces.md`:
   - `src/pap/capa0/encuestas.py` y `curados/capa0/definiciones_endes.yaml`:
     - universo, peso, estrato (`f"{HV024:02d}-{HV022}"`) y UPM (HV021);
     - anemia = HC57 o HC57A en 1–3, con universo en 1–4;
     - DCI = HC70 < −200, con HC70 válido;
     - población de hecho (HV103);
   - `src/pap/capa0/ambitos_lima.py` y `calculo.py:157-160`: cómo se arman el departamento sin el 07, el Callao, Lima Metropolitana, Lima Región y el área;
   - `src/pap/motor/calculo.py`: `_svy_niveles`, `n_efectivo` (sin tope) y el redondeo a 8 decimales (`DECIMALES`, líneas 643–646);
   - `src/pap/motor/validador/reglas_etapa4.py`: R-ENC-02 a R-ENC-04 (el oráculo de las compuertas);
   - `reglas/consolidador/`: cómo se cambia una regla (`ajustes_dueno.py`, `CAMPOS_REGLAS`, reglas nuevas con etapa, `vp3_checks.py`, `prueba_guardia.py`);
   - `src/pap/registrar.py`, `src/pap/capa0/insumos.py` (`escribir_lock`) y `curados/insumos.lock.yaml`;
   - `curados/recetas/inei_microdatos_catalogo.json` (los 13 módulos de la ENDES 2024, código 968).
4. **Filas del cubo de 2024** → `evidencia/m0-00_filas_cubo_2024.csv`:
   - **90 filas** (3 indicadores × 30);
   - columnas: indicador_id, nivel, territorio_id, valor, ee, cv, ic_inf, ic_sup, gl, n_muestra, n_efectivo, deff, numerador y avisos.
5. **Estado de las compuertas** de esas 90 filas según `reglas_etapa4.py` → `evidencia/m0-00_estados_cubo.csv` (es el oráculo de M0-09).

## Criterios de aceptación

- [ ] Los documentos nuevos están en el primer commit de la rama.
- [ ] Base de pytest guardada; huella del cubo `010ea965`; copia del cubo hecha.
- [ ] Interfaces documentadas con sus líneas exactas.
- [ ] CSV con 90 filas y CSV de estados.

## Fuera

Cualquier cambio de código.
