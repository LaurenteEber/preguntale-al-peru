# M1-02 — Deuda de M0

Se completa a medida que avanzan las tareas.

## Tarea 3 — H05-1: `reparar_dos` (12/11/2026)

- **Qué pasaba:** `reparar_dos` releía todo el texto como cp850 cuando encontraba ¤ ¥ ¢ £. Así arreglaba «Ni¤o», pero estropeaba otros signos: `¿Ni¤o?` salía `┐Niño?`. El control de mojibake no veía el `┐`.
- **Qué se hizo** (`src/pap/inferencia/indice.py`):
  - se cambia **cada carácter de DOS pegado a una letra** por la letra que representa (¤→ñ, ¥→Ñ, ¢→ó, £→ú, ‚→é; ¡→í solo detrás de una letra, porque delante de una palabra es el signo de exclamación); el resto del texto no se toca;
  - se mantiene la entrada de antes: solo se repara si el texto trae alguno de ¤ ¥ ¢ £, no trae vocales con tilde bien escritas y se puede escribir en cp1252;
  - el control de mojibake ve también los dibujos de caja (U+2500 a U+259F) que deja una relectura cp850.
- **Pruebas** (`tests/inferencia/test_indice_sintetico.py`): `test_reparar_dos_no_corrompe_signos_del_espanol_ni_otros_caracteres_H05_1` y `test_control_de_mojibake_ve_los_dibujos_de_caja_de_una_relectura_cp850_H05_1`. Fallaban antes del cambio y pasan después.
- **El índice de 2024 no cambia:** las 4 263 etiquetas distintas de `biblioteca/variables/*.parquet` dan la misma `etiqueta_curada`, los mismos arreglos y el mismo resultado del control con el código anterior y con el nuevo (0 diferencias).
- **Suite completa:** 1 820 pasan y 1 se salta (la base del slice: 1 818 y 1; las 2 nuevas son estas).
