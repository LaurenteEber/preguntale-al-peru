# M1-05, tarea 0 — Clase de cada variable del índice

Hecho el 12/11/2026 por el agente (estado de las variables: sigue `propuesto`; la regla y la lista de excepciones las revisa el auditor-agente con M1-06 y el dueño en el lote de M1-07).

## Qué se hizo

Antes, `clase` estaba vacía en 2 770 de las 2 856 variables. Ahora las 2 856 tienen clase. Se clasificó **solo el índice** (`biblioteca/variables/variables.parquet`): no se tocó `curados/inferencia/clases_columnas.yaml` y no se reconvirtió nada.

La regla (`src/pap/inferencia/clases_indice.py`), en este orden:

1. Si la variable está en `clases_columnas.yaml`, se queda con esa clase (86 variables, sin cambio).
2. Si está en la lista curada `curados/inferencia/clases_excepciones.yaml`, esa clase (53 entradas; cada una lleva su motivo).
3. Si es parte de la llave del archivo (`archivos_endes_2024.yaml`), `llave` (14).
4. Por el tipo de valor y el número de categorías:
   - texto → `texto` (14);
   - con etiquetas de valor y **dos o más** categorías con sentido (no «no sabe», «inconsistente»…) → `categoria` (2 028);
   - con etiquetas pero **una sola o ninguna** con sentido → `medida` (349): el número es la medida y las etiquetas marcan sus bordes (edad «97 o más», día «97 = inconsistente»);
   - numérica o fecha sin etiquetas → `medida` (260).

Las excepciones son de tres clases: marcas y unidades de una sola etiqueta que sí son categorías (p. ej. `QS203U`, `V042`, `S476AN1`…), campos de la operación de campo y de la identificación de la encuesta (`ID1`, códigos del equipo de campo, factores `AWFACT*`…) y los identificadores alternos que el documento n.º 11 da como llave (`BORD`, `Q452`, `Q1035NO`).

## Conteo por clase (total) y por tabla

Ver [`m1-05_clases_informe.md`](m1-05_clases_informe.md) (lo escribe `uv run pap variables clasificar --encuesta ENDES --anio 2024 --informe …`).

| Clase | Variables |
|---|---|
| llave | 100 |
| geo | 17 |
| categoria | 1 984 |
| medida | 625 |
| peso | 11 |
| diseno | 105 |
| texto | 14 |
| **Total** | **2 856** |

Las tablas del lote de M1 (19) tienen 2 036 variables `categoria` o `medida` (el 100 % queda con bloque en M1-06); las otras 15 tablas, 573 más.

## Qué no cambió (comprobado)

- Las huellas de los 34 Parquet de microdatos y del manifiesto: **iguales antes y después** (`shasum -a 256` de los 35 archivos de `biblioteca/microdatos/ENDES/2024/`; las 34 `huella_contenido_v1` del manifiesto no cambian porque el manifiesto es el mismo archivo).
- El cubo `biblioteca/indicadores/fact_indicador.parquet` sigue en `010ea965…`.
- `archivos.parquet` y `categorias.parquet`: iguales.
- `variables.parquet`: solo cambia la columna `clase` (2 770 filas, exactamente las que estaban vacías) y se agrega `bloque_id` (M1-06). Comparación columna por columna: [`m1-06_comparar_indice.md`](m1-06_comparar_indice.md).
- `pap variables indexar` (que construye el índice desde los ZIP) ahora llama a la misma regla: la prueba `test_los_archivos_escritos_son_los_del_indice_calculado` (regresión con microdatos) comprueba que reindexar da el mismo `clase` que `pap variables clasificar`.

## Pruebas

