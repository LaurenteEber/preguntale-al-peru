# M0-10 — Recetas 2024 que igualan al cubo

**Se deriva de** el diseño §8.1, R-02 y E-05 (editadas en M0-01) y el anexo A.

## Tareas

1. **Recetas** en `curados/inferencia/recetas/`. Usan las variables que el INEI ya entrega ajustadas; **no hay transformaciones** (`transformaciones: []`):
   - `endes_anemia_6_35m.yaml`: indicador `HC57 en [1,2,3]`; universo `nino_hecho_hb_medida` con `HC1 entre [6,35]` y `HC57 en [1,2,3,4]`;
   - `endes_anemia_6_35m_oms2024.yaml`: lo mismo con `HC57A`;
   - `endes_dci_menores_5.yaml`: indicador `HC70 < -200`; universo de niños menores de 5 de hecho con `HC70 entre [-9989, 9989]`.

   Cada una lleva los cortes permitidos, sus doradas y `estado: revisado` con `pendiente: visto_dueno`. Las líneas exactas salen de `definiciones_endes.yaml` y `encuestas.py:160-171`.

   Si alguna receta necesitara una transformación que no está en el código actual, es tipo C.
2. **Revisión:** el auditor-agente revisa las 3 recetas (`evidencia/m0-10_revision.md`) y entran en el lote del visto del dueño (K-03).
3. **`dim_indicador`:** agregar el campo `receta` a los 3 indicadores.
4. **Comando** `pap inferencia receta <id> --anio 2024 [--comparar-cubo]`: calcula por el camino nuevo (plan → verificador → ejecutor → compuertas) para los 30 territorios de `territorios.yaml` y compara con `evidencia/m0-00_filas_cubo_2024.csv`.
5. **Prueba `regresion_microdatos`:** las 3 recetas igualan al cubo con los criterios de la definición de hecho del README (punto 1).
6. **`verificado`:** se pone cuando se cumplen las tres cosas:
   - las recetas igualan al cubo;
   - reproducen sus doradas de 2024 (E-05: ENDES ±0,1 pp);
   - el dueño dio el visto (K-03).

## Criterios de aceptación

- [ ] `evidencia/m0-10_recetas_vs_cubo.csv` con las 90 filas y 0 diferencias por encima de la tolerancia.
- [ ] Las 3 recetas en `verificado`, con sus doradas citadas.
- [ ] Si alguna fila no iguala: consulta tipo C con el diagnóstico (universo, peso, estrato, territorio o formato), **sin ajustar datos ni tolerancias**.

## Fuera

Otros años, la pobreza y el «¿cuántos?».
