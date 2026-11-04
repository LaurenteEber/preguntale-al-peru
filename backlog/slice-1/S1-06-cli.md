# S1-06 — CLI `pap preguntar` con consulta mínima

## Tareas

1. `pap preguntar` acepta, además de los `q*.yaml` actuales:
   - un archivo JSON de consulta mínima (o varios, o una carpeta);
   - opciones directas: `--intencion`, `--tema` (acepta los alias de `temas.alias_cli`) o `--indicador`, `--territorio "<texto>"`, `--anio` o `--desde/--hasta`, `--comparar-con "<texto>"`.
2. Si hay aclaración: la imprime con sus opciones numeradas (en el orden de `territorio.aclaracion_orden`), no escribe respuesta y sale con el código de `cli.codigo_salida.aclaracion`. `--elegir <n>` (solo un número) permite responderla sin modo interactivo (para pruebas).
3. Salida igual que hoy (`respuesta.json` y `.md` por capas) en la carpeta de `--salida` (por defecto `cli.salida_por_defecto`, fuera de git: agregarla a `.gitignore`). Hoy la salida está fija en `00_proyecto/piloto/p3/respuestas`, que está en git y la matriz la sobrescribiría. El JSON incluye la consulta mínima, el plan generado y la versión de la biblioteca. Si el periodo no viene, se usa `periodo.por_intencion` (con `--intencion evolucion` es una serie).
4. `--plan` imprime solo el plan (sin calcular) para depurar.
5. Pruebas de la CLI con `CliRunner` o subproceso.

## Criterios de aceptación

- [ ] `uv run pap preguntar --intencion evolucion --tema anemia --territorio Huancavelica` pide aclarar el nivel (homónimo departamento, provincia y distrito) y la primera opción es el departamento (`aclaracion_orden`); con `--elegir 1` responde como Q1.
- [ ] `uv run pap preguntar curados/motor/consultas_minimas/` responde Q1–Q4.
- [ ] Los `q*.yaml` antiguos siguen funcionando hasta S1-10 (luego se archivan).
- [ ] `--help` explica cada opción en español.