- Rojo: `tests/inferencia/test_m105_clases.py` se escribió antes que `clases_indice.py`; la primera corrida falló en la recolección con `ImportError: cannot import name 'clases_indice'`. Después de escribir el módulo, 6 de 13 fallaron por errores del propio test (datos de prueba mal armados, ruta de importación, el comando de ayuda) y por no tener aún el índice real clasificado; se corrigieron y la salida del rojo no se guardó.
- Verde: [`m1-05_clases_verde.txt`](m1-05_clases_verde.txt) (49 pruebas, incluidas las de `test_indice_sintetico.py`); regresión con microdatos: [`m1-06_regresion_microdatos.txt`](m1-06_regresion_microdatos.txt) (101 pasan).
- Dos pruebas existentes se actualizaron porque fijaban el comportamiento anterior: `test_indice_sintetico.py::test_clases_y_grupos_y_tipo_de_valor` (ya no hay variables sin clase) y `test_indice_regresion.py::test_los_archivos_escritos_son_los_del_indice_calculado` (el `variables.parquet` escrito puede traer, además, `bloque_id` y las columnas de M1-04).

## Para quien revise

- Supuestos M1-05-s1 a s3 en `consultas_al_dueno.md`.
- El caso que más se presta a duda es «una sola etiqueta con sentido → medida» (349 variables). Se miraron las 172 que no eran de solo códigos especiales y las que son marcas de sí/no o unidades se pasaron a `categoria` por excepción; las demás son días, meses, años, conteos y edades con un borde etiquetado.

## Ronda de corrección del auditor independiente (12/11/2026)

El auditor dio «con hallazgos abiertos»; se corrigió así (rojo primero: [`m1-06_rojo_auditor.txt`](m1-06_rojo_auditor.txt), 11 pruebas de `tests/inferencia/test_m106_auditor.py` fallando antes del cambio y pasando después, [`m1-06_verde.txt`](m1-06_verde.txt)):

- **Regla nueva:** una categórica con 15 o más valores distintos **sin etiqueta** en el Parquet (solo los bordes 0, 95, 98… están etiquetados) es `medida`. Parámetro `reglas.min_valores_sin_etiqueta: 15` en `clases_excepciones.yaml`; la cuenta se hace con DuckDB en `clases_indice.contar_sin_etiqueta`, tanto en `pap variables clasificar` como al reindexar. Corrigió **56** variables que eran `categoria`: 47 de las 49 que listó el auditor (las otras dos, `HV246B` y `HV246F`, por excepción; las 49 quedan `medida`, comprobadas una por una) y 9 más (7 `QS212*` de CSALUD01, `D109` de REC84DV y `HC60` de RECH6, que luego pasó a `llave`).
- **Excepciones equivocadas, quitadas:** `QS212*B/V` (16, cantidades de 0 a 30) y `S476AN1–7` (conteos 0–7); ahora salen `medida` por la regla. `HV246B` y `HV246F` (cantidades de ganado con menos de 15 valores) quedan `medida` por excepción para que las diez `HV246A–J` sean iguales.
- **Llaves:** `QSNUMERO` (CSALUD01), `V003`, `HV002`, `HV002A`, `HV003` y todas las **líneas de personas** (HC60, HC51, HA51, HW51, HV112, HV114, HV218, V034, V452B, QS800, B16, PS1 a PS6). Solo el índice: la llave declarada de `CSALUD01` no se cambió (consulta C-M1-06-1).
- **Geografía y campo:** `geo` para coordenadas, provincia y distrito, y tipo y lugar de residencia (V102, V140, V141, V026, HV026); `diseno` para lo que define la muestra (HV023, V023, V101, V139, HV004, V004), para año y fecha de entrevista o medición (HV007, HV008, V007, V008, HC19, HW19, BAA, QSINTY), la operación de campo (HV030 a HV033) y `QHHOME`/`QHNUMBER` iguales en todas las tablas. `QH25A` sigue `texto`: es una lista de gentilicios («PERUANA», «VENEZOLANA»…), no un código.
- **Conteo por clase** (total): llave 100, geo 17, categoria 1 984, medida 625, peso 11, diseno 105, texto 14 = 2 856. Por tabla: [`m1-05_clases_informe.md`](m1-05_clases_informe.md).
- `variables.parquet` otra vez: solo `clase` (140 filas respecto de la primera ronda) y `bloque_id` (54) cambian; ver [`m1-06_comparar_indice.md`](m1-06_comparar_indice.md), segunda comparación.
