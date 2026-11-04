#!/usr/bin/env bash
# S2-00: base de la vía estructurada. Uso (desde la raíz): bash backlog/slice-2/evidencia/base_estructurada/generar.sh <carpeta>
# Cada línea es el comando exacto; las respuestas van a <carpeta>/<nn>/.
set -u
O="${1:?carpeta de salida}"
P="uv run pap preguntar"
$P curados/motor/consultas_minimas/ --salida "$O/00_q1_q4"
$P --intencion nivel_actual --tema anemia --territorio "departamento de Puno" --salida "$O/01_nivel_actual"
$P --intencion evolucion --tema anemia --territorio "Perú" --salida "$O/02_evolucion"
$P --intencion comparacion --tema pobreza --territorio "Cusco" --comparar-con "Puno" --elegir 1,1 --salida "$O/03_comparacion"
$P --intencion cruce --tema gasto --territorio "departamento de Puno" --salida "$O/04_cruce"
$P --intencion identificar_extremo --tema anemia --nivel departamento --salida "$O/05_identificar_extremo"
$P --intencion efecto --tema anemia --territorio "departamento de Puno" --salida "$O/06_efecto"
$P --intencion nivel_actual --tema anemia --territorio "Huancavelica" --elegir 2 --salida "$O/07_homonimo"
$P --intencion nivel_actual --tema anemia --territorio "Lima" --elegir 1 --salida "$O/08_lima"
$P --intencion comparacion --tema anemia --territorio "Lima Metropolitana" --comparar-con "Lima Región" --salida "$O/09_comparacion_lima"
$P --intencion nivel_actual --tema desnutrición --territorio "Ayaviri, Melgar" --salida "$O/10_no_se_puede"
$P --intencion evolucion --tema gasto --territorio "Perú" --salida "$O/11_evolucion_gasto"
$P --intencion nivel_actual --tema anemia --territorio "Ayaviri, Melgar" --salida "$O/12_sien_distrito"
