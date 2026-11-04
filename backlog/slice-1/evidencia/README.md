# Evidencia del slice 1

Lo que prueba cada criterio de aceptación. Nombres sugeridos:

| Historia | Archivo |
|---|---|
| S1-00 | `pytest_base.txt` (línea de base antes de empezar), `s1-00_comparacion_cubo.txt` (cubo y gasto antes y después; solo cambian nombres), `s1-00_datos_territorio.txt` (alternos de 060506, homónimos más frecuentes, distritos sin SIEN) |
| S1-07 | `regresion/Q1.yaml … Q4.yaml`: cada diferencia de texto aprobada (`capa`, `antes`, `despues`, `motivo`, `aprobado_por`; formato en la historia) |
| S1-08 | `matriz.md` (reporte completo de la matriz de cobertura) |
| S1-09 | `encargo_s1-09_<rol>.md` (auditor, revisor, verificador), `auditoria_estadistica.md`, `revision_usuario.md`, `verificacion_correcciones.md` |
| S1-10 | `cierre.md` |

Salidas de `pytest` o de la CLI: como `.txt`, con la fecha y el commit en la primera línea.
