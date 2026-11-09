# M0-06 — Revisión del auditor-agente (9/11/2026)

Auditor independiente, de solo lectura (subagente `gentle-ai-verify`). Revisó fila por fila las 6 tablas de `curados/inferencia/` contra la ficha técnica ENDES 2024 (recurso `endes-2024-ficha-tecnica`, sha256 `ad40972d…`, pp. 2–4, 7–11 y 13–16), `curados/capa0/definiciones_endes.yaml` y el código (`encuestas.py`, `ambitos_lima.py`, `calculo.py`).

## Veredicto por fila

| Tabla | Fila | Veredicto | Evidencia |
|---|---|---|---|
| diseno_muestral | RECH0 hogar | conforme | Ficha p. 11: «HV001: conglomerado, HV022: estrato, peso=HV005/1000000»; estrato HV024×HV022 = E-01, `definiciones_endes.yaml:8`, `encuestas.py:140`; UPM HV021 = `definiciones_endes.yaml:10`, `encuestas.py:137` |
| diseno_muestral | RECH23 hogar | conforme | Ficha p. 11; unión por HHID declarada |
| diseno_muestral | RECH6 hemoglobina / talla | conforme | Ficha p. 9 y p. 11; HV005A no existe en 2024 |
| diseno_muestral | REC0111 | conforme | Ficha p. 11: «V001: conglomerado, V022: estrato, peso=V005/1000000» |
| diseno_muestral | CSALUD01 / CSALUD08 | conforme | Ficha p. 11: «peso= PESO15_AMAS/1000000» y «peso= Pesomen12/1000000»; diseño por la unión con RECH0 |
| diseno_muestral | UPM estable HV001 | conforme | Ficha p. 3; HV001 = HV021 en las 37 390 filas de RECH0 |
| universos | nino_hecho | hallazgo H-1 → **resuelto** | Valor HV103 = 1 conforme (`definiciones_endes.yaml:20`, `encuestas.py:146,225-226`); la cita a §5.1 p. 8 no lo respaldaba |
| universos | nino_hecho_hb_medida | conforme | `definiciones_endes.yaml:18,20`; `encuestas.py:150,165,219-220` |
| universos | anemia rm363 / oms2024 | conforme | `definiciones_endes.yaml:15-27`; `encuestas.py:154-155,217-226`; ficha p. 16 |
| universos | nino_dci_0_59m | conforme | `encuestas.py:84-86,157`; `definiciones_endes.yaml:33`; ficha p. 15 |
| territorios | nacional / dominio_subnacional / departamento | conforme | `calculo.py:157-159`; `encuestas.py:141-142`; ficha p. 7 |
| territorios | CALLAO / LIMA_METROPOLITANA / LIMA_REGION | conforme | `ambitos_lima.py:45-47`; Cuadro N° 1 (p. 4), notas 1/ y 2/ |
| perfil_anual | 2024 | conforme | Ficha pp. 3, 4 (3 254 conglomerados), 7 y 10 |
| relacion | 2023–2024 conglomerados_repetidos | conforme | Ficha p. 3 y p. 7 («se mantendrá el 66.7% de muestra de conglomerados de un año a otro») |
| relacion | 2024–2025 independiente | conforme | Ficha p. 7: «Para el año 2025 se deberán seleccionar una nueva muestra maestra»; diseño §7.4 (si la ficha no lo declara, `independiente`) |
| cortes | área, sexo, grupo de edad, región natural, quintil | conforme | Las 13 variables existen en 2024 con la etiqueta citada; ficha p. 7, pp. 13-14 |

Nota del auditor: la historia ubica la etiqueta del estrato en `encuestas.py:142`; está en la 140, y la tabla cita bien la 140.

## Hallazgos

- **H-1 (baja, solo la cita) — resuelto.** `nino_hecho.fuente` citaba la ficha §5.1 p. 8, que excluye a los visitantes que pernoctaron, mientras HV103 = 1 los incluye. Se cambió la cita a la ficha §II p. 2 («…y aquellas que no siendo residentes pernoctaron en la vivienda la noche anterior»), con una nota sobre §5.1. El valor no cambia: reproduce 9 959 y 19 511, las cifras del cubo validado. Tras el cambio, `pap inferencia validar-tablas` sale con 0 y las 34 pruebas de las tablas pasan.

**Hallazgos abiertos: ninguno.**

## Opinión sobre las consultas abiertas

- **C-M0-06-1 (relación 2024–2025): de acuerdo, tipo C.** La ficha declara el panel solo para 2023–2024 y anuncia una muestra maestra nueva para 2025; lo que suponía la historia no se sostiene para 2025.
- **C-M0-06-2 (tramos de edad): de acuerdo, tipo C.** Cambian cifras y n; la ficha solo da los tramos de anemia (p. 16).
- **C-M0-06-3 (región natural): de acuerdo, tipo C.** La ficha dice Costa/Sierra/Selva y el archivo separa Lima metropolitana y Resto Costa.
- **C-M0-06-4 (quintil HV270): de acuerdo, tipo C.** La ficha (p. 14) describe dos versiones y las etiquetas no dicen cuál es.

## Comandos

- `uv run pap inferencia validar-tablas` → 6 tablas, todas con cita, salida 0.
- `uv run pytest -q -p no:cacheprovider tests/inferencia/test_tablas_curadas.py tests/inferencia/test_tablas_curadas_microdatos.py` → `34 passed`.

**Visto del dueño (K-03):** pendiente. Solo condiciona el `verificado` de M0-10.
