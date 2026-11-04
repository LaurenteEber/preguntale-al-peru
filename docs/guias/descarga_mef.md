# Guía: descargar y registrar los archivos del MEF (gasto e inversiones)

Pendiente de S3 (6/10/2026). El portal fs.datosabiertos.mef.gob.pe tiene el **certificado de seguridad vencido**:
Chrome muestra «Error de privacidad» y la extensión de Claude no puede aceptarlo por ti.

## 1. Descargar (desde tu Chrome)

| Archivo | Enlace | Tamaño aprox. | Carpeta de destino |
|---|---|---|---|
| Gasto 2023 | https://fs.datosabiertos.mef.gob.pe/datastorefiles/2023-Gasto.csv | 1–3 GB | `biblioteca/cruda/bandeja/MEF-DA-PRESUPUESTO-EJECUCION-GASTO/` |
| Gasto 2024 | https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto.csv | 1–3 GB | ídem |
| Gasto 2025 | https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Mensual.csv | 1–3 GB | ídem |
| Diccionario | https://fs.datosabiertos.mef.gob.pe/datastorefiles/Gastos_Diccionario.csv | < 1 MB | ídem |
| Detalle de inversiones | https://fs.datosabiertos.mef.gob.pe/datastorefiles/DETALLE_INVERSIONES.csv | cientos de MB | `biblioteca/cruda/bandeja/MEF-DETALLE-INVERSIONES/` |

- En 2025 usa **solo** `-Gasto-Mensual.csv`; nunca el `-Diario` (R-GASTO-04: sumarlos duplica).
- Al abrir el primer enlace: «Configuración avanzada» → «Acceder a fs.datosabiertos.mef.gob.pe (sitio no seguro)».
  Si prefieres no hacerlo, espera a que el MEF renueve el certificado (reintenta abriendo el diccionario).
- Atajo: acepta la advertencia una vez y avísame; con eso yo hago las descargas con tu Chrome.

## 2. Registrar (en la carpeta del proyecto)

```bash
cd ~/Documents/SideProjects/pregunta-al-peru
B=biblioteca/cruda/bandeja
U=https://fs.datosabiertos.mef.gob.pe/datastorefiles
NOTA="Descargado con el certificado HTTPS del MEF vencido; integridad verificada por conciliación con Consulta Amigable"
for f in 2023-Gasto.csv 2024-Gasto.csv 2025-Gasto-Mensual.csv Gastos_Diccionario.csv; do
  uv run pap registrar MEF-DA-PRESUPUESTO-EJECUCION-GASTO "$B/MEF-DA-PRESUPUESTO-EJECUCION-GASTO/$f" --url-descarga "$U/$f" --nota "$NOTA"
done
uv run pap registrar MEF-DETALLE-INVERSIONES "$B/MEF-DETALLE-INVERSIONES/DETALLE_INVERSIONES.csv" --url-descarga "$U/DETALLE_INVERSIONES.csv" --nota "$NOTA"
uv run pap verificar --rapido
git add biblioteca/cruda/capturas biblioteca/cruda/verificaciones.jsonl && git commit -m "Registro de gasto MEF 2023-2025 e inversiones"
```

Los originales quedan en el almacén; después puedes borrar los de la bandeja y de Descargas.

## 3. Avisarme

Dime «sigamos con el gasto de S3». Construyo `dim_unidad_ejecutora` (con el Gobierno Regional de Lima → Lima Región),
`dim_tema_gasto` (PP 0001 → 1001), `dim_inversion_ubicacion` y la atribución territorial con la prueba de conservación
(R-GASTO-01: la suma por niveles = total nacional del archivo, tolerancia 0), más la conciliación con la Consulta Amigable
(R-GASTO-04, ≤ 0,5 %).
