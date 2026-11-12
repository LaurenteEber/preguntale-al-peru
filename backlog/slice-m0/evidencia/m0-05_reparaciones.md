# M0-05 — Reparaciones de etiquetas (`etiqueta_original` → `etiqueta_curada`)

De 2,856 etiquetas de variable y 7,602 de categoría, **200 cambian al curarse** (127 de variable y 73 de categoría). **Ninguna es mojibake**: las 200 son solo espacios (dobles, iniciales o duros U+00A0); `ftfy` no encontró texto mal decodificado en los 34 DTA de 2024 (son DTA formato 118, UTF-8), no apareció cp850 («Ni¤o») y el control `mojibake_sin_reparar` da 0. Por eso las «primeras 50 reparaciones» son, todas, de espacios. Desglose: espacios dobles: 146; espacio inicial: 53; espacio duro, espacio inicial: 1.

Se conservan `etiqueta_original` y `etiqueta_curada`; se corrió con `ftfy` 6.3.1 (sin deshacer comillas tipográficas ni entidades HTML) + NFC + espacios simples. Marcas: `··` = dos espacios seguidos; `⍽` = espacio duro. Revisadas a mano el 9/11/2026 (agente); el criterio es que la curada diga lo mismo que la original, sin cambiar ni una palabra.

