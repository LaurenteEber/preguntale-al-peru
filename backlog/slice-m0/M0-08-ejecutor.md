# M0-08 — Ejecutor: pool y adaptador de `svy`

**Se deriva de** el diseño §14 y de `docs/diseno/tecnologias.md` §2 y §4.

## Tareas

1. **Adaptador** `src/pap/inferencia/svy_adaptador.py`, el **único** módulo que importa `svy`.
   - Usa `Design(stratum, psu, wgt)`, `Singleton("center", domains="standard")` y `estimation.prop(..., by=, where=u)` con `ci_method="korn-graubard"`.
   - **Reindexa los dominios pedidos:** un dominio vacío sale con `n=0` y «sin datos».
   - n efectivo = mín(n, p(1−p)/ee²), o n si ee = 0.
   - Devuelve una `Estimacion` por dominio: valor, ee, gl, n, n efectivo, deff, IC, eventos y tasa de no respuesta.
2. **Ejecutor** `src/pap/inferencia/ejecutor.py`.
   - DuckDB endurecido → `.arrow()` → `pl.from_arrow` → adaptador.
   - Un nulo de `y` dentro de `u` es un error interno, y queda registrado.
   - **Varios años** según `relacion_entre_anios.csv`:
     - `independiente`: se calcula año por año;
     - `conglomerados_repetidos`: un solo `Sample` apilado con la UPM estable.
   - Si una llamada excede el tiempo, se parte y se reintenta una vez.
3. **Pool de procesos** (`tecnologias.md` §4):
   - `spawn`, `max_tasks_per_child` y precalentamiento;
   - tiempo suave con `signal.alarm` y tiempo duro: el padre mata al trabajador y recrea el pool;
   - vigía de memoria con `ru_maxrss` (bytes en macOS, KiB en Linux);
   - variables de hilos fijadas antes de importar;
   - DuckDB con `threads=1` y `memory_limit` por trabajador.
4. **Pruebas del pool:** exceso de tiempo en Python, una llamada nativa larga (275 dominios), exceso de memoria y caída del trabajador. En cada caso, error controlado en ≤ timeout + 3 s, y la tarea siguiente funciona.

## Criterios de aceptación

- [ ] Las pruebas del pool pasan en el Mac y en Linux.
- [ ] **Equivalencia:** anemia 2024 nacional, por área y por departamento sale igual por el ejecutor nuevo (sobre `endes_nino.parquet`) que por `calculo._svy_niveles`.
  - Valor, ee, IC, gl, n y deff con |dif| ≤ 1e-12.
  - El n efectivo igual a mín(n, el de `calculo.py`). El cubo no lo topa: en 2024 hay 12 filas con n efectivo > n.
- [ ] **p95 en el Mac** → `evidencia/m0-08_tiempos.md`.
  - Sobre microdatos de 2024: 1 año con 25 y con 100 dominios.
  - Sobre `endes_nino.parquet` 2023–2024 y 2021–2024: 2 y 4 años apilados.
  - Sobre el sintético: 275 dominios en una llamada.

## Fuera

Las comparaciones (`contrast`, Rao-Scott): van en M1 y M2, salvo las pruebas del adaptador.
