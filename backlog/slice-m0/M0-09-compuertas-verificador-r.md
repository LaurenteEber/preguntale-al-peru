# M0-09 — Compuertas y verificador en R

**Se deriva de** el diseño §15.1–15.2 y §23.1, de `docs/diseno/tecnologias.md` §3 y de R-ENC-02 a R-ENC-04.

## Tareas

1. **Compuertas** `src/pap/inferencia/compuertas.py`.
   - Leen los parámetros de R-ENC-02, 03 y 04 desde `reglas/reglas.json`. Conviene reutilizar las funciones de `src/pap/motor/validador/reglas_etapa4.py` en lugar de reescribirlas (`agents.md`: se reutiliza, no se duplica).
   - Árbol del §15.1: las reglas que suprimen cortan, las que marcan referencial se acumulan y gana la más severa.
   - Rótulo cuando p = 0 o p = 1.
   - El paso 8 (no respuesta) solo si K-07 está aprobada.
   - Devuelven `estado`, `motivos[]` y la confianza del §15.2.
2. **Microdato sintético** `tests/inferencia/datos/sintetico.parquet`, generado con un script y semilla fija. Cubre:
   - 6 estratos con 1 a 8 UPM;
   - 1 estrato con una sola UPM;
   - ids de UPM repetidos entre estratos;
   - pesos variables;
   - 2 años con UPM estable;
   - p = 0;
   - un dominio vacío;
   - una UPM por estrato dentro de un dominio;
   - n < 25;
   - CV > 30 %;
   - un corte de 5 grupos;
   - un `y` nulo dentro de `u`.
3. **Verificador en R** en `verificador_r/`:
   - `verificar.R`, que reutiliza el prototipo de la carpeta de trabajo anterior si el dueño lo copia (K-02); si no, se escribe con el Korn-Graubard NCHS a mano;
   - `renv.lock` con `renv` **1.3.1** y `nanoparquet` **0.5.2** (las versiones 1.2.4 y 0.5.1 no pasaron la auditoría), CRAN fijado a una instantánea con fecha; documenta la versión de `survey` y si incluye la corrección de la 4.5-2;
   - una prueba de pytest que valida `renv.lock` (versiones y repositorio);
   - se invoca con `Rscript --vanilla`, lista de argumentos sin shell, parámetros en un JSON y entorno mínimo sin `PAP_ANTHROPIC_API_KEY` ni `GH_TOKEN` (C11);
   - `README.md`;
   - escribe `tests/esperados/r_survey_sintetico.csv`, con las versiones en la cabecera;
   - una tarea `esperados-r` en el `justfile`.
4. **Pruebas rápidas:**
   - el adaptador frente a los esperados de R (1e-9 en est, ee e IC; gl y n exactos);
   - las compuertas, rama por rama.

## Criterios de aceptación

- [ ] Esperados de R generados en el Mac y guardados en el repo.
- [ ] **`svy` 0.35.0 coincide con R** en todos los casos del sintético (esto cierra la política de versiones de M0-03).
- [ ] Cada rama de las compuertas tiene al menos una prueba.
- [ ] **Las compuertas sobre las 90 filas del cubo** dan el mismo estado que `evidencia/m0-00_estados_cubo.csv` (calculado con `reglas_etapa4.py`). Si alguna difiere, es tipo C con su explicación.

## Fuera

Compuertas de medias, razones y medianas (M3).