| # | Dónde | Original | Curada | Juicio |
|--:|---|---|---|---|
| 1 | `CSALUD01·QS200` | En los··últimos 12 meses ha fumado cigarrillos | En los últimos 12 meses ha fumado cigarrillos | Correcta: solo quita espacios; no cambia palabras |
| 2 | `CSALUD01·QS207C` | Cantidad··Edad primera vez que tomo bebidas alcohólicas | Cantidad Edad primera vez que tomo bebidas alcohólicas | Correcta: solo quita espacios; no cambia palabras |
| 3 | `CSALUD01·QS413` | Recogió o llegó a··conocer los resultados de la prueba de Papanicolaou | Recogió o llegó a conocer los resultados de la prueba de Papanicolaou | Correcta: solo quita espacios; no cambia palabras |
| 4 | `CSALUD01·QS700A` | Últimos 14 días ha sentido molestias o problemas como:··Poco interés | Últimos 14 días ha sentido molestias o problemas como: Poco interés | Correcta: solo quita espacios; no cambia palabras |
| 5 | `CSALUD01·QS708_AA` | ¿Dónde recibió tratamiento? -··Hospital Psiquiátrico | ¿Dónde recibió tratamiento? - Hospital Psiquiátrico | Correcta: solo quita espacios; no cambia palabras |
| 6 | `CSALUD01·QS708_AB` | ¿Dónde recibió tratamiento? -··Instituto Nacional de Salud Mental | ¿Dónde recibió tratamiento? - Instituto Nacional de Salud Mental | Correcta: solo quita espacios; no cambia palabras |
| 7 | `CSALUD01·QS708_D` | ¿Dónde recibió tratamiento? -··Hospital/ Otro Municipal | ¿Dónde recibió tratamiento? - Hospital/ Otro Municipal | Correcta: solo quita espacios; no cambia palabras |
| 8 | `CSALUD01·QS708_E` | ¿Dónde recibió tratamiento? -··Centro/ Puesto del MINSA | ¿Dónde recibió tratamiento? - Centro/ Puesto del MINSA | Correcta: solo quita espacios; no cambia palabras |
| 9 | `CSALUD01·QS708_EA` | ¿Dónde recibió tratamiento? -··Centro de Salud Mental Comunitaria | ¿Dónde recibió tratamiento? - Centro de Salud Mental Comunitaria | Correcta: solo quita espacios; no cambia palabras |
| 10 | `CSALUD01·QS708_F` | ¿Dónde recibió tratamiento? -··Policlínico/ Posta de ESSALUD/ UBAP | ¿Dónde recibió tratamiento? - Policlínico/ Posta de ESSALUD/ UBAP | Correcta: solo quita espacios; no cambia palabras |
| 11 | `CSALUD01·QS708_G` | ¿Dónde recibió tratamiento? -··Clínica Particular | ¿Dónde recibió tratamiento? - Clínica Particular | Correcta: solo quita espacios; no cambia palabras |
| 12 | `CSALUD01·QS708_H` | ¿Dónde recibió tratamiento? -··Consultorio Particular | ¿Dónde recibió tratamiento? - Consultorio Particular | Correcta: solo quita espacios; no cambia palabras |
| 13 | `CSALUD01·QS708_I` | ¿Dónde recibió tratamiento? -··Clínica/ Posta de ONG | ¿Dónde recibió tratamiento? - Clínica/ Posta de ONG | Correcta: solo quita espacios; no cambia palabras |
| 14 | `CSALUD01·QS708_X` | ¿Dónde recibió tratamiento? -··Otro | ¿Dónde recibió tratamiento? - Otro | Correcta: solo quita espacios; no cambia palabras |
| 15 | `CSALUD01·QS708_Y` | ¿Dónde recibió tratamiento? -··No Sabe/No Recuerda | ¿Dónde recibió tratamiento? - No Sabe/No Recuerda | Correcta: solo quita espacios; no cambia palabras |
| 16 | `CSALUD01·QS731_AA` | ¿Dónde recibió tratamiento? -··Hospital Psiquiátrico | ¿Dónde recibió tratamiento? - Hospital Psiquiátrico | Correcta: solo quita espacios; no cambia palabras |
| 17 | `CSALUD01·QS731_AB` | ¿Dónde recibió tratamiento? -··Instituto Nacional de Salud Mental | ¿Dónde recibió tratamiento? - Instituto Nacional de Salud Mental | Correcta: solo quita espacios; no cambia palabras |
| 18 | `CSALUD01·QS731_D` | ¿Dónde recibió tratamiento? -··Hospital/ Otro Municipal | ¿Dónde recibió tratamiento? - Hospital/ Otro Municipal | Correcta: solo quita espacios; no cambia palabras |
| 19 | `CSALUD01·QS731_E` | ¿Dónde recibió tratamiento? -··Centro/ Puesto del MINSA | ¿Dónde recibió tratamiento? - Centro/ Puesto del MINSA | Correcta: solo quita espacios; no cambia palabras |
| 20 | `CSALUD01·QS731_EA` | ¿Dónde recibió tratamiento? -··Centro de Salud Mental Comunitaria | ¿Dónde recibió tratamiento? - Centro de Salud Mental Comunitaria | Correcta: solo quita espacios; no cambia palabras |
| 21 | `CSALUD01·QS731_F` | ¿Dónde recibió tratamiento? -··Policlínico/ Posta de ESSALUD/ UBAP | ¿Dónde recibió tratamiento? - Policlínico/ Posta de ESSALUD/ UBAP | Correcta: solo quita espacios; no cambia palabras |
| 22 | `CSALUD01·QS731_G` | ¿Dónde recibió tratamiento? -··Clínica Particular | ¿Dónde recibió tratamiento? - Clínica Particular | Correcta: solo quita espacios; no cambia palabras |
| 23 | `CSALUD01·QS731_H` | ¿Dónde recibió tratamiento? -··Consultorio Particular | ¿Dónde recibió tratamiento? - Consultorio Particular | Correcta: solo quita espacios; no cambia palabras |
| 24 | `CSALUD01·QS731_I` | ¿Dónde recibió tratamiento? -··Clínica/ Posta de ONG | ¿Dónde recibió tratamiento? - Clínica/ Posta de ONG | Correcta: solo quita espacios; no cambia palabras |
| 25 | `CSALUD01·QS731_X` | ¿Dónde recibió tratamiento? -··Otro | ¿Dónde recibió tratamiento? - Otro | Correcta: solo quita espacios; no cambia palabras |
| 26 | `CSALUD01·QS731_Y` | ¿Dónde recibió tratamiento? -··No Sabe/No Recuerda | ¿Dónde recibió tratamiento? - No Sabe/No Recuerda | Correcta: solo quita espacios; no cambia palabras |
| 27 | `DIT·QI478I3` |  Ella (él) juega a ser un personaje de televisión, o de cuentos como superhéroes | Ella (él) juega a ser un personaje de televisión, o de cuentos como superhéroes | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 28 | `DIT·QI478I5` | Ella (él) Llora, grita o hace pataletas··la mayor parte del tiempo | Ella (él) Llora, grita o hace pataletas la mayor parte del tiempo | Correcta: solo quita espacios; no cambia palabras |
| 29 | `RE223132·V395` | En el centro de salud, se le informó acerca de métodos··planificación familiar | En el centro de salud, se le informó acerca de métodos planificación familiar | Correcta: solo quita espacios; no cambia palabras |
| 30 | `RE223132·V3A04` | ··Le dijeron qué hacer si llegaba a experimentar efectos secundarios con ese mét | Le dijeron qué hacer si llegaba a experimentar efectos secundarios con ese mét | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 31 | `RE223132·V3A09B` | Cuantos Condónes obtuvo··la última vez | Cuantos Condónes obtuvo la última vez | Correcta: solo quita espacios; no cambia palabras |
| 32 | `RE516171·V732` | Usualmente trabaja··todo el año/por temporada o sólo de vez en cuado | Usualmente trabaja todo el año/por temporada o sólo de vez en cuado | Correcta: solo quita espacios; no cambia palabras |
| 33 | `REC0111·V134` | El lugar en el que se realizó la entrevista··De-facto | El lugar en el que se realizó la entrevista De-facto | Correcta: solo quita espacios; no cambia palabras |
| 34 | `REC41·M19` | Peso del niño al nacer··(kilos - 3 dec.) | Peso del niño al nacer (kilos - 3 dec.) | Correcta: solo quita espacios; no cambia palabras |
| 35 | `REC41·M1A` | Antes del embarazo cuantas dosis de la vacuna contra el··tétano recibió | Antes del embarazo cuantas dosis de la vacuna contra el tétano recibió | Correcta: solo quita espacios; no cambia palabras |
| 36 | `REC43·H37L` | Tomó··Acetaminofeno para fiebre/tos | Tomó Acetaminofeno para fiebre/tos | Correcta: solo quita espacios; no cambia palabras |
| 37 | `REC43·H37M` | Tomó··Ibuprofeno para la fiebre/tos | Tomó Ibuprofeno para la fiebre/tos | Correcta: solo quita espacios; no cambia palabras |
| 38 | `REC43·H37N` | Tomó··remedio casero para fiebre/tos | Tomó remedio casero para fiebre/tos | Correcta: solo quita espacios; no cambia palabras |
| 39 | `REC43·H39` | Le dió usted la misma cantidad de comida que antes de la diarrea, le dio··màs o | Le dió usted la misma cantidad de comida que antes de la diarrea, le dio màs o | Correcta: solo quita espacios; no cambia palabras; queda la errata de acento grave del INEI (marcada `etiqueta_acento_grave`) |
| 40 | `REC44·HW56` | Nivel de hemoglobina ajustada por altitud en··g/dl - 1 decimal RM 363-2022-MINSA | Nivel de hemoglobina ajustada por altitud en g/dl - 1 decimal RM 363-2022-MINSA | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 41 | `REC44·HW56A` | Nivel de hemoglobina ajustada por altitud en··g/dl - 1 decimal NUEVA DIRECTRIZ O | Nivel de hemoglobina ajustada por altitud en g/dl - 1 decimal NUEVA DIRECTRIZ O | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 42 | `REC84DV·D103D` | Su esposo/compañero la··ha amenzado con irse de casa, quitarle a las hijas e hij | Su esposo/compañero la ha amenzado con irse de casa, quitarle a las hijas e hij | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 43 | `REC84DV·D110C` | A causa de su esposo/compañero alguna vez··tuvo que ir al médico o centro de sal | A causa de su esposo/compañero alguna vez tuvo que ir al médico o centro de sal | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 44 | `REC84DV·D110D` | A causa de su esposo/compañero alguna vez··tuvo una herida, hueso roto, y diente | A causa de su esposo/compañero alguna vez tuvo una herida, hueso roto, y diente | Correcta: solo quita espacios; no cambia palabras; etiqueta cortada por Stata a 80 caracteres (marcada) |
| 45 | `REC84DV·D112A` | Con qué frecuencia lastimó físicamente a su esposo/compañero··en los últimos 12 | Con qué frecuencia lastimó físicamente a su esposo/compañero en los últimos 12 | Correcta: solo quita espacios; no cambia palabras |
| 46 | `REC84DV·D115B` | Desde cuando tenía 15 años de edad fue maltratada··físicamente por: madre | Desde cuando tenía 15 años de edad fue maltratada físicamente por: madre | Correcta: solo quita espacios; no cambia palabras |
| 47 | `REC84DV·D115C` | Desde cuando tenía 15 años de edad fue maltratada··físicamente por: padre | Desde cuando tenía 15 años de edad fue maltratada físicamente por: padre | Correcta: solo quita espacios; no cambia palabras |
| 48 | `REC84DV·D115D` | Desde cuando tenía 15 años de edad fue maltratada··físicamente por: hija | Desde cuando tenía 15 años de edad fue maltratada físicamente por: hija | Correcta: solo quita espacios; no cambia palabras |
| 49 | `REC84DV·D115E` | Desde cuando tenía 15 años de edad fue maltratada··físicamente por: hijo | Desde cuando tenía 15 años de edad fue maltratada físicamente por: hijo | Correcta: solo quita espacios; no cambia palabras |
| 50 | `REC84DV·D115F` | Desde cuando tenía 15 años de edad fue maltratada··físicamente por: hermana | Desde cuando tenía 15 años de edad fue maltratada físicamente por: hermana | Correcta: solo quita espacios; no cambia palabras |

**Resultado de la revisión:** las 50 son correctas. Ninguna toca una palabra, una cifra ni un signo. Observación fuera de alcance: la errata «amenzado» (D103D), «cuado» (V732) y las etiquetas cortadas a 80 caracteres no se corrigen aquí (no son mojibake; las ve M1 con el cuestionario).
