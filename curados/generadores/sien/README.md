# Validación del SIEN contra la publicación oficial del INS

> Registro de la validación del 12/10/2026, traído al repositorio con sus scripts. Uso desde la raíz: `python curados/generadores/sien/generar_doradas_sien.py <xlsx> <salida.csv>` y `python curados/generadores/sien/comparar_distritos.py <xlsx> <salida.csv>`. El XLSX es el recurso `indicadores-ninos-2025-diciembre` de `INS-CENAN-SIEN` (en el almacén).

12/10/2026 · rama `doradas-sien` · indicador `sien_anemia_tamizados_6_35m` (anemia 6–35 m, OMS 2024, 2025).

## Por qué

La auditoría del piloto (12/10) señaló que el SIEN es la cifra principal a nivel distrito (Q2, Q3) y era el único indicador del piloto sin doradas. Además da valores muy por debajo de la ENDES (nacional 14,2 % frente a 34,9 %). Había que saber si eso era un error nuestro o una característica de la fuente.

## Fuentes oficiales (registradas en `INS-CENAN-SIEN`)

| Recurso | Documento | Huella |
|---|---|---|
| `informe-gerencial-ninos-2025` | INS/CENAN, *Informe Gerencial SIEN-HIS Niños 2025* (PDF, 38 págs., 29/4/2026) | `sha256:ea743cdbc496…` |
| `indicadores-ninos-2025-diciembre` | INS/CENAN, *Indicadores Niños – diciembre 2025 (Base de Datos HIS-Minsa)*, periodo enero a diciembre 2025 (XLSX) | `sha256:dd33bf36ba36…` |

Las dos se bajaron de gob.pe (compendio «Informes de Vigilancia del SIEN en establecimientos de salud»); la receta acepta ahora `pdf`.

## Resultado

| Nivel | Comparación | Resultado |
|---|---|---|
| Nacional | numerador y denominador | **idénticos**: 107 834 / 759 314 = 14,2 % |
| 24 departamentos + Callao | numerador y denominador (Cuadro N.º 11) | **25/25 idénticos** (incluye Lima como departamento 15 entero) |
| Lima Región | «LIMA REGION» (Cuadro 14) = «LIMA PROVINCIAS» (Tabla 8.18) | idéntico: 3 791 / 27 077 |
| Lima Metropolitana | suma de las 4 DIRIS (Cuadro 14) | idéntica: 14 920 / 129 303 (cifra derivada: solo control) |
| Distritos (Cuadro N.º 15) | 1 837 filas del INS | **1 789 idénticos (97 %)**; Ayaviri 52/547 y San Juan de Lurigancho 1 621/19 750, idénticos |
| PDF frente al XLSX | Tabla 8.18, p. 36 | las 26 filas comunes coinciden |

**Diferencias en distritos (no bloquean):** 48 distritos con conteos distintos y 50 que solo están en el cubo (3 598 evaluados, mediana 4). Se explican porque ubicamos cada establecimiento con el ubigeo de RENIPRESS y la geografía vigente (distritos creados después de 2017; corrección de SP-03 y GA-09), mientras el INS usa el ubigeo del HIS. Además, la tabla distrital del INS no suma su propio total nacional (759 205 frente a 759 314) y repite 2 ubigeos. Los totales por departamento son idénticos, así que solo cambia la asignación dentro de cada departamento. Detalle: `comparacion_distritos.csv`.

## Lo que confirma el INS

- **Unidad = el último control del año.** El INS trabaja con «la atención más reciente de cada niño si acudió más de una vez» (Informe Gerencial 2025, p. 13). Se elimina el «supuesto pendiente de confirmar» de `dim_indicador`.
- **No es comparable con la ENDES.** «Los resultados corresponden a población usuaria de establecimientos de salud del MINSA, por lo que no son estrictamente comparables con estimaciones poblacionales como ENDES» (p. 9).
- **Puede subestimar.** «El 72,3 % de los niños atendidos … contaron con evaluación de hemoglobina … lo que podría subestimar la prevalencia real de anemia» (p. 14).

**Conclusión:** el cálculo es correcto; la distancia con la ENDES es de la fuente, no un error. Lo que falla es cómo se comunica (ver la revisión de usuario).

## Cambios (rama `doradas-sien`)

- `cifras_doradas.csv`: +30 doradas `DOR-SIEN-2025-*` (29 bloqueantes; Lima Metropolitana como control). `tipo_cita = oficial_ins`, `proposito = control_registro`, tolerancia 0 y número de evaluados exacto. Generadas con `generar_doradas_sien.py` desde el XLSX, sin transcripción a mano.
- `pap construir indicadores`: DOR-04 acepta `oficial_ins` y `control_registro`.
- `pap calcular`: nueva prueba bloqueante **CAL-10** (el SIEN reproduce las cifras del INS). Cubo `8e0bb0d4…`: solo cambian `validada_dorada` e `indicador_validado` del SIEN.
- Ficha: el contraste oficial nombra a la entidad («El INS publica 9,5 % … Nuestra cifra coincide.»). Q2 y Q3 lo muestran; Q1 y Q4 no cambian.
- Pruebas: `test_doradas_sien_ins`, `test_sien_contraste_oficial_ins`; 89 doradas bloqueantes.
