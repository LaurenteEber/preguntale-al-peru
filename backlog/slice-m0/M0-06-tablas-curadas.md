# M0-06 — Tablas curadas de 2024

**Se deriva de** el diseño §7.4 y anexo A, y de E-01, E-02, E-07 y P-06, esta última editada en M0-01: revisa el auditor-agente y el dueño da el visto por lote.

## Tareas

1. **`curados/inferencia/diseno_muestral.csv`:** las filas de la ENDES 2024 (hogar, individual, salud y mediciones), cada una con su cita.
   - **Peso:** `HV005/1e6` para hogar y mediciones de 2024, `V005/1e6` para el cuestionario individual, y el del cuestionario de salud.
   - **Estrato:** la misma etiqueta que el código actual, `printf('%02d-%d', HV024, HV022)` (`encuestas.py:142`).
   - **UPM:** **HV021** (`definiciones_endes.yaml:10`, `encuestas.py:139`).
   - **UPM estable:** la que declare la ficha técnica 2024. Si es HV001, se agrega una prueba que muestre si HV001 = HV021 en 2024.
   - **Otras columnas:** `peso_normalizado = sí`, `nivel_submuestra` y `uniones_para_diseno`.
2. **`curados/inferencia/universos_analiticos.yaml`:** los universos de las recetas, con las líneas exactas de `definiciones_endes.yaml` y `encuestas.py`:
   - población de hecho (HV103);
   - edad (HC1);
   - anemia: HC57 o HC57A en 1–4;
   - DCI: HC70 válido entre −9989 y 9989.
3. **`curados/inferencia/territorios.yaml`:** los niveles de la ENDES, igual que hoy (`ambitos_lima.py:60-72`, `calculo.py:157-160`, `dim_indicador.niveles_validos`):
   - `nacional`;
   - `dominio_subnacional` (HV025 urbano o rural);
   - `departamento` (HV024 sin el 07);
   - `CALLAO` (HV024 = 7);
   - `LIMA_METROPOLITANA` (provincia de UBIGEO = 1501);
   - `LIMA_REGION` (HV024 = 15 y fuera de 1501).

   Todos como dominio. Con estas definiciones salen las 30 unidades por indicador.
4. **`curados/inferencia/perfil_anual.csv`:** la fila de 2024 (estratos, UPM, modo, meses, `ubigeo_minimo` y cita).
5. **`curados/inferencia/relacion_entre_anios.csv`:** la fila 2024–2025 (`conglomerados_repetidos`; la ficha declara panel el 66,7 % de los conglomerados por HV001), con su cita. Solo se prueba con el sintético, porque en M0 no hay microdatos de 2025.
6. **`curados/inferencia/cortes_estandar.yaml`:** área, sexo, grupo de edad, región natural y quintil de riqueza, con su variable por archivo.
7. **Esquemas** (pydantic) de las 6 tablas y comando `pap inferencia validar-tablas`.
8. **Revisión:**
   - el auditor-agente revisa cada fila contra la ficha y `definiciones_endes.yaml` → `evidencia/m0-06_revision.md`;
   - el dueño da el visto al lote (K-03). M0-07 puede avanzar sin el visto; el visto solo condiciona el `verificado` de M0-10.

## Criterios de aceptación

- [ ] Las 6 tablas validan contra su esquema y cada fila tiene su cita.
- [ ] Revisión del auditor-agente sin hallazgos abiertos.
- [ ] Prueba: el universo de las recetas, aplicado a los Parquet de 2024, da **9 959** casos (anemia, los dos criterios) y **19 511** (DCI) sobre 20 290 niños, igual que `endes_nino.parquet` y que el `n_muestra` nacional del cubo.
- [ ] Prueba: `territorios.yaml` produce las 30 unidades por indicador.

## Fuera

Otros años (M2) y la ENAHO (M3).
