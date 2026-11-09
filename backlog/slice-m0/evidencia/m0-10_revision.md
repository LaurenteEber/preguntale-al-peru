# M0-10 — Revisión del auditor-agente de las 3 recetas (9/11/2026)

Auditor independiente, de solo lectura (subagente `gentle-ai-verify`). Revisó `curados/inferencia/recetas/{endes_anemia_6_35m,endes_anemia_6_35m_oms2024,endes_dci_menores_5}.yaml` contra `curados/capa0/definiciones_endes.yaml`, `src/pap/capa0/encuestas.py`, `curados/inferencia/cortes_estandar.yaml`, `cifras_doradas.csv` / `cifras_control_inei.yaml`, E-05, R-02 y el diseño §8.1.

| Receta | Aspecto | Veredicto | Evidencia |
|---|---|---|---|
| anemia (criterio anterior) | indicador HC57 en [1,2,3] | conforme | `definiciones_endes.yaml:15`; `encuestas.py:154`, `:166-168` |
| anemia (criterio anterior) | universo HC1 6–35, HC57 en 1–4, HV103 = 1 | conforme (ver D-M0-10-1) | `definiciones_endes.yaml:17-20`; `encuestas.py:146`, `:148`, `:213-227` |
| anemia OMS 2024 | indicador HC57A en [1,2,3]; mismo universo | conforme | `definiciones_endes.yaml:25-27`; `encuestas.py:155`, `:166-168` |
| DCI | indicador HC70 < −200 | conforme | `definiciones_endes.yaml:30`; `encuestas.py:157`, `:170` |
| DCI | universo 0–59 meses, HC70 en [−9989, 9989], HV103 = 1 | conforme | `definiciones_endes.yaml:32-34`; `encuestas.py:169`; n = 19 511 |
| las 3 | `transformaciones: []` | conforme | diseño §8.1 |
| las 3 | cortes `area` y `sexo` permitidos; los otros tres no, por C-M0-06-2/3/4 | conforme | `cortes_estandar.yaml`; la prueba de cortes pasa |
| anemia (criterio anterior) | 9 doradas 2024 | conforme | `cifras_doradas.csv:2-5,12-16`; nacional 43,7 (cubo 43,739) |
| anemia OMS 2024 | 9 doradas 2024 | conforme | `cifras_doradas.csv:44-52`; `cifras_control_inei.yaml:15-17,27`; nacional 35,3 |
| DCI | 3 doradas 2024, con casos y CV | conforme | `cifras_doradas.csv:61-63`: 12,1 (19 511; CV 2,8), 8,5, 20,9 |
| las 3 | reproducción E-05 (±0,1 pp) | conforme | 21 de 21 doradas, dif. máx. 0 pp |
| las 3 | `estado: revisado` + `pendiente: visto_dueno` (no `verificado`) | conforme | `recetas.py:107,125` |
| las 3 | campo `receta` en `dim_indicador` (R-02) | conforme | `dim_indicador.yaml:11,258,484` |
| las 3 | 90 filas iguales al cubo (definición de hecho, punto 1) | conforme | cálculo propio sobre `m0-10_recetas_vs_cubo.csv`: 0 en todas las columnas, redondeadas y sin redondear |

**Límite:** los PDF del INEI no se abrieron (sin red); las doradas se comprobaron contra el registro del repo (`cifras_doradas.csv`), que cita documento, página y quién las verificó.

## Hallazgos

- **H-1 (baja, redacción) — resuelto.** El motivo de `region_natural` y `quintil_riqueza` decía «el corte no tiene variable en un archivo que se una a RECH6». RECH23 y RECH6 cuelgan de RECH0 por HHID; lo que falta es la unión declarada. Ahora dice «no hay unión declarada RECH6 → RECH23 (las dos cuelgan de RECH0 por HHID)», en las 3 recetas. No cambia ninguna cifra: `validar-recetas` sale bien y las 56 pruebas de las recetas pasan.

**Hallazgos abiertos: ninguno.**

## D-M0-10-1 (universo `nino_hecho_hb_medida` frente a `nino_hecho`)

- **Comprobado por el auditor:** en 2024 hay 0 niños con HC57 o HC57A en 1–4 y HC55 ≠ 0 (o nulo), en 6–35 y en 0–59 meses, con o sin pernocte; n = 9 959 con y sin la condición, igual al cubo.
- **Seguro para M0** y no bloquea `verificado` (no hay diferencia de cifra en 2024). La prueba `test_recetas_microdatos.py:78-83` queda de control.
- **Antes de usar las recetas en otro año (M1):** que el verificador aplique el `universo_analitico` que nombra la receta, o que `validar-recetas` falle si la receta declara predicados que el verificador no aplica.

## Comandos

```
$ uv run pap inferencia validar-recetas
✔ endes_anemia_6_35m: estado revisado, pendiente visto_dueno, 9 dorada(s)
✔ endes_anemia_6_35m_oms2024: estado revisado, pendiente visto_dueno, 9 dorada(s)
✔ endes_dci_menores_5: estado revisado, pendiente visto_dueno, 3 dorada(s)

$ uv run pap inferencia receta endes_dci_menores_5 --anio 2024 --comparar-cubo
  Contra el cubo (30 de 30 filas), máxima |dif| redondeada a 8 decimales: todas 0.00e+00
  Compuertas: 0 fila(s) con estado o reglas distintos de m0-00_estados_cubo.csv
  Doradas (E-05): 3 de 3 se reproducen

$ uv run pytest -q tests/inferencia/test_recetas.py tests/inferencia/test_recetas_microdatos.py
56 passed
```

**Visto del dueño (K-03):** pendiente. Hasta entonces las recetas quedan en `revisado`.
